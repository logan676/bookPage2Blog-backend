# Use official Python runtime as base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    python3-dev \
    musl-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install gunicorn dj-database-url

# Copy project
COPY . /app/

# Collect static files
RUN python manage.py collectstatic --noinput || true

# Create media directory
RUN mkdir -p /app/media

# Expose port
EXPOSE 8000

# Run the application
CMD ["sh", "-c", "python manage.py migrate && gunicorn bookpost_project.wsgi:application --bind 0.0.0.0:8000 --workers 2 --threads 4 --timeout 120"]
