# Use Python base image
FROM python:3.9-slim

# Install Node.js
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy backend requirements and install
COPY backend/requirements.txt backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# Copy frontend package files and install
COPY frontend/package*.json frontend/
WORKDIR /app/frontend
RUN npm install

# Copy all files
WORKDIR /app
COPY . .

# Build frontend
WORKDIR /app/frontend
RUN npm run build

# Back to app root
WORKDIR /app

# Make start script executable
RUN chmod +x start.sh

# Expose port
EXPOSE 8080

# Start command
CMD ["./start.sh"]
