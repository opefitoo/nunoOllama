# Security Configuration Guide

This guide covers security measures to protect your nunoAIPlanning deployment from attacks and unauthorized access.

## IP Filtering Options

### Option 1: Traefik Middleware (Recommended for Dokploy)

Traefik supports IP whitelisting through middleware. You can configure this in Dokploy:

#### In Dokploy Domain Settings:

1. Go to your service's domain configuration
2. Add Custom Labels:

```yaml
# Allow only specific IPs or ranges
traefik.http.middlewares.ip-whitelist.ipwhitelist.sourcerange: 46.224.6.0/24,10.0.0.0/8,YOUR_OFFICE_IP
traefik.http.routers.ai-planning-secure.middlewares: ip-whitelist@docker

# Or block specific IPs
traefik.http.middlewares.ip-blacklist.ipallowlist.sourcerange: 0.0.0.0/0
traefik.http.middlewares.ip-blacklist.ipallowlist.ipstrategy.excludedips: BLOCKED_IP_1,BLOCKED_IP_2
```

#### Example for your setup:

```yaml
# In Dokploy, add these labels to your service:
traefik.http.middlewares.nuno-security.ipwhitelist.sourcerange: "46.224.6.0/24,YOUR_OFFICE_IP,YOUR_HOME_IP"
traefik.http.routers.ai-planning-secure.middlewares: nuno-security@docker
```

### Option 2: Rate Limiting (Recommended)

Rate limiting prevents brute force attacks and excessive scanning:

```yaml
# Traefik rate limiting middleware
traefik.http.middlewares.rate-limit.ratelimit.average: 20
traefik.http.middlewares.rate-limit.ratelimit.burst: 50
traefik.http.middlewares.rate-limit.ratelimit.period: 1m
traefik.http.routers.ai-planning-secure.middlewares: rate-limit@docker
```

This allows 20 requests per minute on average, with bursts up to 50.

### Option 3: Server Firewall (UFW)

If you have direct server access, use UFW (Uncomplicated Firewall):

```bash
# Install UFW (if not already installed)
sudo apt-get update
sudo apt-get install ufw

# Allow SSH (IMPORTANT - do this first!)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow Ollama port (only from localhost)
sudo ufw allow from 127.0.0.1 to any port 11434

# Allow Docker network
sudo ufw allow from 172.16.0.0/12

# Deny specific IPs (replace with scanner IPs)
sudo ufw deny from SCANNER_IP

# Enable firewall
sudo ufw enable

# Check status
sudo ufw status verbose
```

### Option 4: iptables (Advanced)

For more granular control:

```bash
# Block specific IP
sudo iptables -I INPUT -s SCANNER_IP -j DROP

# Rate limit connections (max 20 per minute)
sudo iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --set
sudo iptables -A INPUT -p tcp --dport 443 -m state --state NEW -m recent --update --seconds 60 --hitcount 20 -j DROP

# Save rules
sudo netfilter-persistent save
```

## Security Headers

Add security headers via Traefik middleware:

```yaml
# In Dokploy, add these labels:
traefik.http.middlewares.security-headers.headers.framedeny: "true"
traefik.http.middlewares.security-headers.headers.browserxssfilter: "true"
traefik.http.middlewares.security-headers.headers.contenttypenosniff: "true"
traefik.http.middlewares.security-headers.headers.forcestsheader: "true"
traefik.http.middlewares.security-headers.headers.stsincludesubdomains: "true"
traefik.http.middlewares.security-headers.headers.stsseconds: "31536000"
traefik.http.middlewares.security-headers.headers.customresponseheaders.X-Robots-Tag: "noindex,nofollow,nosnippet,noarchive,notranslate,noimageindex"
traefik.http.routers.ai-planning-secure.middlewares: security-headers@docker
```

## Monitoring and Alerting

### 1. Monitor Traefik Access Logs

Check real external IPs of scanners:

```bash
# View Traefik logs in Dokploy
docker logs traefik -f | grep "GET"

# Or if you have access to log files:
tail -f /var/log/traefik/access.log
```

### 2. Set Up Fail2Ban

Automatically ban IPs that show malicious behavior:

```bash
# Install fail2ban
sudo apt-get install fail2ban

# Create custom filter for Traefik
sudo nano /etc/fail2ban/filter.d/traefik-auth.conf
```

Add this content:

```ini
[Definition]
failregex = ^<HOST> - .* "(GET|POST|HEAD) .* HTTP/.*" 404 .*$
            ^<HOST> - .* "(GET|POST|HEAD) /.env HTTP/.*" .*$
            ^<HOST> - .* "(GET|POST|HEAD) /.git/ HTTP/.*" .*$
ignoreregex =
```

Configure jail:

```bash
sudo nano /etc/fail2ban/jail.local
```

Add:

```ini
[traefik-auth]
enabled = true
port = http,https
filter = traefik-auth
logpath = /var/log/traefik/access.log
maxretry = 5
bantime = 3600
findtime = 600
```

Restart fail2ban:

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status traefik-auth
```

## Recommended Security Stack

For your deployment, I recommend combining:

1. **Rate Limiting** (blocks excessive requests)
2. **Security Headers** (prevents common attacks)
3. **Fail2Ban** (automatic IP banning)
4. **Optional IP Whitelist** (if you have fixed IPs)

### Combined Traefik Configuration

In Dokploy, add these labels to your service:

```yaml
# Rate limiting
traefik.http.middlewares.nuno-ratelimit.ratelimit.average: 20
traefik.http.middlewares.nuno-ratelimit.ratelimit.burst: 50
traefik.http.middlewares.nuno-ratelimit.ratelimit.period: 1m

# Security headers
traefik.http.middlewares.nuno-headers.headers.framedeny: "true"
traefik.http.middlewares.nuno-headers.headers.browserxssfilter: "true"
traefik.http.middlewares.nuno-headers.headers.contenttypenosniff: "true"
traefik.http.middlewares.nuno-headers.headers.forcestsheader: "true"
traefik.http.middlewares.nuno-headers.headers.stsincludesubdomains: "true"
traefik.http.middlewares.nuno-headers.headers.stsseconds: "31536000"

# IP whitelist (optional - replace with your IPs)
# traefik.http.middlewares.nuno-ipfilter.ipwhitelist.sourcerange: "46.224.6.0/24,YOUR_IP"

# Apply all middlewares
traefik.http.routers.ai-planning-secure.middlewares: nuno-ratelimit@docker,nuno-headers@docker
```

## Application-Level Security

The FastAPI application already has some security, but you can enhance it:

### Add Request Validation

Edit `docker/server.py` to add IP-based access control:

```python
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class IPFilterMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host

        # Block known scanner IPs
        blocked_ips = ["10.0.1.11", "SCANNER_IP_HERE"]
        if client_ip in blocked_ips:
            raise HTTPException(status_code=403, detail="Access denied")

        # Log suspicious paths
        suspicious_paths = [".env", ".git", "graphql", "swagger-ui", "actuator"]
        if any(path in str(request.url.path) for path in suspicious_paths):
            logger.warning(f"Suspicious request from {client_ip}: {request.url.path}")

        response = await call_next(request)
        return response

# Add to app
app.add_middleware(IPFilterMiddleware)
```

## Testing Your Security

After implementing security measures:

```bash
# Test rate limiting (should get 429 after many requests)
for i in {1..30}; do curl -k https://nunoollama.opefitoo.com/health; done

# Test from blocked IP (should get 403)
curl --interface BLOCKED_IP https://nunoollama.opefitoo.com/

# Check firewall status
sudo ufw status
sudo fail2ban-client status

# Monitor Traefik logs
docker logs traefik -f
```

## Response to Current Scanner

The scanner you detected (IP 10.0.1.11) is probing for:
- ✅ GraphQL endpoints - Your service correctly returns 404
- ✅ API documentation - Protected
- ✅ Sensitive files (.env, .git) - Not exposed
- ✅ Framework-specific endpoints - Not present

**Your service is responding correctly.** The scanner found nothing.

However, you should:
1. Check Traefik logs to find the real external IP
2. Add rate limiting to prevent resource exhaustion
3. Consider IP whitelisting if you have fixed IPs

## Priority Actions

1. **Immediate**: Add rate limiting via Traefik labels in Dokploy
2. **Short-term**: Set up Fail2Ban for automatic IP banning
3. **Long-term**: Consider IP whitelisting if you have static IPs
4. **Ongoing**: Monitor Traefik access logs regularly

## Notes

- The IP `10.0.1.11` is a private Docker network IP, meaning requests are coming through Traefik
- Check Traefik access logs to see the real external source IP
- Rate limiting is more practical than IP whitelisting for most use cases
- Always test security changes carefully to avoid locking yourself out
