#!/usr/bin/env python3
"""
Setup Cursor Integration
Ensures all Cursor integration components are properly configured and working.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


def check_environment_variables():
    """Check if required environment variables are set."""
    
    print("🔧 Checking Environment Variables...")
    
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


def check_file_structure():
    """Check if all required files exist."""
    
    print("\n📁 Checking File Structure...")
    
    required_files = [
        "src/cursor/__init__.py",
        "src/cursor/cursor_client.py",
        "src/cursor/auto_invocation.py",
        "src/cursor/enforcement.py",
        "src/knowledge/auto_loader.py",
        "src/mobile/mobile_app.py",
        "src/knowledge/brain_blocks_integration.py",
        "scripts/bootstrap_integration.py",
        "scripts/enforce_cursor_usage.py",
        "scripts/test_cursor_integration.py"
    ]
    
    missing_files = []
    
    for file_path in required_files:
        if Path(file_path).exists():
            print(f"✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"❌ {file_path}")
    
    if missing_files:
        print(f"\n❌ Missing files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    return True


def check_imports():
    """Check if all imports are working."""
    
    print("\n📦 Checking Imports...")
    
    try:
        # Test core Cursor imports
        from src.cursor import (
            CursorClient,
            CursorConfig,
            AgentType,
            CursorAutoInvoker,
            AutoInvocationRule,
            get_auto_invoker,
            start_cursor_auto_invocation,
            enforce_cursor_integration,
            require_cursor_agent,
            validate_cursor_compliance,
            get_cursor_usage_report
        )
        print("✅ Core Cursor imports working")
        
        # Test knowledge imports
        from src.knowledge.auto_loader import get_auto_loader, start_knowledge_auto_loading
        from src.knowledge.brain_blocks_integration import get_brain_blocks_integration, start_brain_blocks_integration
        print("✅ Knowledge imports working")
        
        # Test mobile imports
        from src.mobile.mobile_app import get_mobile_app, start_mobile_app
        print("✅ Mobile imports working")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def create_environment_template():
    """Create environment template file."""
    
    print("\n📝 Creating Environment Template...")
    
    template_content = """# Cursor Integration Environment Variables
# Copy these to your Codex environment settings

# Cursor API Configuration
CURSOR_API_URL=https://api.cursor.sh
CURSOR_API_KEY=your_cursor_api_key_here

# Optional Configuration
CURSOR_TIMEOUT=30
CURSOR_MAX_RETRIES=3
CURSOR_RETRY_DELAY=1.0

# Knowledge Integration
KNOWLEDGE_AUTO_LOAD=true
BRAIN_BLOCKS_AUTO_LOAD=true

# Mobile Integration
MOBILE_CONTROL_ENABLED=true
MOBILE_NOTIFICATIONS_ENABLED=true

# Performance Monitoring
CURSOR_PERFORMANCE_MONITORING=true
CURSOR_USAGE_TRACKING=true
"""
    
    template_path = Path("config/cursor_environment_template.env")
    template_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(template_path, 'w') as f:
        f.write(template_content)
    
    print(f"✅ Environment template created: {template_path}")
    return template_path


def create_integration_config():
    """Create integration configuration file."""
    
    print("\n⚙️ Creating Integration Configuration...")
    
    config = {
        "cursor_integration": {
            "enabled": True,
            "auto_invocation": True,
            "enforcement": True,
            "performance_monitoring": True
        },
        "knowledge_integration": {
            "enabled": True,
            "auto_loading": True,
            "brain_blocks": True,
            "real_time_sync": True
        },
        "mobile_integration": {
            "enabled": True,
            "notifications": True,
            "goal_management": True,
            "approval_workflows": True
        },
        "agent_configuration": {
            "frontend": {
                "enabled": True,
                "auto_trigger": True,
                "patterns": ["**/*.tsx", "**/*.jsx"]
            },
            "backend": {
                "enabled": True,
                "auto_trigger": True,
                "patterns": ["**/*.py"]
            },
            "qa": {
                "enabled": True,
                "auto_trigger": True,
                "patterns": ["**/test_*.py", "**/*.test.js"]
            },
            "architect": {
                "enabled": True,
                "auto_trigger": True,
                "patterns": ["**/*.md", "**/ARCHITECTURE.md"]
            },
            "cicd": {
                "enabled": True,
                "auto_trigger": True,
                "patterns": ["**/.github/workflows/**", "**/Dockerfile"]
            },
            "knowledge": {
                "enabled": True,
                "auto_trigger": True,
                "patterns": ["**/*.ndjson", "**/docs/**"]
            },
            "meta": {
                "enabled": True,
                "auto_trigger": True,
                "patterns": ["**/*"]
            }
        }
    }
    
    config_path = Path("config/cursor_integration_config.json")
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✅ Integration configuration created: {config_path}")
    return config_path


def create_startup_script():
    """Create startup script for Cursor integration."""
    
    print("\n🚀 Creating Startup Script...")
    
    startup_content = """#!/usr/bin/env python3
\"\"\"
Cursor Integration Startup Script
Starts all Cursor integration components.
\"\"\"

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
    \"\"\"Start all integration components.\"\"\"
    
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
"""
    
    startup_path = Path("scripts/start_cursor_integration.py")
    startup_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(startup_path, 'w') as f:
        f.write(startup_content)
    
    # Make executable
    startup_path.chmod(0o755)
    
    print(f"✅ Startup script created: {startup_path}")
    return startup_path


def create_validation_script():
    """Create validation script for Cursor integration."""
    
    print("\n✅ Creating Validation Script...")
    
    validation_content = """#!/usr/bin/env python3
\"\"\"
Cursor Integration Validation Script
Validates that all Cursor integration components are working.
\"\"\"

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cursor import (
    validate_cursor_compliance,
    get_cursor_usage_report,
    get_auto_invoker
)
from src.knowledge.auto_loader import get_auto_loader
from src.mobile.mobile_app import get_mobile_app
from src.knowledge.brain_blocks_integration import get_brain_blocks_integration


async def validate_integration():
    \"\"\"Validate Cursor integration.\"\"\"
    
    print("🔍 Validating Cursor Integration...")
    
    try:
        # Validate Cursor compliance
        print("1. Validating Cursor compliance...")
        compliance = validate_cursor_compliance()
        print(f"✅ Cursor compliance: {compliance}")
        
        # Get usage report
        print("2. Getting usage report...")
        report = get_cursor_usage_report()
        print(f"✅ Usage report: {report['compliance_status']}")
        
        # Validate auto-invoker
        print("3. Validating auto-invoker...")
        auto_invoker = get_auto_invoker()
        stats = auto_invoker.get_rule_stats()
        print(f"✅ Auto-invoker: {stats['total_rules']} rules")
        
        # Validate knowledge integration
        print("4. Validating knowledge integration...")
        auto_loader = get_auto_loader()
        knowledge_stats = auto_loader.get_source_stats()
        print(f"✅ Knowledge: {knowledge_stats['total_sources']} sources")
        
        # Validate mobile integration
        print("5. Validating mobile integration...")
        mobile_app = get_mobile_app()
        await mobile_app.initialize()
        dashboard = await mobile_app.get_dashboard()
        print(f"✅ Mobile: {dashboard.total_goals} goals")
        
        # Validate brain blocks integration
        print("6. Validating brain blocks integration...")
        brain_blocks = get_brain_blocks_integration()
        print("✅ Brain blocks integration accessible")
        
        print("🎉 All Cursor integration components validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Validation failed: {e}")
        return False


if __name__ == "__main__":
    asyncio.run(validate_integration())
"""
    
    validation_path = Path("scripts/validate_cursor_integration.py")
    validation_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(validation_path, 'w') as f:
        f.write(validation_content)
    
    # Make executable
    validation_path.chmod(0o755)
    
    print(f"✅ Validation script created: {validation_path}")
    return validation_path


def main():
    """Main setup function."""
    
    print("🔧 CURSOR INTEGRATION SETUP")
    print("=" * 50)
    print("Setting up Cursor integration components...")
    print()
    
    setup_results = {}
    
    # Check environment variables
    setup_results["environment"] = check_environment_variables()
    
    # Check file structure
    setup_results["files"] = check_file_structure()
    
    # Check imports
    setup_results["imports"] = check_imports()
    
    # Create configuration files
    setup_results["environment_template"] = create_environment_template()
    setup_results["integration_config"] = create_integration_config()
    setup_results["startup_script"] = create_startup_script()
    setup_results["validation_script"] = create_validation_script()
    
    # Summary
    print("\n📊 SETUP RESULTS:")
    print("=" * 30)
    
    for name, result in setup_results.items():
        if isinstance(result, bool):
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{name.upper():20} {status}")
        else:
            print(f"{name.upper():20} ✅ CREATED")
    
    # Final status
    if all(isinstance(r, bool) and r for r in setup_results.values() if isinstance(r, bool)):
        print("\n🎉 CURSOR INTEGRATION SETUP COMPLETE!")
        print("✅ All components are properly configured")
        print("✅ All files are in place")
        print("✅ All imports are working")
        print("✅ Configuration files created")
        print("✅ Startup and validation scripts created")
        print("\n🚀 Next steps:")
        print("1. Set your CURSOR_API_KEY in Codex environment settings")
        print("2. Run: python scripts/start_cursor_integration.py")
        print("3. Run: python scripts/validate_cursor_integration.py")
        print("4. Run: python scripts/test_cursor_integration.py")
    else:
        print("\n⚠️ Some setup issues need to be resolved")
        print("Check the failed components above and fix them")
    
    return all(isinstance(r, bool) and r for r in setup_results.values() if isinstance(r, bool))


if __name__ == "__main__":
    main()
