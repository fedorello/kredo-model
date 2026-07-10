"""Built-in simulation scenarios."""

from __future__ import annotations

from app.application.scenarios.bank_run import bank_run_scenario
from app.application.scenarios.base import (
    BootstrapMember,
    ScenarioConfig,
    build_initial_state,
)
from app.application.scenarios.fraud_attack import fraud_attack_scenario
from app.application.scenarios.mature_steady import mature_steady_scenario
from app.application.scenarios.normal_growth import normal_growth_scenario
from app.application.scenarios.registry import (
    SCENARIOS,
    build_scenario,
    list_scenarios,
)

__all__ = [
    "SCENARIOS",
    "BootstrapMember",
    "ScenarioConfig",
    "bank_run_scenario",
    "build_initial_state",
    "build_scenario",
    "fraud_attack_scenario",
    "list_scenarios",
    "mature_steady_scenario",
    "normal_growth_scenario",
]
