#!/bin/bash
# deploy/setup.sh - Run on VPS to set up Eva gateway

set -e

echo "=== Eva Gateway Setup ==="

# Clone or update repo
if [ -d /opt/eva ]; then
    echo "Updating existing installation..."
    cd /opt/eva
    git pull
else
    echo "Fresh installation..."
    git clone https://github.com/safarivis/agents_eva.git /opt/eva
    cd /opt/eva
fi

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
pip install gunicorn

# Create .env if not exists
if [ ! -f .env ]; then
    echo "Creating .env template..."
    cat > .env << 'EOF'
EVA_PROVIDER=nvidia
NVIDIA_API_KEY=your_key_here
COMPOSIO_API_KEY=your_key_here
META_VERIFY_TOKEN=your_verify_token
META_APP_SECRET=your_app_secret
ALLOWED_PHONE=27123456789
EVA_REPO_DIR=/opt/eva
EOF
    echo ">>> EDIT /opt/eva/.env with your actual keys!"
fi

# Install systemd service
cp deploy/eva-gateway.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable eva-gateway
systemctl start eva-gateway

echo ""
echo "=== Setup Complete ==="
echo "1. Edit /opt/eva/.env with your keys"
echo "2. Add Nginx config from deploy/nginx-eva.conf"
echo "3. Reload nginx: systemctl reload nginx"
echo "4. Check status: systemctl status eva-gateway"
