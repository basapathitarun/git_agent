# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies required for psycopg2 and other potential native extensions
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container at /app
COPY requirement.txt .

# Install any needed packages specified in requirement.txt
RUN pip install --no-cache-dir -r requirement.txt

# Copy the rest of the application code
COPY . .

# Run the application
CMD ["python", "main.py"]
