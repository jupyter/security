# https://packaging.python.org/en/latest/specifications/inline-script-metadata/
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "aiohttp",
#   "diskcache",
#   "humanize",
#   "rich",
# ]
# ///
"""Jupyter Repository Activity Tracker.

For every repository across all Jupyter-related GitHub organizations, report:

* the date/time of the last commit (on the default branch),
* the date/time of the most recently opened issue that is still open,
* the date/time of the most recently opened pull request that is still open,
* the date/time of the last action performed by a maintainer.

The "last maintainer action" is the most recent event in the repository's public
event stream that either (a) was performed by a known org member, or (b) required
write/admin access — a push, a *merged* pull request, a release, a tag/branch
create-or-delete, or a membership change. This catches maintainers who merge or
push even when their org membership is private. Note that the GitHub events API
only exposes public events from roughly the last 90 days, so this is a best-effort
proxy that can read as "never" for repositories quiet for longer than that.

All GitHub API responses are cached on disk (via ``diskcache``) so that repeated
runs stay well under the API rate limit. Provide a read-only token via the
``GH_TOKEN`` environment variable::

    GH_TOKEN=ghp_xxx uv run tools/repo_activity.py

Requires only the ``public_repo`` / read-only scope. Owner-level access is not
needed, but a token that can see private org repos will include them.
"""

from __future__ import annotations

import argparse
import asyncio
import html
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone
from itertools import count
from typing import Any, Optional

import aiohttp
import diskcache
import humanize
from rich import print
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.table import Table

# Same set of orgs tracked by tools/all_repos.py and tools/last_user_activity.py.
default_orgs = [
    "binder-examples",
    "binderhub-ci-repos",
    "ipython",
    "jupyter",
    "jupyter-attic",
    "jupyter-book",
    "jupyter-governance",
    "jupyter-incubator",
    "jupyter-resources",
    "jupyter-server",
    "jupyter-standard",
    "jupyter-standards",
    "jupyter-widgets",
    "jupyter-xeus",
    "jupytercon",
    "jupyterhub",
    "jupyterlab",
    "voila-dashboards",
    "voila-gallery",
    "pickleshare",
]

API = "https://api.github.com"

token = os.getenv("GH_TOKEN")
if not token:
    print("[red]Error: GH_TOKEN environment variable not set[/red]")
    print("Provide a read-only GitHub token: [blue]GH_TOKEN=ghp_xxx uv run tools/repo_activity.py[/blue]")
    exit(1)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}

# Monthly cache directory, matching the convention in tools/all_repos.py.
CACHE_DIR = f"github_cache-repo_activity-{datetime.now().strftime('%Y%m')}"
cache = diskcache.Cache(CACHE_DIR)

# Throttle concurrent in-flight requests to be gentle on the API.
semaphore = asyncio.Semaphore(15)


class Stats:
    """Live counters shared across all requests, shown in the progress bars."""

    def __init__(self) -> None:
        self.requests = 0  # actual network fetches this run (cache misses)
        self.rate_remaining: Optional[int] = None
        self.rate_limit: Optional[int] = None

    def note_response(self, response: aiohttp.ClientResponse) -> None:
        self.requests += 1
        rem = response.headers.get("X-RateLimit-Remaining")
        lim = response.headers.get("X-RateLimit-Limit")
        if rem is not None:
            self.rate_remaining = int(rem)
        if lim is not None:
            self.rate_limit = int(lim)

    def rate_str(self) -> str:
        rem = self.rate_remaining
        rem = "?" if rem is None else str(rem)
        return f"API ~{rem} left · {self.requests} req this run"


stats = Stats()


def parse_dt(value: Optional[str]) -> Optional[datetime]:
    """Parse a GitHub ISO-8601 timestamp into an aware datetime."""
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def ago(dt: Optional[datetime]) -> str:
    """Human-friendly 'x days ago' for a datetime, or a red 'never'."""
    if dt is None:
        return "[red]never[/red]"
    now = datetime.now(dt.tzinfo or timezone.utc)
    return humanize.naturaltime(now - dt)


async def cached_get(
    session: aiohttp.ClientSession,
    url: str,
    *,
    expire: int,
    debug: bool = False,
    req_headers: Optional[dict] = None,
) -> Any:
    """GET ``url`` returning parsed JSON, backed by the on-disk cache.

    A ``None`` result is cached as well (e.g. a 404 or an empty list) so that
    known-empty resources are not re-fetched on every run. ``req_headers``
    overrides the default GitHub auth headers (used for non-GitHub hosts such
    as PyPI, which must not receive the token).
    """
    cache_key = f"GET {url}"
    sentinel = object()
    cached = cache.get(cache_key, default=sentinel, retry=True)
    if cached is not sentinel:
        if debug:
            print(f"[cyan]cache hit[/cyan] {url}")
        return cached

    async with semaphore:
        if debug:
            print(f"[yellow]fetch[/yellow] {url}")
        async with session.get(url, headers=req_headers or headers) as response:
            stats.note_response(response)
            if response.status == 200:
                data = await response.json()
            elif response.status in (403, 404, 409, 451):
                # 404/409 (empty repo), 403/451 (blocked/DMCA): nothing to see.
                data = None
            else:
                text = await response.text()
                print(f"[red]HTTP {response.status} for {url}: {text[:120]}[/red]")
                data = None

    cache.set(cache_key, data, expire=expire)
    return data


async def get_org_members(
    session: aiohttp.ClientSession, org: str, *, expire: int, debug: bool
) -> set[str]:
    """Return the set of (public) member logins for an org."""
    logins: set[str] = set()
    for page in count(1):
        url = f"{API}/orgs/{org}/members?per_page=100&page={page}"
        members = await cached_get(session, url, expire=expire, debug=debug)
        if not members:
            break
        logins.update(m["login"] for m in members)
        if len(members) < 100:
            break
    return logins


async def list_repos_for_org(
    session: aiohttp.ClientSession,
    org: str,
    *,
    expire: int,
    include_archived: bool,
    debug: bool,
) -> list[dict]:
    """Return repo objects for an org (optionally excluding archived ones)."""
    repos: list[dict] = []
    for page in count(1):
        url = f"{API}/orgs/{org}/repos?per_page=100&page={page}&type=all"
        page_repos = await cached_get(session, url, expire=expire, debug=debug)
        if not page_repos:
            break
        repos.extend(page_repos)
        if len(page_repos) < 100:
            break
    if not include_archived:
        repos = [r for r in repos if not r.get("archived")]
    return repos


async def last_commit(
    session: aiohttp.ClientSession, org: str, repo: str, *, expire: int, debug: bool
) -> Optional[datetime]:
    url = f"{API}/repos/{org}/{repo}/commits?per_page=1"
    data = await cached_get(session, url, expire=expire, debug=debug)
    if not data:
        return None
    commit = data[0].get("commit", {})
    # Prefer committer date, fall back to author date.
    date = commit.get("committer", {}).get("date") or commit.get("author", {}).get("date")
    return parse_dt(date)


async def last_open_issue(
    session: aiohttp.ClientSession, org: str, repo: str, *, expire: int, debug: bool
) -> Optional[datetime]:
    """Creation time of the most recently opened, still-open issue.

    The issues endpoint also returns PRs, so entries with a ``pull_request``
    key are skipped.
    """
    url = (
        f"{API}/repos/{org}/{repo}/issues"
        "?state=open&sort=created&direction=desc&per_page=20"
    )
    data = await cached_get(session, url, expire=expire, debug=debug)
    if not data:
        return None
    for issue in data:
        if "pull_request" in issue:
            continue
        return parse_dt(issue.get("created_at"))
    return None


_LINK_LAST = re.compile(r'[?&]page=(\d+)[^>]*>;\s*rel="last"')


async def open_pr_info(
    session: aiohttp.ClientSession, org: str, repo: str, *, expire: int, debug: bool
) -> tuple[int, Optional[datetime]]:
    """Return ``(open_pr_count, newest_open_pr_created_at)``.

    The count comes from the ``Link`` header's ``rel="last"`` page number when
    the result is paginated (``per_page=1`` → one page == one PR), so this is a
    single request rather than a full listing.
    """
    cache_key = f"open_pr_info {org}/{repo}"
    sentinel = object()
    cached = cache.get(cache_key, default=sentinel, retry=True)
    if cached is not sentinel:
        count, newest = cached
        return count, parse_dt(newest)

    url = (
        f"{API}/repos/{org}/{repo}/pulls"
        "?state=open&sort=created&direction=desc&per_page=1"
    )
    async with semaphore:
        if debug:
            print(f"[yellow]fetch[/yellow] {url}")
        async with session.get(url, headers=headers) as response:
            stats.note_response(response)
            if response.status != 200:
                cache.set(cache_key, (0, None), expire=expire)
                return 0, None
            data = await response.json()
            link = response.headers.get("Link", "")

    newest_iso = data[0].get("created_at") if data else None
    match = _LINK_LAST.search(link)
    count = int(match.group(1)) if match else len(data)
    cache.set(cache_key, (count, newest_iso), expire=expire)
    return count, parse_dt(newest_iso)


PYPI_HEADERS = {"User-Agent": "jupyter-security/repo_activity"}


def load_repo_packages(path: str) -> dict[tuple[str, str], list[str]]:
    """Parse ``all_repos.txt`` into ``{(org, repo): [pypi_package, ...]}``.

    Lines look like ``org/repo : <spec>`` where the spec is ``<none>`` or empty
    (no package), ``-`` (eponymous: package name == repo name with ``_``→``-``),
    a bare package name, or a full ``https://pypi.org/project/<name>`` URL. A
    repo may appear on several lines to map to several packages.
    """
    mapping: dict[tuple[str, str], list[str]] = {}
    try:
        lines = pathlib.Path(path).read_text().splitlines()
    except FileNotFoundError:
        print(f"[yellow]Package mapping file not found: {path} (skipping releases)[/yellow]")
        return mapping
    for line in lines:
        if line.startswith("#") or ":" not in line:
            continue
        slug, spec = line.split(":", 1)
        slug = slug.strip(" /")
        if "/" not in slug:
            continue
        org, repo = slug.split("/", 1)
        spec = spec.replace("<none>", "").strip(" /")
        if not spec:
            continue
        package = repo.replace("_", "-") if spec == "-" else spec.rstrip("/").split("/")[-1]
        if package:
            mapping.setdefault((org, repo), [])
            if package not in mapping[(org, repo)]:
                mapping[(org, repo)].append(package)
    return mapping


async def last_package_release(
    session: aiohttp.ClientSession, package: str, *, expire: int, debug: bool
) -> tuple[Optional[datetime], Optional[str]]:
    """Return ``(last_upload_datetime, version)`` for a PyPI package.

    Uses the most recent file upload across all releases, so yanked or
    out-of-order version numbers don't matter.
    """
    url = f"https://pypi.org/pypi/{package}/json"
    data = await cached_get(
        session, url, expire=expire, debug=debug, req_headers=PYPI_HEADERS
    )
    if not data:
        return None, None
    best_dt: Optional[datetime] = None
    best_ver: Optional[str] = None
    for version, files in (data.get("releases") or {}).items():
        for f in files:
            dt = parse_dt(f.get("upload_time_iso_8601") or f.get("upload_time"))
            if dt and (best_dt is None or dt > best_dt):
                best_dt, best_ver = dt, version
    return best_dt, best_ver


async def last_maintainer_action(
    session: aiohttp.ClientSession,
    org: str,
    repo: str,
    members: set[str],
    *,
    expire: int,
    debug: bool,
) -> tuple[Optional[datetime], Optional[str], Optional[str]]:
    """Most recent repo event that represents a maintainer action.

    An event counts as a maintainer action when either the actor is a known org
    member, or the event itself requires write/admin access (a push, a *merged*
    pull request, a release, a tag/branch create-or-delete, or a membership
    change). This catches maintainers who merge/push even when their org
    membership is private, or who have write access without being org members.

    Returns ``(datetime, actor_login, description)``. The events API is limited
    to public events from roughly the last 90 days, so quiet repos may still
    report no maintainer action within that window.
    """
    for page in count(1):
        url = f"{API}/repos/{org}/{repo}/events?per_page=100&page={page}"
        events = await cached_get(session, url, expire=expire, debug=debug)
        if not events:
            break
        # Events are returned newest-first.
        for event in events:
            label = maintainer_action_label(event, members)
            if label is not None:
                actor = (event.get("actor") or {}).get("login")
                return parse_dt(event.get("created_at")), actor, label
        if len(events) < 100 or page >= 3:
            # The events feed is capped at 300 events / 90 days anyway.
            break
    return None, None, None


# Event types that inherently require write/admin access to the repository.
_PRIVILEGED_EVENTS = {"PushEvent", "ReleaseEvent", "MemberEvent", "GollumEvent"}


def maintainer_action_label(event: dict, members: set[str]) -> Optional[str]:
    """Return a short description if ``event`` is a maintainer action, else None."""
    etype = event.get("type") or ""
    payload = event.get("payload") or {}
    actor = (event.get("actor") or {}).get("login")

    if etype in _PRIVILEGED_EVENTS:
        return etype
    if etype == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        if payload.get("action") == "closed" and pr.get("merged"):
            num = payload.get("number") or pr.get("number")
            return f"merged PR #{num}" if num else "merged PR"
    if etype in ("CreateEvent", "DeleteEvent") and payload.get("ref_type") in (
        "branch",
        "tag",
    ):
        return f"{etype[:-5].lower()}d {payload.get('ref_type')}"
    # Any action performed by a known org member also counts (e.g. commenting,
    # labelling, opening/closing issues).
    if actor in members:
        return etype
    return None


async def gather_repo(
    session: aiohttp.ClientSession,
    org: str,
    repo: dict,
    members: set[str],
    packages: list[str],
    *,
    expire: int,
    debug: bool,
) -> dict:
    name = repo["name"]
    commit, issue, pr_info, maint, *releases = await asyncio.gather(
        last_commit(session, org, name, expire=expire, debug=debug),
        last_open_issue(session, org, name, expire=expire, debug=debug),
        open_pr_info(session, org, name, expire=expire, debug=debug),
        last_maintainer_action(
            session, org, name, members, expire=expire, debug=debug
        ),
        *(last_package_release(session, p, expire=expire, debug=debug) for p in packages),
    )
    open_pr_count, pr = pr_info
    maint_dt, maint_actor, maint_type = maint
    # GitHub's open_issues_count includes pull requests; subtract them to get
    # the count of genuine open issues. No extra request needed.
    open_issue_count = max(0, repo.get("open_issues_count", 0) - open_pr_count)
    # Release info for each mapped PyPI package, plus the most recent across all.
    package_info = []
    last_release = None
    for pkg, (rel_dt, ver) in zip(packages, releases):
        package_info.append({"name": pkg, "version": ver, "last_release": rel_dt})
        if rel_dt and (last_release is None or rel_dt > last_release):
            last_release = rel_dt
    return {
        "org": org,
        "repo": name,
        "archived": repo.get("archived", False),
        "private": repo.get("private", False),
        "last_commit": commit,
        "last_open_issue": issue,
        "last_open_pr": pr,
        "open_issue_count": open_issue_count,
        "open_pr_count": open_pr_count,
        "last_maintainer_action": maint_dt,
        "maintainer_actor": maint_actor,
        "maintainer_event": maint_type,
        "last_release": last_release,
        "packages": package_info,
    }


async def check_rate_limit(session: aiohttp.ClientSession) -> None:
    async with session.get(f"{API}/rate_limit", headers=headers) as response:
        if response.status != 200:
            print(f"[red]Could not read rate limit: {response.status}[/red]")
            return
        data = await response.json()
        core = data["resources"]["core"]
        # /rate_limit itself does not count against the quota; seed the counters.
        stats.rate_remaining = core["remaining"]
        stats.rate_limit = core["limit"]
        reset = datetime.fromtimestamp(core["reset"])
        print(
            f"Rate limit: [bold]{core['remaining']}[/bold]/{core['limit']} remaining, "
            f"resets {humanize.naturaltime(reset)}"
        )
        if core["remaining"] < 50:
            print("[yellow]Warning: low rate limit; cached data will still work.[/yellow]")


def cache_size() -> str:
    try:
        path = pathlib.Path(CACHE_DIR)
        if path.exists():
            total = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            return f"{total / 1024 / 1024:.1f} MB"
    except Exception:
        pass
    return "unknown size"


async def main(
    orgs: list[str],
    *,
    include_archived: bool,
    expire: int,
    debug: bool,
    sort_key: str,
    json_path: Optional[str],
    html_path: Optional[str],
    packages_file: str,
) -> None:
    print(f"[blue]Cache: {CACHE_DIR} ({cache_size()}, {len(cache)} entries)[/blue]")
    repo_packages = load_repo_packages(packages_file)
    n_pkgs = sum(len(v) for v in repo_packages.values())
    print(f"[blue]Loaded {n_pkgs} PyPI package(s) for {len(repo_packages)} repos from {packages_file}[/blue]")

    async with aiohttp.ClientSession() as session:
        async with session.get(f"{API}/user", headers=headers) as response:
            if response.status == 200:
                who = (await response.json())["login"]
                print(f"[blue]Authenticated as: {who}[/blue]")
            else:
                print(f"[red]Bad token ({response.status}). Need a valid GH_TOKEN.[/red]")
                sys.exit(1)

        await check_rate_limit(session)

        rows: list[dict] = []
        progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            transient=False,
        )
        with progress:
            # Phase 1: discover repos and members for every org (usually cached).
            list_task = progress.add_task("Listing orgs", total=len(orgs))
            org_members: dict[str, set[str]] = {}
            org_repos: dict[str, list[dict]] = {}
            for org in orgs:
                progress.update(
                    list_task,
                    description=f"Listing [bold]{org}[/bold] · {stats.rate_str()}",
                )
                org_members[org] = await get_org_members(
                    session, org, expire=expire, debug=debug
                )
                org_repos[org] = await list_repos_for_org(
                    session,
                    org,
                    expire=expire,
                    include_archived=include_archived,
                    debug=debug,
                )
                progress.advance(list_task)
            progress.update(
                list_task, description=f"Listed {len(orgs)} orgs · {stats.rate_str()}"
            )

            total_repos = sum(len(r) for r in org_repos.values())
            # Rough upper bound: commit + issue + pr + up to 3 event pages per
            # repo, plus one PyPI request per mapped package.
            est = total_repos * 6 + n_pkgs
            progress.console.print(
                f"[dim]{total_repos} repos to scan · up to ~{est} API requests "
                f"before cache hits.[/dim]"
            )

            overall = progress.add_task("[bold]All repos[/bold]", total=total_repos)

            for org in orgs:
                repos = org_repos[org]
                members = org_members[org]
                if not repos:
                    continue
                org_task = progress.add_task(f"[cyan]{org}[/cyan]", total=len(repos))

                async def process(repo: dict, *, org=org, members=members) -> dict:
                    rtask = progress.add_task(
                        f"  [dim]{org}/{repo['name']}[/dim]", total=None
                    )
                    try:
                        packages = repo_packages.get((org, repo["name"]), [])
                        return await gather_repo(
                            session, org, repo, members, packages,
                            expire=expire, debug=debug,
                        )
                    finally:
                        progress.remove_task(rtask)
                        progress.advance(org_task)
                        progress.advance(overall)
                        progress.update(
                            overall,
                            description=f"[bold]All repos[/bold] · {stats.rate_str()}",
                        )

                org_rows = await asyncio.gather(*(process(r) for r in repos))
                rows.extend(org_rows)
                progress.remove_task(org_task)

    render(rows, sort_key=sort_key)
    if json_path:
        export_json(rows, json_path, sort_key=sort_key)
    if html_path:
        export_html(rows, html_path, sort_key=sort_key)


# Distant-past sentinel so that "never" sorts last regardless of direction.
_EPOCH = datetime.fromtimestamp(0, tz=timezone.utc)


def render(rows: list[dict], *, sort_key: str) -> None:
    def key(row: dict):
        return row.get(sort_key) or _EPOCH

    rows = sorted(rows, key=key, reverse=True)

    table = Table(title="Jupyter repository activity", show_lines=False)
    table.add_column("repo", style="cyan", no_wrap=True)
    table.add_column("visibility")
    table.add_column("archived")
    table.add_column("open\nissues", justify="right")
    table.add_column("open\nPRs", justify="right")
    table.add_column("last commit")
    table.add_column("last open issue")
    table.add_column("last open PR")
    table.add_column("last maintainer action")
    table.add_column("last release")

    for row in rows:
        visibility = (
            "[magenta]private[/magenta]" if row["private"] else "[green]public[/green]"
        )
        archived = "[yellow]yes[/yellow]" if row["archived"] else "[dim]no[/dim]"
        maint = ago(row["last_maintainer_action"])
        if row["maintainer_actor"]:
            maint += f" [dim]({row['maintainer_actor']}, {row['maintainer_event']})[/dim]"
        release = ago(row["last_release"])
        pkgs = row.get("packages", [])
        if len(pkgs) > 1:
            release += f" [dim]({len(pkgs)} pkgs)[/dim]"
        elif len(pkgs) == 1 and pkgs[0]["version"]:
            release += f" [dim]({pkgs[0]['name']} {pkgs[0]['version']})[/dim]"
        table.add_row(
            f"{row['org']}/{row['repo']}",
            visibility,
            archived,
            str(row["open_issue_count"]),
            str(row["open_pr_count"]),
            ago(row["last_commit"]),
            ago(row["last_open_issue"]),
            ago(row["last_open_pr"]),
            maint,
            release,
        )

    print(table)
    print(
        f"[dim]{len(rows)} repositories. Maintainer actions come from the public "
        "events feed (~90 day / public-only window).[/dim]"
    )


def _iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def row_to_dict(row: dict) -> dict:
    """A JSON-serializable view of a result row."""
    return {
        "org": row["org"],
        "repo": row["repo"],
        "full_name": f"{row['org']}/{row['repo']}",
        "url": f"https://github.com/{row['org']}/{row['repo']}",
        "visibility": "private" if row["private"] else "public",
        "archived": bool(row["archived"]),
        "open_issue_count": row["open_issue_count"],
        "open_pr_count": row["open_pr_count"],
        "last_commit": _iso(row["last_commit"]),
        "last_open_issue": _iso(row["last_open_issue"]),
        "last_open_pr": _iso(row["last_open_pr"]),
        "last_maintainer_action": _iso(row["last_maintainer_action"]),
        "maintainer_actor": row["maintainer_actor"],
        "maintainer_event": row["maintainer_event"],
        "last_release": _iso(row["last_release"]),
        "packages": [
            {"name": p["name"], "version": p["version"], "last_release": _iso(p["last_release"])}
            for p in row.get("packages", [])
        ],
    }


def export_json(rows: list[dict], path: str, *, sort_key: str) -> None:
    ordered = sorted(rows, key=lambda r: r.get(sort_key) or _EPOCH, reverse=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "count": len(ordered),
        "note": (
            "last_maintainer_action derives from the public events feed "
            "(~90 day / public-only window); null means no such event was found."
        ),
        "repositories": [row_to_dict(r) for r in ordered],
    }
    pathlib.Path(path).write_text(json.dumps(payload, indent=2))
    print(f"[green]Wrote JSON to {path}[/green]")


def export_html(rows: list[dict], path: str, *, sort_key: str) -> None:
    ordered = sorted(rows, key=lambda r: r.get(sort_key) or _EPOCH, reverse=True)
    data = [row_to_dict(r) for r in ordered]
    generated = datetime.now(timezone.utc).isoformat()
    # Data is embedded as JSON and the table is rendered client-side, with a
    # search box and click-to-sort headers. Fully self-contained (no CDN), so
    # the file works offline.
    doc = _HTML_TEMPLATE.replace("__GENERATED__", html.escape(generated)).replace(
        "__DATA__", json.dumps(data)
    )
    pathlib.Path(path).write_text(doc)
    print(f"[green]Wrote HTML to {path}[/green]")


_HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Jupyter repository activity</title>
<style>
  :root {
    --bg: #ffffff; --fg: #1b1f24; --muted: #6a737d; --line: #d0d7de;
    --head: #f6f8fa; --accent: #0969da; --priv: #8250df; --arch: #9a6700;
  }
  @media (prefers-color-scheme: dark) {
    :root {
      --bg: #0d1117; --fg: #e6edf3; --muted: #8b949e; --line: #30363d;
      --head: #161b22; --accent: #4493f8; --priv: #d2a8ff; --arch: #d29922;
    }
  }
  * { box-sizing: border-box; }
  body { margin: 0; padding: 1.2rem; background: var(--bg); color: var(--fg);
         font: 14px/1.45 -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif; }
  h1 { font-size: 1.15rem; margin: 0 0 .2rem; }
  .meta { color: var(--muted); margin-bottom: .8rem; }
  .controls { display: flex; flex-wrap: wrap; gap: .6rem 1rem; align-items: center;
              margin-bottom: .8rem; }
  input[type=search] { padding: .4rem .6rem; min-width: 16rem; border: 1px solid var(--line);
                       border-radius: 6px; background: var(--bg); color: var(--fg); }
  label { color: var(--muted); user-select: none; }
  .count { color: var(--muted); margin-left: auto; }
  .wrap { overflow-x: auto; border: 1px solid var(--line); border-radius: 8px; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: .45rem .6rem; border-bottom: 1px solid var(--line);
           white-space: nowrap; }
  th { position: sticky; top: 0; background: var(--head); cursor: pointer; user-select: none; }
  th .arrow { color: var(--muted); font-size: .8em; }
  tbody tr:hover { background: color-mix(in srgb, var(--accent) 8%, transparent); }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }
  .tag { font-size: .75rem; padding: .05rem .4rem; border-radius: 999px; border: 1px solid var(--line); }
  .priv { color: var(--priv); border-color: var(--priv); }
  .pub { color: var(--muted); }
  .arch { color: var(--arch); border-color: var(--arch); }
  .muted { color: var(--muted); }
  .delta { font-size: .85em; }
  .delta-fresh { color: #1a7f37; }
  .delta-mid   { color: #9a6700; }
  .delta-old   { color: #bc4c00; }
  .delta-stale { color: #cf222e; }
  @media (prefers-color-scheme: dark) {
    .delta-fresh { color: #3fb950; }
    .delta-mid   { color: #d4a72c; }
    .delta-old   { color: #ec8e2c; }
    .delta-stale { color: #f85149; }
  }
  td.date { color: var(--fg); }
  td.never { color: var(--muted); font-style: italic; }
  #colToggles { font-size: .9em; }
  #colToggles .muted { margin-right: .2rem; }
</style>
<style id="colStyle"></style>
</head>
<body>
  <h1>Jupyter repository activity</h1>
  <div class="meta">Generated <span id="gen"></span> · times shown relative to now
    (hover a cell for the exact timestamp). Last maintainer action comes from the public
    events feed (~90&nbsp;day / public-only window).</div>
  <div class="controls">
    <input id="q" type="search" placeholder="Filter by org / repo…" autocomplete="off">
    <label><input type="checkbox" id="onlyPrivate"> private only</label>
    <label><input type="checkbox" id="hideArchived"> hide archived</label>
    <span class="count" id="count"></span>
  </div>
  <div class="controls" id="colToggles"><span class="muted">Columns:</span></div>
  <div class="wrap">
    <table id="t">
      <thead>
        <tr>
          <th data-key="full_name" data-type="text">Repository <span class="arrow"></span></th>
          <th data-key="visibility" data-type="text">Visibility <span class="arrow"></span></th>
          <th data-key="archived" data-type="bool">Archived <span class="arrow"></span></th>
          <th data-key="open_issue_count" data-type="num">Open issues <span class="arrow"></span></th>
          <th data-key="open_pr_count" data-type="num">Open PRs <span class="arrow"></span></th>
          <th data-key="last_commit" data-type="date">Last commit <span class="arrow"></span></th>
          <th data-key="last_open_issue" data-type="date">Last open issue <span class="arrow"></span></th>
          <th data-key="last_open_pr" data-type="date">Last open PR <span class="arrow"></span></th>
          <th data-key="last_maintainer_action" data-type="date">Last maintainer action <span class="arrow"></span></th>
          <th data-key="last_release" data-type="date">Last release <span class="arrow"></span></th>
        </tr>
      </thead>
      <tbody></tbody>
    </table>
  </div>
<script>
const DATA = __DATA__;
const GENERATED = "__GENERATED__";
document.getElementById("gen").textContent = GENERATED;

const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g,
  c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const ts = v => v ? Date.parse(v) : -Infinity;
const DATE_KEYS = new Set(
  ["last_commit","last_open_issue","last_open_pr","last_maintainer_action","last_release"]);

// Signed, compact time-delta between two ISO timestamps, e.g. "+2mo", "-5d".
function fmtDelta(laterMs, refMs) {
  const diff = laterMs - refMs;
  const sign = diff >= 0 ? "+" : "−";
  let s = Math.abs(Math.round(diff / 1000));
  const units = [["y",31536000],["mo",2592000],["d",86400],["h",3600],["m",60]];
  for (const [name, secs] of units) {
    const n = Math.floor(s / secs);
    if (n >= 1) return sign + n + name;
  }
  return "0";
}

// Colour the delta by magnitude: green < 2w, yellow < 8w, orange < 16w, else red.
const WEEK = 604800000;
function deltaClass(absMs) {
  if (absMs < 2 * WEEK) return "delta-fresh";
  if (absMs < 8 * WEEK) return "delta-mid";
  if (absMs < 16 * WEEK) return "delta-old";
  return "delta-stale";
}

// Parenthetical delta of this cell's value vs the current sort column's value,
// shown only while sorting by a (different) date column and both dates exist.
function deltaSpan(key, row) {
  if (!DATE_KEYS.has(sortKey) || key === sortKey) return "";
  if (!row[key] || !row[sortKey]) return "";
  const diff = Date.parse(row[key]) - Date.parse(row[sortKey]);
  return ` <span class="delta ${deltaClass(Math.abs(diff))}">(${fmtDelta(Date.parse(row[key]), Date.parse(row[sortKey]))})</span>`;
}

function rel(v) {
  if (!v) return {text: "never", cls: "never", title: ""};
  const d = Date.parse(v), now = Date.now();
  let s = Math.max(0, Math.floor((now - d) / 1000));
  const units = [["year",31536000],["month",2592000],["day",86400],["hour",3600],["minute",60]];
  for (const [name, secs] of units) {
    const n = Math.floor(s / secs);
    if (n >= 1) return {text: n + " " + name + (n>1?"s":"") + " ago", cls: "date", title: new Date(d).toISOString()};
  }
  return {text: "just now", cls: "date", title: new Date(d).toISOString()};
}

let sortKey = "last_maintainer_action", sortDir = -1;

function render() {
  const q = document.getElementById("q").value.trim().toLowerCase();
  const onlyPrivate = document.getElementById("onlyPrivate").checked;
  const hideArchived = document.getElementById("hideArchived").checked;

  let rows = DATA.filter(r => {
    if (q && !r.full_name.toLowerCase().includes(q)) return false;
    if (onlyPrivate && r.visibility !== "private") return false;
    if (hideArchived && r.archived) return false;
    return true;
  });

  const type = document.querySelector(`th[data-key="${sortKey}"]`).dataset.type;
  rows.sort((a, b) => {
    let av, bv;
    if (type === "date") { av = ts(a[sortKey]); bv = ts(b[sortKey]); }
    else if (type === "num") { av = a[sortKey]||0; bv = b[sortKey]||0; }
    else if (type === "bool") { av = a[sortKey]?1:0; bv = b[sortKey]?1:0; }
    else { av = (a[sortKey]||"").toLowerCase(); bv = (b[sortKey]||"").toLowerCase(); }
    if (av < bv) return -1 * sortDir;
    if (av > bv) return 1 * sortDir;
    return a.full_name.localeCompare(b.full_name);
  });

  const tb = document.querySelector("#t tbody");
  tb.innerHTML = "";
  for (const r of rows) {
    const tr = document.createElement("tr");
    const vis = r.visibility === "private"
      ? '<span class="tag priv">private</span>'
      : '<span class="tag pub">public</span>';
    const arch = r.archived
      ? '<span class="tag arch">yes</span>'
      : '<span class="muted">no</span>';
    const cells = [];
    cells.push(`<td class="col-full_name"><a href="${esc(r.url)}" target="_blank" rel="noopener">${esc(r.full_name)}</a></td>`);
    cells.push(`<td class="col-visibility">${vis}</td>`);
    cells.push(`<td class="col-archived">${arch}</td>`);
    cells.push(`<td class="col-open_issue_count" style="text-align:right">${r.open_issue_count}</td>`);
    cells.push(`<td class="col-open_pr_count" style="text-align:right">${r.open_pr_count}</td>`);
    for (const k of ["last_commit","last_open_issue","last_open_pr"]) {
      const x = rel(r[k]);
      cells.push(`<td class="col-${k} ${x.cls}" title="${x.title}">${x.text}${deltaSpan(k, r)}</td>`);
    }
    const m = rel(r.last_maintainer_action);
    let who = "";
    if (r.maintainer_actor) who = ` <span class="muted">(${esc(r.maintainer_actor)}, ${esc(r.maintainer_event)})</span>`;
    cells.push(`<td class="col-last_maintainer_action ${m.cls}" title="${m.title}">${m.text}${deltaSpan("last_maintainer_action", r)}${who}</td>`);
    const packages = r.packages || [];
    const rr = rel(r.last_release);
    const pkgs = packages.map(p => p.name + (p.version ? " " + p.version : "")).join(", ");
    const pkgTitle = pkgs ? esc(pkgs) : "no mapped PyPI package";
    // Link the date to the PyPI project page when exactly one package maps.
    let relText = rr.text;
    if (packages.length === 1 && r.last_release) {
      const purl = "https://pypi.org/project/" + encodeURIComponent(packages[0].name) + "/";
      relText = `<a href="${esc(purl)}" target="_blank" rel="noopener">${rr.text}</a>`;
    }
    let pkgTag = "";
    if (packages.length > 1) pkgTag = ` <span class="muted">(${packages.length} pkgs)</span>`;
    cells.push(`<td class="col-last_release ${rr.cls}" title="${rr.title || pkgTitle}">${relText}${deltaSpan("last_release", r)}${pkgTag}</td>`);
    tr.innerHTML = cells.join("");
    tb.appendChild(tr);
  }
  document.getElementById("count").textContent = rows.length + " / " + DATA.length + " repos";
  document.querySelectorAll("th .arrow").forEach(a => a.textContent = "");
  const th = document.querySelector(`th[data-key="${sortKey}"] .arrow`);
  if (th) th.textContent = sortDir === -1 ? "▼" : "▲";
}

document.querySelectorAll("th").forEach(th => th.addEventListener("click", () => {
  const k = th.dataset.key;
  if (k === sortKey) sortDir *= -1;
  else { sortKey = k; sortDir = th.dataset.type === "date" ? -1 : 1; }
  render();
}));
["q","onlyPrivate","hideArchived"].forEach(id =>
  document.getElementById(id).addEventListener("input", render));

// Per-column show/hide toggles, generated from the table headers.
const hiddenCols = new Set();
function applyCols() {
  document.getElementById("colStyle").textContent =
    [...hiddenCols].map(k => `.col-${k}{display:none}`).join("");
}
const colWrap = document.getElementById("colToggles");
document.querySelectorAll("#t thead th").forEach(th => {
  const key = th.dataset.key;
  th.classList.add("col-" + key);
  const label = th.textContent.replace(/[▲▼]/g, "").trim();
  const lbl = document.createElement("label");
  const cb = document.createElement("input");
  cb.type = "checkbox";
  cb.checked = true;
  cb.addEventListener("change", () => {
    if (cb.checked) hiddenCols.delete(key);
    else hiddenCols.add(key);
    applyCols();
  });
  lbl.appendChild(cb);
  lbl.appendChild(document.createTextNode(" " + label));
  colWrap.appendChild(lbl);
});

render();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jupyter repository activity tracker")
    parser.add_argument(
        "--orgs",
        nargs="+",
        default=default_orgs,
        help="GitHub organizations to scan (default: all Jupyter orgs)",
    )
    parser.add_argument(
        "--skip-archived",
        action="store_true",
        help="Exclude archived repositories (default: include them, marked 'archived')",
    )
    parser.add_argument(
        "--cache-ttl",
        type=int,
        default=6 * 3600,
        help="Seconds before a cached API response expires (default: 21600 = 6h)",
    )
    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the on-disk cache before running",
    )
    parser.add_argument(
        "--sort-by",
        choices=[
            "last_commit",
            "last_open_issue",
            "last_open_pr",
            "last_maintainer_action",
            "last_release",
        ],
        default="last_maintainer_action",
        help="Column to sort the report by (most recent first)",
    )
    parser.add_argument(
        "--packages-file",
        default="all_repos.txt",
        metavar="PATH",
        help="repo→PyPI package mapping used for last-release dates (default: all_repos.txt)",
    )
    parser.add_argument(
        "--json",
        dest="json_path",
        metavar="PATH",
        help="Also write the results as JSON to PATH",
    )
    parser.add_argument(
        "--html",
        dest="html_path",
        metavar="PATH",
        help="Also write a self-contained HTML table (search + click-to-sort) to PATH",
    )
    parser.add_argument("--debug", action="store_true", help="Verbose cache/fetch logs")
    args = parser.parse_args()

    if args.clear_cache:
        cache.clear()
        print("[green]Cache cleared.[/green]")

    asyncio.run(
        main(
            args.orgs,
            include_archived=not args.skip_archived,
            expire=args.cache_ttl,
            debug=args.debug,
            sort_key=args.sort_by,
            json_path=args.json_path,
            html_path=args.html_path,
            packages_file=args.packages_file,
        )
    )
