"""GitHub Organization Activity Tracker

This module tracks and reports the last activity of members across GitHub organizations.
It implements disk-based caching to minimize API requests and respect rate limits.
"""

import os
import sys
import asyncio
import aiohttp
from rich import print
from datetime import datetime, timezone, timedelta
import humanize
from itertools import count
import diskcache
import pathlib
from typing import Optional, List, Dict
import argparse

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


async def list_repos(orgs):
    async with aiohttp.ClientSession() as session:
        tasks = [
            session.get(f"https://api.github.com/orgs/{org}/repos", headers=headers)
            for org in orgs
        ]
        for org, response in zip(orgs, await asyncio.gather(*tasks)):
            repos = await response.json()
            for repo in repos:
                yield org, repo["name"]


async def get_private_report(session, org, repo):
    private_report_url = (
        f"https://api.github.com/repos/{org}/{repo}/private-vulnerability-reporting"
    )
    async with session.get(
        f"https://api.github.com/repos/{org}/{repo}", headers=headers
    ) as repo_response:
        repo_info = await repo_response.json()
        archived = repo_info.get("archived", False)
        private = repo_info.get("private", False)
    async with session.get(private_report_url, headers=headers) as response:
        if response.status == 200:
            return (
                org,
                repo,
                (await response.json()).get("enabled", False),
                archived,
                private,
            )
        else:
            return org, repo, False, archived, private


async def main():
    with pathlib.Path("private_sec_ignore.txt").open("r") as ignore_file:
        ignore_repos = [line.strip() for line in ignore_file.readlines()]

    async with aiohttp.ClientSession() as session:
        tasks = []
        async for org, repo in list_repos(default_orgs):
            tasks.append(get_private_report(session, org, repo))

        results = await asyncio.gather(*tasks)
        prev_org = None
        for org, repo, enabled, archived, private in results:
            if org != prev_org:
                print()
                print(f"[bold]{org}[/bold]")
                prev_org = org
            if enabled:
                print(f"    [green]{repo}: {enabled}[/green]")
            else:
                if private:
                    print(f"    [yellow]{org}/{repo}: {enabled} (private)[/yellow]")
                if archived:
                    print(f"    [yellow]{org}/{repo}: {enabled} (archived)[/yellow]")
                elif f"{org}/{repo}" in ignore_repos:
                    print(f"    [yellow]{org}/{repo}: {enabled} (ignored)[/yellow]")
                else:
                    print(f"    [red]{org}/{repo}: {enabled}[/red]")


asyncio.run(main())
