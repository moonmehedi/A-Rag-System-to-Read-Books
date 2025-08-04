# Environment Setup Guide

## Quick Setup

1. **Copy the environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Edit the `.env` file and replace the placeholder values:**

### Required API Keys

#### HuggingFace Token
- Go to [HuggingFace Settings](https://huggingface.co/settings/tokens)
- Create a new token with `read` permissions
- Replace `your_huggingface_token_here` in `.env`

#### LangChain API Key (Optional but recommended)
- Go to [LangSmith](https://smith.langchain.com/)
- Create an account and get your API key
- Replace `your_langchain_api_key_here` in `.env`

#### JWT Secret Key
- Generate a strong random string (at least 32 characters)
- Replace `your_super_secret_jwt_key_change_this_in_production_123456` in `.env`
- You can use: `openssl rand -hex 32` to generate a secure key

### Database Setup

The project uses PostgreSQL. Start the database with Docker:

```bash
cd chatbot_backend_FastAPI/backend
docker-compose up -d
```

### Environment Variables Reference

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Yes | - |
| `HUGGINGFACE_TOKEN` | HuggingFace API token | Yes | - |
| `LANGCHAIN_API_KEY` | LangChain API key | Yes | - |
| `JWT_SECRET_KEY` | Secret key for JWT tokens | No | supersecretkey |
| `JWT_ALGORITHM` | JWT algorithm | No | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration time | No | 10080 (7 days) |
| `ENVIRONMENT` | Application environment | No | development |
| `DEBUG` | Debug mode | No | True |
| `LOG_LEVEL` | Logging level | No | INFO |

## Security Notes

- **Never commit the `.env` file** to version control
- Use strong, unique passwords and keys in production
- Consider using a proper secret management system for production
- The `.env` file is already included in `.gitignore`

## Troubleshooting

### Common Issues

1. **Import Error for pydantic_settings:**
   ```bash
   pip install pydantic-settings
   ```

2. **Database Connection Issues:**
   - Ensure PostgreSQL is running: `docker-compose ps`
   - Check the DATABASE_URL format
   - Verify database credentials

3. **HuggingFace Authentication:**
   - Verify your token has proper permissions
   - Check for typos in the token

4. **Environment File Not Found:**
   - Ensure `.env` is in the project root directory
   - Check the path in `config.py` matches your structure
