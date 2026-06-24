"""
Push all tracked files to GitHub via the REST API.
Requires GITHUB_TOKEN environment variable with repo scope.
"""
import base64
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OWNER = "wcy88"
REPO = "HyperBrain"
BRANCH = "main"
API_BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"

TOKEN = os.environ.get("GITHUB_TOKEN")
if not TOKEN:
    print("错误：未设置 GITHUB_TOKEN 环境变量", file=sys.stderr)
    sys.exit(1)

HEADERS = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "HyperBrain-Publisher",
}


def api_request(method, url, data=None, retries=3):
    """Make a GitHub API request with retries."""
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        HEADERS["Content-Type"] = "application/json"

    for attempt in range(retries):
        req = urllib.request.Request(url, data=body, headers=HEADERS, method=method)
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            err = e.read().decode("utf-8", errors="ignore")
            print(f"HTTP {e.code}: {err[:500]}", file=sys.stderr)
            if e.code in (401, 403, 404):
                raise
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"Retry in {wait}s...", file=sys.stderr)
                time.sleep(wait)
        except Exception as e:
            print(f"Request error: {e}", file=sys.stderr)
            if attempt < retries - 1:
                wait = 2 ** attempt
                print(f"Retry in {wait}s...", file=sys.stderr)
                time.sleep(wait)
    raise RuntimeError(f"Failed after {retries} attempts: {url}")


def list_tracked_files():
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=True,
    )
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def read_file_bytes(path):
    with open(os.path.join(ROOT, path), "rb") as f:
        return f.read()


def get_branch_sha():
    ref = api_request("GET", f"{API_BASE}/git/ref/heads/{BRANCH}")
    return ref["object"]["sha"]


def create_blob(content_bytes):
    data = {
        "content": base64.b64encode(content_bytes).decode("ascii"),
        "encoding": "base64",
    }
    result = api_request("POST", f"{API_BASE}/git/blobs", data)
    return result["sha"]


def create_tree(file_blobs, base_tree_sha):
    tree = []
    for path, blob_sha in file_blobs.items():
        tree.append({
            "path": path,
            "mode": "100644",
            "type": "blob",
            "sha": blob_sha,
        })
    data = {
        "base_tree": base_tree_sha,
        "tree": tree,
    }
    result = api_request("POST", f"{API_BASE}/git/trees", data)
    return result["sha"]


def create_commit(tree_sha, parent_sha, message):
    data = {
        "message": message,
        "tree": tree_sha,
        "parents": [parent_sha],
    }
    result = api_request("POST", f"{API_BASE}/git/commits", data)
    return result["sha"]


def update_ref(commit_sha):
    data = {"sha": commit_sha, "force": False}
    api_request("PATCH", f"{API_BASE}/git/refs/heads/{BRANCH}", data)


def delete_remote_only_files(paths):
    """Delete files that exist on remote but not in local tracked files."""
    if not paths:
        return
    print(f"Deleting {len(paths)} remote-only files: {paths}")
    parent_sha = get_branch_sha()
    current_tree = api_request("GET", f"{API_BASE}/git/trees/{parent_sha}?recursive=1")
    new_tree_entries = [
        {"path": item["path"], "mode": item["mode"], "type": item["type"], "sha": item["sha"]}
        for item in current_tree.get("tree", [])
        if item["type"] == "blob" and item["path"] not in paths
    ]
    tree_data = {"tree": new_tree_entries}
    new_tree = api_request("POST", f"{API_BASE}/git/trees", tree_data)
    commit_sha = create_commit(new_tree["sha"], parent_sha, "chore: remove test files")
    update_ref(commit_sha)
    print(f"Deleted remote-only files, new commit: {commit_sha}")


def main():
    files = list_tracked_files()
    print(f"Pushing {len(files)} tracked files to {OWNER}/{REPO}:{BRANCH}")

    parent_sha = get_branch_sha()
    print(f"Parent commit: {parent_sha}")

    # Create blobs in batches to avoid memory issues
    file_blobs = {}
    batch_size = 100
    for i in range(0, len(files), batch_size):
        batch = files[i:i + batch_size]
        for path in batch:
            content = read_file_bytes(path)
            blob_sha = create_blob(content)
            file_blobs[path] = blob_sha
            print(f"  blob {path} -> {blob_sha[:7]}")

    print(f"Created {len(file_blobs)} blobs")

    tree_sha = create_tree(file_blobs, parent_sha)
    print(f"Created tree: {tree_sha}")

    commit_sha = create_commit(tree_sha, parent_sha, "chore: publish project to GitHub via MCP")
    print(f"Created commit: {commit_sha}")

    update_ref(commit_sha)
    print(f"Updated {BRANCH} to {commit_sha}")

    # Clean up test files created during MCP connectivity tests
    delete_remote_only_files(["test_mcp_push.txt", "test_binary.webp", "test_mcp_batch.txt", "test_mcp_batch2.txt"])

    print(f"Done: https://github.com/{OWNER}/{REPO}/tree/{BRANCH}")


if __name__ == "__main__":
    main()
