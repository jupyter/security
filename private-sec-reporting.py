import os
import json
import asyncio
import aiohttp
from rich import print

org = "jupyter"
token = os.getenv("GH_TOKEN")

async def check_private_vulnerability_reporting(session, repo_name):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{org}/{repo_name}/private-vulnerability-reporting'
    
    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            return data.get('enabled', False)
    return False

async def get_org_repos(session):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    repos = []
    page = 1
    while True:
        url = f'https://api.github.com/orgs/{org}/repos?page={page}&per_page=100'
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                print(f"Error fetching repos: {response.status}")
                break
                
            page_repos = await response.json()
            if not page_repos:
                break
             
            repos.extend(page_repos)
            page += 1
    
    return repos

async def main():
    async with aiohttp.ClientSession() as session:
        repos = await get_org_repos(session)
        tasks = []
        
        for repo in repos:
            repo_name = repo['name']
            
            task = check_private_vulnerability_reporting(session, repo_name)
            tasks.append((repo_name, task))
        
        results = await asyncio.gather(*[task for _, task in tasks])
        
        for repo, (repo_name, _), has_vuln_reporting in zip(repos,tasks, results):
            if repo['private']:
                print(f"{repo_name:>25}: [yellow]Private[/yellow] {'[green]Enabled[/green]' if has_vuln_reporting else '[red]Disabled[/red]'}")
            else:
                print(f"{repo_name:>25}: {'[green]Enabled[/green]' if has_vuln_reporting else '[red]Disabled[/red]'}")

if __name__ == "__main__":
    asyncio.run(main())