# MCP Local Server – Task Management

This is a **local MCP server** (Model Context Protocol) that allows agents (e.g., LLMs) to **manage tasks** via JSON-RPC.  
It is built with **Python and Flask** and uses a lightweight **CSV file (`tasks.csv`)** for storage.

---

## 📦 Features

- ✅ Create new tasks with title, due date and priority  
- ✅ List tasks filtered by status (pending/completed) or by date range  
- ✅ Mark tasks as completed  
- ✅ Snooze tasks by minutes  
- ✅ Fully MCP-compatible (`/initialize`, `/describe`, `/run`)  

---

## 🖥️ Requirements

- Python 3.8+  
- `pip` (Python package manager)  
- (Optional) Virtual environment (`venv`)  

---

## ⚙️ Installation and Execution

### 1. Clone the repository

```bash
git clone https://github.com/vgcarlol/MCP_Local_Server.git
cd MCP_Local_Server
```

### 2. Install dependencies

```bash
pip install flask
```

### 3. Run the server

```bash
python app.py
```

The server will be available at:

```
http://localhost:6000
```

---

## 🔁 MCP Methods – JSON-RPC

### 1. `create_task`
**Description:** Creates a new task with title, due date and priority.  
**Parameters:**
```json
{
  "title": "Submit report",
  "due": "2025-09-12 10:00",
  "priority": 1
}
```
**Response:**
```json
"Task #1 created."
```

---

### 2. `list_tasks`
**Description:** Lists tasks, with optional filters by status or dates.  
**Parameters:**
```json
{
  "status": "pending"
}
```
**Response:**
```json
[
  {
    "id": "1",
    "title": "Submit report",
    "due": "2025-09-12 10:00",
    "priority": "1",
    "status": "pending"
  }
]
```

---

### 3. `complete_task`
**Description:** Marks a task as completed.  
**Parameters:**
```json
{
  "id": 1
}
```
**Response:**
```json
"Task #1 completed."
```

---

### 4. `snooze_task`
**Description:** Postpones a task’s due date.  
**Parameters:**
```json
{
  "id": 1,
  "minutes": 30
}
```
**Response:**
```json
"Task #1 snoozed for 30 min. New due: 2025-09-12 10:30."
```

---

## 🧪 Example `tasks.csv` file

On first run, the server creates a CSV file with headers:

```csv
id,title,due,priority,status
```

Each new or updated task is stored in this file.

---

## 👤 Author

Carlos Valladares – Student ID 221164  
Universidad del Valle de Guatemala  
Course: CC3067 Networks – Project 1  
