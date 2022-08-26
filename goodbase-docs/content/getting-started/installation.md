---
weight: 1
---

## Dependencies

You'll need an installation of [Python](https://www.python.org/) on your computer. It needs to
be version [3.7.1](https://www.python.org/downloads/release/python-371/) or higher.

* [git](https://git-scm.com): Version 2.17 or higher
* [Evergreen config file](https://github.com/evergreen-ci/evergreen/wiki/Using-the-Command-Line-Tool#downloading-the-command-line-tool)
* [evergreen](https://github.com/evergreen-ci/evergreen/wiki/Using-the-Command-Line-Tool): The evergreen command line tool.

## Installation

We strongly recommend using a tool like [pipx](https://pypa.github.io/pipx/) to install
this tool. This will isolate the dependencies and ensure they don't conflict with other tools.

```bash
$ pipx install git-co-evg-base
```

### Debugging installation issues

A common issue that arises during installation is pipx failing to install git-co-evg-base and printing out the following error:
```bash
$ pipx install git-co-evg-base
Fatal error from pip prevented installation. Full pip output in file:
    /home/ubuntu/.local/pipx/logs/cmd_2022-03-31_13.24.42_pip_errors.log
 
Some possibly relevant errors from pip install:
    ERROR: Could not find a version that satisfies the requirement git-co-evg-base (from versions: none)
    ERROR: No matching distribution found for git-co-evg-base
 
Error installing git-co-evg-base.
```

This error indicates that pipx could not find a version of git-co-evg-base that was built to support the version of Python installed on your machine.
Make sure to check that your version of Python matches the requirements called out in the [Dependencies]({{< relref "installation.md#dependencies" >}}) section. You
can check the version of Python that is on your computer by running
```bash
$ python --version
```

If you are running into the issue above but are sure that the correct version of Python is installed on your computer,
you can explicitly specify a path to the correct Python version during installation.

```bash
$ which python3.9
/usr/bin/python3.9
$ pipx install git-co-evg-base --python /usr/bin/python3.9
```
