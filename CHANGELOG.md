# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Semantic versioning system
- Version endpoint in API
- Dynamic version management from `__version__.py`

### Changed
- Updated project description to reflect client-side tool execution focus

## [0.1.0] - 2025-08-05

### Added
- Initial release of Actors multi-agent system
- FastAPI backend with OpenAI Agents SDK integration
- Supabase authentication and data persistence
- Multi-agent orchestration with triage system
- Client-side tool execution with callback mechanisms
- MCP server integration (weather, time, context7, perplexity)
- Real-time streaming conversations via NDJSON
- Built-in tools: calculator, weather, time, currency, stocks
- Comprehensive logging system with file rotation
- RESTful API with authentication middleware
- PostgreSQL database with RLS policies
- Docker support for development
- Comprehensive test suite with end-to-end testing

### Security
- Row Level Security (RLS) enabled on all user data
- JWT token validation on protected endpoints
- Input sanitization via Pydantic validation
- Environment variable protection for secrets