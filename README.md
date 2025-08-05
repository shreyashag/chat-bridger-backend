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