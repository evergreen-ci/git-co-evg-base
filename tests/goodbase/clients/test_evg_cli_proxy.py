"""Unit tests for evg_cli_proxy.py."""
from pathlib import Path
from unittest.mock import MagicMock

import pytest

import goodbase.clients.evg_cli_proxy as under_test


@pytest.fixture()
def evg_cli():
    evg_cli = MagicMock()
    return evg_cli


@pytest.fixture()
def evg_cli_proxy(evg_cli):
    evg_cli_proxy = under_test.EvgCliProxy(evg_cli)
    return evg_cli_proxy


class TestEvaluate:
    def test_evaluate_should_call_out_to_evg_cli(self, evg_cli_proxy, evg_cli):
        project_location = Path("project_location")

        evg_cli_proxy.evaluate(project_location)

        evg_cli.__getitem__.assert_called_with(["evaluate", "--path", project_location])
