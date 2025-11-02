# API Authentication Guide

This document explains how to configure and use API key authentication for the nunoAIPlanning service.

## Overview

The `/analyze-planning` and `/quick-advice` endpoints are protected by API key authentication to:
- Prevent unauthorized access to LLM resources
- Control costs (especially when using cloud LLM providers)
- Protect against abuse and attacks
- Track usage per client

Public endpoints like `/health`, `/`, and `/supported-providers` remain open for monitoring and discovery.

## Configuration

### 1. Generate a Secure API Key

```bash
# Generate a cryptographically secure random key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"
```

Example output:
```
79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs
```

### 2. Set the API Key in Your Environment

#### Option A: In `.env` file (for Docker Compose)

```bash
# Edit .env file
API_KEY=79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs
```

#### Option B: In Dokploy Environment Variables

1. Go to your service in Dokploy
2. Navigate to "Environment Variables" section
3. Add:
   - **Name**: `API_KEY`
   - **Value**: `79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs`
4. Save and redeploy

#### Option C: Export in Shell (for local testing)

```bash
export API_KEY=79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs
```

### 3. Restart the Service

```bash
# Docker Compose
docker-compose down
docker-compose up -d

# Or in Dokploy
# Click "Restart" button in service dashboard
```

## Usage

### Authentication Methods

The API supports two authentication methods:

#### Method 1: HTTP Header (Recommended)

```bash
curl -X POST https://nunoollama.opefitoo.com/analyze-planning \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs" \
  -d '{
    "planning_id": 1,
    "month": 12,
    "year": 2025,
    ...
  }'
```

#### Method 2: Query Parameter

```bash
curl -X POST "https://nunoollama.opefitoo.com/analyze-planning?api_key=79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs" \
  -H "Content-Type: application/json" \
  -d '{
    "planning_id": 1,
    ...
  }'
```

**Note**: The header method is more secure as query parameters may be logged in server access logs.

### Testing Authentication

#### Test Without API Key (Should Fail)

```bash
curl -X POST https://nunoollama.opefitoo.com/quick-advice \
  -H "Content-Type: application/json" \
  -d '{
    "failure_message": "INFEASIBLE",
    "strategies_attempted": ["full", "relaxed"]
  }'
```

**Expected Response** (403 Forbidden):
```json
{
  "detail": "Invalid or missing API key. Provide via X-API-Key header or ?api_key= query parameter."
}
```

#### Test With Valid API Key (Should Succeed)

```bash
curl -X POST https://nunoollama.opefitoo.com/quick-advice \
  -H "Content-Type: application/json" \
  -H "X-API-Key: 79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs" \
  -d '{
    "failure_message": "INFEASIBLE",
    "strategies_attempted": ["full", "relaxed"]
  }'
```

**Expected Response** (200 OK):
```json
{
  "advice": "The optimization failed with INFEASIBLE status...",
  "timestamp": "2025-01-02T10:30:00.000Z"
}
```

## Client Integration

### React Admin / JavaScript

Update your API client to include the API key:

```javascript
// In your React Admin OptimizerAIChat component or API service

const API_KEY = '79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs';

// Method 1: Using fetch with header
const response = await fetch('https://nunoollama.opefitoo.com/analyze-planning', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': API_KEY,
  },
  body: JSON.stringify(diagnosticData),
});

// Method 2: Using axios with header
import axios from 'axios';

const client = axios.create({
  baseURL: 'https://nunoollama.opefitoo.com',
  headers: {
    'X-API-Key': API_KEY,
  },
});

const response = await client.post('/analyze-planning', diagnosticData);
```

**Important**: Store the API key securely in your frontend configuration:

```javascript
// Option 1: Environment variable (recommended)
const API_KEY = process.env.REACT_APP_NUNO_AI_API_KEY;

// Option 2: Configuration file (not committed to git)
import config from './config.local.js';
const API_KEY = config.nunoAiApiKey;
```

### Python Client

```python
import os
import requests

API_KEY = os.getenv('NUNO_AI_API_KEY')
BASE_URL = 'https://nunoollama.opefitoo.com'

# Using requests library
response = requests.post(
    f'{BASE_URL}/analyze-planning',
    headers={
        'Content-Type': 'application/json',
        'X-API-Key': API_KEY,
    },
    json=diagnostic_data
)

if response.status_code == 200:
    advice = response.json()
    print(advice['root_cause_summary'])
elif response.status_code == 403:
    print('Invalid API key')
else:
    print(f'Error: {response.status_code}')
```

## Security Best Practices

### 1. Keep API Keys Secret

- ✅ **DO**: Store in environment variables
- ✅ **DO**: Use `.env` files (add to `.gitignore`)
- ✅ **DO**: Use secret management systems (Dokploy env vars, AWS Secrets Manager, etc.)
- ❌ **DON'T**: Hard-code in source files
- ❌ **DON'T**: Commit to git
- ❌ **DON'T**: Share in public channels

### 2. Rotate Keys Regularly

Generate a new API key periodically:

```bash
# Generate new key
python3 -c "import secrets; print(secrets.token_urlsafe(32))"

# Update .env file with new key
# Restart service
# Update all clients with new key
```

### 3. Use Different Keys for Different Environments

```bash
# Development
API_KEY=dev_key_abc123...

# Staging
API_KEY=staging_key_xyz789...

# Production
API_KEY=prod_key_secure_random_string...
```

### 4. Monitor Usage

Check server logs for authentication attempts:

```bash
# View service logs
docker logs nuno-ai-planning -f

# Look for 403 errors (unauthorized attempts)
docker logs nuno-ai-planning 2>&1 | grep "403"
```

### 5. Combine with Other Security Measures

API key authentication works well with:
- **Rate limiting** (via Traefik middleware)
- **IP whitelisting** (for internal services)
- **HTTPS/TLS** (always use encrypted connections)
- **Network isolation** (Docker networks, VPCs)

See `SECURITY.md` for comprehensive security configuration.

## Troubleshooting

### Problem: "Invalid or missing API key" error

**Solutions**:
1. Check that `API_KEY` is set in environment variables
2. Verify the key matches exactly (no extra spaces)
3. Ensure the service was restarted after setting the key
4. Check that the client is sending the key correctly

```bash
# Verify environment variable in container
docker exec nuno-ai-planning env | grep API_KEY

# Should output:
# API_KEY=79FNVaF6Y3W241B4ZWHRwHHWa_L5ca7f-L-qFR_GYhs
```

### Problem: Service generates temporary key on startup

**Cause**: `API_KEY` environment variable not set

**Solution**: Set the `API_KEY` in your `.env` file or Dokploy environment variables

**Logs will show**:
```
⚠️  WARNING: API_KEY not set in environment!
🔑 Generated temporary API key: [random-key]
   Set API_KEY environment variable for production use.
```

### Problem: Authentication works locally but not in production

**Possible causes**:
1. `.env` file not copied to production server
2. Environment variables not set in Dokploy
3. Reverse proxy (Traefik) stripping headers

**Solutions**:
1. Set `API_KEY` directly in Dokploy environment variables
2. Check Traefik configuration for header passthrough
3. Verify with curl from production server:

```bash
# SSH to production server
ssh your-server

# Test from inside the server
curl -k https://localhost:8001/health

# Test with API key
curl -k -X POST https://localhost:8001/quick-advice \
  -H "X-API-Key: YOUR_KEY" \
  -H "Content-Type: application/json" \
  -d '{"failure_message": "test", "strategies_attempted": []}'
```

## API Endpoints

### Protected Endpoints (Require API Key)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze-planning` | POST | Full diagnostic analysis with LLM |
| `/quick-advice` | POST | Quick advice without full diagnostics |

### Public Endpoints (No API Key Required)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Service info and health status |
| `/health` | GET | Detailed health check |
| `/docs` | GET | OpenAPI/Swagger documentation |
| `/supported-providers` | GET | List of supported LLM providers |

## Advanced: Multiple API Keys

For supporting multiple clients with different keys, modify `docker/server.py`:

```python
# In docker/server.py

# Load multiple API keys
VALID_API_KEYS = set()
if os.getenv("API_KEY"):
    VALID_API_KEYS.add(os.getenv("API_KEY"))
if os.getenv("API_KEY_CLIENT_A"):
    VALID_API_KEYS.add(os.getenv("API_KEY_CLIENT_A"))
if os.getenv("API_KEY_CLIENT_B"):
    VALID_API_KEYS.add(os.getenv("API_KEY_CLIENT_B"))

async def get_api_key(
    api_key_header: str = Security(api_key_header),
    api_key_query: str = Security(api_key_query),
) -> str:
    if api_key_header in VALID_API_KEYS:
        return api_key_header
    if api_key_query in VALID_API_KEYS:
        return api_key_query
    raise HTTPException(status_code=403, detail="Invalid or missing API key")
```

Then set multiple keys in environment:
```bash
API_KEY=primary_key_here
API_KEY_CLIENT_A=client_a_key_here
API_KEY_CLIENT_B=client_b_key_here
```

## Summary

1. **Generate** a secure API key using `secrets.token_urlsafe(32)`
2. **Configure** the key in `.env` or Dokploy environment variables
3. **Restart** the service to apply the change
4. **Use** the key in client requests via `X-API-Key` header
5. **Secure** the key (never commit to git, use env vars)
6. **Monitor** logs for unauthorized access attempts
7. **Rotate** keys periodically for security

Your API is now protected from unauthorized access! 🔐
