#!/usr/bin/env python
"""
MCP client to call GitHub push_files tool via stdio.
Communicates with @modelcontextprotocol/server-github via JSON-RPC.
"""
import json
import subprocess
import sys
import uuid
import base64
import os
import time
from pathlib import Path

ROOT_DIR = "e:\\超脑\\超脑002"
OWNER = "wcy88"
REPO = "HyperBrain"
BRANCH = "main"

# Binary file extensions
BINARY_EXTENSIONS = {
    ".webp", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".exe", ".dll", ".so", ".dylib",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv",
    ".woff", ".woff2", ".ttf", ".eot",
    ".db", ".sqlite", ".sqlite3",
    ".pkl", ".pickle", ".npy", ".npz",
    ".pyc", ".pyo",
    ".o", ".obj",
}


def is_binary(filepath):
    ext = Path(filepath).suffix.lower()
    return ext in BINARY_EXTENSIONS


def read_file(filepath):
    full_path = os.path.join(ROOT_DIR, filepath)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "rb") as f:
        content = f.read()
    return content


class MCPClient:
    def __init__(self):
        self.proc = None
        self.request_id = 0

    def connect(self):
        # Try to find GITHUB_TOKEN from environment
        env = os.environ.copy()
        # If no token is set, the server will use unauthenticated access
        self.proc = subprocess.Popen(
            ["npx", "-y", "@modelcontextprotocol/server-github"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        # Initialize
        self._send_request("initialize", {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {"name": "hyperbrain-push", "version": "1.0.0"},
        })
        result = self._read_response()
        print(f"Initialize: {json.dumps(result, indent=2)[:200]}")

        # Send initialized notification
        self._send_notification("notifications/initialized", {})

    def _send_request(self, method, params):
        self.request_id += 1
        req = {
            "jsonrpc": "2.0",
            "id": self.request_id,
            "method": method,
            "params": params,
        }
        print(f">>> {method} (id={self.request_id})")
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()

    def _send_notification(self, method, params):
        req = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
        }
        print(f">>> {method} (notification)")
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()

    def _read_response(self):
        line = self.proc.stdout.readline()
        if not line:
            stderr = self.proc.stderr.read()
            print(f"Server stderr: {stderr[:500]}")
            return None
        try:
            return json.loads(line.strip())
        except json.JSONDecodeError:
            print(f"Failed to parse: {line[:200]}")
            return None

    def call_tool(self, tool_name, arguments):
        self._send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments,
        })
        result = self._read_response()
        return result

    def close(self):
        if self.proc:
            self.proc.terminate()
            self.proc.wait(timeout=5)


def get_local_files():
    """Get all git-tracked files from the local repository."""
    result = subprocess.run(
        ["git", "ls-files", "--full-name"],
        capture_output=True, text=True, cwd=ROOT_DIR
    )
    files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
    return files


def main():
    # Check if GITHUB_TOKEN is set
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("错误: 未设置 GITHUB_TOKEN 环境变量")
        print("请设置 GITHUB_TOKEN 后再运行此脚本")
        print("用法: set GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxx")
        sys.exit(1)

    print(f"GITHUB_TOKEN 已设置: {token[:4]}...{token[-4:]}")

    # Get local files
    print("\n获取本地跟踪文件列表...")
    local_files = get_local_files()
    print(f"共 {len(local_files)} 个文件")

    # Try to use the MCP server
    print("\n连接 GitHub MCP 服务器...")
    client = MCPClient()
    try:
        client.connect()
    except Exception as e:
        print(f"连接失败: {e}")
        client.close()
        sys.exit(1)

    # Test with get_file_contents
    print("\n获取远程仓库根目录文件列表...")
    result = client.call_tool("get_file_contents", {
        "owner": OWNER,
        "repo": REPO,
        "path": "",
        "branch": BRANCH,
    })
    print(f"Result: {json.dumps(result, indent=2)[:500]}")

    # Push files in batches
    BATCH_SIZE = 20
    total_batches = (len(local_files) + BATCH_SIZE - 1) // BATCH_SIZE

    for batch_idx in range(0, len(local_files), BATCH_SIZE):
        batch = local_files[batch_idx:batch_idx + BATCH_SIZE]
        batch_num = batch_idx // BATCH_SIZE + 1
        print(f"\n--- 批次 {batch_num}/{total_batches} ({len(batch)} 个文件) ---")

        files_data = []
        for filepath in batch:
            content = read_file(filepath)
            if content is None:
                print(f"  ⚠ 跳过: {filepath} (文件不存在)")
                continue

            if is_binary(filepath):
                files_data.append({
                    "path": filepath,
                    "content": base64.b64encode(content).decode("ascii"),
                })
            else:
                files_data.append({
                    "path": filepath,
                    "content": content.decode("utf-8", errors="replace"),
                })

        if not files_data:
            continue

        # Call push_files
        result = client.call_tool("push_files", {
            "owner": OWNER,
            "repo": REPO,
            "branch": BRANCH,
            "files": files_data,
            "message": f"chore: push files batch {batch_num}/{total_batches}",
        })

        if result:
            print(f"  ✓ 批次 {batch_num} 推送成功")
        else:
            print(f"  ✗ 批次 {batch_num} 失败")

        time.sleep(1)

    client.close()
    print("\n✓ 所有批次推送完成!")


if __name__ == "__main__":
    main()