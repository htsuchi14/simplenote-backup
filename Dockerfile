FROM python:3.13-slim

WORKDIR /app

# Install simperium
RUN pip install --no-cache-dir simperium

# Copy scripts
COPY simplenote-backup.py .
COPY simplenote-import.py .
COPY simplenote-pull.py .
COPY simplenote-classify.py .

# Default backup directory
ENV BACKUP_DIR=/data

# Default command: backup
CMD ["python3", "simplenote-backup.py"]
