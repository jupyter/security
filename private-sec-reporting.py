import os
import requests
import os
import json
org = "jupyter"

token = os.getenv("GH_TOKEN")

def check_private_vulnerability_reporting(repo_name):
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    url = f'https://api.github.com/repos/{org}/{repo_name}/private-vulnerability-reporting'
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('enabled', False)
    return False

def get_org_repos():
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    repos = []
    page = 1
    while True:
        url = f'https://api.github.com/orgs/{org}/repos?page={page}&per_page=100'
        response = requests.get(url, headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching repos: {response.status_code}")
            break
            
        page_repos = response.json()
        if not page_repos:
            break
         
        repos.extend(page_repos)
        page += 1
    
    return repos

# Get all repos and check their vulnerability reporting status
repos = get_org_repos()
results = {}
from rich import print
for repo in repos:
    repo_name = repo['name']
    repo_is_private = repo['private']
    if repo_is_private:
        print(f"{repo_name:>25}: [yellow]Private[/yellow]")
        continue
    has_vuln_reporting = check_private_vulnerability_reporting(repo_name)
    results[repo_name] = has_vuln_reporting
    print(f"{repo_name:>25}: {'[green]Enabled[/green]' if has_vuln_reporting else '[red]Disabled[/red]'}")