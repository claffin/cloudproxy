# Security Best Practices

This guide covers security best practices for deploying and managing CloudProxy with Docker in production environments.

## Docker Deployment Security

### Running CloudProxy Securely with Docker

```bash
# Create a dedicated user for CloudProxy
docker run -d \
  --name cloudproxy \
  --user 1000:1000 \
  --read-only \
  --tmpfs /tmp \
  --security-opt no-new-privileges \
  --cap-drop ALL \
  --cap-add NET_BIND_SERVICE \
  -p 8000:8000 \
  --env-file .env \
  laffin/cloudproxy:latest
```

### Docker Compose with Security Settings

```yaml
version: '3.8'
services:
  cloudproxy:
    image: laffin/cloudproxy:latest
    user: "1000:1000"
    read_only: true
    tmpfs:
      - /tmp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    ports:
      - "127.0.0.1:8000:8000"  # Bind only to localhost
    env_file:
      - .env
    restart: unless-stopped
```

## Credential Management

### Never Commit Credentials

**DO NOT** commit credentials to version control or include them in Docker images:

```dockerfile
# Bad - credentials in Dockerfile
ENV AWS_ACCESS_KEY_ID="AKIAIOSFODNN7EXAMPLE"  # Never do this!

# Good - use runtime environment variables
# Pass credentials when running the container
docker run -e AWS_ACCESS_KEY_ID="$AWS_ACCESS_KEY_ID" ...
```

### Use Environment Files Safely

When using `.env` files:

```bash
# Create .env file
cat > .env << EOF
PROXY_USERNAME=secure_user
PROXY_PASSWORD=strong_password_here
DIGITALOCEAN_ACCESS_TOKEN=your_token
EOF

# Add to .gitignore immediately
echo ".env" >> .gitignore

# Set restrictive permissions
chmod 600 .env
```

### Secret Management Tools

Use proper secret management in production:

#### Docker Secrets
```bash
# Create secret
echo "your_token" | docker secret create do_token -

# Use in docker-compose.yml
services:
  cloudproxy:
    image: laffin/cloudproxy
    secrets:
      - do_token
    environment:
      DIGITALOCEAN_ACCESS_TOKEN_FILE: /run/secrets/do_token
```

#### Kubernetes Secrets
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: cloudproxy-secrets
type: Opaque
data:
  digitalocean-token: <base64-encoded-token>
---
apiVersion: apps/v1
kind: Deployment
spec:
  template:
    spec:
      containers:
      - name: cloudproxy
        env:
        - name: DIGITALOCEAN_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: cloudproxy-secrets
              key: digitalocean-token
```

#### AWS Secrets Manager
```python
import boto3
import json

def get_cloudproxy_secrets():
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId='cloudproxy/credentials')
    secrets = json.loads(response['SecretString'])
    
    for key, value in secrets.items():
        os.environ[key] = value
```

## Provider-Specific Security

### AWS

#### Use IAM Roles When Possible
```python
# When running on EC2, use IAM roles instead of keys
# No credentials needed in code!
import boto3
ec2 = boto3.client('ec2')  # Uses instance role automatically
```

#### Minimum IAM Permissions
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ec2:RunInstances",
        "ec2:TerminateInstances",
        "ec2:DescribeInstances",
        "ec2:CreateTags",
        "ec2:DescribeInstanceStatus"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "ec2:InstanceType": ["t2.micro", "t3.micro"]
        }
      }
    }
  ]
}
```

### Google Cloud Platform

#### Service Account Best Practices
- Create dedicated service accounts for CloudProxy
- Use minimum required permissions
- Rotate keys regularly

```bash
# Create service account with minimal permissions
gcloud iam service-accounts create cloudproxy-sa \
  --display-name="CloudProxy Service Account"

# Grant only required roles
gcloud projects add-iam-policy-binding PROJECT_ID \
  --member="serviceAccount:cloudproxy-sa@PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/compute.instanceAdmin"
```

### DigitalOcean

#### Token Scoping
- Use read & write scopes only
- Create separate tokens for different environments
- Set token expiration when possible

### Hetzner

#### API Token Security
- Generate project-specific tokens
- Use read & write permissions only for required projects
- Regularly audit token usage

## Proxy Authentication

### Strong Credentials

```python
import secrets
import string

def generate_secure_password(length=20):
    """Generate a secure random password"""
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))

# Use strong credentials
os.environ["PROXY_USERNAME"] = "cloudproxy_" + secrets.token_hex(4)
os.environ["PROXY_PASSWORD"] = generate_secure_password()
```

### IP Whitelisting

Combine authentication methods for maximum security:

```bash
# Use both password and IP restriction
export PROXY_USERNAME="secure_user"
export PROXY_PASSWORD="strong_password"
export ONLY_HOST_IP=True  # Only allow connections from host server
```

### Network Security

#### Use VPN or Private Networks
```bash
# Connect through VPN before accessing proxies
sudo openvpn --config cloudproxy-vpn.conf

# Then use proxies normally
curl --proxy http://user:pass@proxy-ip:8899 https://example.com
```

#### Firewall Rules
```bash
# Restrict proxy access to specific IPs
iptables -A INPUT -p tcp --dport 8899 -s YOUR_IP/32 -j ACCEPT
iptables -A INPUT -p tcp --dport 8899 -j DROP
```

## Monitoring and Auditing

### Log Sensitive Operations

```python
from loguru import logger
import hashlib

def log_proxy_access(username, ip_address):
    """Log proxy access without exposing sensitive data"""
    user_hash = hashlib.sha256(username.encode()).hexdigest()[:8]
    logger.info(f"Proxy access: user_hash={user_hash}, ip={ip_address}")
```

### Regular Audits

Create audit scripts:

```bash
#!/bin/bash
# audit_cloudproxy.sh

echo "=== CloudProxy Security Audit ==="
echo "Checking for exposed credentials..."
grep -r "ACCESS_TOKEN\|SECRET_KEY\|PASSWORD" --include="*.py" --include="*.yml" .

echo "Checking file permissions..."
find . -name ".env*" -exec ls -la {} \;

echo "Checking running containers..."
docker ps --format "table {{.Names}}\t{{.Ports}}"

echo "Checking cloud resources..."
# Add provider-specific checks
```

## Production Deployment with Docker

### Docker Deployment Behind HTTPS Proxy

```yaml
# docker-compose.yml with Traefik reverse proxy
version: '3.8'

services:
  traefik:
    image: traefik:v2.9
    command:
      - "--providers.docker=true"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "443:443"
    volumes:
      - "/var/run/docker.sock:/var/run/docker.sock:ro"
      - "./letsencrypt:/letsencrypt"

  cloudproxy:
    image: laffin/cloudproxy:latest
    env_file: .env
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.cloudproxy.rule=Host(`cloudproxy.example.com`)"
      - "traefik.http.routers.cloudproxy.entrypoints=websecure"
      - "traefik.http.routers.cloudproxy.tls.certresolver=letsencrypt"
    restart: unless-stopped
```

### Nginx Reverse Proxy for Docker

```nginx
server {
    listen 443 ssl http2;
    server_name cloudproxy.example.com;
    
    ssl_certificate /etc/ssl/certs/cloudproxy.crt;
    ssl_certificate_key /etc/ssl/private/cloudproxy.key;
    
    location / {
        proxy_pass http://cloudproxy:8000;  # Docker container name
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Automated Security Updates

```yaml
# .github/workflows/security.yml
name: Security Updates
on:
  schedule:
    - cron: '0 0 * * 1'  # Weekly
jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Update dependencies
        run: |
          pip install --upgrade pip
          pip install --upgrade -r requirements.txt
          pip audit
```

## Incident Response

### Credential Compromise

If credentials are compromised:

1. **Immediately revoke** the compromised credentials
2. **Generate new credentials** with all providers
3. **Audit logs** for unauthorized usage
4. **Terminate** any unauthorized resources
5. **Update** all systems with new credentials
6. **Review** how the compromise occurred

### Quick Revocation Commands

```bash
# DigitalOcean - Delete token via UI or API
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "https://api.digitalocean.com/v2/account/tokens/$TOKEN_ID"

# AWS - Deactivate access key
aws iam delete-access-key --access-key-id AKIAIOSFODNN7EXAMPLE

# GCP - Delete service account key
gcloud iam service-accounts keys delete KEY_ID \
  --iam-account=cloudproxy-sa@project.iam.gserviceaccount.com

# Hetzner - Delete token via UI or API
curl -X DELETE -H "Authorization: Bearer $TOKEN" \
  "https://api.hetzner.cloud/v1/tokens/$TOKEN_ID"
```

## Security Checklist

- [ ] Credentials stored in secure secret management system
- [ ] No credentials in source code or version control
- [ ] Using strong, randomly generated passwords
- [ ] API tokens have minimum required permissions
- [ ] Regular rotation of credentials (monthly/quarterly)
- [ ] Audit logs enabled and monitored
- [ ] Network access restricted (VPN/IP whitelist)
- [ ] HTTPS enabled for API access
- [ ] Container running as non-root user
- [ ] Regular security updates applied
- [ ] Incident response plan documented
- [ ] Backup credentials stored securely

## See Also

- [AWS IAM Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [GCP Security Best Practices](https://cloud.google.com/security/best-practices)
- [Docker Security](https://docs.docker.com/engine/security/)
- [OWASP Security Guidelines](https://owasp.org/www-project-top-ten/)