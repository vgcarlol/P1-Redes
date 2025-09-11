import os
import json
import datetime
import threading
import re
import requests
from openai import OpenAI

# ========== CONFIGURACIÓN ==========
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

# Endpoints:
# - REST clásico: base SIN /mcp (ej: http://localhost:6000)
# - Streamable HTTP: base TERMINA en /mcp (ej: http://127.0.0.1:7001/mcp)
MCP_ENDPOINTS = {
    "local":  "http://localhost:6000",
    "remoto": "https://mcp-remoto-783329965527.us-central1.run.app",
    "git":    "http://127.0.0.1:7001/mcp",  # Git MCP (streamable HTTP)
}

LOG_PATH = "interactions.log"
client = OpenAI(api_key=OPENAI_API_KEY)

# ========== SOPORTE STREAMABLE HTTP (JSON-RPC + Sesión + SSE) ==========
PROTOCOL_VERSION = "2025-03-26"
MCP_SESSIONS: dict[str, str] = {}         # alias -> session_id
MCP_SESSIONS_LOCK = threading.Lock()

# Mapa nombre-seguro -> nombre-real por alias (lo llenamos en fetch_tools)
SAFE_TO_REAL: dict[str, dict[str, str]] = {}   # {alias: {safe_bare: real_bare}}

SAFE_NAME_RE = re.compile(r"[^a-zA-Z0-9_-]+")

def slug_tool_name(name: str) -> str:
    """Convierte nombres raros (con ., /, espacios, etc.) a formato válido para OpenAI."""
    safe = SAFE_NAME_RE.sub("_", name).strip("_")
    return safe or "tool"

def is_streamable_http(url: str) -> bool:
    """Heurística: endpoints que terminan en /mcp usan JSON-RPC streamable."""
    return url.rstrip("/").endswith("/mcp")

def mcp_jsonrpc_post(base_url: str, method: str, params: dict | None, session_id: str | None):
    """
    POST JSON-RPC al endpoint /mcp.
    Devuelve (response, maybe_new_session_id).
    """
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",  # requerido por HTTP streamable
    }
    if session_id:
        headers["Mcp-Session-Id"] = session_id
    payload = {"jsonrpc": "2.0", "id": "req-1", "method": method}
    if params is not None:
        payload["params"] = params
    r = requests.post(base_url, json=payload, headers=headers, timeout=30)
    new_sid = r.headers.get("Mcp-Session-Id")
    return r, new_sid

def parse_streamable_json(r):
    """Si Content-Type es SSE, extrae el JSON de líneas 'data:'; si no, usa r.json()."""
    ctype = (r.headers.get("Content-Type") or "").lower()
    if "text/event-stream" in ctype:
        payload_lines = []
        for line in r.text.splitlines():
            line = line.strip()
            if line.startswith("data:"):
                payload_lines.append(line[len("data:"):].strip())
        if not payload_lines:
            raise ValueError("SSE sin líneas 'data:'")
        return json.loads("\n".join(payload_lines))
    return r.json()

def ensure_streamable_session(alias: str, base_url: str) -> str:
    """Crea/recupera sesión para endpoints /mcp (initialize con parámetros obligatorios)."""
    with MCP_SESSIONS_LOCK:
        sid = MCP_SESSIONS.get(alias)
    if not sid:
        init_params = {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"roots": {"listChanged": False}},
            "clientInfo": {"name": "P1-Redes-Chatbot", "version": "1.0.0"},
        }
        r, new_sid = mcp_jsonrpc_post(base_url, "initialize", init_params, session_id=None)
        try:
            _ = parse_streamable_json(r)  # solo para levantar errores si vinieran en body
        except Exception:
            pass
        if not new_sid:
            body_preview = ""
            try:
                body_preview = r.text[:400]
            except Exception:
                pass
            raise RuntimeError(
                f"No se obtuvo Mcp-Session-Id al inicializar {alias}. "
                f"status={r.status_code} body={body_preview}"
            )
        with MCP_SESSIONS_LOCK:
            MCP_SESSIONS[alias] = new_sid
        sid = new_sid
    return sid

# ========== UTILIDADES ==========
def log_interaction(prompt, tool_name, params, result):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = (
        f"[{timestamp}]\n"
        f"Usuario: {prompt}\n"
        f"Tool usada: {tool_name}\n"
        f"Parámetros: {params}\n"
        f"Respuesta: {result}\n"
        f"{'-'*40}\n"
    )
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(entry)

def fetch_tools(alias: str, base_url: str):
    """
    Descubre tools del servidor MCP y las publica para el modelo con nombres SEGUROS:
      - OpenAI solo permite ^[a-zA-Z0-9_-]+$ → aplicamos slug + mapeo safe→real.
      - Namespace con 'alias__' para rutear.
    """
    try:
        if is_streamable_http(base_url):
            sid = ensure_streamable_session(alias, base_url)
            # Intento: describe -> si falla, list_tools
            r, _ = mcp_jsonrpc_post(base_url, "describe", {}, session_id=sid)
            try:
                data = parse_streamable_json(r)
                if "error" in data:
                    r, _ = mcp_jsonrpc_post(base_url, "list_tools", {}, session_id=sid)
                    data = parse_streamable_json(r)
            except Exception:
                r, _ = mcp_jsonrpc_post(base_url, "list_tools", {}, session_id=sid)
                data = parse_streamable_json(r)
            raw_tools = data.get("result", {}).get("tools", [])
        else:
            r = requests.post(f"{base_url}/describe", timeout=10)
            r.raise_for_status()
            raw_tools = r.json().get("tools", [])

        # Construir mapping seguro->real por alias
        SAFE_TO_REAL[alias] = {}
        wrapped = []

        for t in raw_tools:
            real_name = t["name"]
            safe_bare = slug_tool_name(real_name)
            SAFE_TO_REAL[alias][safe_bare] = real_name  # guardar mapeo

            # Build tool para OpenAI
            wrapped.append({
                "type": "function",
                "function": {
                    "name": f"{alias}__{safe_bare}",
                    "description": f"[{alias}] {t.get('description', '')}",
                    "parameters": t.get("input_schema", {"type": "object"})
                }
            })

        # Debug útil
        print(f"🔧 {alias}: {len(wrapped)} tools cargadas")
        for safe_bare, real in SAFE_TO_REAL[alias].items():
            print(f"   - {alias}__{safe_bare}  ->  {real}")

        return wrapped

    except Exception as e:
        print(f"⚠️ No se pudieron cargar tools de {alias}: {e}")
        try:
            print("   ↳ headers:", r.headers if 'r' in locals() else "n/a")
            print("   ↳ first 300 chars:", r.text[:300] if 'r' in locals() else "n/a")
        except Exception:
            pass
        return []

def call_mcp(alias: str, tool_name: str, params: dict):
    """
    Invoca una tool:
      - REST:   POST {base}/run  con {"tool_name","input"}
      - STREAM: POST {base} JSON-RPC call_tool con sesión (SSE)
    """
    base = MCP_ENDPOINTS[alias]
    try:
        if is_streamable_http(base):
            sid = ensure_streamable_session(alias, base)
            # tool_name viene en forma segura (porque es el que eligió el modelo)
            real_bare = SAFE_TO_REAL.get(alias, {}).get(tool_name, tool_name)
            r, _ = mcp_jsonrpc_post(
                base,
                "call_tool",
                {"name": real_bare, "arguments": params},
                session_id=sid
            )
            data = parse_streamable_json(r)
            if "result" in data:
                return {"output": data["result"]}
            if "error" in data:
                return {"error": {"message": data["error"].get("message", str(data))}}
            return {"output": data}
        else:
            payload = {"tool_name": tool_name, "input": params}
            r = requests.post(f"{base}/run", json=payload, timeout=20)
            r.raise_for_status()
            return r.json()
    except Exception as e:
        return {"error": {"message": str(e)}}

def init_servers():
    """Inicializa cada MCP (REST: /initialize | STREAM: initialize JSON-RPC)."""
    for alias, base in MCP_ENDPOINTS.items():
        try:
            if is_streamable_http(base):
                ensure_streamable_session(alias, base)
            else:
                requests.post(f"{base}/initialize", timeout=5)
        except Exception as e:
            print(f"⚠️ No se pudo inicializar {alias}: {e}")

# ========= RUTEO POR INTENCIÓN =========
def detect_intent(text: str) -> str:
    s = text.lower()
    git_kw = [
        " git", "git ", "repositorio", "repo", "commit", "branch", "rama", "merge",
        "status", "log", "checkout", " add", " init", "push", "pull", "tag", "clone",
        "inicializa un repositorio", "inicializar repositorio", "crear repo", "crear repositorio"
    ]
    pay_kw = ["pago", "pagos", "saldo", "abono", "deuda", "transferencia"]
    task_kw = ["tarea", "tareas", "snooze", "pendiente", "recordatorio",
               "crear tarea", "completar tarea", "listar tareas", "lista de tareas"]

    if any(k in s for k in git_kw):
        return "git"
    if any(k in s for k in pay_kw):
        return "remoto"
    if any(k in s for k in task_kw):
        return "local"
    return "all"

# ========== LOOP PRINCIPAL ==========
def main():
    print("🤖 Chatbot MCP (OpenAI + Local + Remoto + Git)")
    print("Escribe 'salir' para terminar.\n")

    init_servers()

    # Descubrir tools de todos los servidores
    all_tools = []
    for alias, base in MCP_ENDPOINTS.items():
        all_tools.extend(fetch_tools(alias, base))
    if not all_tools:
        print("❌ No hay herramientas disponibles.")
        return

    # Agrupar tools por alias para ruteo
    TOOLS_BY_ALIAS: dict[str, list[dict]] = {}
    for t in all_tools:
        name = t["function"]["name"]
        alias = name.split("__", 1)[0] if "__" in name else "misc"
        TOOLS_BY_ALIAS.setdefault(alias, []).append(t)

    # Prompt del sistema (reglas de ruteo)
    history = [{
        "role": "system",
        "content": (
            "Eres un asistente conectado a servidores MCP:\n"
            "- 'local__' para tareas (crear, listar, completar, snooze).\n"
            "- 'remoto__' para finanzas (consultar saldo, registrar pagos).\n"
            "- 'git__' para operaciones Git (init, add, commit, status, log, etc.).\n"
            "Regla de ruteo estricta:\n"
            "- Si el usuario menciona git/repositorio/commit/branch/status/log, usa SOLO 'git__'.\n"
            "- Si menciona pagos/saldos, usa SOLO 'remoto__'.\n"
            "- Si menciona tareas/listas/snooze, usa SOLO 'local__'.\n"
            "Nunca conviertas una instrucción git en una tarea. Responde en español."
        )
    }]

    while True:
        user_input = input("👤 Tú: ").strip()
        if user_input.lower() in ("salir", "exit"):
            break

        history.append({"role": "user", "content": user_input})

        # Elegir tools del turno según intención
        intent = detect_intent(user_input)
        if intent in TOOLS_BY_ALIAS and TOOLS_BY_ALIAS[intent]:
            tools_for_turn = TOOLS_BY_ALIAS[intent]
            hint = f"Para esta petición usa exclusivamente el namespace '{intent}__'."
        else:
            tools_for_turn = all_tools
            hint = "Puedes usar cualquier herramienta disponible."

        history.append({"role": "system", "content": hint})

        try:
            resp = client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=history,
                tools=tools_for_turn,
                tool_choice="auto"
            )
            msg = resp.choices[0].message
            history.append(msg)

            if getattr(msg, "tool_calls", None):
                for tc in msg.tool_calls:
                    full_name = tc.function.name  # ej: git__git_init_seguro
                    args = json.loads(tc.function.arguments or "{}")

                    if "__" not in full_name:
                        print("⚠️ Tool inválida:", full_name)
                        continue

                    alias, safe_bare = full_name.split("__", 1)

                    # Mapear nombre SEGURO -> nombre REAL antes de llamar al MCP
                    real_bare = SAFE_TO_REAL.get(alias, {}).get(safe_bare, safe_bare)

                    mcp_resp = call_mcp(alias, real_bare, args)
                    if "output" in mcp_resp:
                        result = mcp_resp["output"]
                    else:
                        result = mcp_resp.get("error", {}).get("message", "Error desconocido")

                    print("🤖", result)
                    log_interaction(user_input, full_name, args, result)

                    history.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "content": [{"type": "text", "text": str(result)}]
                    })
            else:
                print("🤖", msg.content)
                log_interaction(user_input, "LLM", {}, msg.content)

        except Exception as e:
            print("⚠️ Error:", e)

if __name__ == "__main__":
    main()