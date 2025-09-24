#!/usr/bin/env python3
"""
Cursor Integration Startup Hook
Automatically runs when Codex starts a new task.
"""

import asyncio
import sys
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import and run auto-setup
from auto_setup_cursor import auto_start_cursor_integration

if __name__ == "__main__":
    asyncio.run(auto_start_cursor_integration())
