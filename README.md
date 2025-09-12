# Chatbot MCP – Integration with Local, Remote, Filesystem and Git Servers

This project implements a **chatbot** that connects an OpenAI language model (**GPT-3.5-turbo**) with multiple **MCP (Model Context Protocol) servers**.  
It demonstrates how a conversational agent can interact with different backends in a unified way.

---

## 🚀 Features

- **Local MCP (Task Management)** → Create, list, complete and snooze tasks (Flask + SQLAlchemy).  
- **Remote MCP (Payments on Google Cloud Run)** → Query balances and register user payments.  
- **Filesystem MCP (Official server)** → Read, write and list files inside the `workspace/` directory.  
- **Git MCP (Official server)** → Perform Git operations such as `status`, `add`, `commit`, `log`.  

All interactions are logged for traceability.

---

## 🖥️ Requirements

- Python 3.8+  
- OpenAI account with a valid API key  
- Node.js and `npx` (for Filesystem MCP server)  
- Git installed (for Git MCP server)  

---

## ⚙️ Installation & Execution

### 1. Clone the repository

MCP_Local: https://github.com/vgcarlol/MCP_Local_Server 

```bash
git clone https://github.com/vgcarlol/P1-Redes.git
cd P1-Redes/chatbot
```

### 2. Create and activate virtual environment

```bash
python -m venv env
.\env\Scripts\activate
```

*(Linux/Mac: `source env/bin/activate`)*

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

Sample `requirements.txt`:

```
flask
sqlalchemy
pandas
openai
requests
mcp
```

### 4. Configure environment variables

Set your OpenAI API key (replace `your_api_key_here`):

```bash
setx OPENAI_API_KEY "your_api_key_here"
```

On Linux/Mac:

```bash
export OPENAI_API_KEY="your_api_key_here"
```

### 5. Run the chatbot

```bash
python chatbot_mcp.py
```

You will see:

```
🤖 Chatbot MCP (OpenAI + Local + Remote + Filesystem + Git)
Type 'exit' to quit.
```

---

## 🤖 Example Interactions

### 🔹 Local MCP (Tasks)
```text
Create a task called "Submit report" for 2025-09-12 10:00 with high priority
Show all pending tasks
Mark task 1 as completed
Snooze task 2 for 30 minutes
```

### 🔹 Remote MCP (Payments)
```text
How much does Andrea owe?
Register a payment of 50 for Carlos
Show pending balance of Carlos and Andrea
```

### 🔹 Filesystem MCP
```text
Read the file README.md inside workspace
Write a new file workspace/note.txt with content "Hello MCP"
```

### 🔹 Git MCP
```text
Show git status
Add README.md and commit with message "initial commit"
Show git log
```

---

## 📂 Interaction Logs

All user interactions are saved in:

```
interactions.log
```

Each entry includes timestamp, user prompt, tool invoked and response.

---

## 🗂️ Version Control

- The project is maintained in **Git** with incremental commits.  
- Each commit message is descriptive (in English).  
- A separate repository exists for the **Local MCP server** as required.  
- Branches were used for development and testing to maintain clean history.  

---

## 📖 Documentation & Code Practices

- All Python code is documented with clear function and class descriptions.  
- Tools are namespaced (`local__`, `remoto__`, `fs__`, `git__`) to enforce proper routing.  
- Error handling and logging are included.  

---

## 👤 Author

**Carlos Valladares – ID 221164**  
Universidad del Valle de Guatemala  
Course: CC3067 – Networks, Project 1  
