# Chatbot MCP – Integración con Servidores Local y Remoto

Este chatbot utiliza un modelo de lenguaje (**OpenAI GPT-3.5-turbo**) conectado a dos servidores MCP:  

- **MCP Local (Gestión de Tareas)** → Crear, listar, completar y posponer tareas.  
- **MCP Remoto (Pagos – en Google Cloud Run)** → Consultar saldos y registrar pagos de usuarios.  

Permite interactuar en **lenguaje natural** y mantiene contexto de la conversación, además de registrar logs de las interacciones.

---

## 🖥️ Requisitos

- Python 3.8 o superior  
- Una cuenta de OpenAI con API key válida  
- (Opcional) `git` para clonar el repositorio  

---

## ⚙️ Instrucciones de instalación y ejecución

### 1. Clona el repositorio

```bash
git clone https://github.com/vgcarlol/P1-Redes.git
cd P1-Redes/chatbot
```

### 2. Crea y activa entorno virtual

```bash
python -m venv env
.\env\Scripts\activate
```

*(En Linux/Mac sería `source env/bin/activate`)*

### 3. Instala dependencias

```bash
pip install -r requirements.txt
```

Asegúrate de incluir en `requirements.txt`:
```
flask
pandas
openai
requests
```

### 4. Configura variables (opcional)

El API Key de OpenAI ya está en el código, pero puedes sobreescribirlo con variable de entorno:

```bash
setx OPENAI_API_KEY "tu_api_key_aqui"
```

### 5. Ejecuta el chatbot

```bash
python chatbot_mcp.py
```

---

## 🤖 Ejemplo de uso del chatbot

Cuando se ejecute, verás:

```
🤖 Chatbot MCP (OpenAI + Local + Remoto)
Escribe 'salir' para terminar.
```

Ahora puedes interactuar en **lenguaje natural**.  

---

## 📌 Preguntas posibles

### 🔹 Para el **MCP Local (Gestión de Tareas)**
1. **Crear tarea**  
   ```
   Crea una tarea llamada "Entregar informe" para el 2025-09-12 10:00 con prioridad alta
   ```

2. **Listar tareas pendientes**  
   ```
   Muéstrame todas las tareas pendientes
   ```

3. **Completar una tarea**  
   ```
   Marca la tarea 1 como completada
   ```

4. **Posponer una tarea**  
   ```
   Pospón la tarea 1 por 30 minutos
   ```

---

### 🔹 Para el **MCP Remoto (Pagos en la nube)**  
1. **Consultar saldo**  
   ```
   ¿Cuánto debe Andrea en el remoto?
   ```

2. **Registrar un pago**  
   ```
   Registra un pago de Q50 para Carlos en el remoto
   ```

3. **Escenario combinado**  
   ```
   ¿Cuánto debe Carlos en el remoto y qué tareas pendientes tiene en el local?
   ```

---

## 📂 Logs de interacción

Todas las interacciones se guardan en el archivo:

```
interactions.log
```

Incluye fecha, prompt del usuario, herramienta usada y respuesta.

---

## 🧑‍💻 Autor

Carlos Valladares – Carnet 221164  
Universidad del Valle de Guatemala  
Curso: CC3067 Redes – Proyecto 1  
