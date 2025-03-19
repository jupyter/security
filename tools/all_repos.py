# https://packaging.python.org/en/latest/specifications/inline-script-metadata/
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests",
#   "rich",
#   "beautifulsoup4",
# ]
# ///
"""GitHub Organization Activity Tracker

This module tracks and reports the last activity of members across GitHub organizations.
It implements disk-based caching to minimize API requests and respect rate limits.
"""

import os
import asks
from rich import print
import trio

import requests
from rich import print
from bs4 import BeautifulSoup


def get_packages(url):
    # Send a GET request to the webpage with a custom user agent
    headers = {"User-Agent": "python/request/jupyter"}
    response = requests.get(url, headers=headers, allow_redirects=True)

    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        exit(1)

    if "A required part of this site couldn’t load" in response.text:
        print("Fastly is blocking us. Status code: 403")
        exit(1)

    # Parse the HTML content
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all <h3> tags and accumulate their text in a list
    h3_tags = [h3.get_text(strip=True) for h3 in soup.find_all("h3")]

    # Sort the list of <h3> contents
    h3_tags.sort()

    if not h3_tags:
        print("No packages found")
        exit(1)
    return h3_tags


default_orgs = [
    # "binder-examples",
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
    # "jupytercon",
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
    async with trio.open_nursery() as nursery:
        results = []
        for org in orgs:

            async def _loc(results, org):
                results.append(await list_repos_for_org(org))

            nursery.start_soon(_loc, results, org)
    for org_repos in results:
        for org, repo in org_repos:
            yield org, repo


async def list_repos_for_org(org):
    reps = []
    for p in range(1, 10):
        response = await asks.get(
            f"https://api.github.com/orgs/{org}/repos?per_page=100&page={p}",
            headers=headers,
        )
        response.raise_for_status()
        repos = response.json()
        for repo in repos:
            reps.append((org, repo["name"]))
        if len(repos) < 100:
            break
    return reps


async def main():

    packages = get_packages(f"https://pypi.org/org/jupyter/")
    print(f"Found {len(packages)} packages in the pypi jupyter org")

    map = {p.lower().replace("-", "_"): p for p in packages}

    todo = []
    async for org, repo in list_repos(default_orgs):
        lowname = repo.lower().replace("-", "_")
        if lowname in map:
            print(
                f"{org}/{repo}".ljust(40),
                f"https://pypi.org/project/{map[lowname]}",
                " in jupyter org",
            )
            del map[lowname]
        else:
            todo.append((org, repo))

    print()
    print("check potentially matching Pypi names:")

    async with trio.open_nursery() as nursery:
        targets = []
        for org, repo in todo:

            async def _loc(targets, org, repo):
                targets.append(
                    (
                        org,
                        repo,
                        (
                            await asks.get(f"https://pypi.org/pypi/{repo}/json")
                        ).status_code,
                    )
                )

            nursery.start_soon(_loc, targets, org, repo)
    corg = ""
    for org, repo, status in sorted(targets):
        if org != corg:
            print()
            corg = org
        if status == 200:
            print(
                f"https://github.com/{org}/{repo}".ljust(70),
                f"{status} for https://pypi.org/project/{repo}",
            )

    print()
    print("repos with no Pypi package:")
    corg = ""
    for org, repo, status in sorted(targets):
        if org != corg:
            print()
            corg = org
        if status != 200:
            print(f"https://github.com/{org}/{repo}")

    print()
    print("Packages with no repos.")
    print(map)


trio.run(main)
