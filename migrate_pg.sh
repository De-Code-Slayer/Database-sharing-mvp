#!/bin/bash
set -e

# === CONFIGURATION ===
OLD_HOST="46.202.195.6"
OLD_USER="admin"
AWS_HOST="51.21.246.180"
AWS_USER="root"
AWS_SSH="ec2-user"
AWS_SSH_HOST="51.21.246.180"

# === FILE LOCATIONS ===
BACKUP_DIR="/tmp/pg_backup_$(date +%F_%H-%M-%S)"
mkdir -p "$BACKUP_DIR"

echo "📦 Dumping roles and databases from $OLD_HOST ..."

# 1️⃣ Dump all roles (users, privileges, passwords)
pg_dumpall -h "$OLD_HOST" -U "$OLD_USER" --globals-only > "$BACKUP_DIR/roles.sql"

# 2️⃣ Dump all databases (structure + data)
pg_dumpall -h "$OLD_HOST" -U "$OLD_USER" > "$BACKUP_DIR/full_backup.sql"

echo "✅ Dump complete. Files saved to $BACKUP_DIR"
echo "🚀 Transferring files to EC2 ($AWS_SSH_HOST)..."

# 3️⃣ Copy to AWS
scp "$BACKUP_DIR/roles.sql" "$AWS_SSH@$AWS_SSH_HOST:/tmp/"
scp "$BACKUP_DIR/full_backup.sql" "$AWS_SSH@$AWS_SSH_HOST:/tmp/"

echo "🗄️ Restoring on AWS PostgreSQL ($AWS_HOST)..."

# 4️⃣ Restore on AWS
ssh "$AWS_SSH@$AWS_SSH_HOST" "
  sudo -u postgres psql -h localhost -U $AWS_USER -f /tmp/roles.sql &&
  sudo -u postgres psql -h localhost -U $AWS_USER -f /tmp/full_backup.sql &&
  echo '✅ Migration completed successfully!'
"

echo "🎉 All databases and users have been migrated successfully!"
