"""Transact — the core operation.

Math §4.1 + ARCHITECTURE §16.3. Steps in order:

1. Validate parties exist, are not frozen, are distinct.
2. Compute confidence(τ) and reject if below θ_min.
3. Determine credit portion ``N_credit = max(0, amount − max(0, b_receiver))``.
4. Check the credit limit ``b - N ≥ -L(r)`` for the receiver.
5. **Auto-repay actor's open loans (FIFO)** from incoming amount.
   Released escrow is distributed across all members by turnover share.
6. Move balances:
     receiver.balance -= amount
     actor.balance    += residual_after_repayment
7. If N_credit > 0, open a Loan and reserve ε(t)·N_credit in escrow.
8. Increment turnover and reputation for both parties.
9. Append a TransactionRecord to history.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from decimal import Decimal

from app.domain.entities import (
    ClubState,
    DistributionEscrow,
    Loan,
    Member,
    TransactionRecord,
)
from app.domain.events import (
    DomainEvent,
    EscrowReleased,
    LoanOpened,
    LoanRepaid,
    TransactionConfirmed,
)
from app.domain.operations.base import (
    Command,
    ErrorCode,
    OperationError,
    OperationResult,
)
from app.domain.operations.commands import TransactCommand
from app.domain.services.auto_score import AutoScoreCalculator
from app.domain.services.confidence import ConfidenceCalculator
from app.domain.services.credit_limit import CreditLimitService
from app.domain.services.distribution import DistributionService
from app.domain.services.epsilon import EpsilonCalculator
from app.domain.services.reputation_delta import ReputationDeltaService
from app.domain.value_objects import (
    Confidence,
    LoanId,
    LoanState,
    MemberId,
    V,
    new_loan_id,
    new_transaction_id,
)


class TransactOperation:
    """Settle a transaction between actor and receiver."""

    def __init__(self, observed_default_rate: Decimal = Decimal(0)) -> None:
        self._observed_default_rate = observed_default_rate

    def execute(self, state: ClubState, command: Command) -> OperationResult:
        assert isinstance(command, TransactCommand)

        guard_error = _validate(state, command)
        if guard_error is not None:
            return OperationResult.fail(state, guard_error)

        actor = state.members[command.actor]
        receiver = state.members[command.receiver]
        confidence = _confidence(state, command)
        if confidence < state.parameters.theta_min:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.CONFIDENCE_TOO_LOW,
                    message=(
                        f"confidence {confidence.root} below θ_min "
                        f"{state.parameters.theta_min.root}"
                    ),
                ),
            )

        n_credit = _credit_portion(receiver, command.amount)
        post_balance_receiver = receiver.balance - command.amount
        if not _within_credit_limit(state, receiver, post_balance_receiver):
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.CREDIT_LIMIT_EXCEEDED,
                    message=f"receiver post-balance {post_balance_receiver} below limit",
                ),
            )

        # v2 currency board (improvements/01): when η > 0, credit emission is
        # capped by the revenue-backed budget. A transaction that needs more
        # fresh credit than the budget allows is refused, so supply growth
        # cannot outrun realised revenue.
        if state.parameters.emission_budget_share > 0 and n_credit > state.emission_budget:
            return OperationResult.fail(
                state,
                OperationError(
                    code=ErrorCode.EMISSION_BUDGET_EXCEEDED,
                    message=(
                        f"credit {n_credit} exceeds emission budget {state.emission_budget}"
                    ),
                ),
            )

        # Step 5: auto-repay actor's open loans, release escrow. The
        # outcome already contains an actor with the full incoming amount
        # added to balance — see _apply_repayments docstring.
        repay_outcome = _apply_repayments(state, actor, command.amount)
        actor_after = repay_outcome.actor
        receiver_after = receiver.model_copy(update={"balance": post_balance_receiver})
        state = state.model_copy(
            update={
                "loans": repay_outcome.loans,
                "escrow": DistributionEscrow(total=repay_outcome.escrow_total),
                "members": {
                    **state.members,
                    actor.id: actor_after,
                    receiver.id: receiver_after,
                },
            }
        )

        # Step 7: open new loan if credit emitted.
        new_loan_event: LoanOpened | None = None
        new_loan_id_value: LoanId | None = None
        if n_credit.is_positive():
            epsilon = EpsilonCalculator(state.parameters).compute(self._observed_default_rate)
            escrow_amount = V(n_credit.root * epsilon)
            new_loan_id_value = new_loan_id()
            loan = Loan(
                id=new_loan_id_value,
                borrower=receiver.id,
                principal=n_credit,
                repaid=V.zero(),
                opened_at=state.tick,
                epsilon_at_creation=epsilon,
                escrow_reserved=escrow_amount,
                state=LoanState.OPEN,
            )
            loan_update = {
                "loans": {**state.loans, new_loan_id_value: loan},
                "escrow": DistributionEscrow(total=state.escrow.total + escrow_amount),
            }
            # v2: draw the emitted credit down from the revenue-backed budget.
            if state.parameters.emission_budget_share > 0:
                loan_update["emission_budget"] = state.emission_budget - n_credit
            state = state.model_copy(update=loan_update)
            new_loan_event = LoanOpened(
                loan_id=new_loan_id_value,
                borrower=receiver.id,
                principal=n_credit,
                epsilon=epsilon,
            )

        # Step 8 & 9: distribute released escrow, accrue R, append record.
        state, distribution_event = _distribute_escrow(
            state, _sum_v(repay_outcome.escrow_released.values())
        )
        state = _accrue_reputation_and_record(
            state,
            actor_id=actor.id,
            receiver_id=receiver.id,
            command=command,
            confidence=confidence,
            n_credit=n_credit,
            tx_loan=new_loan_id_value,
            repaid_loan_ids=tuple(repay_outcome.escrow_released.keys()),
        )

        events = _build_events(
            repaid=repay_outcome.escrow_released,
            distribution=distribution_event,
            new_loan=new_loan_event,
            state=state,
            actor_id=actor.id,
            receiver_id=receiver.id,
            amount=command.amount,
        )
        return OperationResult.ok(state, *events)


# ---------------------------------------------------------------------------
# Helpers — pure functions on entities
# ---------------------------------------------------------------------------


def _validate(state: ClubState, command: TransactCommand) -> OperationError | None:
    if command.actor not in state.members or command.receiver not in state.members:
        return OperationError(code=ErrorCode.MEMBER_NOT_FOUND, message="actor or receiver missing")
    if command.actor == command.receiver:
        return OperationError(code=ErrorCode.SAME_PARTIES, message="actor and receiver must differ")
    actor = state.members[command.actor]
    receiver = state.members[command.receiver]
    if actor.is_frozen or receiver.is_frozen:
        return OperationError(
            code=ErrorCode.MEMBER_FROZEN, message="frozen members cannot transact"
        )
    if not command.amount.is_positive():
        return OperationError(code=ErrorCode.INVALID_AMOUNT, message="amount must be positive")
    return None


def _confidence(state: ClubState, command: TransactCommand) -> Confidence:
    category_params = state.parameters.categories[command.category]
    auto = AutoScoreCalculator().compute(command.amount, category_params)
    return ConfidenceCalculator().compute(
        auto_score=auto,
        review_score=command.review_score,
        audit_score=command.audit_score,
    )


def _credit_portion(receiver: Member, amount: V) -> V:
    receiver_positive = receiver.balance if receiver.balance.is_positive() else V.zero()
    return max(V.zero(), amount - receiver_positive)


def _within_credit_limit(state: ClubState, receiver: Member, post_balance: V) -> bool:
    limit = CreditLimitService(state.parameters).compute(receiver.reputation)
    # b ≥ −L  ⇔  b + L ≥ 0
    return (post_balance + limit) >= V.zero()


# ---------------------------------------------------------------------------
# Repayment & escrow flow
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class _RepayOutcome:
    """Result of FIFO-applying incoming V to an actor's open loans.

    The actor's balance has been incremented by the full ``incoming``
    amount; repaid loans simply track that the negative portion of the
    actor's balance has been settled, and escrow is released for any
    fully-repaid loans.
    """

    actor: Member
    loans: dict[LoanId, Loan]
    escrow_total: V
    escrow_released: dict[LoanId, V]


def _apply_repayments(state: ClubState, actor: Member, incoming: V) -> _RepayOutcome:
    actor_loans = sorted(
        (loan for loan in state.loans.values() if loan.borrower == actor.id and loan.is_open()),
        key=lambda loan: loan.opened_at,
    )
    new_loans = dict(state.loans)
    escrow_total = state.escrow.total
    released: dict[LoanId, V] = {}
    coverage = incoming  # how much of incoming is still available to clear debt

    for loan in actor_loans:
        if not coverage.is_positive():
            break
        outstanding = loan.outstanding()
        apply_amount = min(coverage, outstanding)
        new_repaid = loan.repaid + apply_amount
        becomes_repaid = new_repaid >= loan.principal
        updated = loan.model_copy(
            update={
                "repaid": new_repaid,
                "state": LoanState.REPAID if becomes_repaid else LoanState.OPEN,
                "escrow_reserved": V.zero() if becomes_repaid else loan.escrow_reserved,
            }
        )
        new_loans[loan.id] = updated
        if becomes_repaid:
            released[loan.id] = loan.escrow_reserved
            escrow_total = escrow_total - loan.escrow_reserved
        coverage = coverage - apply_amount

    new_actor = actor.model_copy(update={"balance": actor.balance + incoming})
    return _RepayOutcome(
        actor=new_actor,
        loans=new_loans,
        escrow_total=escrow_total,
        escrow_released=released,
    )


def _distribute_escrow(state: ClubState, total: V) -> tuple[ClubState, EscrowReleased | None]:
    if not total.is_positive():
        return state, None
    turnovers = {m.id: m.turnover_90d for m in state.members.values()}
    if not turnovers:
        return state, None
    shares = DistributionService(state.parameters).shares(turnovers)
    new_members = {**state.members}
    for member_id, share in shares.items():
        recipient = new_members[member_id]
        increment = V(total.root * share)
        new_members[member_id] = recipient.model_copy(
            update={"balance": recipient.balance + increment}
        )
    state = state.model_copy(update={"members": new_members})
    return state, EscrowReleased(total_released=total, recipients=len(turnovers))


def _accrue_reputation_and_record(
    state: ClubState,
    *,
    actor_id: MemberId,
    receiver_id: MemberId,
    command: TransactCommand,
    confidence: Confidence,
    n_credit: V,
    tx_loan: LoanId | None,
    repaid_loan_ids: tuple[LoanId, ...],
) -> ClubState:
    actor = state.members[actor_id]
    receiver = state.members[receiver_id]
    rep_service = ReputationDeltaService(state.parameters)
    new_actor = actor.model_copy(
        update={
            "reputation": actor.reputation.add(rep_service.for_actor_transaction(confidence)),
            "turnover_90d": actor.turnover_90d + command.amount,
            "cumulative_contribution": actor.cumulative_contribution + command.amount,
            "last_active_tick": state.tick,
        }
    )
    new_receiver = receiver.model_copy(
        update={
            "reputation": receiver.reputation.add(rep_service.for_receiver_transaction(confidence)),
            "turnover_90d": receiver.turnover_90d + command.amount,
            "last_active_tick": state.tick,
        }
    )
    record = TransactionRecord(
        id=new_transaction_id(),
        tick=state.tick,
        actor=actor_id,
        receiver=receiver_id,
        amount=command.amount,
        category=command.category,
        confidence=confidence,
        n_credit=n_credit,
        loan_id=tx_loan,
        repaid_loans=repaid_loan_ids,
    )
    return state.model_copy(
        update={
            "members": {**state.members, actor_id: new_actor, receiver_id: new_receiver},
            "transactions": (*state.transactions, record),
        }
    )


def _build_events(
    *,
    repaid: dict[LoanId, V],
    distribution: EscrowReleased | None,
    new_loan: LoanOpened | None,
    state: ClubState,
    actor_id: MemberId,
    receiver_id: MemberId,
    amount: V,
) -> list[DomainEvent]:
    events: list[DomainEvent] = [
        LoanRepaid(loan_id=loan_id, amount=v_amount, fully_repaid=True)
        for loan_id, v_amount in repaid.items()
    ]
    if distribution is not None:
        events.append(distribution)
    if new_loan is not None:
        events.append(new_loan)
    last_tx = state.transactions[-1]
    events.append(
        TransactionConfirmed(
            tx_id=last_tx.id,
            actor=actor_id,
            receiver=receiver_id,
            amount=amount,
        )
    )
    return events


def _sum_v(values: Iterable[V]) -> V:
    total = V.zero()
    for value in values:
        total = total + value
    return total
