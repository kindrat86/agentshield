FROM python:3.11-slim

WORKDIR /app

# Copy project files
COPY . .

# Set environment
ENV PORT=7100
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 7100

# Run the server
CMD ["python3.11", "run_app.py"]
