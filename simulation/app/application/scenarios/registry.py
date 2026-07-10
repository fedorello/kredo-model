"""Registry of built-in scenarios."""

from __future__ import annotations

from collections.abc import Callable

from app.application.scenarios.bank_run import bank_run_scenario
from app.application.scenarios.base import ScenarioConfig
from app.application.scenarios.fraud_attack import fraud_attack_scenario
from app.application.scenarios.mature_steady import mature_steady_scenario
from app.application.scenarios.normal_growth import normal_growth_scenario

ScenarioFactory = Callable[[], ScenarioConfig]


SCENARIOS: dict[str, ScenarioFactory] = {
    "normal_growth": normal_growth_scenario,
    "mature_steady": mature_steady_scenario,
    "fraud_attack": fraud_attack_scenario,
    "bank_run": bank_run_scenario,
}


def list_scenarios() -> list[str]:
    return sorted(SCENARIOS.keys())


def build_scenario(name: str) -> ScenarioConfig:
    if name not in SCENARIOS:
        raise KeyError(f"unknown scenario {name!r}; available: {list_scenarios()}")
    return SCENARIOS[name]()
