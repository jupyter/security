"""GitHub Organization Activity Tracker

This module tracks and reports the last activity of members across GitHub organizations.
It implements disk-based caching to minimize API requests and respect rate limits.
"""

import argparse
import asyncio
import os
import pathlib
import sys
from datetime import datetime, timedelta, timezone
from itertools import count
from pathlib import Path
from typing import Dict, List, Optional

import aiohttp
import diskcache
import humanize
from rich import print

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

token = os.getenv("GH_TOKEN")
if not token:
    print("[red]Error: GH_TOKEN environment variable not set[/red]")
    exit(1)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
}


class DateTimeCache(diskcache.Cache):
    """Custom cache class that handles datetime serialization."""

    def __setitem__(self, key, value):
        """Override to serialize datetime objects."""
        if isinstance(value, datetime):
            value = {"__datetime__": value.isoformat()}
        super().__setitem__(key, value)

    def __getitem__(self, key):
        """Override to deserialize datetime objects."""
        value = super().__getitem__(key)
        if isinstance(value, dict) and "__datetime__" in value:
            return datetime.fromisoformat(value["__datetime__"])
        assert not isinstance(value, dict), value
        return value

    def get(self, key, default=None, retry=False):
        """Override to handle datetime deserialization in get method with retry."""
        try:
            value = super().get(key, default=default, retry=retry)
            if isinstance(value, dict) and "__datetime__" in value:
                return datetime.fromisoformat(value["__datetime__"])
            return value

        except KeyError:
            return default


# Configure DiskCache in the current directory
# todo: auto clear after ~24 hours
CACHE_DIR = "github_cache"
cache = DateTimeCache(CACHE_DIR)


async def get_org_members(
    session: aiohttp.ClientSession, org: str, debug: bool
) -> List[Dict]:
    """Fetch all members of a GitHub organization with caching.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The HTTP session to use for requests
    org : str
        The name of the GitHub organization

    Returns
    -------
    List[Dict]
        A list of dictionaries containing member information.
        Each dictionary contains at least:
        - 'login': str, the username
        - 'id': int, the user ID
        - 'type': str, usually 'User'

    Notes
    -----
    Results are cached for 24 hours to minimize API requests.
    Pagination is handled automatically (100 items per page).
    """
    cache_key = f"org_members_{org}"

    # Try to get from cache with retry
    cached_data = cache.get(cache_key, retry=True)
    if cached_data is not None:
        if debug:
            print(f"[cyan]Cache hit for {org} members[/cyan]")
        return cached_data

    print(f"[yellow]Cache miss for {org} members - fetching from API[/yellow]")
    members = []

    try:
        for page in count(1):
            url = f"https://api.github.com/orgs/{org}/members?page={page}&per_page=100"
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    print(
                        f"[red]Error fetching members for {org}: {response.status}[/red]"
                    )
                    break

                page_members = await response.json()
                if not page_members:
                    break

                members.extend(page_members)

        tasks = [check_user_admin(session, org, member["login"]) for member in members]
        admin_statuses = await asyncio.gather(*tasks)

        for member, is_owner in zip(members, admin_statuses):
            member["is_owner"] = is_owner

        # Cache the results
        cache[cache_key] = members  # Using __setitem__ instead of set()
        print(f"[green]Cached {len(members)} members for {org}[/green]")
        return members

    except Exception as e:
        print(f"[red]Error fetching members for {org}: {str(e)}[/red]")
        return []


async def get_user_activity(
    session: aiohttp.ClientSession, username: str, debug: bool
) -> Optional[datetime]:
    """Fetch the last public activity date for a GitHub user."""
    cache_key = f"user_activity_{username}"

    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        if debug:
            print(f"[cyan]Cache hit for {username} activity[/cyan]")
        assert isinstance(cached_data, datetime), cached_data
        return cached_data
    if debug:
        print(
            f"[yellow]Cache miss for {username} activity - fetching from API[/yellow]"
        )

    try:
        if debug:
            print(f"[blue]Getting activity for {username}[/blue]")
        url = f"https://api.github.com/users/{username}/events/public"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                if debug:
                    print(f"Got activity for {username}")
                events = await response.json()
                if events:
                    last_activity = datetime.fromisoformat(
                        events[0]["created_at"].replace("Z", "+00:00")
                    )
                    # Cache the results
                    assert isinstance(last_activity, datetime)
                    cache[cache_key] = (
                        last_activity  # Using __setitem__ instead of set()
                    )
                    if debug:
                        print(f"[green]Cached activity for {username}[/green]")
                    assert isinstance(last_activity, datetime)
                    return last_activity
                else:
                    if debug:
                        print(f"[yellow]No activity found for {username}[/yellow]")
                    cache[cache_key] = None  # Using __setitem__ instead of set()
            else:
                print(
                    f"[red]Error fetching activity for {username}: {response.status}[/red]"
                )
    except Exception as e:
        print(f"[red]Error fetching activity for {username}: {str(e)}[/red]")

    return None


def get_cache_size() -> str:
    """Get the current cache size in a human-readable format."""
    try:
        cache_path = pathlib.Path(CACHE_DIR)
        if cache_path.exists():
            total_size = sum(
                f.stat().st_size for f in cache_path.rglob("*") if f.is_file()
            )
            return f"{total_size / 1024 / 1024:.1f} MB"
    except Exception:
        pass
    return "unknown size"


def clear_cache() -> None:
    """Clear the disk cache."""
    try:
        cache.clear()
        print("[green]Cache cleared successfully[/green]")
    except Exception as e:
        print(f"[red]Error clearing cache: {str(e)}[/red]")


async def check_user_admin(
    session: aiohttp.ClientSession, org: str, username: str
) -> bool:
    url = f"https://api.github.com/orgs/{org}/memberships/{username}"
    async with session.get(url, headers=headers) as response:
        if response.status == 404:
            return False
        elif response.status != 200:
            print(
                f"[red]Error fetching membership for {username} in {org}: {response.status}[/red]"
            )
            return False
        return (await response.json())["role"] == "admin"


async def main(orgs, debug: bool, timelimit_days: int, config_file: str):
    """Main execution function."""
    # Show cache status
    print(f"[blue]Cache directory: {CACHE_DIR} (size: {get_cache_size()})[/blue]")
    print(f"[blue]Cache contains {len(cache)} items[/blue]")
    now = datetime.now(timezone.utc)
    manual_users = {}
    for line in Path(config_file).read_text().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        user, inviter, date_last_activity, reason = [x.strip() for x in line.split(":")]
        manual_users[user] = {
            "manual_last_activity": datetime.strptime(
                date_last_activity, "%Y-%m"
            ).replace(tzinfo=timezone.utc),
            "last_activity_reason": reason,
            "inviter": inviter,
        }
        if not manual_users[user]["last_activity_reason"]:
            print(
                f"[yellow]Warning: No last_activity_reason for {user['username']}, skipping[/yellow]"
            )
            continue
        if now < manual_users[user]["manual_last_activity"]:
            print(
                f"[red]Warning: manual_last_activity for {user['username']} is in the future, skipping[/red]"
            )
            continue
    # check who the current user is
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.github.com/user", headers=headers
        ) as response:
            if response.status == 200:
                user_data = await response.json()
                current_user = user_data["login"]
                print(f"[blue]Current user: {current_user}[/blue]")
            else:
                sys.exit(f"[red]Error fetching user data: {response.status}[/red]")

    async with aiohttp.ClientSession() as session:
        # Check rate limit
        async with session.get(
            "https://api.github.com/rate_limit", headers=headers
        ) as response:
            if response.status == 200:
                rate_data = await response.json()
                remaining = rate_data["resources"]["core"]["remaining"]
                reset_time = datetime.fromtimestamp(
                    rate_data["resources"]["core"]["reset"]
                )
                reset_in = humanize.naturaltime(reset_time)
                print(f"Rate limit remaining: {remaining}")
                print(f"Rate limit resets {reset_in}")
                if remaining < 100:
                    print(
                        f"[yellow]Warning: Low rate limit ({remaining} remaining)[/yellow]"
                    )
                    if remaining < 10:
                        print("[red]Aborting due to very low rate limit[/red]")
                        return

        # Get all members from all orgs
        all_members = {}
        org_owners = {}
        for org in orgs:
            members = await get_org_members(session, org, debug)
            for member in members:
                if member["login"] not in all_members:
                    all_members[member["login"]] = []
                all_members[member["login"]].append(org)
                if member.get("is_owner", None):
                    org_owners.setdefault(org, []).append(member["login"])

        # Get activity for each user
        tasks = []
        for username in all_members:
            task = get_user_activity(session, username, debug)
            tasks.append((username, task))

        results = await asyncio.gather(*(task for _, task in tasks))

        # Print results sorted by last activity
        user_activities = []
        for (username, _), last_activity in zip(tasks, results):
            if last_activity is not None:
                assert isinstance(last_activity, datetime), last_activity

            if last_activity is None:
                last_activity = manual_users.get(username, {}).get(
                    "manual_last_activity", None
                )
            user_activities.append(
                (
                    username,
                    last_activity if last_activity is not None else None,
                    all_members[username],
                )
            )

        admin_check_tasks = [
            check_user_admin(session, org, current_user) for org in orgs
        ]
        admin_check_results = await asyncio.gather(*admin_check_tasks)
        for org, is_admin in zip(orgs, admin_check_results):
            print(f"[bold]{org}[/bold]")
            if is_admin:
                if debug:
                    print(f"    [green]{current_user} is an admin in {org}[/green]")
            else:
                print(
                    f"    [yellow]{current_user} is not an admin in {org}, list of users will be incomplete (limited to public membership)[/yellow]"
                )
            n_active = 0
            n_inactive = 0
            for username, last_activity, user_orgs in sorted(
                user_activities,
                key=lambda x: (
                    (x[1], x[0])
                    if x[1] is not None
                    else (datetime.fromtimestamp(0).replace(tzinfo=timezone.utc), x[0])
                ),
                reverse=True,
            ):
                if org not in user_orgs:
                    continue
                if last_activity is not None and last_activity > (
                    datetime.now().replace(tzinfo=timezone.utc)
                    - timedelta(days=timelimit_days)
                ):
                    n_active += 1
                    if debug:
                        print(f"    [green]{username}[/green] is active in {org}")
                    continue
                n_inactive += 1
                last_activity_ago = (
                    humanize.naturaltime(
                        datetime.now(last_activity.tzinfo) - last_activity
                    )
                    if last_activity
                    else "[red]never[/red]"
                )
                u_owner = " (owner)" if username in org_owners.get(org, []) else ""
                inviter = manual_users.get(username, {}).get("inviter", None)
                if inviter:
                    inviter = f"[green]@{inviter}[/green]"
                else:
                    inviter = "[red]unknown[/red]"
                reason = manual_users.get(username, {}).get(
                    "last_activity_reason", None
                )
                if reason:
                    reason = f"[green]{reason}[/green]"
                else:
                    reason = "[red]unknown[/red]"
                print(
                    f"    {username + u_owner:<20}: Last activity {last_activity_ago}: reason: {reason}, inviter: {inviter}"
                )
            print(
                f"    Found [red]{n_inactive} inactive[/red] and [green]{n_active} active[/green] users in {org} with last activity more recent than {timelimit_days} days."
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Organization Activity Tracker")
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear the cache before running"
    )
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    parser.add_argument(
        "--config-file",
        type=str,
        default="last_user_activity.json",
        help="Path to the config file (default: last_user_activity.json)",
    )

    parser.add_argument(
        "--timelimit-days",
        type=int,
        default=365,
        help="Maximum number of days since last activity before an account is marked as inactive. (default: 365)",
    )
    parser.add_argument(
        "--orgs",
        nargs="+",
        default=default_orgs,
        help="GitHub organizations to track (default: all)",
    )
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()

    asyncio.run(main(args.orgs, args.debug, args.timelimit_days, args.config_file))
