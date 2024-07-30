"""Service to interact with evergreen."""
from concurrent.futures import ThreadPoolExecutor as Executor
from pathlib import Path
from typing import Dict, List, Optional

import inject
import structlog
import yaml
from evergreen import Build, EvergreenApi, Task, Version
from requests.exceptions import HTTPError

from goodbase.build_checker import BuildChecks
from goodbase.clients.evg_cli_proxy import EvgCliProxy
from goodbase.models.build_status import BuildStatus

N_THREADS = 16

LOGGER = structlog.get_logger(__name__)


class EvergreenService:
    """A service to interact with Evergreen."""

    @inject.autoparams()
    def __init__(self, evg_api: EvergreenApi, evg_cli_proxy: EvgCliProxy) -> None:
        """
        Initialize the service.

        :param evg_api: Evergreen API client.
        :param evg_cli_proxy: Proxy for evergreen cli.
        """
        self.evg_api = evg_api
        self.evg_cli_proxy = evg_cli_proxy

    def analyze_build(
        self, build: Build, allow_known_failures: bool = False
    ) -> Optional[BuildStatus]:
        """
        Get a summary of results for the given build.

        :param build: Evergreen build to analyze.
        :param allow_known_failures: Whether to allow known failures as passing ones.
        :return: Summary of build.
        """
        try:
            tasks = build.get_tasks()
        except HTTPError as err:
            LOGGER.debug(
                "Could not get data from Evergreen for a build",
                status_code=err.response.status_code,
                build_id=build.id,
                exc_info=True,
            )
            return None

        successful_tasks = self._get_successful_tasks(tasks, allow_known_failures)
        inactive_tasks = {task.display_name for task in tasks if task.is_undispatched()}
        all_tasks = {task.display_name for task in tasks}

        return BuildStatus(
            build_name=build.display_name,
            build_variant=build.build_variant,
            successful_tasks=successful_tasks,
            inactive_tasks=inactive_tasks,
            all_tasks=all_tasks,
        )

    def _get_successful_tasks(self, tasks: List[Task], allow_known_failures: bool) -> set[str]:
        """
        Get the set of successful tasks from a list of tasks.

        If allow_known_failures is True, known failures will be included in the set.
        Otherwise only passing tasks will be returned.

        :param tasks: The list of tasks to check.
        :param allow_known_failures: If true - consider known failures as successful.
        :return: The set of successful tasks according to the given criteria.
        """
        return {
            task.display_name
            for task in tasks
            if task.is_success()
            or (
                allow_known_failures and task.is_completed() and self._is_task_a_known_failure(task)
            )
        }

    def _is_task_a_known_failure(self, task: Task) -> bool:
        """
        Check if a task is a known failure. A known failure will be annotated with an issue.

        :param task: the task to check.
        :return: True if the task is a known failure.
        """
        return any(
            annotation.issues for annotation in self.evg_api.get_task_annotation(task.task_id)
        )

    def check_version(
        self,
        evg_version: Version,
        build_checks: List[BuildChecks],
        allow_known_failures: bool = False,
    ) -> bool:
        """
        Check if the given version meets the specified criteria.

        :param evg_version: Evergreen version to check.
        :param build_checks: Build criteria to use.
        :param allow_known_failures: Whether to allow known failures as passing ones.
        :return: True if the version matches the specified criteria.
        """
        build_status_list = self.get_build_statuses_for_version(
            evg_version, build_checks, allow_known_failures
        )
        if not build_status_list:
            LOGGER.debug("No build status found for version, skipping", commit=evg_version.revision)
            return False
        checks_without_failure_threshold = [
            bc for bc in build_checks if bc.failure_threshold is None
        ]
        success_check = all(
            bc.check(bs) for bs in build_status_list for bc in checks_without_failure_threshold
        )

        checks_with_failure_thresholds = [
            bc for bc in build_checks if bc.failure_threshold is not None
        ]
        failure_check = any(
            bc.check(bs) for bs in build_status_list for bc in checks_with_failure_thresholds
        )

        return success_check and (len(checks_with_failure_thresholds) == 0 or failure_check)

    def get_build_statuses_for_version(
        self,
        evg_version: Version,
        build_checks: List[BuildChecks],
        allow_known_failures: bool = False,
    ) -> Optional[List[BuildStatus]]:
        """
        Get the build status for this version that match the predicate.

        :param evg_version: Evergreen version to check.
        :param build_checks: Build criteria to use.
        :param allow_known_failures: Whether to allow known failures as passing ones.
        :return: List of build statuses.
        """
        if not evg_version.build_variants_status or len(evg_version.build_variants_status) == 0:
            return None
        builds = evg_version.get_builds()
        with Executor(max_workers=N_THREADS) as exe:
            jobs = [
                exe.submit(self.analyze_build, build, allow_known_failures)
                for build in builds
                if any(
                    bc.should_apply(build.build_variant, build.display_name) for bc in build_checks
                )
            ]

        results = []
        for j in jobs:
            result = j.result()
            if result is not None:
                results.append(result)
        return results

    def get_modules_revisions(self, project_id: str, revision: str) -> Dict[str, str]:
        """
        Get a map of the modules and git revisions they ran with on the given commit.

        :param project_id: Evergreen project being queried.
        :param revision: Commit revision to query.
        :return: Dictionary of modules and revisions associated with specified commit.
        """
        try:
            manifest = self.evg_api.manifest(project_id, revision)
        except HTTPError as err:
            if err.response.status_code == 404:
                # If a project does not use modules, the manifest will return 404.
                return {}
            raise err
        modules = manifest.modules
        if modules is not None:
            return {module_name: module.revision for module_name, module in modules.items()}
        return {}

    def get_project_config_location(self, project_id: str) -> str:
        """
        Get the path to the evergreen config file for this project.

        :param project_id: ID of Evergreen project being queried.
        :return: Path to project config file.
        """
        project_config_list = self.evg_api.all_projects(
            project_filter_fn=lambda p: p.identifier == project_id
        )
        if len(project_config_list) != 1:
            raise ValueError(f"Could not find unique project configuration for : '{project_id}'.")
        project_config = project_config_list[0]
        return project_config.remote_path

    def get_module_locations(self, project_id: str) -> Dict[str, str]:
        """
        Get the paths that project modules are stored.

        :param project_id: ID of project to query.
        :return: Dictionary of modules and their paths.
        """
        project_config_location = self.get_project_config_location(project_id)
        project_config = yaml.safe_load(self.evg_cli_proxy.evaluate(Path(project_config_location)))
        return {module["name"]: module["prefix"] for module in project_config.get("modules", [])}
