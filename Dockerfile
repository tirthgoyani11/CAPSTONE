
# Use an official lightweight Python image.
# 3.10-slim is a good balance of size and compatibility.
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies required for building some Python packages (like psycopg2)
# and git if needed for some dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
# Upgrade pip first to avoid errors
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose the port the app runs on (Render uses 10000 by default sometimes, or 5000)
# We will use PORT environment variable properly in command
EXPOSE 5000 10000

# Define the command to run the application
# We use Gunicorn for production
# Workers: 1 (to save RAM on free tier), Threads: 8 (for concurrency)
CMD gunicorn --bind 0.0.0.0:$PORT app:app --workers 1 --threads 8 --timeout 0
