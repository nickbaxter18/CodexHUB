#!/usr/bin/env python3
"""
Validate Cursor Integration
Validates that all Cursor integration components are working.
"""

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
    """Validate Cursor integration."""
    
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
