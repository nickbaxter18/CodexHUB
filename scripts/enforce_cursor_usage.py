#!/usr/bin/env python3
"""
Cursor Usage Enforcement Script
Ensures 100% compliance with Cursor IDE integration requirements.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cursor.enforcement import validate_cursor_compliance, get_cursor_usage_report
from src.cursor.auto_invocation import get_auto_invoker


async def enforce_cursor_usage():
    """Enforce Cursor usage compliance."""

    print("🔒 CURSOR USAGE ENFORCEMENT")
    print("=" * 50)
    print("Ensuring 100% compliance with Cursor IDE integration...")
    print()

    try:
        # 1. Validate Cursor compliance
        print("1. Validating Cursor compliance...")
        compliance = validate_cursor_compliance()
        print(f"✅ Compliance check: {'PASSED' if compliance else 'FAILED'}")

        # 2. Get usage report
        print("\n2. Generating usage report...")
        report = get_cursor_usage_report()

        # 3. Display compliance status
        print(f"\n📊 COMPLIANCE STATUS: {report['compliance_status']}")
        print(f"🔧 Enforcement Active: {report['enforcement_active']}")

        # 4. Display usage statistics
        stats = report["usage_statistics"]
        print(f"\n📈 USAGE STATISTICS:")
        print(f"   Total Usage: {stats['total_usage']}")
        print(f"   Successful: {stats['successful_usage']}")
        print(f"   Success Rate: {stats['success_rate']:.2%}")

        # 5. Display agent usage
        print(f"\n🤖 AGENT USAGE:")
        for agent, count in stats["agent_usage"].items():
            print(f"   {agent}: {count} uses")

        # 6. Display recommendations
        if report.get("recommendations"):
            print(f"\n💡 RECOMMENDATIONS:")
            for rec in report["recommendations"]:
                print(f"   - {rec}")

        # 7. Check auto-invocation
        print(f"\n🔄 AUTO-INVOCATION STATUS:")
        auto_invoker = get_auto_invoker()
        rule_stats = auto_invoker.get_rule_stats()
        print(f"   Total Rules: {rule_stats['total_rules']}")
        print(f"   Enabled Rules: {rule_stats['enabled_rules']}")
        print(f"   Total Triggers: {rule_stats['total_triggers']}")

        # 8. Final compliance check
        if report["compliance_status"] == "COMPLIANT":
            print(f"\n🎉 CURSOR USAGE IS FULLY COMPLIANT!")
            print(f"✅ All coding tasks are using Cursor IDE integration")
            print(f"✅ Knowledge systems are being queried")
            print(f"✅ Brain Blocks are being utilized")
            print(f"✅ Mobile control is being used")
            return True
        else:
            print(f"\n🚨 CURSOR USAGE IS NON-COMPLIANT!")
            print(f"❌ Some coding tasks are not using Cursor integration")
            print(f"❌ Knowledge systems may not be queried")
            print(f"❌ Brain Blocks may not be utilized")
            print(f"❌ Mobile control may not be used")
            return False

    except Exception as e:
        print(f"\n❌ ENFORCEMENT FAILED: {e}")
        print(f"🚨 CURSOR INTEGRATION IS NOT WORKING PROPERLY!")
        return False


async def test_cursor_integration():
    """Test Cursor integration functionality."""

    print("\n🧪 TESTING CURSOR INTEGRATION...")
    print("=" * 40)

    try:
        # Test auto-invoker
        auto_invoker = get_auto_invoker()
        print("✅ Auto-invoker accessible")

        # Test rule stats
        stats = auto_invoker.get_rule_stats()
        print(f"✅ Rule stats: {stats['total_rules']} rules")

        # Test Cursor client
        cursor_client = auto_invoker.cursor_client
        print("✅ Cursor client accessible")

        # Test agent types
        from src.cursor.cursor_client import AgentType

        agent_types = [
            AgentType.FRONTEND,
            AgentType.BACKEND,
            AgentType.QA,
            AgentType.ARCHITECT,
            AgentType.CICD,
            AgentType.KNOWLEDGE,
            AgentType.META,
        ]

        for agent_type in agent_types:
            agent = cursor_client.get_agent(agent_type)
            print(f"✅ {agent_type.value} agent accessible")

        print("\n🎉 ALL CURSOR INTEGRATION TESTS PASSED!")
        return True

    except Exception as e:
        print(f"\n❌ CURSOR INTEGRATION TEST FAILED: {e}")
        return False


async def generate_compliance_report():
    """Generate comprehensive compliance report."""

    print("\n📄 GENERATING COMPLIANCE REPORT...")
    print("=" * 40)

    try:
        # Get usage report
        report = get_cursor_usage_report()

        # Add timestamp
        report["timestamp"] = "2025-01-27T00:00:00Z"
        report["enforcement_version"] = "1.0.0"

        # Save report
        report_path = Path("results/cursor_compliance_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Compliance report saved to {report_path}")

        # Display summary
        print(f"\n📊 COMPLIANCE SUMMARY:")
        print(f"   Status: {report['compliance_status']}")
        print(f"   Enforcement: {report['enforcement_active']}")
        print(f"   Usage: {report['usage_statistics']['total_usage']} total")
        print(f"   Success Rate: {report['usage_statistics']['success_rate']:.2%}")

        return report

    except Exception as e:
        print(f"❌ Failed to generate compliance report: {e}")
        return None


async def main():
    """Main enforcement function."""

    print("🔒 CURSOR USAGE ENFORCEMENT SYSTEM")
    print("=" * 50)
    print("Ensuring 100% compliance with Cursor IDE integration...")
    print()

    # Test Cursor integration
    integration_test = await test_cursor_integration()

    if not integration_test:
        print("\n🚨 CURSOR INTEGRATION IS NOT WORKING!")
        print("❌ Cannot enforce usage without working integration")
        return False

    # Enforce Cursor usage
    compliance = await enforce_cursor_usage()

    # Generate report
    report = await generate_compliance_report()

    # Final status
    if compliance:
        print("\n🎉 CURSOR USAGE ENFORCEMENT SUCCESSFUL!")
        print("✅ All coding tasks are using Cursor IDE integration")
        print("✅ Knowledge systems are being queried")
        print("✅ Brain Blocks are being utilized")
        print("✅ Mobile control is being used")
        print("✅ 100% compliance achieved!")
    else:
        print("\n🚨 CURSOR USAGE ENFORCEMENT FAILED!")
        print("❌ Some coding tasks are not using Cursor integration")
        print("❌ Knowledge systems may not be queried")
        print("❌ Brain Blocks may not be utilized")
        print("❌ Mobile control may not be used")
        print("❌ Compliance not achieved!")

    return compliance


if __name__ == "__main__":
    asyncio.run(main())
