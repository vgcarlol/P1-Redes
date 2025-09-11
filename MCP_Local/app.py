from flask import Flask, request, jsonify
import json, csv, os
from datetime import datetime, timedelta

app = Flask(__name__)

DATA_FILE = "tasks.csv"

with open("spec.json","r",encoding="utf-8") as f:
    spec = json.load(f)

def ensure_datafile():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE,"w",newline="",encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["id","title","due","priority","status"])
            w.writeheader()

def read_tasks():
    ensure_datafile()
    with open(DATA_FILE, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def write_tasks(rows):
    with open(DATA_FILE,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","title","due","priority","status"])
        w.writeheader()
        w.writerows(rows)

def next_id(rows):
    ids = [int(r["id"]) for r in rows] if rows else []
    return (max(ids)+1) if ids else 1

@app.route("/initialize", methods=["POST"])
def initialize():
    ensure_datafile()
    return jsonify({"status":"ready"})

@app.route("/describe", methods=["POST"])
def describe():
    return jsonify(spec)

@app.route("/run", methods=["POST"])
def run():
    try:
        payload = request.get_json() or {}
        name = payload.get("tool_name")
        params = payload.get("input", {}) or {}
        if name == "create_task": return create_task(params)
        if name == "list_tasks": return list_tasks(params)
        if name == "complete_task": return complete_task(params)
        if name == "snooze_task": return snooze_task(params)
        return error("Tool not found", 404)
    except Exception as e:
        return error(str(e), 500)

def create_task(p):
    for k in ["title","due","priority"]:
        if p.get(k) in (None,""): return error(f"Missing '{k}'",400)
    try:
        due_dt = datetime.strptime(p["due"], "%Y-%m-%d %H:%M")
    except ValueError:
        return error("Invalid 'due' format. Use YYYY-MM-DD HH:MM",400)
    rows = read_tasks()
    # conflict: any pending task within same 30-minute window
    conflict = [r for r in rows if r["status"]!="done" and
                abs((datetime.strptime(r["due"],"%Y-%m-%d %H:%M") - due_dt).total_seconds()) <= 30*60]
    new = {
        "id": str(next_id(rows)),
        "title": p["title"],
        "due": due_dt.strftime("%Y-%m-%d %H:%M"),
        "priority": str(int(p["priority"])),
        "status": "pending"
    }
    rows.append(new); write_tasks(rows)
    msg = f"Tarea #{new['id']} creada. "
    if conflict: msg += f"⚠️ {len(conflict)} conflicto(s) de horario detectado(s)."
    return jsonify({"output": msg})

def list_tasks(p):
    rows = read_tasks()
    status = p.get("status")
    if status: rows = [r for r in rows if r["status"]==status]
    frm, to = p.get("from"), p.get("to")
    if frm:
        rows = [r for r in rows if r["due"][:10] >= frm]
    if to:
        rows = [r for r in rows if r["due"][:10] <= to]
    return jsonify({"output": rows})

def complete_task(p):
    if not p.get("id"): return error("Missing 'id'",400)
    rows = read_tasks()
    found = False
    for r in rows:
        if int(r["id"]) == int(p["id"]):
            r["status"]="done"; found=True; break
    if not found: return error("Task not found",404)
    write_tasks(rows)
    return jsonify({"output": f"Tarea #{p['id']} completada."})

def snooze_task(p):
    if not p.get("id") or not p.get("minutes"): return error("Missing 'id' or 'minutes'",400)
    rows = read_tasks()
    for r in rows:
        if int(r["id"]) == int(p["id"]):
            due = datetime.strptime(r["due"], "%Y-%m-%d %H:%M")
            new_due = due + timedelta(minutes=int(p["minutes"]))
            r["due"] = new_due.strftime("%Y-%m-%d %H:%M")
            write_tasks(rows)
            return jsonify({"output": f"Tarea #{p['id']} pospuesta {p['minutes']} min. Nuevo due: {r['due']}."})
    return error("Task not found",404)

def error(message, code=500):
    return jsonify({"error":{"code":code,"message":message,"type":"mcp_error"}}), code

if __name__=="__main__":
    app.run(port=6000)  # local distinto al remoto
