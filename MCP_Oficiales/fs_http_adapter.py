from flask import Flask, request, jsonify
import requests, os, threading

UPSTREAM = os.environ.get("FS_UPSTREAM", "http://127.0.0.1:7000/mcp")
TIMEOUT = float(os.environ.get("FS_TIMEOUT", "30"))

app = Flask(__name__)
session_lock = threading.Lock()
session_id = None  # guardamos el Mcp-Session-Id

def post_jsonrpc(method: str, params: dict | None = None, with_session: bool = False):
    global session_id
    headers = {"Content-Type": "application/json"}
    if with_session and session_id:
        headers["Mcp-Session-Id"] = session_id
    payload = {"jsonrpc": "2.0", "id": 1, "method": method}
    if params is not None:
        payload["params"] = params
    r = requests.post(UPSTREAM, json=payload, headers=headers, timeout=TIMEOUT)
    # si la inicialización fue exitosa, algunos servidores devuelven el id de sesión en cabecera
    sid = r.headers.get("Mcp-Session-Id")
    if sid:
        with session_lock:
            session_id = sid
    r.raise_for_status()
    return r.json()

@app.post("/initialize")
def initialize():
    try:
        # initialize SIEMPRE sin header de sesión; el server regresará el Mcp-Session-Id en cabecera
        resp = post_jsonrpc("initialize", params={}, with_session=False)
        return jsonify(resp)
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

@app.post("/describe")
def describe():
    try:
        # algunos servers usan "describe", otros "list_tools"
        try:
            resp = post_jsonrpc("describe", params={}, with_session=True)
        except Exception:
            resp = post_jsonrpc("list_tools", params={}, with_session=True)
        return jsonify(resp)
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

@app.post("/run")
def run():
    try:
        data = request.get_json() or {}
        tool = data.get("tool_name")
        args = data.get("input", {}) or {}
        # convención del transport: call_tool con { name, arguments }
        resp = post_jsonrpc("call_tool", {"name": tool, "arguments": args}, with_session=True)
        return jsonify(resp)
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

if __name__ == "__main__":
    # por defecto corre en 7100
    app.run(port=int(os.environ.get("FS_ADAPTER_PORT", "7100")))