"""Service for working with the evergreen CLI."""
from __future__ import annotations

from pathlib import Path

from plumbum import local
from plumbum.machines.local import LocalCommand


class EvgCliProxy:
    """A proxy for interacting with the Evergreen CLI."""

    def __init__(self, evg_cli: LocalCommand) -> None:
        """
        Initialize the service.

        :param evg_cli: Object for executing cli command.
        """
        self.evg_cli = evg_cli

    @classmethod
    def create(cls) -> EvgCliProxy:
        """Create evergreen CLI service instance."""
        return cls(local.cmd.evergreen)

    def evaluate(self, project_config_location: Path) -> str:
        """
        Evaluate the given evergreen project configuration.

        :param project_config_location: Location of project configuration to evaluate.
        :return: Evaluated project configuration.
        """
        args = ["evaluate", "--path", project_config_location]
        return self.evg_cli[args]()
