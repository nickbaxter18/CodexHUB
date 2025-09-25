#!/usr/bin/env python3
"""
Codex Cursor Startup Script
Automatically runs when Codex starts a new task to ensure Cursor IDE is used.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
current_dir = Path(__file__).parent.parent
src_dir = current_dir / "src"
sys.path.insert(0, str(src_dir))
sys.path.insert(0, str(current_dir))  # Also add root directory for relative imports


def check_environment_variables():
    """Check if all required environment variables are set."""

    print("🔍 Checking Environment Variables...")

    # Check CURSOR_API_URL
    cursor_url = os.getenv("CURSOR_API_URL")
    if cursor_url:
        print(f"✅ CURSOR_API_URL: {cursor_url}")
    else:
        print("⚠️ CURSOR_API_URL not set, using default: https://api.cursor.sh")
        os.environ["CURSOR_API_URL"] = "https://api.cursor.sh"

    # Check CURSOR_API_KEY
    cursor_key = os.getenv("CURSOR_API_KEY")
    if cursor_key:
        print(f"✅ CURSOR_API_KEY: {'*' * 8}")
        return True
    else:
        print("❌ CURSOR_API_KEY not found in environment variables")
        print("💡 Please ensure CURSOR_API_KEY is set in your Codex environment settings")
        print("💡 The key should be configured as a secret in your Codex environment")

        # Try to continue anyway - the Cursor client will handle the error
        print("⚠️ Continuing without API key validation - Cursor client will handle authentication")
        return True


async def start_cursor_integration():
    """Start all Cursor integration components."""

    print("🚀 STARTING CURSOR INTEGRATION")
    print("=" * 50)
    print("Setting up Cursor IDE for this task...")
    print()

    try:
        # Import Cursor components
        from cursor import (
            start_cursor_auto_invocation,
            get_auto_invoker,
            validate_cursor_compliance,
        )
        from knowledge.auto_loader import start_knowledge_auto_loading
        from mobile.mobile_app import start_mobile_app
        from knowledge.brain_blocks_integration import start_brain_blocks_integration

        print("✅ Cursor components imported successfully")

        # Start Cursor auto-invocation
        print("🔄 Starting Cursor auto-invocation...")
        await start_cursor_auto_invocation([Path(".")])
        print("✅ Cursor auto-invocation started")

        # Start knowledge integration
        print("📚 Starting knowledge integration...")
        await start_knowledge_auto_loading()
        print("✅ Knowledge integration started")

        # Start mobile control
        print("📱 Starting mobile control...")
        await start_mobile_app()
        print("✅ Mobile control started")

        # Start brain blocks integration
        print("🧠 Starting brain blocks integration...")
        await start_brain_blocks_integration()
        print("✅ Brain blocks integration started")

        # Validate compliance
        print("✅ Validating Cursor compliance...")
        try:
            compliance = validate_cursor_compliance()
            print(f"✅ Cursor compliance: {compliance}")
        except Exception as e:
            print(f"⚠️ Compliance check: {e}")

        # Get auto-invoker stats
        print("📊 Getting auto-invoker status...")
        auto_invoker = get_auto_invoker()
        stats = auto_invoker.get_rule_stats()
        print(f"✅ Auto-invoker: {stats['total_rules']} rules, {stats['enabled_rules']} enabled")

        print("\n🎉 CURSOR INTEGRATION STARTUP COMPLETE!")
        print("✅ Cursor IDE is now active and will be used for all coding tasks")
        print("✅ Knowledge systems are loaded and ready")
        print("✅ Mobile control is available")
        print("✅ Brain blocks are integrated")
        print("✅ All systems are operational")

        return True

    except Exception as e:
        print(f"❌ Error starting Cursor integration: {e}")
        print("💡 Please check your Cursor API configuration")
        return False


async def query_knowledge_systems():
    """Query knowledge systems for context."""

    print("📚 Querying Knowledge Systems...")

    try:
        from knowledge.auto_loader import get_knowledge_entries
        from knowledge.brain_blocks_integration import query_brain_blocks

        # Query knowledge entries
        knowledge_entries = await get_knowledge_entries()
        print(f"📚 Loaded {len(knowledge_entries)} knowledge entries")

        # Query brain blocks
        brain_blocks = await query_brain_blocks()
        print(f"🧠 Loaded {len(brain_blocks)} brain blocks")

        return knowledge_entries, brain_blocks

    except Exception as e:
        print(f"⚠️ Knowledge query error: {e}")
        return [], []


async def setup_mobile_control():
    """Setup mobile control for goal management."""

    print("📱 Setting up Mobile Control...")

    try:
        from mobile.mobile_app import create_goal, get_goals

        # Create initial goal
        goal = await create_goal(
            title="Codex Task Execution",
            description="Execute coding task using Cursor IDE",
            priority="high",
        )

        # Get goals
        goals = await get_goals()
        print(f"📱 Active goals: {len(goals)}")

        return goal

    except Exception as e:
        print(f"⚠️ Mobile control error: {e}")
        return None


def enforce_cursor_usage():
    """Enforce Cursor usage for all coding tasks."""

    print("🚨 Enforcing Cursor Usage...")

    try:
        from cursor.enforcement import enforce_cursor_integration, validate_cursor_compliance

        # Enforce Cursor integration
        enforce_cursor_integration()
        print("✅ Cursor integration enforced")

        # Validate compliance
        compliance = validate_cursor_compliance()
        print(f"✅ Cursor compliance: {compliance}")

        if compliance < 100:
            print(f"⚠️ Warning: Compliance is {compliance}% - should be 100%")

        return True

    except Exception as e:
        print(f"❌ Cursor enforcement error: {e}")
        return False


async def main():
    """Main startup function."""

    print("🎯 CODEX CURSOR STARTUP")
    print("=" * 50)
    print("Automatically setting up Cursor IDE for new task...")
    print()

    # Check environment (but don't fail if not perfect)
    check_environment_variables()
    print("✅ Environment check completed")

    # Start Cursor integration
    try:
        if not await start_cursor_integration():
            print("⚠️ Cursor integration had issues, but continuing...")
    except Exception as e:
        print(f"⚠️ Cursor integration error: {e}")
        print("⚠️ Continuing with limited Cursor functionality...")

    # Query knowledge systems
    try:
        knowledge_entries, brain_blocks = await query_knowledge_systems()
        print(f"✅ Knowledge systems: {len(knowledge_entries)} entries, {len(brain_blocks)} blocks")
    except Exception as e:
        print(f"⚠️ Knowledge systems error: {e}")
        knowledge_entries, brain_blocks = [], []

    # Setup mobile control
    try:
        _goal = await setup_mobile_control()
        print("✅ Mobile control setup completed")
    except Exception as e:
        print(f"⚠️ Mobile control error: {e}")

    # Enforce Cursor usage
    try:
        if not enforce_cursor_usage():
            print("⚠️ Cursor enforcement had issues, but continuing...")
    except Exception as e:
        print(f"⚠️ Cursor enforcement error: {e}")
        print("⚠️ Continuing with limited enforcement...")

    print("\n🎉 CODEX CURSOR STARTUP COMPLETE!")
    print("✅ Cursor IDE integration attempted")
    print("✅ Knowledge systems queried")
    print("✅ Mobile control setup attempted")
    print("✅ Brain blocks integration attempted")
    print("✅ Cursor usage enforcement attempted")
    print("✅ All systems operational (with potential limitations)")
    print("\n🚀 Ready to start coding with Cursor IDE!")
    print("\n💡 Note: Some Cursor features may be limited if API key is not properly configured")

    return True


if __name__ == "__main__":
    asyncio.run(main())
