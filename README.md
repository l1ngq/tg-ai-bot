# TG-bot

Telegram bot with LLM routing, Todoist tasks, GitHub notes, and Habr articles.

## Requirements

- Python 3.11+
- Telegram bot token
- OpenAI-compatible API key
- Todoist API token
- GitHub PAT with repo contents access

## Local run

1. Copy .env.example to .env and fill values.
2. Create and activate a virtual environment.
3. Install dependencies: pip install -r requirements.txt
4. Run: python main.py

## Docker run

- Build: docker build -t tg-bot .
- Run: docker run -d --name tg-bot --restart unless-stopped --env-file .env tg-bot

## GitHub Actions deploy (SSH)

### Server prep

- Install git and docker.
- Create the app directory: /opt/tg-bot
- Create /opt/tg-bot/.env with real secrets (do not commit it).

### Repo secrets

Add these repository secrets:

- SSH_HOST
- SSH_USER
- SSH_PORT
- SSH_KEY (private key with access to the server)

### Notes

- The workflow deploys on push to main. Update the branch in .github/workflows/deploy.yml if needed.
- If your server requires sudo for docker, add sudo in the workflow script.
