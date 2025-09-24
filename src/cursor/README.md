# Cursor Client Integration
## U-DIG IT WebsiteOS Meta-Intelligence v4.3+

This directory contains the Cursor client implementations that map your JSON configuration into actual API calls, providing full Cursor leverage for your Codex system.

## Files

- `cursor_client.js` - JavaScript/Node.js implementation
- `cursor_client.py` - Python implementation with async support
- `__init__.py` - Python package initialization

## Quick Start

### JavaScript
```javascript
const { CursorClient } = require('./src/cursor/cursor_client.js');

const client = new CursorClient({
  apiBaseUrl: process.env.CURSOR_API_URL,
  apiKey: process.env.CURSOR_API_KEY
});

// Generate code
const result = await client.generateCode({
  requirements: ['Create a React component'],
  language: 'javascript',
  framework: 'react'
});
```

### Python
```python
from src.cursor import CursorClient, AgentType

async def main():
    async with CursorClient() as client:
        result = await client.generate_code({
            'requirements': ['Create a FastAPI endpoint'],
            'language': 'python',
            'framework': 'fastapi'
        })

import asyncio
asyncio.run(main())
```

## Environment Variables

Set these environment variables for the Cursor client:

```bash
CURSOR_API_URL=https://api.cursor.sh
CURSOR_API_KEY=your_api_key_here
CURSOR_TIMEOUT=30
CURSOR_MAX_RETRIES=3
CURSOR_RETRY_DELAY=1.0
```

## Available Scripts

- `npm run cursor:client` - Run the JavaScript cursor client
- `python -m src.cursor.cursor_client` - Run the Python cursor client

## Documentation

See `docs/cursor_client_examples.md` for comprehensive usage examples and integration patterns.
