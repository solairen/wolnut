FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy project files
COPY . /app

# Install system tools
RUN apt-get update && apt-get install -y \
    iputils-ping \
    nut-client \
    net-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set correct PYTHONPATH
ENV PYTHONPATH=/app

# Run the script
CMD ["python", "-u", "wolnut/main.py"]