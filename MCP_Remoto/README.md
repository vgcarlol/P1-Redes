# Servidor MCP Remoto – Pagos

Este es un servidor remoto basado en el protocolo Model Context Protocol (MCP), que permite a agentes (por ejemplo, LLMs) consultar saldos pendientes y registrar pagos utilizando JSON-RPC.  
El servidor está desarrollado con Python, Flask, SQLAlchemy y utiliza una base de datos local SQLite.

---

## 📦 Funcionalidades

- ✅ Consultar el saldo pendiente de un usuario
- ✅ Registrar un pago para un usuario y actualizar su saldo
- ✅ Implementación del protocolo JSON-RPC compatible con MCP
- ✅ Base de datos SQLite precargada con usuarios de prueba

---

## 🖥️ Requisitos

Asegúrate de tener instalado lo siguiente:

- Python 3.8 o superior
- `pip` (administrador de paquetes de Python)
- (Opcional pero recomendado) Uso de entorno virtual (`venv`)

---

## ⚙️ Instrucciones de instalación y ejecución

### 1. Clona el repositorio

```bash
git clone https://github.com/vgcarlol/P1-Redes.git
cd P1-Redes
```

### 2. Instala las dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- `flask`
- `flask_jsonrpc`
- `sqlalchemy`

### 3. Inicializa la base de datos

Ejecuta el script para crear el archivo `database.db` y precargar usuarios de prueba:

```bash
python init_db.py
```

### 4. Inicia el servidor

```bash
python app.py
```

El servidor quedará disponible en:

```
http://localhost:5000/api
```

---

## 🔁 Métodos MCP – JSON-RPC

### 1. `get_pending_balance`

**Descripción:** Devuelve el saldo pendiente actual de un usuario.

**Parámetros:**
```json
{
  "name": "Carlos"
}
```

**Respuesta:**
```json
300.0
```

---

### 2. `register_payment`

**Descripción:** Registra un pago y devuelve un mensaje de confirmación.

**Parámetros:**
```json
{
  "name": "Carlos",
  "amount": 50
}
```

**Respuesta:**
```json
"Pago de Q50 registrado exitosamente. Nuevo saldo: Q250.0"
```

---

## 🧪 Usuarios precargados

| Nombre  | Saldo pendiente |
|---------|------------------|
| Carlos  | Q300.00          |
| Andrea  | Q150.00          |
| Luis    | Q0.00            |

---

## 🧑‍💻 Autor

Carlos Valladares - Carnét 221164  
Universidad del Valle de Guatemala  
Curso: CC3067 Redes – Proyecto 1
