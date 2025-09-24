#!/usr/bin/env python3
"""
Start Cursor Integration
Starts all Cursor integration components.
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cursor import start_cursor_auto_invocation
from src.knowledge.auto_loader import start_knowledge_auto_loading
from src.mobile.mobile_app import start_mobile_app
from src.knowledge.brain_blocks_integration import start_brain_blocks_integration


async def start_all_integrations():
    """Start all integration components."""

    print("🚀 Starting Cursor Integration System...")

    try:
        # Start Cursor auto-invocation
        print("Starting Cursor auto-invocation...")
        await start_cursor_auto_invocation([Path(".")])
        print("✅ Cursor auto-invocation started")

        # Start knowledge auto-loading
        print("Starting knowledge auto-loading...")
        await start_knowledge_auto_loading()
        print("✅ Knowledge auto-loading started")

        # Start mobile app
        print("Starting mobile app...")
        await start_mobile_app()
        print("✅ Mobile app started")

        # Start brain blocks integration
        print("Starting brain blocks integration...")
        await start_brain_blocks_integration()
        print("✅ Brain blocks integration started")

        print("🎉 All Cursor integration components started successfully!")

    except Exception as e:
        print(f"❌ Error starting integrations: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(start_all_integrations())
