"""Criteria for checking an evergreen build."""
import re
from typing import List, Optional, Set

import structlog
from pydantic import BaseModel

from goodbase.models.build_status import BuildStatus

LOGGER = structlog.get_logger(__name__)


class BuildChecks(BaseModel):
    """
    Set of checks to perform to check build criteria.

    build_variant_regex: List of build variant regexes to which checks should apply.
    display_name_regex: List of build variant display name regexes to which checks should apply.
    success_threshold: Percentage of tasks that need to pass to use the build.
    failure_threshold: Percentage of tasks that need to fail to use the build.
    run_threshold: Percentage of tasks that need to have run to use the build.
    successful_tasks: Set of tasks that need to have passed to use the build.
    active_tasks: Set of tasks that need to have run to use the build.
    """

    build_variant_regex: Optional[List[str]] = []
    display_name_regex: Optional[List[str]] = []
    success_threshold: Optional[float] = None
    failure_threshold: Optional[float] = None
    run_threshold: Optional[float] = None
    successful_tasks: Optional[Set[str]] = None
    active_tasks: Optional[Set[str]] = None

    def should_apply(self, build_variant: Optional[str], display_name: Optional[str]) -> bool:
        """
        Check if the given build variant should apply to these checks.

        :param build_variant: Name of build variant to check.
        :param display_name: Display name of build variant to check.
        :return: True if these checks apply to the given build variant.
        """
        if self.build_variant_regex and build_variant:
            return any(re.match(bv_regex, build_variant) for bv_regex in self.build_variant_regex)
        elif self.display_name_regex and display_name:
            return any(re.match(dn_regex, display_name) for dn_regex in self.display_name_regex)
        return False

    def check(self, build_status: BuildStatus) -> bool:
        """
        Check if the given build stats meet the specified criteria.

        :param build_status: Status of build to check.
        :return: True if the build matches the criteria.
        """
        if not self.should_apply(build_status.build_variant, build_status.build_name):
            return True

        if self.success_threshold and build_status.success_pct() < self.success_threshold:
            LOGGER.debug(
                "Unmet criteria, success_threshold",
                build=build_status.build_name,
                expected_success=self.success_threshold,
                actual_success=build_status.success_pct(),
            )
            return False

        if self.failure_threshold and build_status.failure_pct() < self.failure_threshold:
            LOGGER.debug(
                "Unmet criteria, failure_threshold",
                build=build_status.build_name,
                expected_failure=self.failure_threshold,
                actual_failure=build_status.failure_pct(),
            )
            return False

        if self.run_threshold and build_status.active_pct() < self.run_threshold:
            LOGGER.debug(
                "Unmet criteria, run_threshold",
                build=build_status.build_name,
                expected_run=self.success_threshold,
                actual_run=build_status.success_pct(),
            )
            return False

        if self.successful_tasks:
            if any(
                task in build_status.all_tasks and task not in build_status.successful_tasks
                for task in self.successful_tasks
            ):
                LOGGER.debug(
                    "Unmet criteria, successful_tasks",
                    build=build_status.build_name,
                    expected_tasks=self.successful_tasks,
                )
                return False

        if self.active_tasks:
            if any(
                task in build_status.all_tasks and task in build_status.inactive_tasks
                for task in self.active_tasks
            ):
                LOGGER.debug(
                    "Unmet criteria, active_tasks",
                    build=build_status.build_name,
                    expected_tasks=self.active_tasks,
                )
                return False

        return True
