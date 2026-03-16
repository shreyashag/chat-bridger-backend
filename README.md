# Actors

A powerful AI agent framework that enables client-side tool execution with flexible LLM provider support and extensible multi-agent capabilities.

## Features

- **Client-Side Tool Execution**: Revolutionary approach allowing tools to run directly in the client with secure callback mechanisms
- **Flexible LLM Provider Support**: Choose your own AI provider - OpenRouter, OpenAI, Ollama, or any compatible service
- **Multi-Agent Architecture**: Support for specialized agents that can collaborate and hand off complex tasks
- **Conversation Management**: Full conversation lifecycle with star, archive, list, delete, and automatic title generation
- **MCP Integration**: Extensible tool system using Model Context Protocol servers for seamless tool connectivity
- **Authentication & Persistence**: Complete user management and conversation storage with Supabase
- **Real-Time Streaming**: FastAPI-based endpoints with NDJSON streaming for responsive user experiences

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager

### Installing UV

If you don't have UV installed yet:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

### Installation

```bash
# Clone the repository
git clone https://github.com/shreyashag/chat-bridger-backend
cd chat-bridger-backend
# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API keys and configuration
```

### Environment Variables

See `.env.example` for a complete list of required and optional environment variables with detailed setup instructions.

### Supabase Setup

This project uses Supabase for authentication and conversation persistence. You'll need a Supabase project before running the server.

1. Create a project at [supabase.com](https://supabase.com) and note your **Project URL** and **Service Role Key** (under Project Settings → API).

2. Run the schema to create the required tables. Open the **SQL Editor** in the Supabase dashboard, paste the contents of `src/schema.sql`, and click **Run**.

   This creates four tables:
   - `users` — accounts with bcrypt-hashed passwords
   - `conversations` — conversation metadata per user
   - `messages` — individual messages linked to conversations (cascade-deleted with conversation)
   - `refresh_tokens` — JWT refresh token tracking (cascade-deleted with user)

   > **Note:** The full file must be run in one go — the `update_updated_at_column` function is referenced by triggers defined later in the file.

3. Add the following to your `.env.local`:

   ```
   SUPABASE_URL=https://<project-ref>.supabase.co
   SUPABASE_KEY=<your-service-role-key>
   JWT_SECRET_KEY=<random-string-minimum-32-chars>
   ```

   Optionally, you can point auth and session storage at separate Supabase projects using `SUPABASE_AUTH_URL`/`SUPABASE_AUTH_KEY` and `SESSIONS_SUPABASE_URL`/`SESSIONS_SUPABASE_KEY`.

### Authentication

The API exposes the following auth endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/auth/register` | Create a new account |
| `POST` | `/auth/login` | Login — returns an access token and a refresh token |
| `POST` | `/auth/refresh` | Exchange a refresh token for a new access token |
| `POST` | `/auth/logout` | Invalidate the current refresh token |
| `POST` | `/auth/logout-all` | Invalidate all sessions for the authenticated user |
| `GET`  | `/auth/me` | Get current user details |

Access tokens are short-lived JWTs (default 30 minutes, configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`). Use the refresh token to obtain new access tokens without re-authenticating.

### Running the Server

```bash
docker compose up --build
```

The API will be available at `http://localhost:8000` with interactive documentation at `/docs`.

## Testing

```bash
# Run tests
pytest
```

## Documentation

- API documentation is automatically generated at `/docs` when running the server

## Built on the Shoulders of Giants

This project is made possible by the incredible work of these open-source projects:

- **[OpenAI Agents SDK](https://github.com/openai/openai-agents)** - Powerful agent framework for building AI applications
- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern, fast web framework for building APIs with Python
- **[UV](https://docs.astral.sh/uv/)** - Blazingly fast Python package manager by Astral
- **[Supabase](https://supabase.com/)** - Open-source Firebase alternative with PostgreSQL
- **[Ruff](https://docs.astral.sh/ruff/)** - Lightning-fast Python linter and formatter
- **[Model Context Protocol (MCP)](https://modelcontextprotocol.io/)** - Standardized protocol for AI model-tool integration

Special thanks to the entire Python ecosystem and the open-source community! 🚀

## License

MIT License - see [LICENSE](LICENSE) file for details.