# Security

This repository is for anything Jupyter or IPython security related that can be discussed in public.

If you need to privately disclose security issues please see https://jupyter.org/security

## Jupyter Security Subproject Council

Members
- Matthias Bussonnier [@Carreau](https://github.com/Carreau)
- Jason Grout [@jasongrout](https://github.com/jasongrout)
- David L. Qiu [@dlqqq](https://github.com/dlqqq)
- Mike Krassowski [@krassowski](https://github.com/krassowski)
- Yann Pellegrini [@Yann-P](https://github.com/Yann-P)

The Jupyter Security Subproject representative to the [Jupyter Software Steering Council](https://jupyter.org/governance/software_steering_council.html) is Yann Pellegrini ([@Yann-P](https://github.com/Yann-P)).

# Tools

The `tools/` directory contains scripts used by the security council to track
the Jupyter GitHub organizations, PyPI packages and security-reporting setup.
Unless noted otherwise, run them from the root of this repository, since they
read their input files (`all_repos.txt`, `psc_ignore.txt`, ...) from the
current working directory.

Several scripts need a GitHub token with read access to the organizations:

```bash
export GH_TOKEN=<your personal access token>
```

Scripts that declare their dependencies inline (PEP 723) can be run directly
with [`uv`](https://docs.astral.sh/uv/), which installs what they need on the
fly. For the others, install the packages they import (see `requirements.txt`).

## `tools/all_repos.py`

Cross-references the repositories of the Jupyter GitHub organizations with the
PyPI packages they publish. It reads the mapping from `all_repos.txt`
(one `github_org/repo : pypi-url` per line; use `<none>` if the repo has no
package and `-` if the package name equals the repo name), then:

- lists the PyPI packages declared in `all_repos.txt` that are *not* published
  under the Jupyter PyPI org, together with their maintainers (the work to do
  to add them to the org);
- lists repos that have no matching package in `all_repos.txt` so the mapping
  can be completed, flagging archived and private ones.

Maintainer lookups are cached in `github_cache-all_repos-YYYYMM/` to limit
requests. Requires `GH_TOKEN`.

```bash
uv run tools/all_repos.py
```

## `tools/jupyter_pypi_python_requires.py`

Lists every PyPI project under the Jupyter org in a table with its
`requires-python` constraint, release date and archived status. Useful to spot
packages still supporting old Python versions. It does not need a token; results
are cached for one hour in `~/.cache/jupyter-pypi`. Archived-project detection
falls back to a headless Chromium through Playwright when PyPI's Fastly CDN
blocks plain HTTP requests (optional: `playwright install chromium`).

```bash
uv run tools/jupyter_pypi_python_requires.py                 # sorted by name
uv run tools/jupyter_pypi_python_requires.py --sort python   # by minimum Python
uv run tools/jupyter_pypi_python_requires.py --sort date     # by release date
```

## `tools/last_user_activity.py`

Audits the members of the GitHub organizations and reports how recently each
one was active, based on their last public GitHub event. Members with no
activity within `--timelimit-days` are reported as inactive, along with their
inviter and last-activity reason when known.

Activity that GitHub cannot see (for example, work done before the account
was on GitHub) can be recorded manually in the config file
(`last_user_activity.json` by default), one entry per line:

```
# user : inviter : last activity (YYYY-MM) : reason
someuser:inviter:2016-01:Regular member of the team at BIDS
```

Requires `GH_TOKEN`.

```bash
uv run tools/last_user_activity.py                       # defaults: 365 days, all orgs
uv run tools/last_user_activity.py --debug               # show each active user
uv run tools/last_user_activity.py --timelimit-days 180
uv run tools/last_user_activity.py --orgs jupyter jupyterlab
uv run tools/last_user_activity.py --clear-cache         # refetch everything
```

## `tools/private-sec-reporting.py`

For each repository in the configured Jupyter organizations, checks whether
GitHub [private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
is enabled, and prints the result sorted by most recent push. Archived
repositories and repositories listed in `psc_ignore.txt` (one `org/repo` per
line) are flagged or skipped. Requires `GH_TOKEN`.

```bash
export GH_TOKEN=...
python tools/private-sec-reporting.py
```

## `tools/private_sec_report.py`

Similar to `private-sec-reporting.py`, but with a different set of
organizations and an ignore list in `private_sec_ignore.txt`. Repositories
without private vulnerability reporting are shown in red, except private,
archived or ignored ones, which are shown in yellow. Requires `GH_TOKEN`.

```bash
export GH_TOKEN=...
python tools/private_sec_report.py
```

## `tools/tide.py`

Queries the [Tidelift](https://tidelift.com) bulk estimate API for a set of
PyPI packages and prints, for each one, the estimated cost of getting it
"lifted" (covered by Tidelift's maintenance) and whether it already is. Packages
that the API does not know about are listed with no estimate.

Packages can be given by Jupyter PyPI org or user page, or listed directly:

```bash
uv run tools/tide.py --org jupyter                 # every package of the org
uv run tools/tide.py --user <pypi-username>        # every package of a user
uv run tools/tide.py --packages ipykernel nbconvert
uv run tools/tide.py --org jupyter --only-liftable # hide packages without an estimate
```

`--org` and `--user` can be repeated and combined. `--packages` takes every
argument after it, so put it last. If the PyPI page is blocked by Fastly, the
script prints a JavaScript snippet to run in a browser console on that page;
its output can be passed to `--packages`.

# Misc Security Information

For credential that _must be shared_, or for safekeeping, Jupyter has a team [1Password](https://jupyter.1password.com/)
account which has been graciously provided by the
[1Password-team-open-source](https://github.com/1Password/1password-teams-open-source/pull/441).

If you would like to join us, please contact the Jupyter Security Council at security-council [at] jupyter.org.


