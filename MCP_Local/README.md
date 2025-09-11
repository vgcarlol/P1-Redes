# Servidor MCP Local – Gestión de Tareas

Este es un servidor **local** basado en el protocolo Model Context Protocol (MCP), que permite a agentes (por ejemplo, LLMs) **gestionar tareas** utilizando JSON-RPC.  
El servidor está desarrollado con **Python y Flask**, y utiliza un archivo **CSV (`tasks.csv`)** como almacenamiento ligero.

---

## 📦 Funcionalidades

- ✅ Crear nuevas tareas con título, fecha límite y prioridad  
- ✅ Listar tareas filtradas por estado (pendientes o completadas) o rango de fechas  
- ✅ Marcar tareas como completadas  
- ✅ Posponer tareas (“snooze”) en minutos  
- ✅ Implementación compatible con MCP (`/initialize`, `/describe`, `/run`)  

---

## 🖥️ Requisitos

Asegúrate de tener instalado lo siguiente:

- Python 3.8 o superior  
- `pip` (administrador de paquetes de Python)  
- (Opcional) Uso de entorno virtual (`venv`)  

---

## ⚙️ Instrucciones de instalación y ejecución

### 1. Clona el repositorio

```bash
git clone https://github.com/vgcarlol/P1-Redes.git
cd P1-Redes/MCP_Local
```

### 2. Instala las dependencias

```bash
pip install flask
```

### 3. Inicia el servidor

```bash
python app.py
```

El servidor quedará disponible en:

```
http://localhost:6000
```

---

## 🔁 Métodos MCP – JSON-RPC

### 1. `create_task`

**Descripción:** Crea una nueva tarea con título, fecha y prioridad.  
**Parámetros:**
```json
{
  "title": "Entregar informe",
  "due": "2025-09-12 10:00",
  "priority": 1
}
```

**Respuesta:**
```json
"Tarea #1 creada. ⚠️ 1 conflicto(s) de horario detectado(s)."
```

---

### 2. `list_tasks`

**Descripción:** Lista tareas, con opción de filtrar por estado o fechas.  
**Parámetros:**
```json
{
  "status": "pending"
}
```

**Respuesta:**
```json
[
  {
    "id": "1",
    "title": "Entregar informe",
    "due": "2025-09-12 10:00",
    "priority": "1",
    "status": "pending"
  }
]
```

---

### 3. `complete_task`

**Descripción:** Marca una tarea como completada.  
**Parámetros:**
```json
{
  "id": 1
}
```

**Respuesta:**
```json
"Tarea #1 completada."
```

---

### 4. `snooze_task`

**Descripción:** Pospone la fecha límite de una tarea.  
**Parámetros:**
```json
{
  "id": 1,
  "minutes": 30
}
```

**Respuesta:**
```json
"Tarea #1 pospuesta 30 min. Nuevo due: 2025-09-12 10:30."
```

---

## 🧪 Ejemplo de archivo `tasks.csv`

Al iniciar por primera vez, el servidor crea automáticamente el archivo `tasks.csv` con encabezados:

```csv
id,title,due,priority,status
```

Cada vez que se agrega o modifica una tarea, el archivo se actualiza.

---

## 🧑‍💻 Autor

Carlos Valladares - Carnet 221164  
Universidad del Valle de Guatemala  
Curso: CC3067 Redes – Proyecto 1  
