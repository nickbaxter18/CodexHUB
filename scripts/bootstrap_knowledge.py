#!/usr/bin/env python3
"""
Knowledge Agent Bootstrap Script
Auto-loads NDJSON knowledge sources into the Knowledge agent for immediate use.
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from agents.specialist_agents import KnowledgeAgent, KnowledgeDocument
from qa.qa_engine import QAEngine
from qa.qa_event_bus import QAEventBus


def load_ndjson_files(agent: KnowledgeAgent, data_dir: Path) -> int:
    """Load all NDJSON files from the data directory into the knowledge agent."""
    total_loaded = 0

    # Find all NDJSON files
    ndjson_files = list(data_dir.glob("*.ndjson"))

    if not ndjson_files:
        print(f"No NDJSON files found in {data_dir}")
        return 0

    print(f"Found {len(ndjson_files)} NDJSON files to load...")

    for file_path in ndjson_files:
        try:
            loaded_count = agent.load_ndjson(file_path)
            total_loaded += loaded_count
            print(f"Loaded {loaded_count} documents from {file_path.name}")
        except Exception as e:
            print(f"Error loading {file_path.name}: {e}")

    return total_loaded


def create_knowledge_agent() -> KnowledgeAgent:
    """Create and configure a Knowledge agent with basic QA setup."""
    # Create minimal QA components
    event_bus = QAEventBus()

    # Create a minimal QA engine (in production, load from config)
    from qa.qa_engine import QARules

    rules = QARules(version="1.0", agents={}, macros={})
    qa_engine = QAEngine(rules)

    return KnowledgeAgent(qa_engine, event_bus)


def main():
    """Bootstrap the knowledge agent with available NDJSON data."""
    print("🚀 Bootstrapping Knowledge Agent...")

    # Create knowledge agent
    agent = create_knowledge_agent()

    # Load NDJSON files from common locations
    data_dirs = [
        Path("."),  # Current directory
        Path("docs"),
        Path("data"),
        Path("knowledge"),
    ]

    total_loaded = 0
    for data_dir in data_dirs:
        if data_dir.exists():
            loaded = load_ndjson_files(agent, data_dir)
            total_loaded += loaded

    print(f"✅ Knowledge Agent bootstrapped with {total_loaded} documents")
    print(f"📊 Agent has {len(agent.documents())} total documents")

    # Test the agent with a sample query
    if total_loaded > 0:
        print("\n🧪 Testing Knowledge Agent...")
        try:
            result = agent.perform_task(
                {"action": "query", "payload": {"query": "governance", "limit": 3}}
            )
            print(f"Query results: {result['metrics']['results_returned']} documents found")
        except Exception as e:
            print(f"Query test failed: {e}")

    return agent


if __name__ == "__main__":
    agent = main()
