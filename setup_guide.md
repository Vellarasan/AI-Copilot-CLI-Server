# GitHub Copilot CLI API Server - Setup Guide

## Implementation Summary

This solution provides a REST API server that:
1. Executes GitHub Copilot CLI commands on server-side repositories
2. Performs Git operations (add, commit, push)
3. Provides a complete workflow endpoint combining all operations
4. Includes security features like repository whitelisting

## Prerequisites

### 1. System Requirements
- Python 3.8 or higher
- Git installed and configured
- GitHub CLI (`gh`) installed
- GitHub Copilot CLI extension

### 2. GitHub Account Setup
- GitHub account with Copilot access
- Personal Access Token (PAT) with repo permissions

## Environment Setup

### Step 1: Install GitHub CLI and Copilot

```bash
# Install GitHub CLI (Ubuntu/Debian)
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg | sudo dd of=/usr/share/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" | sudo tee /etc/apt/sources.list.d/github-cli.list > /dev/null
sudo apt update
sudo apt install gh

# For macOS
brew install gh

# Authenticate with GitHub
gh auth login

# Install Copilot CLI extension
gh extension install github/gh-copilot
```

### Step 2: Configure Git

```bash
# Set up Git credentials
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Configure credential helper (optional but recommended)
git config --global credential.helper store
```

### Step 3: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install flask gunicorn
```

### Step 4: Create Directory Structure

```bash
# Create base directory for repositories
mkdir -p /var/repos

# Set appropriate permissions
chmod 755 /var/repos

# Clone your repositories
cd /var/repos
git clone https://github.com/your-org/your-repo.git
```

### Step 5: Configure Environment Variables

Create a `.env` file:

```bash
# Base path where repositories are stored
REPOS_BASE_PATH=/var/repos

# Comma-separated list of allowed repository names
ALLOWED_REPOS=your-repo,another-repo,project-x

# Server port
PORT=5000

# Flask environment
FLASK_ENV=production
```

## Running the Server

### Development Mode

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export REPOS_BASE_PATH=/var/repos
export ALLOWED_REPOS=your-repo,another-repo

# Run the server
python copilot_api_server.py
```

### Production Mode with Gunicorn

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 copilot_api_server:app
```

### Using systemd (Recommended for Production)

Create `/etc/systemd/system/copilot-api.service`:

```ini
[Unit]
Description=GitHub Copilot API Server
After=network.target

[Service]
Type=notify
User=your-user
Group=your-group
WorkingDirectory=/path/to/your/app
Environment="REPOS_BASE_PATH=/var/repos"
Environment="ALLOWED_REPOS=repo1,repo2"
Environment="PORT=5000"
ExecStart=/path/to/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 copilot_api_server:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable copilot-api
sudo systemctl start copilot-api
sudo systemctl status copilot-api
```

## API Endpoints

### 1. Health Check
```bash
GET /health
```

### 2. Execute Copilot Only
```bash
POST /api/copilot/execute
Content-Type: application/json

{
  "repo_name": "your-repo",
  "prompt": "Add error handling to the authentication function",
  "files": ["src/auth.py"]  // optional
}
```

### 3. Commit and Push Only
```bash
POST /api/git/commit-and-push
Content-Type: application/json

{
  "repo_name": "your-repo",
  "commit_message": "Add error handling",
  "branch": "main",  // optional
  "files": ["src/auth.py"]  // optional, defaults to all changes
}
```

### 4. Complete Workflow (Copilot + Commit + Push)
```bash
POST /api/workflow/copilot-commit-push
Content-Type: application/json

{
  "repo_name": "your-repo",
  "prompt": "Add error handling to the authentication function",
  "commit_message": "Add error handling to auth",
  "branch": "main",  // optional
  "files": ["src/auth.py"]  // optional
}
```

## Usage Examples

### Using cURL

```bash
# Complete workflow
curl -X POST http://localhost:5000/api/workflow/copilot-commit-push \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "my-project",
    "prompt": "Add input validation to the user registration endpoint",
    "commit_message": "Add input validation",
    "branch": "feature/validation"
  }'
```

### Using Python Requests

```python
import requests

url = "http://your-server:5000/api/workflow/copilot-commit-push"
payload = {
    "repo_name": "my-project",
    "prompt": "Refactor the database connection logic",
    "commit_message": "Refactor database connection",
    "branch": "main"
}

response = requests.post(url, json=payload)
print(response.json())
```

### Using JavaScript/Node.js

```javascript
const axios = require('axios');

const payload = {
  repo_name: 'my-project',
  prompt: 'Add unit tests for the user service',
  commit_message: 'Add user service tests',
  branch: 'main'
};

axios.post('http://your-server:5000/api/workflow/copilot-commit-push', payload)
  .then(response => console.log(response.data))
  .catch(error => console.error(error));
```

## Security Considerations

### 1. Authentication & Authorization
Add API key authentication:

```python
from functools import wraps

API_KEY = os.getenv('API_KEY', 'your-secret-key')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if api_key != API_KEY:
            return jsonify({'error': 'Invalid API key'}), 401
        return f(*args, **kwargs)
    return decorated_function

# Apply to endpoints
@app.route('/api/copilot/execute', methods=['POST'])
@require_api_key
def execute_copilot():
    # ... existing code
```

### 2. Network Security
- Use HTTPS in production (configure nginx/Apache as reverse proxy)
- Implement rate limiting
- Use firewall rules to restrict access

### 3. Repository Access Control
- Use the `ALLOWED_REPOS` environment variable
- Validate all input paths to prevent directory traversal
- Run the service with limited user permissions

### 4. Secrets Management
- Never commit credentials to version control
- Use environment variables or secret management services
- Rotate API keys regularly

## Monitoring & Logging

### View Logs
```bash
# If using systemd
sudo journalctl -u copilot-api -f

# Application logs
tail -f /var/log/copilot-api.log
```

### Add Logging to File

```python
import logging
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    '/var/log/copilot-api.log',
    maxBytes=10000000,
    backupCount=5
)
handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
)
handler.setFormatter(formatter)
app.logger.addHandler(handler)
```

## Troubleshooting

### Common Issues

1. **Copilot command not found**
   - Verify `gh` CLI is installed: `gh --version`
   - Install Copilot extension: `gh extension install github/gh-copilot`

2. **Git authentication fails**
   - Configure Git credentials: `git config --global credential.helper store`
   - Use SSH keys for authentication

3. **Permission denied errors**
   - Check directory permissions: `ls -la /var/repos`
   - Run with appropriate user permissions

4. **Timeout errors**
   - Increase timeout in `run_command` method
   - Check server resources (CPU, memory)

## Architecture Overview

```
External Client
      ↓
   HTTP API (Flask)
      ↓
CopilotExecutor Class
      ↓
   ├── GitHub Copilot CLI (gh copilot)
   └── Git Commands
         ↓
    Local Repository
         ↓
    Remote Repository (GitHub)
```

## Next Steps

1. **Add Authentication**: Implement JWT or API key authentication
2. **Add Webhooks**: Trigger workflows from GitHub webhooks
3. **Add Queue System**: Use Celery for async processing
4. **Add Database**: Track execution history
5. **Add UI**: Create a web dashboard for monitoring

## Support

For issues or questions:
- Check GitHub Copilot CLI documentation: https://docs.github.com/en/copilot
- Verify Flask documentation: https://flask.palletsprojects.com/