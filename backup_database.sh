#!/bin/bash
BACKUP_DIR="$HOME/pie_backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Backing up PIE database..."
sudo -u postgres pg_dump pie > "$BACKUP_DIR/pie.sql"
sudo -u postgres pg_dumpall --globals-only > "$BACKUP_DIR/globals.sql"

echo "📁 Backing up artifacts..."
cp -r artifacts "$BACKUP_DIR/" 2>/dev/null || true
cp -r deliverables "$BACKUP_DIR/" 2>/dev/null || true

echo "✅ Backup complete: $BACKUP_DIR"
echo "   Files:"
ls -la "$BACKUP_DIR/"
