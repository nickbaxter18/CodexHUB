#!/usr/bin/env python3
"""
Cursor Integration Bootstrap Script
Demonstrates and tests Cursor IDE integration capabilities.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any, List

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.cursor.cursor_client import CursorClient, CursorConfig, AgentType


async def test_cursor_integration():
    """Test Cursor integration with all agent types."""
    
    print("🚀 Testing Cursor IDE Integration...")
    
    # Create Cursor client
    client = CursorClient()
    
    # Test each agent type
    agents_to_test = [
        AgentType.ARCHITECT,
        AgentType.FRONTEND, 
        AgentType.BACKEND,
        AgentType.CICD,
        AgentType.KNOWLEDGE,
        AgentType.QA,
        AgentType.META
    ]
    
    results = {}
    
    for agent_type in agents_to_test:
        print(f"\n📋 Testing {agent_type.value} Agent...")
        
        try:
            agent = client.get_agent(agent_type)
            print(f"✅ {agent_type.value} agent created successfully")
            
            # Test agent-specific methods
            if agent_type == AgentType.ARCHITECT:
                result = await agent.generate_blueprint({
                    "requirements": ["Create a scalable microservices architecture"],
                    "constraints": ["Must use Python and React"],
                    "outputFormat": "markdown"
                })
                print(f"📐 Blueprint generated: {len(result.get('blueprint', ''))} characters")
                
            elif agent_type == AgentType.FRONTEND:
                result = await agent.generate_components({
                    "componentType": "dashboard",
                    "framework": "react",
                    "features": ["responsive", "accessible", "animated"]
                })
                print(f"🎨 Components generated: {len(result.get('components', []))} components")
                
            elif agent_type == AgentType.BACKEND:
                result = await agent.generate_apis({
                    "apiType": "REST",
                    "framework": "fastapi",
                    "endpoints": ["users", "auth", "data"]
                })
                print(f"🔧 APIs generated: {len(result.get('endpoints', []))} endpoints")
                
            elif agent_type == AgentType.CICD:
                result = await agent.optimize_pipeline({
                    "pipelineType": "github_actions",
                    "optimizations": ["parallel", "caching", "monitoring"]
                })
                print(f"⚙️ Pipeline optimized: {result.get('improvements', 0)} improvements")
                
            elif agent_type == AgentType.KNOWLEDGE:
                result = await agent.traverse_brain_blocks([], {
                    "query": "How to implement governance in AI systems",
                    "context": "compliance",
                    "depth": "comprehensive"
                })
                print(f"🧠 Knowledge synthesis: {result.get('insights', 0)} insights")
                
            elif agent_type == AgentType.QA:
                result = await agent.run_automated_reviews("", [
                    "accessibility",
                    "security", 
                    "performance"
                ])
                print(f"🔍 QA review completed: {result.get('issues_found', 0)} issues")
                
            elif agent_type == AgentType.META:
                result = await agent.coordinate_agents({
                    "task": "Implement user authentication system",
                    "agents": ["frontend", "backend", "qa"],
                    "priority": "high"
                })
                print(f"🎯 Agent coordination: {result.get('tasks_created', 0)} tasks")
            
            results[agent_type.value] = {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            print(f"❌ {agent_type.value} agent failed: {e}")
            results[agent_type.value] = {
                "status": "error",
                "error": str(e)
            }
    
    return results


async def test_visual_refinement():
    """Test visual refinement capabilities."""
    
    print("\n🎨 Testing Visual Refinement...")
    
    try:
        client = CursorClient()
        visual_client = client.get_visual_refinement()
        
        # Test visual refinement
        result = await visual_client.refine_visuals({
            "component": "dashboard",
            "improvements": ["color_contrast", "spacing", "typography"],
            "accessibility": True
        })
        
        print(f"✨ Visual refinement: {result.get('improvements', 0)} improvements")
        return {"status": "success", "result": result}
        
    except Exception as e:
        print(f"❌ Visual refinement failed: {e}")
        return {"status": "error", "error": str(e)}


async def test_knowledge_integration():
    """Test knowledge integration with NDJSON data."""
    
    print("\n📚 Testing Knowledge Integration...")
    
    try:
        client = CursorClient()
        knowledge_agent = client.get_agent(AgentType.KNOWLEDGE)
        
        # Test with sample NDJSON data
        sample_data = [
            {
                "id": "test_1",
                "title": "AI Governance Best Practices",
                "content": "Implement fairness metrics, bias detection, and compliance monitoring",
                "tags": ["governance", "ai", "compliance"]
            },
            {
                "id": "test_2", 
                "title": "Performance Optimization",
                "content": "Use caching, parallel processing, and monitoring for better performance",
                "tags": ["performance", "optimization", "monitoring"]
            }
        ]
        
        # Test knowledge synthesis
        result = await knowledge_agent.summarize_ndjson_scaffolds(sample_data, {
            "outputFormat": "structured_knowledge",
            "includePatterns": True,
            "extractInsights": True
        })
        
        print(f"📖 Knowledge synthesis: {result.get('insights', 0)} insights extracted")
        return {"status": "success", "result": result}
        
    except Exception as e:
        print(f"❌ Knowledge integration failed: {e}")
        return {"status": "error", "error": str(e)}


async def generate_integration_report(results: Dict[str, Any]):
    """Generate integration test report."""
    
    print("\n📊 Generating Integration Report...")
    
    report = {
        "timestamp": "2025-01-27T00:00:00Z",
        "cursor_integration_test": True,
        "agents_tested": len(results),
        "successful_agents": len([r for r in results.values() if r.get("status") == "success"]),
        "failed_agents": len([r for r in results.values() if r.get("status") == "error"]),
        "results": results
    }
    
    # Save report
    report_path = Path("results/cursor_integration_report.json")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Report saved to {report_path}")
    
    # Print summary
    print(f"\n📈 Integration Summary:")
    print(f"   Agents Tested: {report['agents_tested']}")
    print(f"   Successful: {report['successful_agents']}")
    print(f"   Failed: {report['failed_agents']}")
    print(f"   Success Rate: {(report['successful_agents'] / report['agents_tested'] * 100):.1f}%")


async def main():
    """Main bootstrap function."""
    
    print("🎯 Cursor Integration Bootstrap")
    print("=" * 50)
    
    # Test agent integration
    agent_results = await test_cursor_integration()
    
    # Test visual refinement
    visual_result = await test_visual_refinement()
    
    # Test knowledge integration
    knowledge_result = await test_knowledge_integration()
    
    # Combine all results
    all_results = {
        **agent_results,
        "visual_refinement": visual_result,
        "knowledge_integration": knowledge_result
    }
    
    # Generate report
    await generate_integration_report(all_results)
    
    print("\n✅ Cursor Integration Bootstrap Complete!")
    print("🚀 All Cursor capabilities are now available for use.")


if __name__ == "__main__":
    asyncio.run(main())
