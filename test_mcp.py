"""Simple MCP test - push one file."""
import json
import os
import subprocess
import sys
import time
import base64

# Flush stdout
def log(msg):
    print(msg, flush=True)

ROOT_DIR = r"e:\超脑\超脑002"

# Read the test file
filepath = "tests/test_e2e_test_model_revert.py"
with open(os.path.join(ROOT_DIR, filepath), "rb") as f:
    content = f.read()

content_text = content.decode("utf-8")

env = os.environ.copy()
env["PATH"] = r"E:\Program Files\nodejs" + os.pathsep + env.get("PATH", "")

log("Starting MCP server...")
# Start MCP server, merging stderr into stdout
proc = subprocess.Popen(
    ["npx.cmd", "-y", "@modelcontextprotocol/server-github"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    bufsize=1,
    env=env,
    cwd=ROOT_DIR,
)
log("MCP server started")

def send(method, params, req_id=1):
    req = {"jsonrpc": "2.0", "id": req_id, "method": method, "params": params}
    log(f">>> {method} (id={req_id})")
    proc.stdin.write(json.dumps(req) + "\n")
    proc.stdin.flush()

def recv(timeout=60):
    start = time.time()
    while time.time() - start < timeout:
        if proc.poll() is not None:
            log(f"Process exited with code {proc.returncode}")
            return None
        line = proc.stdout.readline()
        if not line:
            time.sleep(0.2)
            continue
        line = line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            log(f"Non-JSON output: {line[:200]}")
            time.sleep(0.1)
            continue
    log("Timeout waiting for response")
    return None

# Initialize
log("Sending initialize...")
send("initialize", {
    "protocolVersion": "0.1.0",
    "capabilities": {},
    "clientInfo": {"name": "test", "version": "1.0"},
})
log("Waiting for init response...")
resp = recv()
log(f"Init response: {json.dumps(resp, indent=2)[:500] if resp else 'None'}")

if not resp:
    # Read any remaining output
    remaining = ""
    try:
        while True:
            line = proc.stdout.read(1)
            if not line:
                break
            remaining += line
    except:
        pass
    log(f"Remaining output: {remaining[:500]}")
    proc.terminate()
    proc.wait(timeout=5)
    sys.exit(1)

# Send initialized notification
send("notifications/initialized", {})

# List tools
log("\nListing tools...")
send("tools/list", {}, req_id=2)
resp = recv()
tools = resp.get("result", {}).get("tools", []) if resp else []
tool_names = [t["name"] for t in tools]
log(f"Available tools: {tool_names}")

# Call push_files with one file
log("\nPushing file...")
send("tools/call", {
    "name": "push_files",
    "arguments": {
        "owner": "wcy88",
        "repo": "HyperBrain",
        "branch": "main",
        "files": [
            {"path": filepath, "content": content_text}
        ],
        "message": "test: push single file via MCP"
    }
}, req_id=3)
resp = recv()
log(f"Push response: {json.dumps(resp, indent=2)[:1000] if resp else 'None'}")

proc.terminate()
proc.wait(timeout=5)
log("Done")