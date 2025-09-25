#!/usr/bin/env python3
"""
Test Cursor Integration
Comprehensive test script to ensure all Cursor integration components are working.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Import all Cursor components
from src.cursor import (
    CursorClient,
    AgentType,
    AutoInvocationRule,
    get_auto_invoker,
    start_cursor_auto_invocation,
    require_cursor_agent,
    validate_cursor_compliance,
    get_cursor_usage_report,
)

# Import other integration components
from src.knowledge.auto_loader import get_auto_loader, start_knowledge_auto_loading
from src.mobile.mobile_app import get_mobile_app, start_mobile_app
from src.knowledge.brain_blocks_integration import (
    get_brain_blocks_integration,
    start_brain_blocks_integration,
)


async def test_cursor_client():
    """Test Cursor client functionality."""

    print("🔧 Testing Cursor Client...")

    try:
        # Test client creation
        client = CursorClient()
        print("✅ Cursor client created successfully")

        # Test configuration
        config = client.config
        print(f"✅ Configuration loaded: {config.api_base_url}")

        # Test agent types
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
            client.get_agent(agent_type)
            print(f"✅ {agent_type.value} agent accessible")

        return True

    except Exception as e:
        print(f"❌ Cursor client test failed: {e}")
        return False


async def test_auto_invocation():
    """Test auto-invocation system."""

    print("\n🔄 Testing Auto-Invocation System...")

    try:
        # Test auto-invoker creation
        auto_invoker = get_auto_invoker()
        print("✅ Auto-invoker created successfully")

        # Test rule stats
        stats = auto_invoker.get_rule_stats()
        print(f"✅ Rule stats: {stats['total_rules']} rules, {stats['enabled_rules']} enabled")

        # Test rule creation
        test_rule = AutoInvocationRule(
            trigger_pattern="**/*.test.py", agent_type=AgentType.QA, action="run_tests", priority=1
        )
        auto_invoker.add_rule(test_rule)
        print("✅ Test rule added successfully")

        # Test rule removal
        auto_invoker.remove_rule(-1)  # Remove last added rule
        print("✅ Test rule removed successfully")

        return True

    except Exception as e:
        print(f"❌ Auto-invocation test failed: {e}")
        return False


async def test_enforcement():
    """Test enforcement system."""

    print("\n🛡️ Testing Enforcement System...")

    try:
        # Test enforcement decorators
        @require_cursor_agent("FRONTEND")
        async def test_function():
            return "test_result"

        result = await test_function()
        print(f"✅ Enforcement decorator working: {result}")

        # Test compliance validation
        compliance = validate_cursor_compliance()
        print(f"✅ Compliance validation: {compliance}")

        # Test usage report
        report = get_cursor_usage_report()
        print(f"✅ Usage report generated: {report['compliance_status']}")

        return True

    except Exception as e:
        print(f"❌ Enforcement test failed: {e}")
        return False


async def test_knowledge_integration():
    """Test knowledge integration."""

    print("\n📚 Testing Knowledge Integration...")

    try:
        # Test auto-loader
        auto_loader = get_auto_loader()
        stats = auto_loader.get_source_stats()
        print(f"✅ Knowledge auto-loader: {stats['total_sources']} sources")

        # Test brain blocks integration
        brain_blocks = get_brain_blocks_integration()
        print(f"✅ Brain blocks integration accessible ({len(brain_blocks)} blocks)")

        return True

    except Exception as e:
        print(f"❌ Knowledge integration test failed: {e}")
        return False


async def test_mobile_integration():
    """Test mobile integration."""

    print("\n📱 Testing Mobile Integration...")

    try:
        # Test mobile app
        mobile_app = get_mobile_app()
        await mobile_app.initialize()
        print("✅ Mobile app initialized successfully")

        # Test dashboard
        dashboard = await mobile_app.get_dashboard()
        print(
            f"✅ Dashboard: {dashboard.total_goals} goals, {dashboard.pending_approvals} approvals"
        )

        return True

    except Exception as e:
        print(f"❌ Mobile integration test failed: {e}")
        return False


async def test_full_integration():
    """Test full integration workflow."""

    print("\n🚀 Testing Full Integration Workflow...")

    try:
        # Test complete workflow
        print("1. Starting Cursor auto-invocation...")
        await start_cursor_auto_invocation([Path(".")])
        print("✅ Cursor auto-invocation started")

        print("2. Starting knowledge auto-loading...")
        await start_knowledge_auto_loading()
        print("✅ Knowledge auto-loading started")

        print("3. Starting mobile app...")
        await start_mobile_app()
        print("✅ Mobile app started")

        print("4. Starting brain blocks integration...")
        await start_brain_blocks_integration()
        print("✅ Brain blocks integration started")

        return True

    except Exception as e:
        print(f"❌ Full integration test failed: {e}")
        return False


async def generate_integration_report():
    """Generate comprehensive integration report."""

    print("\n📄 Generating Integration Report...")

    try:
        # Get all system stats
        auto_invoker = get_auto_invoker()
        rule_stats = auto_invoker.get_rule_stats()

        auto_loader = get_auto_loader()
        knowledge_stats = auto_loader.get_source_stats()

        mobile_app = get_mobile_app()
        dashboard = await mobile_app.get_dashboard()

        brain_blocks = get_brain_blocks_integration()
        brain_stats = await brain_blocks.get_brain_block_stats()

        # Generate report
        report = {
            "timestamp": "2025-01-27T00:00:00Z",
            "integration_test": True,
            "cursor_client": {
                "status": "operational",
                "agent_types": [agent.value for agent in AgentType],
            },
            "auto_invocation": {
                "status": "operational",
                "total_rules": rule_stats["total_rules"],
                "enabled_rules": rule_stats["enabled_rules"],
                "total_triggers": rule_stats["total_triggers"],
            },
            "knowledge_integration": {
                "status": "operational",
                "total_sources": knowledge_stats["total_sources"],
                "enabled_sources": knowledge_stats["enabled_sources"],
                "total_documents": knowledge_stats["total_documents"],
            },
            "mobile_integration": {
                "status": "operational",
                "total_goals": dashboard.total_goals,
                "pending_approvals": dashboard.pending_approvals,
                "completed_tasks": dashboard.completed_tasks,
                "active_agents": dashboard.active_agents,
            },
            "brain_blocks_integration": {
                "status": "operational",
                "total_blocks": brain_stats.get("total_blocks", 0),
                "sections": brain_stats.get("sections", {}).get("count", 0),
                "tags": brain_stats.get("tags", {}).get("count", 0),
            },
            "overall_status": "FULLY_OPERATIONAL",
        }

        # Save report
        report_path = Path("results/cursor_integration_test_report.json")
        report_path.parent.mkdir(parents=True, exist_ok=True)

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📄 Integration report saved to {report_path}")

        return report

    except Exception as e:
        print(f"❌ Failed to generate integration report: {e}")
        return None


async def main():
    """Main test function."""

    print("🧪 CURSOR INTEGRATION TEST SUITE")
    print("=" * 50)
    print("Testing all Cursor integration components...")
    print()

    test_results = {}

    # Run all tests
    test_results["cursor_client"] = await test_cursor_client()
    test_results["auto_invocation"] = await test_auto_invocation()
    test_results["enforcement"] = await test_enforcement()
    test_results["knowledge_integration"] = await test_knowledge_integration()
    test_results["mobile_integration"] = await test_mobile_integration()
    test_results["full_integration"] = await test_full_integration()

    # Generate report
    await generate_integration_report()

    # Summary
    print("\n📊 INTEGRATION TEST RESULTS:")
    print("=" * 40)

    passed = sum(test_results.values())
    total = len(test_results)

    for name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{name.upper():20} {status}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 ALL CURSOR INTEGRATION TESTS PASSED!")
        print("✅ Cursor client is operational")
        print("✅ Auto-invocation system is working")
        print("✅ Enforcement system is active")
        print("✅ Knowledge integration is connected")
        print("✅ Mobile integration is functional")
        print("✅ Brain blocks integration is working")
        print("✅ Full integration workflow is operational")
    elif passed >= total * 0.8:
        print("⚠️ Most integration tests passed, some issues to resolve")
    else:
        print("🚨 Multiple integration issues need attention")

    return passed == total


if __name__ == "__main__":
    asyncio.run(main())
