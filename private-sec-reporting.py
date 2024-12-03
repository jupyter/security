import os
import json
import asyncio
import aiohttp
from rich import print
from datetime import datetime
import humanize

orgs = ["jupyter", 'ipython', 'jupyterhub', 'jupyterlab']
token = os.getenv("GH_TOKEN")

async def check_private_vulnerability_reporting(session, org, repo_name):
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

async def get_org_repos(session, org):
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
        tasks = []
        for org in orgs:
            repos = await get_org_repos(session, org)
            
            for repo in sorted(repos, key=lambda x: x['name']):
                repo_name = repo['name']
                
                task = check_private_vulnerability_reporting(session, org, repo_name)
                tasks.append((repo, org, repo_name, task))
        
        results = await asyncio.gather(*[task for _,_,_, task in tasks])
        
        for (repo, org, repo_name, _), has_vuln_reporting in sorted(zip(tasks, results), key=lambda x: x[0][0]['pushed_at'], reverse=True):
            last_activity = repo['pushed_at']
            last_activity_date = datetime.fromisoformat(last_activity).strftime("%Y-%m-%d")
            last_activity_ago_human = humanize.naturaltime(datetime.now(datetime.fromisoformat(last_activity).tzinfo) - datetime.fromisoformat(last_activity))
            
            if repo['archived']:
                print(f"{org+'/'+repo_name:<55}: [yellow]Archived {'Enabled' if has_vuln_reporting else 'Disabled[/yellow]'}")
            elif repo['private']:
                print(f"{org+'/'+repo_name:<55}: [yellow]Private {'Enabled' if has_vuln_reporting else 'Disabled[/yellow]'} –– last activity: {last_activity_date} ({last_activity_ago_human})")

            else:
                print(f"{org+'/'+repo_name:<55}: {'[green]Enabled[/green]' if has_vuln_reporting else '[red]Disabled[/red]'} –– last activity: {last_activity_date} ({last_activity_ago_human})")

if __name__ == "__main__":
    asyncio.run(main())