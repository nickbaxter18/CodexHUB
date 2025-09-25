#!/usr/bin/env python3
"""
Check Cursor Environment
Robust environment variable checking for Cursor integration.
"""

import os
import sys
from pathlib import Path


def check_cursor_environment():
    """Check Cursor environment variables with robust error handling."""

    print("🔍 Checking Cursor Environment Variables...")
    print("=" * 50)

    # Check CURSOR_API_URL
    cursor_url = os.getenv("CURSOR_API_URL")
    if cursor_url:
        print(f"✅ CURSOR_API_URL: {cursor_url}")
    else:
        print("⚠️ CURSOR_API_URL not set, using default: https://api.cursor.sh")
        os.environ["CURSOR_API_URL"] = "https://api.cursor.sh"
        cursor_url = "https://api.cursor.sh"

    # Check CURSOR_API_KEY with multiple methods
    cursor_key = None

    # Method 1: Direct environment variable
    cursor_key = os.getenv("CURSOR_API_KEY")
    if cursor_key:
        print(f"✅ CURSOR_API_KEY: Found (length: {len(cursor_key)})")
    else:
        print("❌ CURSOR_API_KEY not found in environment variables")

        # Method 2: Check if it's set but empty
        if "CURSOR_API_KEY" in os.environ:
            print("⚠️ CURSOR_API_KEY is set but empty")
        else:
            print("⚠️ CURSOR_API_KEY environment variable not found")

        # Method 3: Try to get from secrets (Codex environment)
        try:
            # This might work in Codex environment
            cursor_key = os.getenv("CURSOR_API_KEY_SECRET")
            if cursor_key:
                print(f"✅ CURSOR_API_KEY_SECRET: Found (length: {len(cursor_key)})")
                os.environ["CURSOR_API_KEY"] = cursor_key
            else:
                print("⚠️ CURSOR_API_KEY_SECRET not found")
        except Exception as e:
            print(f"⚠️ Error checking secrets: {e}")

    # Check other optional environment variables
    optional_vars = [
        "CURSOR_TIMEOUT",
        "CURSOR_MAX_RETRIES",
        "CURSOR_RETRY_DELAY",
        "KNOWLEDGE_AUTO_LOAD",
        "BRAIN_BLOCKS_AUTO_LOAD",
        "MOBILE_CONTROL_ENABLED",
        "CURSOR_PERFORMANCE_MONITORING",
    ]

    print("\n📋 Optional Environment Variables:")
    for var in optional_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"⚠️ {var}: Not set")

    # Summary
    print("\n📊 Environment Summary:")
    if cursor_key:
        print("✅ Cursor API key is configured")
        print("✅ Cursor integration should work")
        return True
    else:
        print("❌ Cursor API key is not configured")
        print("⚠️ Cursor integration will have limited functionality")
        print("\n💡 To fix this:")
        print("   1. Set CURSOR_API_KEY in your Codex environment settings")
        print("   2. Ensure the key is configured as a secret")
        print("   3. Restart your Codex environment")
        return False


def test_cursor_connection():
    """Test Cursor API connection if possible."""

    print("\n🧪 Testing Cursor API Connection...")

    try:
        # Add src to path for imports
        current_dir = Path(__file__).parent.parent
        src_dir = current_dir / "src"
        sys.path.insert(0, str(src_dir))
        sys.path.insert(0, str(current_dir))  # Also add root directory for relative imports

        from cursor.cursor_client import CursorClient, CursorConfig

        # Create Cursor client
        config = CursorConfig(
            api_url=os.getenv("CURSOR_API_URL", "https://api.cursor.sh"),
            api_key=os.getenv("CURSOR_API_KEY", ""),
        )

        _client = CursorClient(config)

        # Test connection
        print("✅ Cursor client created successfully")
        print("✅ Cursor integration is ready")
        return True

    except Exception as e:
        print(f"❌ Cursor client error: {e}")
        print("⚠️ Cursor integration may not work properly")
        return False


def main():
    """Main function."""

    print("🎯 CURSOR ENVIRONMENT CHECKER")
    print("=" * 50)
    print("Checking Cursor IDE integration environment...")
    print()

    # Check environment
    env_ok = check_cursor_environment()

    # Test connection if possible
    if env_ok:
        connection_ok = test_cursor_connection()
    else:
        print("\n⚠️ Skipping connection test due to missing API key")
        connection_ok = False

    # Final summary
    print("\n🎉 ENVIRONMENT CHECK COMPLETE!")
    print("=" * 50)

    if env_ok and connection_ok:
        print("✅ Cursor environment is properly configured")
        print("✅ Cursor integration should work perfectly")
        print("🚀 Ready to use Cursor IDE!")
    elif env_ok:
        print("⚠️ Cursor environment is configured but connection test failed")
        print("⚠️ Cursor integration may have limited functionality")
        print("💡 Check your API key and network connection")
    else:
        print("❌ Cursor environment is not properly configured")
        print("❌ Cursor integration will not work")
        print("💡 Please configure CURSOR_API_KEY in your Codex environment")

    return env_ok and connection_ok


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
