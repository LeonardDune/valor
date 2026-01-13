FROM python:3.11-slim

WORKDIR /app

# Install system dependencies if needed (e.g., for building python packages)
# RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Expose port (default for uvicorn)
EXPOSE 8000

# Command to run the application in production mode (no reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
