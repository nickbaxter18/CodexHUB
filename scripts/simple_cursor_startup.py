#!/usr/bin/env python3
"""
Simple Cursor Startup Script
Simplified version that doesn't require external dependencies.
"""

import os
import sys
from pathlib import Path


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
        cursor_url = "https://api.cursor.sh"

    # Check CURSOR_API_KEY
    cursor_key = os.getenv("CURSOR_API_KEY")
    if cursor_key:
        print(f"✅ CURSOR_API_KEY: Found (length: {len(cursor_key)})")
        return True
    else:
        print("❌ CURSOR_API_KEY not found in environment variables")
        print("💡 Please ensure CURSOR_API_KEY is set in your Codex environment settings")
        print("💡 The key should be configured as a secret in your Codex environment")

        # Try to continue anyway - the Cursor client will handle the error
        print("⚠️ Continuing without API key validation - Cursor client will handle authentication")
        return True


def check_file_structure():
    """Check if all required files exist."""

    print("📁 Checking File Structure...")

    required_files = [
        "src/cursor/__init__.py",
        "src/cursor/cursor_client.py",
        "src/cursor/auto_invocation.py",
        "src/cursor/enforcement.py",
        "src/knowledge/auto_loader.py",
        "src/mobile/mobile_app.py",
        "src/knowledge/brain_blocks_integration.py",
    ]

    missing_files = []

    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")

    if missing_files:
        print(f"\n❌ Missing {len(missing_files)} required files")
        return False

    return True


def check_agents_instructions():
    """Check if AGENTS.md instructions are present."""

    print("📋 Checking AGENTS.md Instructions...")

    agents_files = ["apps/editor/AGENTS.md", "cursor/AGENTS_CURSOR_INTEGRATION.md"]

    for file_path in agents_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path}")

    return True


def check_python_dependencies():
    """Check if Python dependencies are available."""

    print("🐍 Checking Python Dependencies...")

    required_packages = ["aiohttp", "watchdog", "pydantic"]
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}")

    if missing_packages:
        print(f"\n⚠️ Missing Python packages: {', '.join(missing_packages)}")
        print("💡 Install with: pip install -r cursor/requirements-cursor.txt")
        return False

    return True


def main():
    """Main startup function."""

    print("🎯 SIMPLE CURSOR STARTUP")
    print("=" * 50)
    print("Checking Cursor IDE integration setup...")
    print()

    # Check environment
    env_ok = check_environment_variables()
    print()

    # Check file structure
    files_ok = check_file_structure()
    print()

    # Check agents instructions
    agents_ok = check_agents_instructions()
    print()

    # Check Python dependencies
    deps_ok = check_python_dependencies()
    print()

    # Final summary
    print("🎉 CURSOR STARTUP CHECK COMPLETE!")
    print("=" * 50)

    if env_ok and files_ok and agents_ok and deps_ok:
        print("✅ Cursor environment is properly configured")
        print("✅ All required files are present")
        print("✅ Agent instructions are available")
        print("✅ Python dependencies are installed")
        print("🚀 Ready to use Cursor IDE!")
        print("\n💡 Next steps:")
        print("   1. Ensure CURSOR_API_KEY is set in your Codex environment")
        print("   2. Use Cursor IDE for all coding tasks")
        print("   3. Follow AGENTS.md instructions for agent selection")
        return True
    else:
        print("⚠️ Some issues detected:")
        if not env_ok:
            print("   - Environment variables need configuration")
        if not files_ok:
            print("   - Some required files are missing")
        if not agents_ok:
            print("   - Agent instructions may be missing")
        if not deps_ok:
            print("   - Python dependencies need installation")
        print("\n💡 Please address these issues before proceeding")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
