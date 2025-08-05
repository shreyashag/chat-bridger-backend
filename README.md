# Actors

A multi-agent conversation system backend that enables AI agents to collaborate and provide specialized expertise across different domains.

## Features

- **Multi-Agent Architecture**: Specialized agents (Math Tutor, History Tutor, Triage Agent) that collaborate and hand off tasks
- **MCP Integration**: Extensible tool system using Model Context Protocol servers
- **Client Tools Support**: Enable client-side tool execution with callback mechanisms
- **Authentication & Persistence**: Supabase integration for user management and conversation storage
- **RESTful API**: FastAPI-based endpoints with streaming support

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
git clone <repository-url>
cd actors

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env.local
# Edit .env.local with your API keys and configuration
```

### Environment Variables

See `.env.example` for a complete list of required and optional environment variables with detailed setup instructions.

### Running the Server

```bash
python -m src.api.api
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