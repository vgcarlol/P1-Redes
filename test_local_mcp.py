# test_local_mcp.py
import asyncio
import json
import os
import shutil
import sys
from pathlib import Path
from typing import List, Optional

# ----- cliente MCP python -----
from mcp import ClientSession, stdio_client, StdioServerParameters

def log_mcp(kind: str, payload):
    print(f"[MCP:{kind}] {payload}")

def _find_tool_by_keywords(tools, keywords: List[str]) -> Optional[str]:
    if not tools:
        return None
    kws = [k.lower() for k in keywords]
    for t in tools:
        name = getattr(t, "name", None) or (isinstance(t, dict) and t.get("name"))
        if not name:
            continue
        n = name.lower()
        if any(k in n for k in kws):
            return name
    return None

class LocalMCP:
    """STDIO client que lanza servidores MCP oficiales via npx (filesystem) o Python (git)."""
    def __init__(self, name: str, command: str, args: List[str]):
        self.name = name
        self.params = StdioServerParameters(command=command, args=args, env=None)
        self._client_cm = None
        self.session: Optional[ClientSession] = None
        self.connected = False

    @staticmethod
    def filesystem(root: str) -> "LocalMCP":
        # Filesystem oficial: NO usa flags, pasa el root como posicional
        # npx -y @modelcontextprotocol/server-filesystem <root>
        return LocalMCP("filesystem", "npx", ["-y", "@modelcontextprotocol/server-filesystem", root])

    @staticmethod
    def git(repo: str) -> "LocalMCP":
        # Server de Git por Python (módulo del curso): python -m mcp_server_git --repository <repo>
        return LocalMCP("git", sys.executable, ["-m", "mcp_server_git", "--repository", repo])

    async def connect(self):
        # verifica que el comando exista
        if not shutil.which(self.params.command):
            raise RuntimeError(f"{self.params.command} no está en PATH")
        # abre STDIO
        self._client_cm = stdio_client(self.params)
        read_stream, write_stream = await self._client_cm.__aenter__()
        self.session = await ClientSession(read_stream, write_stream).__aenter__()
        # initialize
        await self.session.initialize()
        self.connected = True
        log_mcp("sync", {"server": self.name, "raw": "connected"})

    async def list_tools(self):
        if not self.session:
            raise RuntimeError("sin sesión")
        resp = await self.session.list_tools()
        log_mcp("response", {"server": self.name, "raw": getattr(resp, "model_dump", lambda: resp)()})
        return resp

    async def call_tool(self, name: str, arguments: dict):
        if not self.session:
            raise RuntimeError("sin sesión")
        log_mcp("request", {"server": self.name, "raw": {"name": name, "arguments": arguments}})
        resp = await self.session.call_tool(name, arguments=arguments)
        log_mcp("response", {"server": self.name, "raw": getattr(resp, "model_dump", lambda: resp)()})
        return resp

    async def find_tool(self, keywords: List[str]) -> Optional[str]:
        tools = await self.list_tools()
        tool_list = getattr(tools, "tools", None) or (isinstance(tools, dict) and tools.get("tools"))
        return _find_tool_by_keywords(tool_list, keywords)

    async def close(self):
        try:
            if self.session:
                await self.session.__aexit__(None, None, None)
            if self._client_cm:
                await self._client_cm.__aexit__(None, None, None)
        finally:
            self.connected = False

def pp(title, obj):
    print(f"\n=== {title} ===")
    try:
        print(json.dumps(obj, indent=2, ensure_ascii=False))
    except Exception:
        print(obj)

async def main():
    base = Path.cwd()
    workspace = str(base / "workspace")
    repo_path = str(base / "repo_git")
    Path(workspace).mkdir(parents=True, exist_ok=True)

    # ---- Filesystem
    fs = LocalMCP.filesystem(workspace)
    print("[FS] conectando...")
    await fs.connect()
    print("[FS] conectado ✓")
    fs_tools = await fs.list_tools()
    print("[FS] listado de tools OK")

    # busca y lee README.md si existe
    read_tool = await fs.find_tool(["read", "file"])
    if read_tool:
        target = "README.md" if Path("README.md").exists() else ""
        args = {"path": target} if target else {}
        try:
            resp = await fs.call_tool(read_tool, args)
            pp("FS read response", getattr(resp, "model_dump", lambda: resp)())
        except Exception as e:
            print(f"[FS] call_tool fallo: {e}")
    else:
        print("[FS] no encontré tool de lectura (read/file).")

    # ---- Git
    git = LocalMCP.git(repo_path)
    print("[GIT] conectando...")
    await git.connect()
    print("[GIT] conectado ✓")
    git_tools = await git.list_tools()
    print("[GIT] listado de tools OK")

    status_tool = await git.find_tool(["status"])
    if status_tool:
        resp = await git.call_tool(status_tool, {})
        pp("git status", getattr(resp, "model_dump", lambda: resp)())
    else:
        print("[GIT] no encontré tool de status.")

    # cierre ordenado
    await git.close()
    await fs.close()
    print("\nTodo OK. Cerrado. ✓")

if __name__ == "__main__":
    asyncio.run(main())
