"""GitHub Organization Activity Tracker

This module tracks and reports the last activity of members across GitHub organizations.
It implements disk-based caching to minimize API requests and respect rate limits.
"""

import os
import asyncio
import aiohttp
from rich import print
from datetime import datetime
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

# Configure DiskCache in the current directory
CACHE_DIR = "github_cache"
cache = diskcache.Cache(CACHE_DIR)

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
    if cache_key in cache:
        return cache[cache_key]

    members = []
    for page in count(1):
        url = f"https://api.github.com/orgs/{org}/members?page={page}&per_page=100"
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"[red]Error fetching members for {org}: {response.status}[/red]")
                break
                
            page_members = await response.json()
            if not page_members:
                break
                
            members.extend(page_members)
    
    cache.set(cache_key, members, expire=3600 * 24)
    return members

async def get_user_activity(session: aiohttp.ClientSession, username: str) -> Optional[datetime]:
    """Fetch the last public activity date for a GitHub user.

    Parameters
    ----------
    session : aiohttp.ClientSession
        The HTTP session to use for requests
    username : str
        The GitHub username to check

    Returns
    -------
    Optional[datetime]
        The datetime of the user's last public activity,
        or None if no activity was found or an error occurred

    Notes
    -----
    Results are cached for 24 hours to minimize API requests.
    Only public events are considered for activity tracking.
    """
    cache_key = f"user_activity_{username}"
    if cache_key in cache:
        return cache[cache_key]

    url = f"https://api.github.com/users/{username}/events/public"
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            events = await response.json()
            if events:
                last_activity = datetime.fromisoformat(events[0]["created_at"].replace('Z', '+00:00'))
                cache.set(cache_key, last_activity, expire=3600 * 24)
                return last_activity
    return None

def clear_cache() -> None:
    """Clear the disk cache.
    
    Removes all cached data, forcing fresh API requests on next run.
    
    Notes
    -----
    This is useful when you want to ensure you're getting the latest data
    or if the cache becomes corrupted.
    """
    if pathlib.Path(CACHE_DIR).exists():
        cache.clear()
        print("[green]Cache cleared successfully[/green]")
    else:
        print("[yellow]No cache directory found[/yellow]")

async def main():
    """Main execution function.
    
    Fetches and displays the last activity for all members across specified organizations.
    Uses disk caching to minimize API requests and handles GitHub API rate limits.

    Notes
    -----
    The results are displayed organization by organization, with members sorted
    by their last activity date (most recent first).
    """
    # Add cache info at start
    cache_path = pathlib.Path(CACHE_DIR)
    if cache_path.exists():
        cache_size = sum(f.stat().st_size for f in cache_path.rglob('*') if f.is_file())
        print(f"[blue]Using cache directory: {CACHE_DIR} ({cache_size / 1024 / 1024:.1f} MB)[/blue]")
    else:
        print("[yellow]Creating new cache directory[/yellow]")

    async with aiohttp.ClientSession() as session:
        # Check rate limit
        async with session.get("https://api.github.com/rate_limit", headers=headers) as response:
            if response.status == 200:
                rate_data = await response.json()
                remaining = rate_data["resources"]["core"]["remaining"]
                reset_time = datetime.fromtimestamp(rate_data["resources"]["core"]["reset"])
                reset_in = humanize.naturaltime(reset_time)
                print(f"Rate limit remaining: {remaining}")
                print(f"Rate limit resets {reset_in}")
                if remaining < 100:
                    print(f"[yellow]Warning: Low rate limit ({remaining} remaining)[/yellow]")
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
            if last_activity:
                user_activities.append((username, last_activity, all_members[username]))

        for username, last_activity, user_orgs in sorted(user_activities, key=lambda x: x[1], reverse=True):
            last_activity_ago = humanize.naturaltime(datetime.now(last_activity.tzinfo) - last_activity)
            orgs_str = ", ".join(user_orgs)
            print(f"{username:<20}: Last activity {last_activity_ago} in orgs: {orgs_str}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GitHub Organization Activity Tracker")
    parser.add_argument('--clear-cache', action='store_true', help='Clear the cache before running')
    args = parser.parse_args()

    if args.clear_cache:
        clear_cache()
    
    asyncio.run(main())
