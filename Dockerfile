FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PORT=8000

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Collect static files and prepare database
RUN python manage.py collectstatic --noinput || true

# Expose port
EXPOSE 8000

# Run Daphne ASGI server
CMD ["sh", "-c", "python manage.py migrate && python manage.py seed_data && daphne -b 0.0.0.0 -p ${PORT:-8000} connectly.asgi:application"]
