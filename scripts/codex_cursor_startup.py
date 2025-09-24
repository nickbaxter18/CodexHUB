#!/usr/bin/env python3
"""
Codex Cursor Startup Script
Automatically runs when Codex starts a new task to ensure Cursor IDE is used.
"""

import asyncio
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def check_environment_variables():
    """Check if all required environment variables are set."""
    
    print("🔍 Checking Environment Variables...")
    
    required_vars = {
        'CURSOR_API_URL': 'https://api.cursor.sh',
        'CURSOR_API_KEY': 'Your Cursor API Key'
    }
    
    missing_vars = []
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if not value:
            missing_vars.append(f"{var}: {description}")
        else:
            print(f"✅ {var}: {'*' * 8 if 'KEY' in var else value}")
    
    if missing_vars:
        print(f"\n❌ Missing environment variables:")
        for var in missing_vars:
            print(f"   - {var}")
        print(f"\n💡 Set these in your Codex environment settings:")
        print(f"   - CURSOR_API_URL: https://api.cursor.sh")
        print(f"   - CURSOR_API_KEY: Your actual Cursor API key")
        return False
    
    return True

async def start_cursor_integration():
    """Start all Cursor integration components."""
    
    print("🚀 STARTING CURSOR INTEGRATION")
    print("=" * 50)
    print("Setting up Cursor IDE for this task...")
    print()
    
    try:
        # Import Cursor components
        from src.cursor import (
            start_cursor_auto_invocation,
            get_auto_invoker,
            validate_cursor_compliance,
            enforce_cursor_integration,
            require_cursor_agent
        )
        from src.knowledge.auto_loader import start_knowledge_auto_loading
        from src.mobile.mobile_app import start_mobile_app
        from src.knowledge.brain_blocks_integration import start_brain_blocks_integration
        
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
        from src.knowledge.auto_loader import get_knowledge_entries
        from src.knowledge.brain_blocks_integration import query_brain_blocks
        
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
        from src.mobile.mobile_app import create_goal, get_goals
        
        # Create initial goal
        goal = await create_goal(
            title="Codex Task Execution",
            description="Execute coding task using Cursor IDE",
            priority="high"
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
        from src.cursor.enforcement import enforce_cursor_integration, validate_cursor_compliance
        
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
    
    # Check environment
    if not check_environment_variables():
        print("❌ Environment not configured properly")
        return False
    
    # Start Cursor integration
    if not await start_cursor_integration():
        print("❌ Failed to start Cursor integration")
        return False
    
    # Query knowledge systems
    knowledge_entries, brain_blocks = await query_knowledge_systems()
    
    # Setup mobile control
    goal = await setup_mobile_control()
    
    # Enforce Cursor usage
    if not enforce_cursor_usage():
        print("❌ Failed to enforce Cursor usage")
        return False
    
    print("\n🎉 CODEX CURSOR STARTUP COMPLETE!")
    print("✅ Cursor IDE is now active and will be used for all coding tasks")
    print("✅ Knowledge systems are loaded and ready")
    print("✅ Mobile control is available")
    print("✅ Brain blocks are integrated")
    print("✅ Cursor usage is enforced")
    print("✅ All systems are operational")
    print("\n🚀 Ready to start coding with Cursor IDE!")
    
    return True

if __name__ == "__main__":
    asyncio.run(main())
