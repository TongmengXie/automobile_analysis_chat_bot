# Use Python 3.11
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install OS dependencies required for Chroma & UVLoop
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose FastAPI port
EXPOSE 8000

# Create a persistent directory for Chroma
RUN mkdir -p /app/chroma_db

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
