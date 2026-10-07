"""An MCP client, written by hand so the protocol is not a mystery.

WHY NOT THE SDK
    The servers in mcp_servers/ use the official SDK, because a server has to
    be exactly right or nobody else's client can talk to it. The client is
    hand-written for the opposite reason: the week asks you to look at the raw
    messages once, and an SDK hides exactly the part worth seeing.

    It is about 150 lines. That is the whole protocol, for this use.

THE THREE ROLES, AND WHERE THE AI IS
    HOST    our app. It owns the model, the API key and the conversation. The
            AI runs HERE and nowhere else.
    CLIENT  this file. One per server. It speaks JSON-RPC and knows nothing
            about models.
    SERVER  a separate process. It offers tools. It has no idea an AI exists.

    The server never calls the model. The model never talks to the server. The
    host sits between them and does all the deciding.

THE WIRE
    Newline-delimited JSON-RPC 2.0 over the subprocess's stdin and stdout.
    Three messages get a session going:

      -> {"jsonrpc":"2.0","id":1,"method":"initialize","params":{...}}
      <- {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"...", ...}}
      -> {"jsonrpc":"2.0","method":"notifications/initialized"}

    The third has no id, because it is a notification and expects no reply.
    After that, two methods carry the actual work:

      tools/list   what can you do?
      tools/call   do this one

    That is it. Everything else in MCP is more of the same shape.

WHY STDIO
    The server runs on this machine, started by us, so there is no port to
    open, no certificate, no auth to get wrong. Remote servers use HTTP and
    then all of that comes back, which is the honest reason to prefer stdio
    until you actually need remote.

RECOVERABLE ERRORS
    A server that dies, or answers with an error, or takes too long, must not
    take the agent down with it. Every failure here comes back as a value the
    caller can read, the same discipline agent/tools.py already follows for
    its own tools.
"""
from __future__ import annotations

import json
import subprocess
import sys
import threading
from dataclasses import dataclass, field

# What we tell the server we speak. A server may answer with a different
# version; we record it rather than arguing, because the point is to notice a
# mismatch rather than to crash on one.
PROTOCOL_VERSION = "2025-06-18"

CLIENT_INFO = {"name": "helpcentre-agent", "version": "1.0.0"}

# A server that has not answered in this long is treated as dead. Without it a
# hung server hangs the agent, which is the failure this week's "recoverable
# errors" bullet is about.
TIMEOUT_S = 30.0

# Starting up is a different budget from answering. A server may have an index
# to build or a model to load before it can say hello, and that is normal.
# Being slow to answer AFTER it is ready is not. One timeout for both meant
# either killing healthy servers during start-up or waiting two minutes on a
# dead one, so they are separate numbers.
STARTUP_TIMEOUT_S = 180.0


@dataclass
class RemoteTool:
    """One tool, as the server described itself.

    `server` is carried so the caller knows where a tool came from. Two servers
    may both offer a "search", and a name alone is not a routing decision.
    """

    name: str
    description: str
    schema: dict
    server: str
    # What the SERVER calls this tool. The agent may rename it locally to
    # resolve a collision between two servers, and the rename must never reach
    # the wire: the server only knows its own name for it.
    remote_name: str = ""

    def __post_init__(self) -> None:
        if not self.remote_name:
            self.remote_name = self.name

    def arg_line(self) -> str:
        """The argument list, rendered for a prompt from the JSON schema."""
        props = (self.schema or {}).get("properties") or {}
        required = set((self.schema or {}).get("required") or [])
        parts = []
        for arg, spec in props.items():
            kind = spec.get("type", "any")
            parts.append(f"{arg}: {kind}" + ("" if arg in required else " (optional)"))
        return ", ".join(parts)


class MCPError(RuntimeError):
    """A failure talking to a server. Always caught, never raised at the agent."""


class MCPClient:
    """One connection to one MCP server, over its stdin and stdout."""

    def __init__(self, name: str, command: list[str], cwd: str | None = None) -> None:
        self.name = name
        self.command = command
        self.cwd = cwd
        self.proc: subprocess.Popen | None = None
        self.server_info: dict = {}
        self.protocol_version: str = ""
        self._id = 0
        self._log: list[dict] = []

    # -- wire ------------------------------------------------------------
    def _next_id(self) -> int:
        self._id += 1
        return self._id

    def _send(self, payload: dict) -> None:
        if self.proc is None or self.proc.stdin is None:
            raise MCPError(f"{self.name}: not started")
        line = json.dumps(payload)
        self._log.append({"dir": "->", "msg": payload})
        self.proc.stdin.write(line + "\n")
        self.proc.stdin.flush()

    def _read(self, timeout: float | None = None) -> dict:
        """One reply. Skips notifications, which carry no id and are not answers."""
        if self.proc is None or self.proc.stdout is None:
            raise MCPError(f"{self.name}: not started")
        result: dict = {}
        error: list = []

        def pump() -> None:
            while True:
                line = self.proc.stdout.readline()
                if not line:
                    error.append(MCPError(f"{self.name}: server closed the pipe"))
                    return
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    # Servers print to stdout by accident all the time. Skip the
                    # noise rather than dying on it.
                    continue
                self._log.append({"dir": "<-", "msg": msg})
                if "id" not in msg:
                    continue  # a notification, not our answer
                result.update(msg)
                return

        limit = TIMEOUT_S if timeout is None else timeout
        thread = threading.Thread(target=pump, daemon=True)
        thread.start()
        thread.join(limit)
        if thread.is_alive():
            raise MCPError(f"{self.name}: no reply within {limit:.0f}s")
        if error:
            raise error[0]
        if "error" in result:
            raise MCPError(f"{self.name}: {result['error'].get('message', result['error'])}")
        return result.get("result", {})

    def _request(self, method: str, params: dict | None = None,
                 timeout: float | None = None) -> dict:
        self._send(
            {"jsonrpc": "2.0", "id": self._next_id(), "method": method, "params": params or {}}
        )
        return self._read(timeout)

    def _notify(self, method: str, params: dict | None = None) -> None:
        self._send({"jsonrpc": "2.0", "method": method, "params": params or {}})

    # -- session ---------------------------------------------------------
    def start(self) -> None:
        """Launch the server and complete the handshake."""
        self.proc = subprocess.Popen(
            self.command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,  # server logs are not our protocol
            text=True,
            encoding="utf-8",
            bufsize=1,
            cwd=self.cwd,
        )
        result = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": CLIENT_INFO,
            },
            timeout=STARTUP_TIMEOUT_S,
        )
        self.protocol_version = result.get("protocolVersion", "")
        self.server_info = result.get("serverInfo", {})
        # The handshake is only finished once we say so. A server is entitled to
        # refuse work before this.
        self._notify("notifications/initialized")

    def list_tools(self) -> list[RemoteTool]:
        """Ask the server what it can do. This is the discovery step."""
        result = self._request("tools/list")
        return [
            RemoteTool(
                name=t["name"],
                description=t.get("description", ""),
                schema=t.get("inputSchema") or {},
                server=self.name,
            )
            for t in result.get("tools", [])
        ]

    def call_tool(self, name: str, args: dict) -> str:
        """Run one tool and return its text.

        MCP returns a list of typed content blocks. This app only reads text, so
        anything else is named rather than silently dropped.
        """
        result = self._request("tools/call", {"name": name, "arguments": args or {}})
        parts = []
        for block in result.get("content", []):
            if block.get("type") == "text":
                parts.append(block.get("text", ""))
            else:
                parts.append(f"[{block.get('type', 'unknown')} content, not read by this client]")
        text = "\n".join(p for p in parts if p)
        if result.get("isError"):
            return f"The tool reported an error: {text}"
        return text

    def stop(self) -> None:
        if self.proc is None:
            return
        try:
            if self.proc.stdin:
                self.proc.stdin.close()
            self.proc.wait(timeout=5)
        except Exception:
            self.proc.kill()
        finally:
            self.proc = None

    # -- for the write-up -------------------------------------------------
    def transcript(self, limit: int = 12) -> list[dict]:
        """The raw messages, in order. This is the thing worth reading once."""
        return self._log[:limit]

    def __enter__(self) -> "MCPClient":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()


def python_server(module: str) -> list[str]:
    """The command to run one of our own servers, using this interpreter."""
    return [sys.executable, "-m", module]
