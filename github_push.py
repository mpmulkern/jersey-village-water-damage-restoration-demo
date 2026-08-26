#!/usr/bin/env python3
"""Create mpmulkern/jersey-village-water-damage-restoration-demo and push the site/ dir in one commit."""
import os, sys, json, base64, urllib.request, urllib.error, glob

PAT = os.environ.get("GITHUB_PAT", "")
OWNER = "mpmulkern"
REPO = "jersey-village-water-damage-restoration-demo"
API = "https://api.github.com"
SITE_DIR = "/tmp/jv-water-damage-deploy"

def gh(method, path, body=None):
    req = urllib.request.Request(API + path,
        data=json.dumps(body).encode() if body else None, method=method,
        headers={"Authorization": f"Bearer {PAT}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json", "User-Agent": "tf-engineer-deploy"})
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or "{}")
    except urllib.error.HTTPError as e:
        try: return e.code, json.loads(e.read() or "{}")
        except Exception: return e.code, {"message": "error"}

def main():
    if not PAT:
        print(json.dumps({"error": "GITHUB_PAT not set"})); sys.exit(1)

    s, who = gh("GET", "/user")
    print(json.dumps({"auth_status": s, "login": who.get("login") if isinstance(who, dict) else None}))

    s, repo = gh("GET", f"/repos/{OWNER}/{REPO}")
    if s == 404:
        s, repo = gh("POST", "/user/repos", {"name": REPO, "private": False, "auto_init": True,
                     "description": "Demo: Jersey Village Water Damage & Mold Restoration - AI-built SEO/AIO/GEO site (Easy agents, subscription models only)."})
        print(json.dumps({"create_repo": s, "msg": repo.get("message")}))
        if s != 201:
            print(json.dumps({"FATAL": "repo create failed"})); sys.exit(1)
    elif s != 200:
        print(json.dumps({"FATAL": f"repo lookup {s}", "msg": repo.get("message")})); sys.exit(1)
    else:
        print(json.dumps({"repo_exists": True}))

    branch = repo.get("default_branch", "main")
    s, ref = gh("GET", f"/repos/{OWNER}/{REPO}/git/ref/heads/{branch}")
    if s != 200:
        print(json.dumps({"FATAL": f"no branch ref {s}", "ref": ref})); sys.exit(1)
    head = ref["object"]["sha"]
    _, commit = gh("GET", f"/repos/{OWNER}/{REPO}/git/commits/{head}")
    base_tree = commit["tree"]["sha"]

    files = []
    for path in glob.glob(os.path.join(SITE_DIR, "**", "*"), recursive=True):
        if os.path.isdir(path): continue
        rel = os.path.relpath(path, SITE_DIR)
        files.append((rel, path))

    print(json.dumps({"files_to_push": [f[0] for f in files]}))

    tree_entries = []
    for rel, path in files:
        with open(path, "rb") as f:
            raw = f.read()
        content_b64 = base64.b64encode(raw).decode()
        s, blob = gh("POST", f"/repos/{OWNER}/{REPO}/git/blobs", {"content": content_b64, "encoding": "base64"})
        if s != 201:
            print(json.dumps({"FATAL": f"blob failed for {rel}: {s}", "resp": blob})); sys.exit(1)
        tree_entries.append({"path": rel.replace(os.sep, "/"), "mode": "100644", "type": "blob", "sha": blob["sha"]})

    s, tree = gh("POST", f"/repos/{OWNER}/{REPO}/git/trees", {"base_tree": base_tree, "tree": tree_entries})
    if s != 201:
        print(json.dumps({"FATAL": f"tree failed {s}", "resp": tree})); sys.exit(1)

    s, newc = gh("POST", f"/repos/{OWNER}/{REPO}/git/commits",
                 {"message": "Initial site: Jersey Village Water Damage & Mold Restoration demo (SEO/AIO/GEO)", "tree": tree["sha"], "parents": [head]})
    if s != 201:
        print(json.dumps({"FATAL": f"commit failed {s}", "resp": newc})); sys.exit(1)

    s, upd = gh("PATCH", f"/repos/{OWNER}/{REPO}/git/refs/heads/{branch}", {"sha": newc["sha"]})
    print(json.dumps({"update_ref": s, "branch": branch, "commit_sha": newc["sha"],
                       "commit_url": f"https://github.com/{OWNER}/{REPO}/commit/{newc['sha']}",
                       "repo_url": f"https://github.com/{OWNER}/{REPO}"}))

if __name__ == "__main__":
    main()
