# https://packaging.python.org/en/latest/specifications/inline-script-metadata/
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "requests",
#   "rich",
#   "beautifulsoup4",
# ]
# ///
import requests
from rich import print
from bs4 import BeautifulSoup
import sys
from rich.table import Table


def get_packages(url):
    # Send a GET request to the webpage with a custom user agent
    headers = {"User-Agent": "python/request/jupyter"}
    response = requests.get(url, headers=headers, allow_redirects=True)

    if response.status_code != 200:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        exit(1)

    if "A required part of this site couldn’t load" in response.text:
        print(f"Fastly is blocking us for {url}. Status code: 403")
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


def get_tidelift_data(packages):
    packages_data = [{"platform": "pypi", "name": h3} for h3 in packages]

    data = {"packages": packages_data}
    res = requests.post(
        "https://tidelift.com/api/depci/estimate/bulk_estimates", json=data
    )

    res.raise_for_status()

    # Collecting all package data for aligned printing
    package_data = []
    response_data = res.json()

    for package in response_data:
        name = package["name"]
        lifted = package["lifted"]
        estimated_money = package["estimated_money"]
        package_data.append((name, lifted, estimated_money))

    package_names = {p["name"] for p in response_data}
    for package in packages:
        if package not in package_names:
            package_data.append((package, None, None))

    # Print the collected data in aligned columns

    # Create a table for aligned output
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Package Name")
    table.add_column("Estimated Money")
    table.add_column("Lifted")

    def maybefloat(x):
        if x is None:
            return 0
        try:
            return float(x)
        except TypeError:
            return 0

    package_data.sort(
        key=lambda x: (x[1] is None, x[1], -maybefloat(x[2]), x[0])
    )  # sort lifted True first, then None, then False, then amount,  then by name
    for name, lifted, estimated_money in package_data:
        if lifted:
            table.add_row(name, "-- need login ––", f"[green]{lifted}[/green]")
        else:
            table.add_row(name, str(estimated_money), f"[red]{lifted}[/red]")

    print(table)


if __name__ == "__main__":
    # URL of the webpage
    args = sys.argv[1:]
    packages = []
    while args:
        if args[0] == "--org":
            url = f"https://pypi.org/org/{args[1]}/"
            packages += get_packages(url)
            args = args[2:]
        elif args[0] == "--user":
            url = f"https://pypi.org/user/{args[1]}/"
            packages += get_packages(url)
            args = args[2:]
        elif args[0] == "--packages":
            packages += args[1:]
            args = []
        else:
            print(
                "Invalid argument. Please use either --org ORG, --user USER or --packages PACKAGE1 PACKAGE2 ..."
            )
            exit(1)
    get_tidelift_data(packages)
