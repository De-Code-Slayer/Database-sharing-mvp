#!/bin/bash
set -e

# === CONFIGURATION ===
OLD_HOST="46.202.195.6"
OLD_USER="admin"
AWS_HOST="13.51.168.187"
AWS_USER="root"
AWS_SSH="ec2-user"
AWS_SSH_HOST="13.51.168.187"

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

# 3️⃣ Copy to AWS using key-based SSH
SSH_KEY="$HOME/Database-sharing-mvp/BigHulk-SSH.pem"

scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$BACKUP_DIR/roles.sql" "$AWS_SSH@$AWS_SSH_HOST:/tmp/"
scp -i "$SSH_KEY" -o StrictHostKeyChecking=no "$BACKUP_DIR/full_backup.sql" "$AWS_SSH@$AWS_SSH_HOST:/tmp/"

echo "🗄️ Restoring on AWS PostgreSQL ($AWS_HOST)..."

# 4️⃣ Restore on AWS
ssh -i "$SSH_KEY" -o StrictHostKeyChecking=no "$AWS_SSH@$AWS_SSH_HOST" "
  sudo -u postgres psql -f /tmp/roles.sql &&
  sudo -u postgres psql -f /tmp/full_backup.sql &&
  echo '✅ Migration completed successfully!'
"
echo "🎉 All done! Please verify the data on the AWS PostgreSQL server."

