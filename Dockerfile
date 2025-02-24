# Build stage for UI
FROM nikolaik/python-nodejs:python3.11-nodejs16 AS ui-builder
WORKDIR /app/cloudproxy-ui

# Copy only package files first to leverage cache
COPY cloudproxy-ui/package*.json ./
RUN npm install

# Copy UI source and build
COPY cloudproxy-ui/ ./
RUN npm run build

# Final stage
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy Python source code
COPY cloudproxy/ cloudproxy/

# Copy built UI files from ui-builder stage
COPY --from=ui-builder /app/cloudproxy-ui/dist cloudproxy-ui/dist

# Set Python path and expose port
ENV PYTHONPATH=/app
EXPOSE 8000

# Run the application
CMD ["python", "./cloudproxy/main.py"]