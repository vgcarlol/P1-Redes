# log_utils.py
import datetime

def log_interaction(prompt, tool_name, params, response):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}]\nUsuario: {prompt}\nTool usada: {tool_name}\nParámetros: {params}\nRespuesta: {response}\n{'-'*40}\n"
    with open("interactions.log", "a", encoding="utf-8") as f:
        f.write(entry)
