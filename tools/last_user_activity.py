"""GitHub Organization Activity Tracker

This module tracks and reports the last activity of members across GitHub organizations.
It implements disk-based caching to minimize API requests and respect rate limits.
"""

import os
import asyncio
import aiohttp
from rich import print
from datetime import datetime, timezone
import humanize
from itertools import count
import aiosqlite
import diskcache
import json
import pathlib
from typing import Optional, List, Dict
import argparse

orgs = [
    "binder-examples",
    "binderhub-ci-repos",
    "ipython",
    "jupyter",
    "jupyter-book",
    "jupyter-governance",
    "jupyter-incubator",
    "jupyter-server",
    "jupyter-standards",
    "jupyter-widgets",
    "jupyterhub",
    "jupyterlab",
    "jupyter-xeus",
    "jupytercon",
    "voila-dashboards",
    "voila-gallery",
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
        return value

    def get(self, key, default=None, retry=False):
        """Override to handle datetime deserialization in get method with retry."""
        try:
            return super().get(key, default=default, retry=retry)
        except KeyError:
            return default


# Configure DiskCache in the current directory
CACHE_DIR = "github_cache"
cache = DateTimeCache(CACHE_DIR)


async def get_org_members(session: aiohttp.ClientSession, org: str) -> List[Dict]:
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

        # Cache the results
        cache[cache_key] = members  # Using __setitem__ instead of set()
        print(f"[green]Cached {len(members)} members for {org}[/green]")
        return members

    except Exception as e:
        print(f"[red]Error fetching members for {org}: {str(e)}[/red]")
        return []


async def get_user_activity(
    session: aiohttp.ClientSession, username: str
) -> Optional[datetime]:
    """Fetch the last public activity date for a GitHub user."""
    cache_key = f"user_activity_{username}"

    # Try to get from cache
    cached_data = cache.get(cache_key)
    if cached_data is not None:
        print(f"[cyan]Cache hit for {username} activity[/cyan]")
        return cached_data

    print(f"[yellow]Cache miss for {username} activity - fetching from API[/yellow]")

    try:
        print(f"Getting activity for {username}")
        url = f"https://api.github.com/users/{username}/events/public"
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                print(f"Got activity for {username}")
                events = await response.json()
                if events:
                    last_activity = datetime.fromisoformat(
                        events[0]["created_at"].replace("Z", "+00:00")
                    )
                    # Cache the results
                    cache[cache_key] = (
                        last_activity  # Using __setitem__ instead of set()
                    )
                    print(f"[green]Cached activity for {username}[/green]")
                    return last_activity
                else:
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


async def main():
    """Main execution function."""
    # Show cache status
    print(f"[blue]Cache directory: {CACHE_DIR} (size: {get_cache_size()})[/blue]")
    print(f"[blue]Cache contains {len(cache)} items[/blue]")

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
        for org in orgs:
            members = await get_org_members(session, org)
            for member in members:
                if member["login"] not in all_members:
                    all_members[member["login"]] = []
                all_members[member["login"]].append(org)

        # Get activity for each user
        tasks = []
        for username in all_members:
            task = get_user_activity(session, username)
            tasks.append((username, task))

        results = await asyncio.gather(*(task for _, task in tasks))

        # Print results sorted by last activity
        user_activities = []
        for (username, _), last_activity in zip(tasks, results):
            user_activities.append(
                (
                    username,
                    datetime.fromisoformat(last_activity["__datetime__"])
                    if last_activity is not None
                    else datetime.fromtimestamp(0).replace(tzinfo=timezone.utc),
                    all_members[username],
                )
            )

        for username, last_activity, user_orgs in sorted(
            user_activities,
            key=lambda x: x[1] if x[1] is not None else datetime.fromtimestamp(0),
            reverse=True,
        ):
            last_activity_ago = (
                humanize.naturaltime(datetime.now(last_activity.tzinfo) - last_activity)
                if last_activity
                else "[red]never[/red]"
            )
            orgs_str = ", ".join(user_orgs)
            print(
                f"{username:<20}: Last activity {last_activity_ago} in orgs: {orgs_str}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Organization Activity Tracker")
    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear the cache before running"
    )
    parser.add_argument("--debug", action="store_true", help="Show debug information")
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()

    asyncio.run(main())
