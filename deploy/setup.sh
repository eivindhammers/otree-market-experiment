#!/bin/bash
# Run as root on your server

set -e

echo "=== oTree Market Experiment Setup ==="

# Install Python if needed
if ! command -v python3 &> /dev/null; then
    apt update && apt install -y python3 python3-pip python3-venv
fi

# Create directory and clone
mkdir -p /opt/otree-market-experiment
cd /opt/otree-market-experiment

if [ ! -d ".git" ]; then
    git clone https://github.com/eivindhammers/otree-market-experiment.git .
fi

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install otree psycopg2-binary

# Set permissions
chown -R www-data:www-data /opt/otree-market-experiment

# Install systemd service
cp deploy/otree.service /etc/systemd/system/otree.service

echo ""
echo "=== NEXT STEPS ==="
echo "1. Edit /etc/systemd/system/otree.service"
echo "   - Set OTREE_ADMIN_PASSWORD"
echo ""
echo "2. Edit deploy/nginx.conf"
echo "   - Replace experiment.yourdomain.com with your domain"
echo "   - Copy to /etc/nginx/sites-available/otree"
echo "   - ln -s /etc/nginx/sites-available/otree /etc/nginx/sites-enabled/"
echo ""
echo "3. Start services:"
echo "   systemctl daemon-reload"
echo "   systemctl enable otree"
echo "   systemctl start otree"
echo "   systemctl reload nginx"
echo ""
echo "4. Visit https://yourdomain.com/admin"
