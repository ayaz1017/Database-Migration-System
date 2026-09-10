# Use slim Python for smaller image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# pyodbc needs unixODBC
# psycopg2 needs libpq
# oracledb needs libaio (Oracle client)
RUN apt-get update && apt-get install -y \
    unixodbc \
    unixodbc-dev \
    libpq-dev \
    gcc \
    g++ \
    curl \
    libaio1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install MSSQL ODBC driver for pyodbc
# (required for MSSQL connections)
RUN curl https://packages.microsoft.com/keys/microsoft.asc \
    | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list \
    > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y \
    msodbcsql18 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir \
    --upgrade pip \
    && pip install --no-cache-dir \
    -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Create non-root user for security
RUN useradd -m -u 1000 fluxline \
    && chown -R fluxline:fluxline /app
USER fluxline

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s \
    --timeout=10s \
    --start-period=60s \
    --retries=3 \
    CMD curl -f http://localhost:8000/api/health \
    || exit 1

# Start command
CMD ["uvicorn", "main:app", \
    "--host", "0.0.0.0", \
    "--port", "8000", \
    "--workers", "1", \
    "--loop", "uvloop", \
    "--http", "httptools"]
