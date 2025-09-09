# Running Co-DETR API on JS2 <!-- omit from toc -->

The following instructions are for a complete deployment of [KShervington/Co-DETR](https://github.com/KShervington/Co-DETR.git) on Jetstream2 with SSL and a reverse proxy, using two shell scripts.

## Deployment instructions <!-- omit from toc -->

- [Create A GPU instance on Jestream 2](#create-a-gpu-instance-on-jestream-2)
- [Create and run the API initialization script](#create-and-run-the-api-initialization-script)
- [Create and run the NGINX and SSL initialization script](#create-and-run-the-nginx-and-ssl-initialization-script)
- [Verify the API is running](#verify-the-api-is-running)

### Create A GPU instance on Jestream 2

Create a GPU instance on Jetstream2 of size `g3.large`. Adjust the volume size to 100GB and configure the settings so that you have at least one of the following ways to access the instance: SSH, Web shell, or Web desktop. Using either of these methods, open a terminal window so that you can run commands on the instance.

### Create and run the API initialization script

The following shell script script clones the repository, downloads the model, and runs the API on port 8000 using Docker. The container will start when the script completes, and on every reboot.

Create a file called `codetr-api-init-js2.sh` with the following command:

```
sudo vim codetr-api-init-js2.sh
```

Press the `i` key to enter `INSERT` mode, and paste the following commands into the file.

```
#!/bin/bash
set -e

# -------------------------------
# Variables
# -------------------------------
REPO_URL="https://github.com/KShervington/Co-DETR.git"
BRANCH="build-api"
IMAGE_NAME="co-detr-api"
CONTAINER_NAME="co-detr-api-container"
MODEL_URL="https://huggingface.co/zongzhuofan/co-detr-vit-large-coco/resolve/main/pytorch_model.pth"
REPO_DIR="$(pwd)/Co-DETR"
MODEL_PATH="$REPO_DIR/pytorch_model.pth"
CONTAINER_MODEL_PATH="/Co-DETR/pytorch_model.pth"
PORT="8000"

# -------------------------------
# 1. Clone the repo and switch to branch
# -------------------------------
if [ ! -d "$REPO_DIR" ]; then
    git clone "$REPO_URL" "$REPO_DIR"
fi

cd "$REPO_DIR"
git fetch origin
git checkout "$BRANCH"

# -------------------------------
# 2. Download the model if missing
# -------------------------------
if [ ! -f "$MODEL_PATH" ]; then
    echo "Downloading model file..."
    curl -L -o "$MODEL_PATH" "$MODEL_URL"
fi

# -------------------------------
# 3. Build the Docker image
# -------------------------------
docker build -t "$IMAGE_NAME" -f Dockerfile.api .

# -------------------------------
# 4. Stop and remove existing container (if any)
# -------------------------------
if [ "$(docker ps -aq -f name=$CONTAINER_NAME)" ]; then
    docker rm -f "$CONTAINER_NAME"
fi

# -------------------------------
# 5. Run the container (detached)
# -------------------------------
docker run -d --gpus all -p "$PORT:$PORT" \
    -v "$MODEL_PATH":"$CONTAINER_MODEL_PATH":ro \
    --name "$CONTAINER_NAME" \
    "$IMAGE_NAME"

# -------------------------------
# 6. Create systemd service to start container on reboot
# -------------------------------
SERVICE_FILE="/etc/systemd/system/$CONTAINER_NAME.service"

sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Co-DETR API Docker Container
After=docker.service
Requires=docker.service

[Service]
Restart=always
ExecStart=/usr/bin/docker start -a $CONTAINER_NAME
ExecStop=/usr/bin/docker stop $CONTAINER_NAME

[Install]
WantedBy=multi-user.target
EOL

# -------------------------------
# 7. Enable and start the service
# -------------------------------
sudo systemctl daemon-reload
sudo systemctl enable "$CONTAINER_NAME"
sudo systemctl start "$CONTAINER_NAME"

echo "✅ Co-DETR API container is running and will start on reboot."
```

Press the `escape` key, then type `:wq`. Press the `enter` key. The file should now be saved.

Run the file `codetr-api-init-js2.sh`.

```
bash codetr-api-init-js2.sh
```

Once the script has completed without errors, you will see this output:

```
? Co-DETR API container is running and will start on reboot.
```

### Create and run the NGINX and SSL initialization script

The following shell script configures a reverse proxy using NGINX to forward traffic from port 80 (HTTP) to port 443 (HTTPS), and from port 443 to port 8000 where the API runs. During the NGINX installation and configuration, an SSL certificate is created using [Let's Encrypt](https://letsencrypt.org/) Certbot. The SSL certificate will automatically update, and the NGINX server will start on every reboot.

Create another file called `nginx-ssl-init-js2.sh` using the instructions above, and paste the following commands to the file.

```
#!/bin/bash
set -euo pipefail

# Usage check
if [ $# -ne 1 ]; then
  echo "Usage: $0 <domain>"
  exit 1
fi

DOMAIN=$1
EMAIL="admin@$DOMAIN"  # change if you want a different email for certbot

echo "[INFO] Updating system packages..."
sudo apt update -y
sudo apt upgrade -y

echo "[INFO] Installing NGINX and Certbot..."
sudo apt install -y nginx python3-certbot-nginx ufw

echo "[INFO] Configuring UFW firewall..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

echo "[INFO] Ensuring NGINX can handle long domain names..."
sudo tee /etc/nginx/conf.d/server_names_hash.conf > /dev/null <<EOF
server_names_hash_bucket_size 512;
EOF

echo "[INFO] Testing and reloading NGINX..."
sudo nginx -t
sudo systemctl reload nginx

echo "[INFO] Creating NGINX server block for $DOMAIN..."
NGINX_CONF="/etc/nginx/sites-available/$DOMAIN"
sudo tee $NGINX_CONF > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo "[INFO] Enabling NGINX site..."
sudo ln -sf $NGINX_CONF /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

echo "[INFO] Requesting Let's Encrypt SSL certificate..."
sudo certbot --nginx -d $DOMAIN --non-interactive --agree-tos -m $EMAIL

echo "[INFO] Forcing HTTP to HTTPS redirection..."
sudo tee $NGINX_CONF > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

echo "[INFO] Reloading NGINX with SSL config..."
sudo nginx -t
sudo systemctl reload nginx

echo "[SUCCESS] NGINX is now configured with SSL for $DOMAIN."
echo "[INFO] Make sure your Python app is running on port 8000."

```

Run the following command, replacing `JS2_INSTANCE_DOMAIN` with your domain. Your JS2 instance domain will be on the instance details page in Exosphere under Credentials.

```
bash nginx-ssl-init-js2.sh JS2_INSTANCE_DOMAIN
```

Once the script has completed without errors, you will see the following output:

```
[SUCCESS] NGINX is now configured with SSL for test5-gpu-mdurbin-2025-08-22.cis230083.projects.jetstream-cloud.org.
[INFO] Make sure your Python app is running on port 8000.
```

### Verify the API is running

Open the `JS2_INSTANCE_DOMAIN` in a new browser window. You should see the following output:

```
{"message":"Co-DETR Object Detection API is running","status":"healthy","model_loaded":true}
```
