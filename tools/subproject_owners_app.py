# https://packaging.python.org/en/latest/specifications/inline-script-metadata/
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "flask",
#   "requests",
# ]
# ///
"""Small web app to view/edit the `subproject-owners` custom property.

Lists every repository of every organization in the Jupyter GitHub enterprise
with:

    Archived | Org | Repo | URL | Last Push | Description

and, for each repo, a dropdown to view and change the value of the custom
property `subproject-owners`, which is defined at the enterprise level (an
org-level property of the same name, should one exist, shadows it for that
org's repos). Reading the schema needs enterprise read access; writing needs
repository administration write access on the target org. With a read-only
token the table still renders and edits simply report the API error.

Usage:

    GH_TOKEN=ghp_... uv run tools/subproject_owners_app.py
    GH_TOKEN=ghp_... uv run tools/subproject_owners_app.py --enterprise jupyter --port 8000

Options:

    --enterprise SLUG  enterprise slug used to discover orgs (default: jupyter)
    --org ORG          restrict to these orgs (repeatable); skips discovery
    --property NAME    custom property to edit (default: subproject-owners)
    --values A,B,C     override the built-in allowed values (see
                       SUBPROJECT_OWNERS), used when the token cannot read the
                       enterprise schema
    --read-only        never issue writes, even if the token allows them
    --port PORT        port to listen on (default: 5001)
"""

import argparse
import os
import sys
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, jsonify, render_template_string, request

API = "https://api.github.com"

# Fallback when enterprise org discovery is unavailable (token without
# read:enterprise). Kept in sync with tools/all_repos.py.
# The `subproject-owners` values, as defined on the enterprise. Reading the real
# schema needs enterprise admin, which a repo-scoped token does not have, so we
# carry the list here and let --values override it.
SUBPROJECT_OWNERS = [
    "unknown",
    "Executive Council",
    "DEI Standing Committee",
    "Jupyter Accessibility",
    "Jupyter Book",
    "Jupyter Foundations and Standards",
    "Jupyter Frontends",
    "Jupyter Kernels",
    "Jupyter Security",
    "Jupyter Server",
    "Jupyter Widgets",
    "JupyterHub and Binder",
    "Voila",
]

FALLBACK_ORGS = [
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
    "jupyterhub",
    "jupyterlab",
    "voila-dashboards",
    "voila-gallery",
    "pickleshare",
]


class GitHub:
    def __init__(self, token):
        self.s = requests.Session()
        self.s.headers.update(
            {
                "Authorization": f"token {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )

    def paginate(self, url, **params):
        params.setdefault("per_page", 100)
        while url:
            r = self.s.get(url, params=params, timeout=30)
            r.raise_for_status()
            payload = r.json()
            # /orgs/{org}/properties/values returns a bare list, as does /repos
            yield from payload if isinstance(payload, list) else [payload]
            url = r.links.get("next", {}).get("url")
            params = {}  # the `next` link already carries them

    def enterprise_orgs(self, slug):
        """Orgs of an enterprise, via GraphQL. [] if the token can't see it."""
        query = """
        query($slug: String!, $after: String) {
          enterprise(slug: $slug) {
            organizations(first: 100, after: $after) {
              pageInfo { hasNextPage endCursor }
              nodes { login }
            }
          }
        }
        """
        orgs, after = [], None
        while True:
            r = self.s.post(
                f"{API}/graphql",
                json={"query": query, "variables": {"slug": slug, "after": after}},
                timeout=30,
            )
            if r.status_code != 200:
                return []
            data = r.json()
            if data.get("errors") or not (data.get("data") or {}).get("enterprise"):
                return []
            conn = data["data"]["enterprise"]["organizations"]
            orgs += [n["login"] for n in conn["nodes"]]
            if not conn["pageInfo"]["hasNextPage"]:
                return orgs
            after = conn["pageInfo"]["endCursor"]

    def repos(self, org):
        return list(self.paginate(f"{API}/orgs/{org}/repos", type="all"))

    def org_property_values(self, org):
        """{repo_name: {property_name: value}} for one org, in one paginated call.

        Returns None when the token cannot use the bulk endpoint (it needs org
        admin); the caller then falls back to one request per repo.
        """
        r = self.s.get(
            f"{API}/orgs/{org}/properties/values", params={"per_page": 100}, timeout=30
        )
        if r.status_code != 200:
            return None
        out = {}
        url = f"{API}/orgs/{org}/properties/values"
        for entry in self.paginate(url):
            out[entry["repository_name"]] = {
                p["property_name"]: p["value"] for p in entry.get("properties", [])
            }
        return out

    def repo_property_values(self, org, repo):
        """{property_name: value} for a single repo."""
        r = self.s.get(f"{API}/repos/{org}/{repo}/properties/values", timeout=30)
        if r.status_code != 200:
            return {}
        return {p["property_name"]: p["value"] for p in r.json()}

    def _schema_at(self, url, name):
        """The definition of one custom property from a schema endpoint, or None."""
        r = self.s.get(url, timeout=30)
        if r.status_code != 200:
            return None
        for prop in r.json():
            if prop.get("property_name") == name:
                return prop
        return None

    def enterprise_property_schema(self, enterprise, name):
        """`subproject-owners` and friends are defined at the enterprise level."""
        return self._schema_at(f"{API}/enterprises/{enterprise}/properties/schema", name)

    def org_property_schema(self, org, name):
        """An org-level definition, which shadows the enterprise one when present."""
        return self._schema_at(f"{API}/orgs/{org}/properties/schema", name)

    def set_property(self, org, repo, name, value):
        r = self.s.patch(
            f"{API}/repos/{org}/{repo}/properties/values",
            json={"properties": [{"property_name": name, "value": value}]},
            timeout=30,
        )
        if r.status_code >= 400:
            try:
                message = r.json().get("message", r.text)
            except ValueError:
                message = r.text
            raise RuntimeError(f"{r.status_code}: {message}")


def collect(gh, orgs, prop_name, enterprise_schema):
    """Fetch repos + property values for every org.

    `enterprise_schema` is the enterprise-level definition of the property; an
    org that defines a property of the same name shadows it for its own repos.
    Either may be None: reading a schema needs org/enterprise admin, which a
    plain repo-scoped token does not have. In that case the property is still
    readable and writable per repo, and the choices offered in the UI are
    inferred from the values actually in use.
    """
    rows, schemas, errors = [], {}, []

    def repos_of(org):
        try:
            return org, gh.repos(org)
        except Exception as e:  # a private org the token cannot see, etc.
            errors.append(f"{org}: {e}")
            return org, []

    with ThreadPoolExecutor(max_workers=8) as pool:
        per_org_repos = dict(pool.map(repos_of, orgs))

        # One bulk call per org when the token may use it, else one call per repo.
        values = {org: gh.org_property_values(org) for org in per_org_repos}
        missing = [
            (org, r["name"])
            for org, repos in per_org_repos.items()
            if values[org] is None
            for r in repos
        ]
        if missing:
            print(
                f"  bulk org property values unavailable; fetching {len(missing)}"
                " repos individually…",
                flush=True,
            )
            fetched = pool.map(lambda t: (t, gh.repo_property_values(*t)), missing)
            for (org, repo), props in fetched:
                values.setdefault(org, None)
                if values[org] is None:
                    values[org] = {}
                values[org][repo] = props

        for org, schema in zip(
            per_org_repos, pool.map(lambda o: gh.org_property_schema(o, prop_name), per_org_repos)
        ):
            schema = schema or enterprise_schema
            if schema:
                schemas[org] = schema

    for org, repos in per_org_repos.items():
        for r in repos:
            rows.append(
                {
                    "org": org,
                    "repo": r["name"],
                    "archived": bool(r.get("archived")),
                    "private": bool(r.get("private")),
                    "url": r["html_url"],
                    "pushed_at": r.get("pushed_at"),
                    "description": r.get("description") or "",
                    "value": (values.get(org) or {}).get(r["name"], {}).get(prop_name),
                }
            )

    # Orgs whose schema we could not read: infer one from the values in use, so
    # the dropdown still offers the known owners (plus free text for the rest).
    seen = set()
    multi = False
    for row in rows:
        if isinstance(row["value"], list):
            multi = True
            seen.update(str(v) for v in row["value"])
        elif row["value"] is not None:
            seen.add(str(row["value"]))
    for org in per_org_repos:
        if org not in schemas:
            schemas[org] = {
                "property_name": prop_name,
                "value_type": "multi_select" if multi else "single_select",
                "allowed_values": sorted(seen),
                "inferred": True,
            }

    rows.sort(key=lambda r: (r["org"], r["repo"].lower()))
    return rows, schemas, errors


TEMPLATE = """
<!doctype html>
<meta charset="utf-8">
<title>Jupyter enterprise — {{ prop }}</title>
<style>
  :root { color-scheme: light dark; }
  body { font: 14px/1.4 system-ui, sans-serif; margin: 1rem 1.5rem; }
  h1 { font-size: 1.2rem; margin: 0 0 .2rem; }
  .bar { display: flex; gap: .75rem; align-items: center; flex-wrap: wrap;
         margin: .75rem 0; position: sticky; top: 0; padding: .5rem 0;
         background: Canvas; z-index: 2; }
  input[type=search] { padding: .35rem .5rem; min-width: 18rem; }
  .muted { opacity: .65; }
  .wrap { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; }
  th, td { text-align: left; padding: .3rem .5rem; border-bottom: 1px solid
           color-mix(in srgb, currentColor 18%, transparent); vertical-align: top; }
  th { cursor: pointer; user-select: none; white-space: nowrap; }
  th.sorted::after { content: " \\25B4"; }
  th.sorted.desc::after { content: " \\25BE"; }
  tr.archived { opacity: .55; }
  td.desc { max-width: 32rem; }
  select, .val input { max-width: 15rem; padding: .15rem; }
  .status { font-size: .8rem; margin-left: .3rem; }
  .ok { color: seagreen; } .err { color: crimson; }
  .ro { color: crimson; font-weight: 600; }
</style>

<h1>Jupyter enterprise repositories</h1>
<div class="muted">{{ rows|length }} repos across {{ orgs|length }} orgs ·
  editing custom property <code>{{ prop }}</code>
  {% if read_only %}· <span class="ro">read-only mode</span>{% endif %}
</div>
{% if errors %}<div class="err">{{ errors|join('; ') }}</div>{% endif %}

<div class="bar">
  <input type="search" id="q" placeholder="filter org / repo / description / owner…">
  <label><input type="checkbox" id="hide-archived"> hide archived</label>
  <label><input type="checkbox" id="only-unset"> only unset {{ prop }}</label>
  <span class="muted" id="count"></span>
</div>

<div class="wrap"><table>
  <thead><tr>
    <th data-k="archived">Archived</th>
    <th data-k="org">Org</th>
    <th data-k="repo">Repo</th>
    <th data-k="url">URL</th>
    <th data-k="pushed_at">Last Push</th>
    <th data-k="description">Description</th>
    <th data-k="value">{{ prop }}</th>
  </tr></thead>
  <tbody id="body"></tbody>
</table></div>

<script>
const ROWS = {{ rows|tojson }};
const SCHEMAS = {{ schemas|tojson }};
const PROP = {{ prop|tojson }};
const READ_ONLY = {{ read_only|tojson }};
let sortKey = "org", sortDesc = false;

const fmtDate = s => s ? s.slice(0, 10) : "";

function control(row) {
  const schema = SCHEMAS[row.org];
  const cur = row.value;
  if (!schema) {
    const span = document.createElement("span");
    span.className = "muted";
    span.textContent = cur == null ? "n/a in this org" : String(cur);
    return span;
  }
  const type = schema.value_type;
  const allowed = schema.allowed_values || [];
  let el;
  if (type === "multi_select") {
    el = document.createElement("select");
    el.multiple = true;
    el.size = Math.min(Math.max(allowed.length, 2), 6);
    const set = new Set(Array.isArray(cur) ? cur.map(String) : []);
    for (const v of allowed) {
      const o = document.createElement("option");
      o.value = o.textContent = v;
      o.selected = set.has(v);
      el.append(o);
    }
  } else if (schema.inferred || type === "string") {
    // We could not read the real schema, so the known values are a hint, not a
    // closed list: a combobox lets you pick one or type a new one.
    el = document.createElement("input");
    el.type = "text";
    el.value = cur == null ? "" : String(cur);
    el.placeholder = "— unset —";
    el.setAttribute("list", datalistFor(row.org, allowed));
  } else {  // single_select / true_false, with a schema we trust
    el = document.createElement("select");
    const values = type === "true_false" ? ["true", "false"] : allowed;
    for (const v of [null, ...values]) {
      const o = document.createElement("option");
      o.value = v === null ? "" : v;
      o.textContent = v === null ? "— unset —" : v;
      o.selected = (v === null ? cur == null : String(cur) === String(v));
      el.append(o);
    }
  }
  el.disabled = READ_ONLY;
  const status = document.createElement("span");
  status.className = "status";
  let last = JSON.stringify(cur ?? null);
  const commit = async () => {
    let value;
    if (el.multiple) value = [...el.selectedOptions].map(o => o.value);
    else value = el.value.trim() === "" ? null : el.value.trim();
    if (JSON.stringify(value) === last) return;  // blur with nothing changed
    status.className = "status muted";
    status.textContent = "saving…";
    try {
      const r = await fetch("/api/property", {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({org: row.org, repo: row.repo, value}),
      });
      const data = await r.json();
      if (!r.ok) throw new Error(data.error || r.statusText);
      row.value = value;
      last = JSON.stringify(value ?? null);
      status.className = "status ok";
      status.textContent = "saved";
      setTimeout(() => { status.textContent = ""; }, 2000);
    } catch (e) {
      status.className = "status err";
      status.textContent = String(e.message || e);
    }
  };
  el.addEventListener("change", commit);
  if (el.tagName === "INPUT") el.addEventListener("blur", commit);
  const box = document.createElement("span");
  box.className = "val";
  box.append(el, status);
  return box;
}

// One shared <datalist> per org, rather than one per row.
const DATALISTS = new Set();
function datalistFor(org, values) {
  const id = "dl-" + org;
  if (!DATALISTS.has(id)) {
    const list = document.createElement("datalist");
    list.id = id;
    for (const v of values) {
      const o = document.createElement("option");
      o.value = v;
      list.append(o);
    }
    document.body.append(list);
    DATALISTS.add(id);
  }
  return id;
}

function render() {
  const q = document.getElementById("q").value.toLowerCase().trim();
  const hideArchived = document.getElementById("hide-archived").checked;
  const onlyUnset = document.getElementById("only-unset").checked;
  const rows = ROWS.filter(r => {
    if (hideArchived && r.archived) return false;
    if (onlyUnset && r.value != null &&
        !(Array.isArray(r.value) && r.value.length === 0)) return false;
    if (!q) return true;
    const hay = [r.org, r.repo, r.description, r.value].flat().join(" ").toLowerCase();
    return q.split(/\\s+/).every(t => hay.includes(t));
  });
  rows.sort((a, b) => {
    const x = a[sortKey] ?? "", y = b[sortKey] ?? "";
    const c = String(x).localeCompare(String(y), undefined, {numeric: true});
    return sortDesc ? -c : c;
  });
  const body = document.getElementById("body");
  body.replaceChildren(...rows.map(r => {
    const tr = document.createElement("tr");
    if (r.archived) tr.className = "archived";
    const cells = [
      r.archived ? "yes" : "",
      r.org,
      r.repo + (r.private ? " (private)" : ""),
      null,
      fmtDate(r.pushed_at),
      r.description,
      null,
    ];
    cells.forEach((c, i) => {
      const td = document.createElement("td");
      if (i === 3) {
        const a = document.createElement("a");
        a.href = r.url; a.target = "_blank"; a.rel = "noreferrer";
        a.textContent = r.url.replace("https://github.com/", "");
        td.append(a);
      } else if (i === 6) {
        td.append(control(r));
      } else {
        td.textContent = c;
        if (i === 5) td.className = "desc";
      }
      tr.append(td);
    });
    return tr;
  }));
  document.getElementById("count").textContent =
    rows.length + " / " + ROWS.length + " shown";
}

document.querySelectorAll("th").forEach(th => th.addEventListener("click", () => {
  const k = th.dataset.k;
  sortDesc = (k === sortKey) ? !sortDesc : false;
  sortKey = k;
  document.querySelectorAll("th").forEach(o => o.className = "");
  th.className = "sorted" + (sortDesc ? " desc" : "");
  render();
}));
["q", "hide-archived", "only-unset"].forEach(id =>
  document.getElementById(id).addEventListener("input", render));
render();
</script>
"""


def build_app(gh, orgs, prop_name, read_only, enterprise, allowed_values=None):
    app = Flask(__name__)
    enterprise_schema = gh.enterprise_property_schema(enterprise, prop_name)
    if enterprise_schema:
        print(
            f"`{prop_name}` is defined on enterprise `{enterprise}` as "
            f"{enterprise_schema.get('value_type')}",
            flush=True,
        )
    print(f"Fetching repos and property values for {len(orgs)} orgs…", flush=True)
    rows, schemas, errors = collect(gh, orgs, prop_name, enterprise_schema)
    if allowed_values is None and prop_name == "subproject-owners":
        allowed_values = SUBPROJECT_OWNERS
    if allowed_values:
        # A known list beats one inferred from the values happening to be in use.
        in_use = {
            str(v)
            for row in rows
            for v in (row["value"] if isinstance(row["value"], list) else [row["value"]])
            if v is not None
        }
        # Keep any value already set that the list does not cover, so it stays
        # visible and selectable rather than silently reading as unset.
        extra = sorted(in_use - set(allowed_values))
        if extra:
            errors.append(
                f"Values in use but not in the known `{prop_name}` list: "
                + ", ".join(repr(e) for e in extra)
            )
        for sch in schemas.values():
            if sch.get("inferred"):
                sch["allowed_values"] = list(allowed_values) + extra
                sch["inferred"] = False
    inferred = [o for o, sch in schemas.items() if sch.get("inferred")]
    print(f"  {len(rows)} repos; schema inferred for {len(inferred)} orgs", flush=True)
    if inferred:
        errors.append(
            f"Could not read the `{prop_name}` schema for {len(inferred)} orgs "
            f"(that needs enterprise/org admin — enterprise `{enterprise}` and "
            "the org schema endpoints both returned 404 for this token). The "
            "choices offered there are the values already in use; you may also "
            "type a value that is not listed."
        )

    @app.route("/")
    def index():
        return render_template_string(
            TEMPLATE,
            rows=rows,
            schemas=schemas,
            orgs=orgs,
            prop=prop_name,
            errors=errors,
            read_only=read_only,
        )

    @app.route("/api/repos")
    def api_repos():
        return jsonify(rows)

    @app.route("/api/property", methods=["PATCH"])
    def api_property():
        if read_only:
            return jsonify({"error": "server started with --read-only"}), 403
        body = request.get_json(force=True)
        org, repo, value = body["org"], body["repo"], body.get("value")
        try:
            gh.set_property(org, repo, prop_name, value)
        except Exception as e:
            return jsonify({"error": str(e)}), 502
        for row in rows:
            if row["org"] == org and row["repo"] == repo:
                row["value"] = value
        return jsonify({"ok": True, "value": value})

    return app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--enterprise", default="jupyter")
    parser.add_argument("--org", action="append", default=[])
    parser.add_argument("--property", default="subproject-owners")
    parser.add_argument(
        "--values",
        help="comma-separated allowed values, overriding the built-in list; "
        "used when the token cannot read the property schema",
    )
    parser.add_argument("--read-only", action="store_true")
    parser.add_argument("--port", type=int, default=5001)
    args = parser.parse_args()

    token = os.getenv("GH_TOKEN")
    if not token:
        sys.exit("Error: GH_TOKEN environment variable not set")
    gh = GitHub(token)

    orgs = args.org
    if not orgs:
        orgs = gh.enterprise_orgs(args.enterprise)
        if orgs:
            print(f"Discovered {len(orgs)} orgs in enterprise `{args.enterprise}`")
        else:
            orgs = FALLBACK_ORGS
            print(
                f"Could not list orgs of enterprise `{args.enterprise}` "
                "(token likely lacks read:enterprise); using the built-in list."
            )

    values = [v.strip() for v in args.values.split(",") if v.strip()] if args.values else None
    app = build_app(
        gh, sorted(orgs), args.property, args.read_only, args.enterprise, values
    )
    print(f"→ http://127.0.0.1:{args.port}")
    app.run(port=args.port, debug=False)


if __name__ == "__main__":
    main()
