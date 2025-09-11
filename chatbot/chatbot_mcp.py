import os
import json
import datetime
import threading
import re
import asyncio
from typing import Dict, List, Optional

import requests
from openai import OpenAI

# ====== CONFIG ======
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# HTTP servers (tu lógica original)
MCP_HTTP_ENDPOINTS = {
    "local":  "http://localhost:6000",
    "remoto": "https://mcp-remoto-783329965527.us-central1.run.app",
}

# STDIO servers (oficiales)
# Filesystem: npx -y @modelcontextprotocol/server-filesystem <root>
# Git: python -m mcp_server_git --repository <repo>
FS_ROOT = os.path.abspath("./workspace")
GIT_REPO = os.path.abspath("./repo_git")

LOG_PATH = "interactions.log"
client = OpenAI(api_key=OPENAI_API_KEY)

# ====== Utilidades comunes ======
def log_interaction(prompt, tool_name, params, result):
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{ts}]\nUsuario: {prompt}\nTool usada: {tool_name}\n"
        f"Parámetros: {params}\nRespuesta: {result}\n{'-'*40}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)

SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]+")
def slug(name: str) -> str:
    s = SAFE_NAME_RE.sub("_", name).strip("_")
    return s or "tool"

# ====== HTTP: describe/run (como ya tenías) ======
def fetch_tools_http(alias: str, base_url: str):
    try:
        r = requests.post(f"{base_url}/describe", timeout=10)
        r.raise_for_status()
        tools = r.json().get("tools", [])
        wrapped = []
        for t in tools:
            safe_bare = slug(t["name"])
            wrapped.append({
                "type": "function",
                "function": {
                    "name": f"{alias}__{safe_bare}",
                    "description": f"[{alias}] {t.get('description','')}",
                    "parameters": t.get("input_schema", {"type":"object"})
                }
            })
        return wrapped, {slug(t["name"]): t["name"] for t in tools}
    except Exception as e:
        print(f"⚠️ No se pudieron cargar tools HTTP de {alias}: {e}")
        return [], {}

def call_mcp_http(alias: str, tool_name_real: str, params: dict):
    payload = {"tool_name": tool_name_real, "input": params}
    try:
        r = requests.post(f"{MCP_HTTP_ENDPOINTS[alias]}/run", json=payload, timeout=20)
        return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def init_servers_http():
    for alias, base in MCP_HTTP_ENDPOINTS.items():
        try:
            requests.post(f"{base}/initialize", timeout=5)
        except Exception as e:
            print(f"⚠️ No se pudo inicializar (HTTP) {alias}: {e}")

# ====== STDIO: usando librería MCP de Python ======
from mcp import ClientSession, stdio_client, StdioServerParameters  # pip install mcp
import shutil
import sys
from pathlib import Path

class StdioServer:
    """Server STDIO genérico (filesystem/git)."""
    def __init__(self, alias: str, command: str, args: List[str]):
        self.alias = alias
        self.params = StdioServerParameters(command=command, args=args, env=None)
        self.cm = None
        self.session: ClientSession | None = None
        self.safe_to_real: Dict[str, str] = {}
        self.tools_for_openai: List[dict] = []

    async def start(self):
        if not shutil.which(self.params.command):
            raise RuntimeError(f"{self.params.command} no está en PATH")
        self.cm = stdio_client(self.params)
        r, w = await self.cm.__aenter__()
        self.session = await ClientSession(r, w).__aenter__()
        await self.session.initialize()

    async def stop(self):
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self.cm:
            await self.cm.__aexit__(None, None, None)

    async def discover(self):
        assert self.session
        resp = await self.session.list_tools()
        tools = getattr(resp, "tools", None) or (isinstance(resp, dict) and resp.get("tools")) or []
        self.safe_to_real = {}
        self.tools_for_openai = []
        for t in tools:
            real = getattr(t, "name", None) or (isinstance(t, dict) and t.get("name"))
            if not real:
                continue
            safe_bare = slug(real)
            self.safe_to_real[safe_bare] = real
            schema = getattr(t, "inputSchema", None) or (isinstance(t, dict) and t.get("input_schema")) or {"type": "object"}
            desc = getattr(t, "description", None) or (isinstance(t, dict) and t.get("description")) or ""
            self.tools_for_openai.append({
                "type": "function",
                "function": {
                    "name": f"{self.alias}__{safe_bare}",
                    "description": f"[{self.alias}] {desc}",
                    "parameters": schema
                }
            })

    async def call(self, safe_bare: str, arguments: dict):
        assert self.session
        real = self.safe_to_real.get(safe_bare, safe_bare)
        resp = await self.session.call_tool(real, arguments=arguments)
        if hasattr(resp, "model_dump"):
            return {"output": resp.model_dump()}
        return {"output": resp}

# Instancias STDIO para Filesystem y Git
def make_fs_server() -> StdioServer:
    Path(FS_ROOT).mkdir(parents=True, exist_ok=True)
    return StdioServer("fs", "npx", ["-y", "@modelcontextprotocol/server-filesystem", FS_ROOT])

def make_git_server() -> StdioServer:
    Path(GIT_REPO).mkdir(parents=True, exist_ok=True)
    # asegúrate que exista repo git si lo necesitas:
    # os.system(f'git -C "{GIT_REPO}" init')
    return StdioServer("git", sys.executable, ["-m", "mcp_server_git", "--repository", GIT_REPO])

# ====== Intención/ruteo ======
def detect_intent(text: str) -> str:
    s = text.lower()
    if any(k in s for k in [" git", "git ", "commit", "branch", "merge", "status", "log", "push", "pull", "clone"]):
        return "git"
    if any(k in s for k in ["archivo", "archivos", "carpeta", "filesystem", "leer", "escribir", "listar", "directorio"]):
        return "fs"
    if any(k in s for k in ["pago", "pagos", "saldo", "abono", "deuda"]):
        return "remoto"
    if any(k in s for k in ["tarea", "tareas", "snooze", "pendiente", "recordatorio", "crear tarea", "completar tarea", "listar tareas"]):
        return "local"
    return "all"

# ====== Main loop ======
async def main_async():
    print("🤖 Chatbot MCP (HTTP: local/remoto + STDIO: filesystem/git)")
    print("Escribe 'salir' para terminar.\n")

    # 1) HTTP init (tu lógica original)
    init_servers_http()

    # 2) STDIO start + discover
    fs_srv = make_fs_server()
    git_srv = make_git_server()
    try:
        await fs_srv.start()
    except Exception as e:
        print(f"⚠️ FS STDIO no disponible: {e}")
    try:
        await git_srv.start()
    except Exception as e:
        print(f"⚠️ GIT STDIO no disponible: {e}")

    if fs_srv.session:
        await fs_srv.discover()
    if git_srv.session:
        await git_srv.discover()

    # 3) Construir catálogo de tools (HTTP + STDIO)
    all_tools = []
    SAFE_TO_REAL_HTTP: Dict[str, Dict[str, str]] = {}

    # HTTP (local/remoto)
    for alias, base in MCP_HTTP_ENDPOINTS.items():
        tools, mapping = fetch_tools_http(alias, base)
        SAFE_TO_REAL_HTTP[alias] = mapping  # safe->real por alias HTTP
        all_tools.extend(tools)

    # STDIO (fs/git)
    if fs_srv.tools_for_openai:
        all_tools.extend(fs_srv.tools_for_openai)
    if git_srv.tools_for_openai:
        all_tools.extend(git_srv.tools_for_openai)

    if not all_tools:
        print("❌ No hay herramientas disponibles.")
        return

    # 4) System message
    history = [{
        "role": "system",
        "content": (
            "Eres un asistente conectado a 4 namespaces:\n"
            "- 'local__' (HTTP) para tareas.\n"
            "- 'remoto__' (HTTP) para finanzas.\n"
            "- 'fs__' (STDIO) para sistema de archivos.\n"
            "- 'git__' (STDIO) para operaciones Git locales.\n"
            "Regla: usa SOLO el namespace relevante según la intención del usuario. Responde en español."
        )
    }]

    # 5) Loop
    while True:
        user_input = input("👤 Tú: ").strip()
        if user_input.lower() in ("salir", "exit", "quit"):
            break

        history.append({"role": "user", "content": user_input})

        intent = detect_intent(user_input)
        if intent in ("local", "remoto", "fs", "git"):
            tools_turn = [t for t in all_tools if t["function"]["name"].startswith(f"{intent}__")]
            history.append({"role": "system", "content": f"Usa exclusivamente herramientas '{intent}__'."})
        else:
            tools_turn = all_tools
            history.append({"role": "system", "content": "Puedes usar cualquier herramienta disponible."})

        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=history,
                tools=tools_turn,
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            history.append(msg)

            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    full = tc.function.name  # p. ej. fs__read_file, local__list_tasks
                    args = json.loads(tc.function.arguments or "{}")

                    if "__" not in full:
                        print("⚠️ Tool inválida:", full); continue
                    alias, safe_bare = full.split("__", 1)

                    # HTTP aliases
                    if alias in MCP_HTTP_ENDPOINTS:
                        real = SAFE_TO_REAL_HTTP.get(alias, {}).get(safe_bare, safe_bare)
                        mcp_resp = call_mcp_http(alias, real, args)

                    # STDIO aliases
                    elif alias == "fs" and fs_srv.session:
                        mcp_resp = await fs_srv.call(safe_bare, args)
                    elif alias == "git" and git_srv.session:
                        mcp_resp = await git_srv.call(safe_bare, args)
                    else:
                        mcp_resp = {"error": {"message": f"alias '{alias}' no disponible"}}

                    # Normaliza salida
                    if "output" in mcp_resp:
                        result = mcp_resp["output"]
                    else:
                        result = mcp_resp.get("error", {}).get("message", "Error desconocido")

                    print("🤖", result)
                    log_interaction(user_input, full, args, result)

                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False) if not isinstance(result, str) else result}]
                    })
            else:
                print("🤖", msg.content)
                log_interaction(user_input, "LLM", {}, msg.content)

        except Exception as e:
            print("⚠️ Error:", e)

    # 6) Cierre STDIO
    await fs_srv.stop()
    await git_srv.stop()

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
