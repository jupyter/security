import os
import asyncio
import aiohttp
from rich import print
from datetime import datetime
from pathlib import Path
import humanize
from itertools import count

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


async def check_private_vulnerability_reporting(
    session: aiohttp.ClientSession, org: str, repo_name: str
) -> bool:
    """Check if private vulnerability reporting is enabled for a repository

    Parameters
    ----------
    session: aiohttp.ClientSession
        The aiohttp client session
    org: str
        The organization name
    repo_name: str
        The repository name

    Returns
    -------
    bool: True if enabled, False otherwise
    """
    url = f"https://api.github.com/repos/{org}/{repo_name}/private-vulnerability-reporting"

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            return data.get("enabled", False)
    return False


async def get_org_repos(session: aiohttp.ClientSession, org: str) -> list[dict]:
    """Get all repositories for an organization

    Parameters
    ----------
    session: aiohttp.ClientSession
        The aiohttp client session
    org: str
        The organization name

    Returns
    -------
    list[dict]: The list of repositories
    """
    repos = []

    for page in count(1):  # starts at 1 and counts up infinitely
        url = f"https://api.github.com/orgs/{org}/repos?page={page}&per_page=100"
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"[red]Error fetching repos: {response.status}[/red]")
                break

            page_repos = await response.json()
            if not page_repos:  # empty page means we've reached the end
                break

            repos.extend(page_repos)

    return repos


async def main():
    ignores = Path("psc_ignore.txt").read_text().splitlines()
    async with aiohttp.ClientSession() as session:
        # Check rate limit before making requests
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
                if remaining < 100:
                    print(
                        f"[yellow]Warning: Rate limit is low! ({remaining} remaining, full in {reset_in})[/yellow]"
                    )
                    if remaining < 10:
                        print("[red]Aborting due to very low rate limit[/red]")
                        return
                else:
                    print(f"Rate limit remaining: {remaining}")
                    print(f"Rate limit resets {reset_in}")
            else:
                print(f"[red]Error checking rate limit: {response.status}[/red]")
        tasks = []
        org_tasks = [(org, get_org_repos(session, org)) for org in orgs]
        org_results = await asyncio.gather(*(task for _, task in org_tasks))
        repos = []
        for (org, _), org_repos in zip(org_tasks, org_results):
            for repo in org_repos:
                repos.append((org, repo))

        for org, repo in sorted(repos, key=lambda x: x[1]["name"]):
            if f"{org}/{repo['name']}" in ignores:
                print(
                    f"[yellow]Ignoring {org}/{repo['name']} from ignore file[/yellow]"
                )
                continue
            repo_name = repo["name"]

            task = check_private_vulnerability_reporting(session, org, repo_name)
            tasks.append((repo, org, repo_name, task))

        results = await asyncio.gather(*[task for _, _, _, task in tasks])

        for (repo, org, repo_name, _), has_vuln_reporting in sorted(
            zip(tasks, results), key=lambda x: x[0][0]["pushed_at"], reverse=True
        ):
            last_activity = repo["pushed_at"]
            last_activity_date = datetime.fromisoformat(last_activity).strftime(
                "%Y-%m-%d"
            )
            last_activity_ago_human = humanize.naturaltime(
                datetime.now(datetime.fromisoformat(last_activity).tzinfo)
                - datetime.fromisoformat(last_activity)
            )

            if repo["archived"]:
                print(
                    f"{org+'/'+repo_name:<55}: [yellow]Archived {'Enabled' if has_vuln_reporting else 'Disabled[/yellow]'}"
                )
            elif repo["private"]:
                print(
                    f"{org+'/'+repo_name:<55}: [yellow]Private {'Enabled' if has_vuln_reporting else 'Disabled[/yellow]'} –– last activity: {last_activity_date} ({last_activity_ago_human})"
                )

            else:
                print(
                    f"{org+'/'+repo_name:<55}: {'[green]Enabled[/green]' if has_vuln_reporting else '[red]Disabled[/red]'} –– last activity: {last_activity_date} ({last_activity_ago_human})"
                )


if __name__ == "__main__":
    asyncio.run(main())
