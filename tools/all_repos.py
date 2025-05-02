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
    "takowl": "takluyver",
    "Kyle.Kelley": "rgbkrk",
    "bgranger": "ellisonbg",
}

import diskcache
from datetime import datetime

CACHE_DIR = f"github_cache-all_repos-{datetime.now().strftime('%Y%m')}"
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


async def list_github_repos(orgs):
    async with trio.open_nursery() as nursery:
        results = []
        for org in orgs:

            async def _loc(results, org):
                results.append(await list_repos_for_org(org))

            nursery.start_soon(_loc, results, org)

    for org_repos in results:
        for org, repo, archived, private in org_repos:
            yield org, repo, archived, private


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
            archived = repo.get("archived", None)
            private = repo.get("private", None)
            reps.append((org, repo["name"], archived, private))
        if len(repos) < 100:
            break
    return reps


async def get_package_maintainers(package: str) -> tuple[list[str], bool]:
    """Get the maintainers of a package from PyPI.

    The json does not have the right information, so we need to scrape the page.
    """
    assert package, "package is required"
    url = f"https://pypi.org/project/{package}/"
    if package in cache:
        print("c", end="", flush=True)
        return cache[package], True
    response = await asks.get(url)
    # fastly html is 200 even if package is not found, so the json instead
    assert len(package.strip()) > 2, package
    url = f"https://pypi.org/pypi/{package}/json"

    try:
        (await asks.get(url)).raise_for_status()
    except Exception as e:
        raise ValueError("For package", package) from e
    if response.status_code == 200:
        html = response.text
        soup = BeautifulSoup(html, "html.parser")
        maintainers = soup.find_all("span", class_="sidebar-section__maintainer")
        if not maintainers:
            print("x", end="", flush=True)
            return set(["unknown (blocked by fastly?)"]), False
        res = set(a.text.strip() for a in maintainers)
        cache[package] = res
        print(".", end="", flush=True)
        return res, True
    print("f", end="", flush=True)
    return set(["unknown (status code: " + str(response.status_code) + ")"]), False


async def main(config_file: str = "all_repos.txt"):
    from pathlib import Path

    items = Path(config_file).read_text().splitlines()
    known_mapping = []
    for item in items:
        if item.startswith("#") or not item.strip():
            continue
        if item.count(":") == 0:
            print(f"Invalid line: {item}")
            exit(1)
        github_slug, pypi_url = item.split(":", maxsplit=1)
        github_slug = github_slug.strip(" /")
        ghorg, repo = github_slug.split("/")
        assert repo
        pypi_url = pypi_url.replace("<none>", "").strip(" /")
        if pypi_url == "-":
            pypi_url = f"https://pypi.org/project/{repo.replace('_', '-')}"
        if "https://pypi.org/project/" not in pypi_url and pypi_url != "":
            pypi_url = f"https://pypi.org/project/{pypi_url}"

        # pypi name may be empty for repo with no packages.
        # and one repo can create multiple pypi packages.
        assert pypi_url != "https://pypi.org/project/"
        known_mapping.append((github_slug, pypi_url))

    # get all packages in the pypi jupyter org
    packages = get_packages(f"https://pypi.org/org/jupyter/")
    packages_urls = [f"https://pypi.org/project/{p}" for p in packages]
    print(f"Found {len(packages)} packages in the pypi jupyter org")

    missing_from_pypi_org = (
        set([p for _, p in known_mapping]) - set(packages_urls) - {""}
    )

    async with trio.open_nursery() as nursery:
        targets = []
        semaphore = trio.Semaphore(15)  # Throttle to 10 concurrent requests
        for package_url in missing_from_pypi_org:

            async def _loc(targets, package_url):
                async with semaphore:  # Wait for semaphore to be available
                    package = package_url.strip("/").split("/")[-1]
                    assert package != "project", package_url
                    assert package, f"package is required {package_url}"
                    maintainers, is_ok = await get_package_maintainers(package)
                    targets.append(
                        (
                            package_url,
                            maintainers,
                            is_ok,
                        )
                    )

            nursery.start_soon(_loc, targets, package_url)
    by_maintainers = {}
    if targets:
        print()
        print(
            f"{len(targets)} To add to PiPy org – they are listed on the config file, with a "
            "corresponding Pypi package, but the package is not part of Pypi org:"
        )
        for package_url, maintainers, is_ok in targets:
            print(f"  [yellow]{package_url}[/yellow] maintained by")
            for maintainer in maintainers:
                color = "[green]" if is_ok else "[red]"
                end = "[/green]" if is_ok else "[/red]"
                print(f"{color}     pypi: `@{maintainer}` {end}")
                if is_ok:
                    by_maintainers[maintainer] = by_maintainers.setdefault(
                        maintainer, []
                    )
                    by_maintainers[maintainer].append(package_url)
        print()

    by_maintainers = {
        k: v
        for k, v in sorted(
            by_maintainers.items(), key=lambda item: len(item[1]), reverse=True
        )
    }
    for maintainer, packages in by_maintainers.items():
        print(
            f"[green]`@{maintainer}`[/green] {len(packages)} packages (https://pypi.org/user/{maintainer}/):"
        )
        for package in sorted(packages):
            print(f"    {package}")

    missing_from_github_org = set(packages_urls) - set([p for _, p in known_mapping])
    if missing_from_github_org:
        print(
            "Packages missing from github org, they are on PyPI, but I don't know"
            " the source github repo...:"
        )
        for repo in sorted(missing_from_github_org):
            print(f"  {repo}")

    todo = []

    # we've verified the existing mapping,
    # now up to all the org/repo that are not inther

    print(
        "listing all org and repo under jupyter purview, and filtering one without"
        " mathching github repos."
    )

    known_org_rep = {k for k, v in known_mapping}
    async for org, repo, archived, private in list_github_repos(default_orgs):
        org_repo = f"{org}/{repo}"
        if org_repo in known_org_rep:
            continue
        assert repo
        todo.append((org, repo, archived, private))

    print()
    print(
        "check potentially matching Pypi names, all the following seem to correspond"
        " to an existing pypi package, if they indeed are part of Jupyter, "
        "you can copy past the lines as is in the config file. If not just append: `{org}/{repo}:`"
    )

    async with trio.open_nursery() as nursery:
        targets = []
        semaphore = trio.Semaphore(15)  # Throttle to 10 concurrent requests
        for org, repo, archived, private in todo:
            assert repo

            async def _loc(targets, org, repo, archived, private):
                async with semaphore:  # Wait for semaphore to be available
                    # maintainers = await get_package_maintainers(repo)
                    maintainers = []
                    assert repo
                    targets.append(
                        (
                            org,
                            repo,
                            (
                                await asks.get(f"https://pypi.org/pypi/{repo}/json")
                            ).status_code,
                            maintainers,
                            archived,
                            private,
                        )
                    )

            nursery.start_soon(_loc, targets, org, repo, archived, private)

    corg = ""
    for org, repo, status, maintainers, archived, private in sorted(targets):
        if org != corg:
            print()
            corg = org
        if status == 200:
            print(
                f"https://github.com/{org}/{repo}".ljust(40),
                f" :  https://pypi.org/project/{repo}",
                f"[yellow]{'(archived)' if archived else ''}[/yellow] [red]{'(private)' if private else ''}[/red]".ljust(
                    20
                ),
            )

            # for maintainer in maintainers:
            #    if maintainer in maintainers_name_map:
            #        print(f"  @{maintainers_name_map[maintainer]} ({maintainer})")
            #    else:
            #        print(f"  @{maintainer}")

    print()
    print(
        "repos with no Pypi package, either manually add `{org}/{repo}: "
        "{pypi_url}` or `{org}/{repo}: <none>` to config file."
    )
    corg = ""
    counter = 0
    for org, repo, status, maintainers, archived, private in sorted(targets):
        if org != corg:
            print()
            corg = org
        if status != 200:
            counter += 1
            print(
                counter,
                f"https://github.com/{org}/{repo}".ljust(30),
                f"[yellow]{'(archived)' if archived else ''}[/yellow] [red]{'(private)' if private else ''}[/red]",
            )


trio.run(main)
