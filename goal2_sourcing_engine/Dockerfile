# Use the official Microsoft Playwright image as base
FROM mcr.microsoft.com/playwright/python:v1.49.0-noble

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create necessary directories
RUN mkdir -p output/vton playwright_profile

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DISPLAY=:99

# Run the batch generator by default
CMD ["python", "run_vton_batch.py"]
