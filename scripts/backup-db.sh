#!/bin/bash
set -e

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="./backups"
BACKUP_FILE="$BACKUP_DIR/fluxline_backup_$TIMESTAMP.db"

mkdir -p "$BACKUP_DIR"

docker cp fluxline-backend:/app/data/migrations.db "$BACKUP_FILE"

echo "Database backed up to: $BACKUP_FILE"
echo "Size: $(du -h "$BACKUP_FILE" | cut -f1)"
