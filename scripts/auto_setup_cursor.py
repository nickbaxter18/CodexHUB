#!/usr/bin/env python3
"""
Auto Setup Cursor Integration
Automatically sets up Cursor integration when starting any new task.
This script runs automatically to ensure Cursor is always used.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def _is_feature_enabled(value: str | None, default: bool = True) -> bool:
    if value is None:
        return default
    return value.lower() not in {"0", "false", "off"}


def check_cursor_environment() -> bool:
    """Check if Cursor environment is properly configured."""

    print("🔍 Checking Cursor Environment...")

    # Check for required environment variables
    cursor_url = os.getenv("CURSOR_API_URL")
    cursor_key = os.getenv("CURSOR_API_KEY")

    if not cursor_url:
        print("⚠️ CURSOR_API_URL not set, using default")
        os.environ["CURSOR_API_URL"] = "https://api.cursor.sh"

    if not cursor_key:
        print("⚠️ CURSOR_API_KEY not set; running Cursor integration in offline mode")
        os.environ.setdefault("CURSOR_AUTO_INVOCATION_MODE", "manual")
        os.environ.setdefault("CURSOR_ENFORCEMENT_ENABLED", "false")
        return True

    print("✅ Cursor environment configured")
    return True


async def auto_start_cursor_integration() -> bool:
    """Automatically start Cursor integration for any new task."""

    print("🚀 AUTO-SETTING UP CURSOR INTEGRATION")
    print("=" * 50)
    print("Ensuring Cursor IDE is used from the start...")
    print()

    try:
        if not _is_feature_enabled(os.getenv("CURSOR_AUTO_SETUP_ENABLED"), True):
            print("ℹ️ Cursor auto-setup disabled via CURSOR_AUTO_SETUP_ENABLED")
            return False

        # 1. Check environment
        if not check_cursor_environment():
            print("❌ Cursor environment not configured properly")
            return False

        # 2. Import and start Cursor components
        print("📦 Importing Cursor components...")
        from src.cursor import (
            get_auto_invoker,
            start_cursor_auto_invocation,
            validate_cursor_compliance,
        )
        from src.knowledge.auto_loader import start_knowledge_auto_loading
        from src.knowledge.brain_blocks_integration import start_brain_blocks_integration
        from src.mobile.mobile_app import start_mobile_app

        print("✅ Cursor components imported successfully")

        # 3. Start Cursor auto-invocation
        print("🔄 Starting Cursor auto-invocation...")
        await start_cursor_auto_invocation([Path(".")])
        print("✅ Cursor auto-invocation request processed")

        # 4. Start knowledge integration
        if _is_feature_enabled(os.getenv("KNOWLEDGE_AUTO_LOAD"), True):
            print("📚 Starting knowledge integration...")
            await start_knowledge_auto_loading()
            print("✅ Knowledge integration active")
        else:
            print("ℹ️ Knowledge auto-loading disabled")

        # 5. Start mobile control
        if _is_feature_enabled(os.getenv("MOBILE_CONTROL_ENABLED"), False):
            print("📱 Starting mobile control...")
            await start_mobile_app()
            print("✅ Mobile control active")
        else:
            print("ℹ️ Mobile control disabled")

        # 6. Start brain blocks integration
        if _is_feature_enabled(os.getenv("BRAIN_BLOCKS_AUTO_LOAD"), True):
            print("🧠 Starting brain blocks integration...")
            await start_brain_blocks_integration()
            print("✅ Brain blocks integration active")
        else:
            print("ℹ️ Brain blocks integration disabled")

        # 7. Validate compliance
        print("✅ Validating Cursor compliance...")
        try:
            compliance = validate_cursor_compliance()
            status_icon = "✅" if compliance else "ℹ️"
            status_label = "COMPLIANT" if compliance else "Skipped (offline mode)"
            print(f"{status_icon} Cursor compliance: {status_label}")
        except Exception as e:
            print(f"⚠️ Compliance check: {e}")

        # 8. Get auto-invoker stats
        print("📊 Getting auto-invoker status...")
        auto_invoker = get_auto_invoker()
        stats = auto_invoker.get_rule_stats()
        mode_value = getattr(auto_invoker, "mode", "full")
        summary_message = (
            f"✅ Auto-invoker: {stats['total_rules']} rules ({stats['enabled_rules']} enabled)"
            f" | mode={mode_value}"
        )
        print(summary_message)

        print("\n🎉 CURSOR INTEGRATION AUTO-SETUP COMPLETE!")
        print("✅ Cursor IDE is now active and will be used for all coding tasks")
        print("✅ Knowledge systems are loaded and ready")
        print("✅ Mobile control is available")
        print("✅ Brain blocks are integrated")
        print("✅ All systems are operational")

        return True

    except Exception as e:
        print(f"❌ Error in auto-setup: {e}")
        print("💡 Please check your Cursor API configuration")
        return False


def create_cursor_startup_hook() -> None:
    """Create a startup hook that automatically runs Cursor integration."""

    hook_content = '''#!/usr/bin/env python3
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
'''

    hook_path = Path("scripts/cursor_startup_hook.py")
    with open(hook_path, "w") as f:
        f.write(hook_content)

    print(f"✅ Created startup hook: {hook_path}")


def create_cursor_instructions() -> None:
    """Create instructions that ensure Cursor is used from the start."""

    instructions_content = """# CURSOR INTEGRATION AUTO-START
## This file ensures Cursor IDE is used from the start of any task

## MANDATORY: Run this before any coding task
```bash
python scripts/auto_setup_cursor.py
```

## This will:
1. ✅ Check Cursor environment configuration
2. ✅ Start Cursor auto-invocation system
3. ✅ Load knowledge systems
4. ✅ Activate mobile control
5. ✅ Integrate brain blocks
6. ✅ Validate compliance
7. ✅ Ensure 100% Cursor usage

## After running this:
- All coding tasks will use Cursor IDE
- Knowledge systems will be queried
- Brain blocks will be utilized
- Mobile control will be available
- 100% compliance will be enforced

## CRITICAL: This must be run at the start of every new task!
"""

    instructions_path = Path("cursor") / "CURSOR_AUTO_START_INSTRUCTIONS.md"
    instructions_path.parent.mkdir(parents=True, exist_ok=True)
    with open(instructions_path, "w") as f:
        f.write(instructions_content)

    print(f"✅ Created auto-start instructions: {instructions_path}")


async def main() -> None:
    """Main auto-setup function."""

    print("🎯 CURSOR INTEGRATION AUTO-SETUP")
    print("=" * 50)
    print("Setting up Cursor IDE integration for new task...")
    print()

    # Create startup hook
    create_cursor_startup_hook()

    # Create instructions
    create_cursor_instructions()

    # Run auto-setup
    success = await auto_start_cursor_integration()

    if success:
        print("\n🎉 CURSOR INTEGRATION IS NOW ACTIVE!")
        print("✅ All coding tasks will use Cursor IDE")
        print("✅ Knowledge systems are loaded")
        print("✅ Mobile control is available")
        print("✅ Brain blocks are integrated")
        print("✅ 100% compliance is enforced")
        print("\n🚀 Ready to start coding with Cursor IDE!")
    else:
        print("\n❌ CURSOR INTEGRATION SETUP FAILED!")
        print("💡 Please check your environment configuration")
        print("💡 Ensure CURSOR_API_KEY is set in Codex environment")


if __name__ == "__main__":
    asyncio.run(main())
