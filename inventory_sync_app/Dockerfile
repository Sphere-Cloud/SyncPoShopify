# Usar Python 3.11 que es más estable
FROM python:3.11-slim

# Instalar dependencias del sistema necesarias para compilar aiohttp
RUN apt-get update && apt-get install -y \
    build-essential \
    gcc \
    g++ \
    make \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Establecer directorio de trabajo
WORKDIR /app

# Copiar archivos de requirements primero para aprovechar cache de Docker
COPY requirements.txt .

# Actualizar pip y instalar dependencias
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del código
COPY . .

# Comando para ejecutar la aplicación
CMD ["python", "run.py"]