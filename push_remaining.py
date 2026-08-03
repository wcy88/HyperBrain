#!/usr/bin/env python
"""
Push remaining files to GitHub via MCP server (sync version).
Pushes tests/, docs/, and sensenova-skills/ files.
"""
import json
import os
import subprocess
import sys
import base64
import time
from pathlib import Path

ROOT_DIR = r"e:\超脑\超脑002"
OWNER = "wcy88"
REPO = "HyperBrain"
BRANCH = "main"

TEST_FILES = [
    "tests/test_e2e_test_model_revert.py",
    "tests/test_execution.py",
    "tests/test_gui_session_manager.py",
    "tests/test_hermes_auto_skill.py",
    "tests/test_hermes_nudge.py",
    "tests/test_hermes_trajectory.py",
    "tests/test_learning_system.py",
    "tests/test_sensory.py",
    "tests/test_settings_dialog_validation.py",
    "tests/test_thinking_timeout.py",
    "tests/test_thinking_visualization.py",
]

BINARY_EXTENSIONS = {
    ".webp", ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".svg",
    ".zip", ".tar", ".gz", ".7z", ".rar",
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".mp3", ".mp4", ".avi", ".mov", ".wmv", ".flv",
    ".woff", ".woff2", ".ttf", ".eot",
    ".db", ".sqlite", ".sqlite3",
    ".pkl", ".pickle", ".npy", ".npz",
    ".pyc", ".pyo",
    ".o", ".obj",
}


def is_binary(filepath):
    return Path(filepath).suffix.lower() in BINARY_EXTENSIONS


def read_file(filepath):
    full_path = os.path.join(ROOT_DIR, filepath)
    if not os.path.exists(full_path):
        return None
    with open(full_path, "rb") as f:
        return f.read()


def get_git_tracked_files(directory):
    result = subprocess.run(
        ["git", "ls-files", directory],
        capture_output=True, text=True, cwd=ROOT_DIR
    )
    files = [f.strip() for f in result.stdout.split("\n") if f.strip()]
    return files


class MCPClient:
    def __init__(self):
        self.proc = None
        self.req_id = 0

    def start(self):
        env = os.environ.copy()
        env["PATH"] = r"E:\Program Files\nodejs" + os.pathsep + env.get("PATH", "")
        self.proc = subprocess.Popen(
            ["npx.cmd", "-y", "@modelcontextprotocol/server-github"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
            cwd=ROOT_DIR,
        )
        # Initialize
        self._send("initialize", {
            "protocolVersion": "0.1.0",
            "capabilities": {},
            "clientInfo": {"name": "hyperbrain-push", "version": "1.0.0"},
        })
        resp = self._recv()
        print(f"  MCP 初始化: {json.dumps(resp, indent=2)[:200]}")
        if resp and "capabilities" in resp.get("result", {}):
            print("  ✅ MCP 服务器连接成功")
        else:
            print(f"  ❌ MCP 初始化异常: {resp}")
            return False
        
        # Send initialized notification
        self._send_notification("notifications/initialized", {})
        return True

    def _send(self, method, params):
        self.req_id += 1
        req = {"jsonrpc": "2.0", "id": self.req_id, "method": method, "params": params}
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()
        return self.req_id

    def _send_notification(self, method, params):
        req = {"jsonrpc": "2.0", "method": method, "params": params}
        self.proc.stdin.write(json.dumps(req) + "\n")
        self.proc.stdin.flush()

    def _recv(self, timeout=60):
        """Read one JSON-RPC response from stdout."""
        import select
        import socket
        start = time.time()
        while time.time() - start < timeout:
            if self.proc.poll() is not None:
                # Process died
                err = self.proc.stderr.read()
                print(f"  MCP 进程已退出, stderr: {err[:500]}")
                return None
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.1)
                continue
            line = line.strip()
            if not line:
                continue
            try:
                return json.loads(line)
            except json.JSONDecodeError as e:
                print(f"  JSON 解析错误: {e}, 行: {line[:200]}")
                continue
        return None

    def call_tool(self, tool_name, arguments):
        req_id = self._send("tools/call", {"name": tool_name, "arguments": arguments})
        return self._recv()

    def close(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            self.proc.wait(timeout=5)


def main():
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("❌ 错误: 未设置 GITHUB_TOKEN 环境变量")
        sys.exit(1)
    
    print(f"✅ GITHUB_TOKEN 已设置: {token[:4]}...{token[-4:]}")

    # Collect all files
    all_files = list(TEST_FILES)
    docs_files = get_git_tracked_files("docs/")
    print(f"📄 docs/ 目录: {len(docs_files)} 个文件")
    all_files.extend(docs_files)
    ss_files = get_git_tracked_files("sensenova-skills/")
    print(f"📦 sensenova-skills/ 目录: {len(ss_files)} 个文件")
    all_files.extend(ss_files)
    all_files = list(dict.fromkeys(all_files))
    print(f"\n📊 总共需要推送: {len(all_files)} 个文件")
    print(f"   tests/: {len(TEST_FILES)} 个文件")
    print(f"   docs/: {len(docs_files)} 个文件")
    print(f"   sensenova-skills/: {len(ss_files)} 个文件")

    # Check if stderr has any errors
    # Start MCP server
    print("\n🔌 启动 MCP 服务器...")
    client = MCPClient()
    if not client.start():
        print("❌ 无法启动 MCP 服务器")
        # Read stderr
        if client.proc and client.proc.stderr:
            err = client.proc.stderr.read()
            if err:
                print(f"stderr: {err[:500]}")
        sys.exit(1)

    # Push files in batches
    BATCH_SIZE = 10
    total_batches = (len(all_files) + BATCH_SIZE - 1) // BATCH_SIZE
    success_count = 0
    fail_count = 0

    for start_idx in range(0, len(all_files), BATCH_SIZE):
        batch = all_files[start_idx:start_idx + BATCH_SIZE]
        batch_num = start_idx // BATCH_SIZE + 1
        
        # Read file contents
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

        # Determine batch description
        paths = [f["path"] for f in files_data]
        if any(p.startswith("tests/") for p in paths):
            desc = "tests/"
        elif any(p.startswith("docs/") for p in paths):
            desc = "docs/"
        else:
            desc = "sensenova-skills/"
        
        msg = f"chore: push remaining files [{batch_num}/{total_batches}] - {desc}"

        print(f"\n📤 批次 {batch_num}/{total_batches} ({len(files_data)} 个文件, {desc})")
        for f in files_data[:3]:
            print(f"   - {f['path']}")
        if len(files_data) > 3:
            print(f"   ... 还有 {len(files_data)-3} 个文件")

        # Call push_files
        result = client.call_tool("push_files", {
            "owner": OWNER,
            "repo": REPO,
            "branch": BRANCH,
            "files": files_data,
            "message": msg,
        })

        if result:
            content_list = result.get("result", {}).get("content", [])
            text = content_list[0].get("text", "") if content_list else ""
            is_error = result.get("error") is not None
            
            if is_error:
                print(f"  ❌ 批次 {batch_num} 失败: {result.get('error', '')}")
                fail_count += 1
            elif "error" in text.lower():
                print(f"  ❌ 批次 {batch_num} 失败: {text[:200]}")
                fail_count += 1
            else:
                print(f"  ✅ 批次 {batch_num} 推送成功")
                success_count += 1
        else:
            # Check stderr
            err = client.proc.stderr.read() if client.proc.stderr else ""
            print(f"  ❌ 批次 {batch_num} 失败 (无响应)")
            if err:
                print(f"  stderr: {err[:300]}")
            fail_count += 1
            # Try to reinitialize
            print("  尝试重新连接...")
            client.close()
            time.sleep(1)
            if not client.start():
                print("  ❌ 重新连接失败")
                break

        time.sleep(0.5)

    client.close()
    print(f"\n{'='*50}")
    print(f"📊 推送完成: ✅ {success_count} 成功, ❌ {fail_count} 失败 / {total_batches} 批次")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()