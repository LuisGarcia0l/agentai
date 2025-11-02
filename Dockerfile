# Dockerfile para AI Trading System
FROM python:3.11-slim

# Metadatos
LABEL maintainer="AI Trading System"
LABEL version="1.0.0"
LABEL description="Sistema de trading avanzado con agentes IA"

# Variables de entorno
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DEBIAN_FRONTEND=noninteractive

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    libta-lib-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Instalar TA-Lib
RUN curl -L http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz | tar xz && \
    cd ta-lib && \
    ./configure --prefix=/usr && \
    make && \
    make install && \
    cd .. && \
    rm -rf ta-lib

# Copiar requirements
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copiar código fuente
COPY . .

# Crear directorios necesarios
RUN mkdir -p logs data/storage

# Crear usuario no-root
RUN useradd -m -u 1000 trader && \
    chown -R trader:trader /app

USER trader

# Exponer puertos
EXPOSE 8501 8000

# Comando por defecto
CMD ["python", "main.py"]