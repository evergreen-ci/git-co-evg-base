"""Unit tests for evg_service.py."""
from enum import Enum
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

import pytest
import yaml
from evergreen import Build, EvergreenApi, Manifest, Project, Task, Version
from evergreen.manifest import ManifestModule
from evergreen.task_annotations import IssueLink, TaskAnnotation
from requests.exceptions import HTTPError

import goodbase.services.evg_service as under_test
from goodbase.build_checker import BuildChecks
from goodbase.clients.evg_cli_proxy import EvgCliProxy


class TaskStatus(int, Enum):
    SUCCESS = 0
    FAILED = 1
    INACTIVE = 2


def build_mock_task(name: str, status: TaskStatus) -> Task:
    mock_task = MagicMock(spec_set=Task, display_name=name)
    if status == TaskStatus.SUCCESS or status == TaskStatus.FAILED:
        mock_task.is_undispatched.return_value = False
        mock_task.is_success.return_value = status == TaskStatus.SUCCESS
    else:
        mock_task.is_undispatched.return_value = True
        mock_task.is_success.return_value = False
    return mock_task


def build_mock_build(build_variant: str, display_name: str, task_list: List[Task]) -> Build:
    mock_build = MagicMock(spec_set=Build, build_variant=build_variant, display_name=display_name)
    mock_build.get_tasks.return_value = task_list
    return mock_build


def build_mock_version(builds: Dict[str, Build]) -> Version:
    mock_version = MagicMock(spec=Version)
    mock_version.build_variants_status = [
        {"build_variant": build.build_variant, "build_id": _id} for _id, build in builds.items()
    ]
    mock_version.get_builds.return_value = builds.values()
    return mock_version


def build_mock_project(index):
    mock_project = MagicMock(
        spec=Project, identifier=f"project {index}", remote_path=f"remote/path/{index}"
    )
    return mock_project


def build_mock_manifest(modules: Optional[Dict[str, str]]) -> Manifest:
    mock_manifest = MagicMock(spec=Manifest)
    if modules is not None:
        mock_manifest.modules = {
            k: MagicMock(spec=ManifestModule, revision=v) for k, v in modules.items()
        }
    else:
        mock_manifest.modules = None
    return mock_manifest


def build_mock_project_config() -> Dict[str, Any]:
    project_config = {
        "modules": [{"name": f"module {i}", "prefix": f"path/to/{i}"} for i in range(4)]
    }
    return project_config


@pytest.fixture()
def evg_cli_proxy():
    file_service = MagicMock(spec_set=EvgCliProxy)
    file_service.evaluate.return_value = yaml.safe_dump(build_mock_project_config())
    return file_service


@pytest.fixture()
def evergreen_api():
    mock_evg_api = MagicMock(spec_set=EvergreenApi)
    project_list = [build_mock_project(i) for i in range(10)]
    mock_evg_api.all_projects = lambda project_filter_fn: [
        p for p in project_list if project_filter_fn(p)
    ]

    mocked_annotation = MagicMock(spec_set=IssueLink, issue_key="BF-1234")
    mocked_annotations = MagicMock(spec_set=TaskAnnotation)
    mocked_annotations.issues = [mocked_annotation]
    mocked_annotations.suspected_issues = {}
    mock_evg_api.get_task_annotation = MagicMock(return_value=[mocked_annotations])
    return mock_evg_api


@pytest.fixture()
def evg_service(evergreen_api, evg_cli_proxy):
    evg_service = under_test.EvergreenService(evergreen_api, evg_cli_proxy)
    return evg_service


def mock_project_config(service, project_config):
    service.evaluate.return_value = yaml.safe_dump(project_config)


def mock_evg_manifest(service, manifest):
    service.evg_api.manifest.return_value = manifest


def set_build_variant_predicate(service, predicate):
    service.bv_predicate = predicate


class TestAnalyzeBuild:
    def test_build_with_all_tasks_run(self, evg_service):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.SUCCESS) for i in range(n_tasks)]
        mock_build = build_mock_build(
            build_variant="my_build", display_name="my build", task_list=mock_task_list
        )

        build_status = evg_service.analyze_build(mock_build, False)

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == {task.display_name for task in mock_task_list}
        assert build_status.inactive_tasks == set()
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_no_tasks_run(self, evg_service):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.INACTIVE) for i in range(n_tasks)]
        mock_build = build_mock_build(
            build_variant="my_build", display_name="my build", task_list=mock_task_list
        )

        build_status = evg_service.analyze_build(mock_build, False)

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == set()
        assert build_status.inactive_tasks == {task.display_name for task in mock_task_list}
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_all_failed_tasks(self, evg_service):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.FAILED) for i in range(n_tasks)]
        mock_build = build_mock_build(
            build_variant="my_build", display_name="my build", task_list=mock_task_list
        )

        build_status = evg_service.analyze_build(mock_build, False)

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == set()
        assert build_status.inactive_tasks == set()
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_all_failed_known_tasks(self, evg_service):
        n_tasks = 10
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus.FAILED) for i in range(n_tasks)]
        mock_build = build_mock_build(
            build_variant="my_build", display_name="my build", task_list=mock_task_list
        )

        build_status = evg_service.analyze_build(mock_build, True)

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == {task.display_name for task in mock_task_list}
        assert build_status.inactive_tasks == set()
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}

    def test_build_with_a_mix_of_status(self, evg_service):
        n_tasks = 9
        mock_task_list = [build_mock_task(f"task_{i}", TaskStatus(i % 3)) for i in range(n_tasks)]
        mock_build = build_mock_build(
            build_variant="my_build", display_name="my build", task_list=mock_task_list
        )

        build_status = evg_service.analyze_build(mock_build, False)

        assert build_status.build_name == "my build"
        assert build_status.successful_tasks == {"task_0", "task_3", "task_6"}
        assert build_status.inactive_tasks == {"task_2", "task_5", "task_8"}
        assert build_status.all_tasks == {task.display_name for task in mock_task_list}


class TestGetBuildStatusesForVersion:
    def test_all_builds_meet_predicate(self, evg_service):
        n_builds = 5
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = [BuildChecks(build_variant_regex=["^build"], display_name_regex=["^build"])]

        build_status_list = evg_service.get_build_statuses_for_version(mock_version, build_checks)

        assert len(build_status_list) == n_builds

    def test_no_builds_meet_predicate(self, evg_service):
        n_builds = 5
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = [
            BuildChecks(build_variant_regex=["^hello_world"], display_name_regex=["^hello world"])
        ]

        build_status_list = evg_service.get_build_statuses_for_version(mock_version, build_checks)

        assert len(build_status_list) == 0

    def test_some_builds_meet_predicate(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = [
            BuildChecks(build_variant_regex=["^build_1"], display_name_regex=["^build 1"])
        ]

        build_status_list = evg_service.get_build_statuses_for_version(mock_version, build_checks)

        assert len(build_status_list) == 11

    @pytest.mark.parametrize(
        "builds",
        [
            ([]),
            (None),
        ],
    )
    def test_version_with_no_build_statuses(self, evg_service, builds):
        build_checks = [
            BuildChecks(build_variant_regex=["^build_1"], display_name_regex=["^build 1"])
        ]
        mock_version = MagicMock(spec=Version)
        mock_version.build_variants_map = builds

        build_status_list = evg_service.get_build_statuses_for_version(mock_version, build_checks)

        assert build_status_list is None


class TestCheckVersion:
    def test_no_build_meet_checks(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus.INACTIVE) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = BuildChecks(
            build_variant_regex=[".*"], display_name_regex=[], run_threshold=0.9
        )

        result = evg_service.check_version(mock_version, [build_checks], False)

        assert not result

    def test_all_build_meet_checks(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = BuildChecks(
            build_variant_regex=[".*"], display_name_regex=[], run_threshold=0.9
        )

        result = evg_service.check_version(mock_version, [build_checks], False)

        assert result

    def test_all_build_meet_checks_with_failure_threshold(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus.FAILED) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = BuildChecks(
            build_variant_regex=[".*"],
            display_name_regex=[],
            run_threshold=0.9,
            failure_threshold=0.1,
        )

        result = evg_service.check_version(mock_version, [build_checks], False)

        assert result

    def test_one_build_meet_checks_with_failure_threshold(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus.SUCCESS) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_build_map["id_matching_build"] = build_mock_build(
            build_variant="matching_build",
            display_name="matching build",
            task_list=[build_mock_task("task_1", TaskStatus.FAILED)],
        )
        mock_version = build_mock_version(mock_build_map)
        build_checks = BuildChecks(
            build_variant_regex=[".*"],
            display_name_regex=[],
            run_threshold=0.9,
            failure_threshold=0.1,
        )

        result = evg_service.check_version(mock_version, [build_checks], False)

        assert result

    def test_some_build_meet_checks(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus(i % 3)) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = BuildChecks(
            build_variant_regex=[".*"], display_name_regex=[], run_threshold=0.9
        )

        result = evg_service.check_version(mock_version, [build_checks], False)

        assert not result

    def test_some_build_meet_checks_but_are_filtered_out(self, evg_service):
        n_builds = 20
        mock_build_map = {
            f"id_{i}": build_mock_build(
                build_variant=f"build_{i}",
                display_name=f"build {i}",
                task_list=[build_mock_task(f"task_{j}", TaskStatus(i % 3)) for j in range(10)],
            )
            for i in range(n_builds)
        }
        mock_version = build_mock_version(mock_build_map)
        build_checks = BuildChecks(
            build_variant_regex=["^build_0$"], display_name_regex=[], run_threshold=0.9
        )

        result = evg_service.check_version(mock_version, [build_checks], False)

        assert result


class TestGetModulesRevisions:
    def test_empty_modules_returned(self, evg_service):
        modules = {}
        mock_evg_manifest(evg_service, build_mock_manifest(modules))

        assert modules == evg_service.get_modules_revisions("project id", "gitrevision")

    def test_no_modules_returned(self, evg_service):
        modules = None
        mock_evg_manifest(evg_service, build_mock_manifest(modules))

        assert {} == evg_service.get_modules_revisions("project id", "gitrevision")

    def test_multiple_modules_returned(self, evg_service):
        modules = {
            "module 1": "abc123",
            "module 2": "def456",
        }
        mock_evg_manifest(evg_service, build_mock_manifest(modules))

        assert modules == evg_service.get_modules_revisions("project id", "gitrevision")

    def test_manifest_endpoint_returns_404(self, evg_service):
        http_response = MagicMock(status_code=404)

        evg_service.evg_api.manifest.side_effect = HTTPError(response=http_response)

        assert {} == evg_service.get_modules_revisions("project id", "gitrevision")


class TestGetProjectConfigLocation:
    def test_remote_path_is_returned(self, evg_service):
        assert "remote/path/3" == evg_service.get_project_config_location("project 3")

    def test_missing_project_should_throw_exception(self, evg_service):
        with pytest.raises(ValueError) as exp:
            evg_service.get_project_config_location("non-existing-project")
            assert "non-existing-project" in exp.value

    def test_more_than_one_matching_project_should_throw_exception(self, evg_service):
        project_list = [build_mock_project(5) for _ in range(10)]
        evg_service.evg_api.all_projects = lambda project_filter_fn: [
            p for p in project_list if project_filter_fn(p)
        ]

        with pytest.raises(ValueError) as exp:
            evg_service.get_project_config_location("project_5")
            assert "project_5" in exp.value


class TestGetModuleLocations:
    def test_module_locations_should_be_returned(self, evg_service):
        project_locations = evg_service.get_module_locations("project 2")

        assert project_locations == {f"module {i}": f"path/to/{i}" for i in range(4)}

    def test_module_locations_with_no_modules_in_project_should_be_empty(
        self, evg_service, evg_cli_proxy
    ):
        mock_project_config(evg_cli_proxy, {})
        project_locations = evg_service.get_module_locations("project 2")

        assert project_locations == {}
