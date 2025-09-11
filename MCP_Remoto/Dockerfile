# Imagen base oficial de Python
FROM python:3.10-slim

# Crear directorio de la app
WORKDIR /app

# Copiar dependencias
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código
COPY . .

# Exponer el puerto de Flask
ENV PORT=8080
EXPOSE 8080

# Comando para correr Flask
CMD ["python", "app.py"]
