# CodexHUB Editor

A web-based code editor for the CodexHUB project with file management, editing, and AI agent integration capabilities.

## Setup Instructions

### 1. Environment Configuration

#### Option 1: Generate a Secure API Key
```bash
pnpm run editor:generate-key
```

#### Option 2: Manual Configuration
Create a `.env` file in the project root directory with the following content:

```bash
# API Key for CodexHUB Editor authentication
CODEX_API_KEY=your_secure_api_key_here

# Server Configuration
PORT=5000

# Optional: Development settings
NODE_ENV=development
```

**Security Note**: Use a cryptographically secure random string for your API key. The generated key from the script is recommended.

### 2. Prerequisites

- Node.js (v16 or higher)
- pnpm package manager
- Chrome browser (optional, for auto-opening)

### 3. Running the Editor

#### Option 1: Using the Batch Script (Windows)
```bash
cd editor
start-codex.bat
```

#### Option 2: Manual Start
```bash
# Install dependencies (if not already done)
pnpm install

# Start the editor
pnpm run editor:codex
```

### 4. Access the Editor

- **Local**: http://localhost:5000/editor
- **Health Check**: http://localhost:5000/health

## Features

- **File Management**: Browse, edit, create, and delete files
- **Syntax Highlighting**: Support for multiple programming languages
- **Search & Replace**: Find and replace text across files
- **Git Integration**: Basic git status and operations
- **Task Management**: Run commands and monitor status
- **Cursor Agent Integration**: AI-powered code assistance
- **Secure Authentication**: API key-based access control

## Security

- API keys are stored in environment variables
- All requests require valid authentication
- File operations are restricted to the project directory
- Input validation and sanitization

## Troubleshooting

### Common Issues

1. **"API key not found"**: 
   - Generate a secure API key: `pnpm run editor:generate-key`
   - Ensure `.env` file exists in project root with `CODEX_API_KEY`
2. **"Package.json not found"**: Run the script from the `editor` directory
3. **"pnpm not found"**: Install pnpm globally: `npm install -g pnpm`
4. **Port already in use**: Change the PORT in your `.env` file
5. **"Unauthorized" errors**: Verify your API key matches between `.env` file and client

### Logs

Check the console output for detailed error messages and status information.

## Development

The editor consists of:
- `codex-editor.js`: Express server with file operations and API endpoints
- `codex-editor.html`: Frontend interface with CodeMirror editor
- `backend/middleware.js`: Authentication middleware
- `start-codex.bat`: Windows startup script with prerequisite checks
