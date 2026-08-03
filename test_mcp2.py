"""Test MCP server with simpler approach."""
import json
import os
import subprocess
import time

env = os.environ.copy()
env["PATH"] = r"E:\Program Files\nodejs" + os.pathsep + env.get("PATH", "")

# Send initialize request via stdin, read from stdout
init_req = json.dumps({
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "0.1.0", "capabilities": {}, "clientInfo": {"name": "test", "version": "1.0"}}
}) + "\n"

print("Starting MCP server...", flush=True)
proc = subprocess.Popen(
    ["npx.cmd", "-y", "@modelcontextprotocol/server-github"],
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,
    bufsize=1,
    env=env,
    cwd=r"e:\超脑\超脑002",
)

# Send initialize
print("Sending initialize...", flush=True)
proc.stdin.write(init_req)
proc.stdin.flush()

# Read response with timeout
import select
import sys

# Wait for output
time.sleep(3)

# Read available data
stdout_data = ""
stderr_data = ""
while True:
    import msvcrt
    # Check if there's data to read
    if proc.stdout.readable():
        line = proc.stdout.readline()
        if not line:
            break
        stdout_data += line
        if len(stdout_data) > 10000:
            break
    else:
        break

# Also read stderr
try:
    stderr_data = proc.stderr.read()
except:
    pass

print(f"stdout: {stdout_data[:1000]}", flush=True)
print(f"stderr: {stderr_data[:500]}", flush=True)

proc.terminate()
proc.wait(timeout=5)