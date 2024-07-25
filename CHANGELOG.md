# Changelog
## 7.0.3 - 2024-07-25
- Add an option to ignore task failures for known failures

## 7.0.2 - 2024-07-24
- Add an option to check only one specific version with version_override

## 7.0.1 - 2024-06-11
- Fix for unbound variable.
- Add back support for mongo default variants

## 7.0.0 - 2024-06-10
- `--display-variant-name` and `--build-variant` are `xor`'d together, instead of `or`'d.

## 6.0.1 - 2024-03-27
- Merge with the GitHub merge queue (no code changes)

## 6.0.0 - 2024-01-31
- Update Python version to 3.9.
- Upgrade libraries.

## 5.0.1 - 2024-01-30
- Pin `evergreen.py` to `3.6.18` to fix incompatible type `dict`.

## 5.0.0 - 2023-10-18
- Lock `pyyaml` to `6.0.1` to avoid cython issues.

## 4.0.0 - 2023-07-31
- Add `--display-variant-name` optional argument.

## 3.0.6 - 2022-11-07
- Change default build variants to required for mongo projects.

## 3.0.5 - 2022-08-29
- Perform `checkout` by default when branch name is specified.

## 3.0.4 - 2022-08-25
- Document how to install with a specific Python version.

## 3.0.3 - 2022-08-11
- Handle the case when a build has no tasks.

## 3.0.2 - 2022-08-08
- Gracefully handle the case when a version has no build statues.

## 3.0.1 - 2022-08-04
- `Failure threshold` checks are now `or`'d together, instead of `and`'d.

## 3.0.0 - 2022-07-06
- Change default value for build variant to all.

## 2.1.0 - 2022-06-30
- Add failure threshold criteria.

## 2.0.0 - 2022-06-06
- Change the default behavior to not checkout by default.

## 1.0.3 - 2022-06-02
- Document default values for criteria.

## 1.0.2 - 2022-04-12
- Document how to fix common pipx install error.

## 1.0.1 - 2022-04-12

- Evaluate evergreen project configuration before using it.

## 1.0.0 - 2022-04-08
- Add support for Python 3.7.

## 0.5.15 - 2022-04-07
- Setup evergreen project.

## 0.5.14 - 2022-04-06
- Update the message printed when no revision is found.

## 0.5.13 - 2022-04-06
- Migrating to evergreen-ci organization in Github.

## 0.5.12 - 2022-02-13
- Add badge to documentation.

## 0.5.11 - 2022-02-12
- Fix publishing.

## 0.5.10 - 2022-02-12
- Improve how documentation is published.

## 0.5.9 - 2022-02-12
- Documentation improvements.

## 0.5.8 - 2022-02-12
- Fix more issues with publishing documentation.

## 0.5.7 - 2022-02-12
- Fix issue with publishing documentation.

## 0.5.6 - 2022-02-12
- Added published documentation.

## 0.5.5 - 2022-01-19
- Fix bug when running against evergreen projects with no modules.

## 0.5.4 - 2021-11-20
- Improve test dependencies

## 0.5.3 - 2021-11-20
- Support calls from outside a git repo.
- Refactor to be more testable.

## 0.5.2 - 2021-11-15
- Add support for YAML and JSON output formats.

## 0.5.1 - 2021-09-14
- Add branch name option to git checkout operation.
- Add option to limit lookback to a specific commit.

## 0.5.0 - 2021-09-12
- Add support for import and exporting rules.

## 0.4.0 - 2021-09-12
- Add support for saving and loading criteria.

## 0.3.0 - 2021-09-11
- Add support for rebase and merge.

## 0.2.0 - 2021-09-11
- Add support for modules

## 0.1.2 - 2021-09-08
- Add timeout and max lookback options.
- Add option to skip commit.

## 0.1.1 - 2021-09-07
- Relax python version to 3.8.

## 0.1.0 - 2021-08-29
- Initial Release
