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

maintainers_name_map = {
    "mbussonn": "Carreau",
}

import diskcache
from datetime import datetime

CACHE_DIR = f"github_cache-all_repos-{datetime.now().strftime('%Y%m%d')}"
cache = diskcache.Cache(CACHE_DIR)


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


async def get_package_maintainers(package: str) -> list[str]:
    """Get the maintainers of a package from PyPI.

    The json does not have the right information, so we need to scrape the page.
    """
    url = f"https://pypi.org/project/{package}/"
    if package in cache:
        print("c", end="", flush=True)
        return cache[package]
    response = await asks.get(url)
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        maintainers = soup.find_all("span", class_="sidebar-section__maintainer")
        if not maintainers:
            print("x", end="", flush=True)
            return set(["unknown (blocked by fastly?)"])
        res = set(a.text.strip() for a in maintainers)
        cache[package] = res
        print(".", end="", flush=True)
        return res
    print("f", end="", flush=True)
    return set(["unknown (status code: " + str(response.status_code) + ")"])


async def main(config_file: str = "all_repos.txt"):
    from pathlib import Path

    items = Path(config_file).read_text().splitlines()
    known_mapping = []
    for item in items:
        if item.startswith("#") or not item.strip():
            continue
        github_name, pypi_name = item.split(":", maxsplit=1)
        # pypi name may be empty for repo with no packages.
        # and one repo can create multiple pypi packages.
        known_mapping.append((github_name.strip(), pypi_name.strip()))

    # get all packages in the pypi jupyter org
    packages = get_packages(f"https://pypi.org/org/jupyter/")
    packages_urls = [f"https://pypi.org/project/{p}" for p in packages]
    print(f"Found {len(packages)} packages in the pypi jupyter org")

    missing_from_pypi_org = set([p for _, p in known_mapping]) - set(packages_urls)
    if missing_from_pypi_org:
        print(
            "Repos missing from pypi org – they are listed on the config file, with a corresponding Pypi pacakge, but the package is not part of Pypi org:"
        )
        for repo in missing_from_pypi_org:
            print(f"  {repo}")

    missing_from_github_org = set(packages_urls) - set([p for _, p in known_mapping])
    if missing_from_github_org:
        print(
            "Packages missing from github org, they are on PyPI, but I don't know the source github repo...:"
        )
        for repo in sorted(missing_from_github_org):
            print(f"  {repo}")

    map = {p.lower().replace("-", "_"): p for p in packages}

    todo = []
    async for org, repo in list_repos(default_orgs):
        org_repo = f"{org}/{repo}"
        candidates = [v for k, v in known_mapping if k == org_repo]
        if not candidates:
            print(f"Missing: no candidate for {org_repo}")
            todo.append((org, repo))
            continue
        for candidate in candidates:
            if candidate in packages_urls:
                pass
                # print(f"OK: {org_repo} -> {candidate}"")
            else:
                print(f"Missing: {org_repo} -> {candidate}")
                todo.append((org, repo))

    print()
    print("check potentially matching Pypi names:")

    async with trio.open_nursery() as nursery:
        targets = []
        semaphore = trio.Semaphore(10)  # Throttle to 10 concurrent requests
        for org, repo in todo:

            async def _loc(targets, org, repo):
                async with semaphore:  # Wait for semaphore to be available
                    maintainers = await get_package_maintainers(repo)
                    targets.append(
                        (
                            org,
                            repo,
                            (
                                await asks.get(f"https://pypi.org/pypi/{repo}/json")
                            ).status_code,
                            maintainers,
                        )
                    )

            nursery.start_soon(_loc, targets, org, repo)

    corg = ""
    for org, repo, status, maintainers in sorted(targets):
        if org != corg:
            print()
            corg = org
        if status == 200:
            print(
                f"https://github.com/{org}/{repo}".ljust(70),
                f"{status} for https://pypi.org/project/{repo}",
            )

            for maintainer in maintainers:
                if maintainer in maintainers_name_map:
                    print(f"  @{maintainers_name_map[maintainer]} ({maintainer})")
                else:
                    print(f"  @{maintainer}")

    print()
    print("repos with no Pypi package:")
    corg = ""
    for org, repo, status, maintainers in sorted(targets):
        if org != corg:
            print()
            corg = org
        if status != 200:
            print(f"https://github.com/{org}/{repo}")
    print()
    print("Packages with no repos.")
    print(map)


trio.run(main)
