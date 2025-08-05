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

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd actors

# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys and configuration
```

### Environment Variables

```bash
OPENROUTER_KEY=your_openrouter_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
JWT_SECRET_KEY=your_jwt_secret_key
```

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

## License

MIT License - see [LICENSE](LICENSE) file for details.