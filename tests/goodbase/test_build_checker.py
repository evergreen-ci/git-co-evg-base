"""Unit tests for build_checker.py."""
import pytest

import goodbase.build_checker as under_test
from goodbase.models.build_status import BuildStatus


class TestShouldApply:
    @pytest.mark.parametrize(
        "build_variant,display_name",
        [
            ("match-required", "! match"),
            ("match-required", "* match"),
            ("match-suggested", "* match"),
            ("match-suggested", "! match"),
        ],
    )
    def test_build_variant_regexes_match_both(self, build_variant, display_name):
        checker = under_test.BuildChecks(
            build_variant_regex=[".*-required$", ".*-suggested$"],
            display_name_regex=["^! .*", "^\\* .*"],
        )

        assert checker.should_apply(build_variant=build_variant, display_name=display_name)

    @pytest.mark.parametrize(
        "build_variant_regex,display_name_regex",
        [
            (["^match-build-variant$"], ["^not match$"]),
            (["^not-match$"], ["^match display name$"]),
            (["^match-build-variant$"], []),
            ([], ["^match display name$"]),
        ],
    )
    def test_build_variant_regexes_match_partial(self, build_variant_regex, display_name_regex):
        checker = under_test.BuildChecks(
            build_variant_regex=build_variant_regex, display_name_regex=display_name_regex
        )

        assert checker.should_apply(
            build_variant="match-build-variant", display_name="match display name"
        )

    @pytest.mark.parametrize(
        "build_variant_regex,display_name_regex",
        [
            ([".*-required$", ".*-suggested$"], ["^! .*", "^\\* .*"]),
            ([".*-required$", ".*-suggested$"], []),
            ([], ["^! .*", "^\\* .*"]),
            ([], []),
        ],
    )
    def test_build_variant_regexes_do_not_match(self, build_variant_regex, display_name_regex):
        checker = under_test.BuildChecks(
            build_variant_regex=build_variant_regex, display_name_regex=display_name_regex
        )

        assert not checker.should_apply(build_variant="not-match", display_name="not match")


class TestSuccessThreshold:
    def test_success_threshold_is_met(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={f"task_{i}" for i in range(5)},
            inactive_tasks=set(),
            all_tasks={f"task_{i}" for i in range(7)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"], display_name_regex=["my build"], success_threshold=0.5
        )

        assert checker.check(build_status)

    def test_success_threshold_is_not_met(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={f"task_{i}" for i in range(5)},
            inactive_tasks=set(),
            all_tasks={f"task_{i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"], display_name_regex=["my build"], success_threshold=0.8
        )

        assert not checker.check(build_status)


class TestFailureThreshold:
    def test_failure_threshold_is_met(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={f"task_{i}" for i in range(5)},
            inactive_tasks=set(),
            all_tasks={f"task_{i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"], display_name_regex=["my build"], failure_threshold=0.3
        )

        assert checker.check(build_status)

    def test_failure_threshold_is_not_met(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={f"task_{i}" for i in range(8)},
            inactive_tasks=set(),
            all_tasks={f"task_{i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"], display_name_regex=["my build"], failure_threshold=0.3
        )

        assert not checker.check(build_status)


class TestRunThreshold:
    def test_run_threshold_is_met(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks={f"task_{i}" for i in range(3)},
            all_tasks={f"task_{i}" for i in range(9)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"], display_name_regex=["my build"], run_threshold=0.5
        )

        assert checker.check(build_status)

    def test_run_threshold_is_not_met(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks={f"task_{i}" for i in range(8)},
            all_tasks={f"task_{i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"], display_name_regex=["my build"], run_threshold=0.8
        )

        assert not checker.check(build_status)


class TestSuccessfulTasks:
    def test_expected_task_not_part_of_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks=set(),
            all_tasks=set(),
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            successful_tasks={"task 0"},
        )

        assert checker.check(build_status)

    def test_expected_task_failed_in_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks=set(),
            all_tasks={"task 0"},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            successful_tasks={"task 0"},
        )

        assert not checker.check(build_status)

    def test_expected_task_is_inactive_in_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks={"task 0"},
            all_tasks={"task 0"},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            successful_tasks={"task 0"},
        )

        assert not checker.check(build_status)

    def test_expected_task_is_successful_in_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={"task 0"},
            inactive_tasks=set(),
            all_tasks={"task 0"},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            successful_tasks={"task 0"},
        )

        assert checker.check(build_status)

    def test_multiple_tasks_can_be_specified_successfully(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={f"task {i}" for i in range(10)},
            inactive_tasks=set(),
            all_tasks={f"task {i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            successful_tasks={f"task {i}" for i in range(3)},
        )

        assert checker.check(build_status)

    def test_multiple_tasks_can_be_specified_with_failures(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={f"task {i}" for i in range(5)},
            inactive_tasks=set(),
            all_tasks={f"task {i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            successful_tasks={f"task {i+5}" for i in range(3)},
        )

        assert not checker.check(build_status)


class TestActiveTasks:
    def test_expected_task_not_part_of_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks=set(),
            all_tasks=set(),
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            active_tasks={"task 0"},
        )

        assert checker.check(build_status)

    def test_expected_task_failed_in_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks=set(),
            all_tasks={"task 0"},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            active_tasks={"task 0"},
        )

        assert checker.check(build_status)

    def test_expected_task_is_inactive_in_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks={"task 0"},
            all_tasks={"task 0"},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            active_tasks={"task 0"},
        )

        assert not checker.check(build_status)

    def test_expected_task_is_successful_in_build(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={"task 0"},
            inactive_tasks=set(),
            all_tasks={"task 0"},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            active_tasks={"task 0"},
        )

        assert checker.check(build_status)

    def test_multiple_tasks_can_be_specified_successfully(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks=set(),
            inactive_tasks=set(),
            all_tasks={f"task {i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            active_tasks={f"task {i}" for i in range(3)},
        )

        assert checker.check(build_status)

    def test_multiple_tasks_can_be_specified_with_failures(self):
        build_status = BuildStatus(
            build_name="my build",
            build_variant="my_build",
            successful_tasks={f"task {i}" for i in range(5)},
            inactive_tasks={f"task {i}" for i in range(6)},
            all_tasks={f"task {i}" for i in range(10)},
        )
        checker = under_test.BuildChecks(
            build_variant_regex=["my_build"],
            display_name_regex=["my build"],
            active_tasks={f"task {i+5}" for i in range(3)},
        )

        assert not checker.check(build_status)
