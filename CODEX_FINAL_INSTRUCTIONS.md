# CODEX FINAL INSTRUCTIONS
## COMPLETE INSTRUCTIONS FOR CURSOR IDE INTEGRATION

### 🚨 **MANDATORY PROTOCOL - NO EXCEPTIONS**
**EVERY SINGLE CODING TASK MUST USE CURSOR IDE INTEGRATION**
**THESE INSTRUCTIONS ARE NON-NEGOTIABLE AND MANDATORY**

---

## 🔧 **ENVIRONMENT CONFIGURATION (ALREADY SET)**

### **✅ Required Environment Variables (Configured in Your Codex Environment):**
- `CURSOR_API_URL=https://api.cursor.sh` ✅ **CONFIGURED**
- `CURSOR_API_KEY=**********` ✅ **CONFIGURED AS SECRET**

### **✅ Additional Environment Variables to Set:**
```bash
# Knowledge Integration
KNOWLEDGE_AUTO_LOAD=true
KNOWLEDGE_NDJSON_PATHS=Brain docs cleansed .ndjson,Bundle cleansed .ndjson
KNOWLEDGE_WATCH_INTERVAL=10

# Mobile Control
MOBILE_CONTROL_ENABLED=true
MOBILE_NOTIFICATIONS_ENABLED=true
MOBILE_APP_PORT=3001

# Brain Blocks Integration
BRAIN_BLOCKS_AUTO_LOAD=true
BRAIN_BLOCKS_DATA_SOURCE=Brain docs cleansed .ndjson
BRAIN_BLOCKS_QUERY_DEPTH=comprehensive

# Performance Monitoring
CURSOR_PERFORMANCE_MONITORING=true
CURSOR_USAGE_TRACKING=true
CURSOR_COMPLIANCE_REPORTING=true

# Auto-Invocation Settings
CURSOR_AUTO_INVOCATION_ENABLED=true
CURSOR_MONITOR_INTERVAL=5
CURSOR_FILE_PATTERNS=**/*.tsx,**/*.py,**/*.md,**/*.js,**/*.ts

# Enforcement Settings
CURSOR_ENFORCEMENT_ENABLED=true
CURSOR_STRICT_MODE=true
CURSOR_COMPLIANCE_INTERVAL=3600
```

---

## 🚀 **MANDATORY STARTUP PROTOCOL**

### **STEP 1: ALWAYS START WITH CURSOR INTEGRATION**
```python
# MANDATORY: Run this at the start of EVERY task
import asyncio
import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(".") / "src"))

# MANDATORY: Start Cursor integration
async def start_cursor_integration():
    """Start all Cursor integration components."""
    
    print("🚀 STARTING CURSOR INTEGRATION")
    print("=" * 50)
    
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
    
    # 1. Start Cursor auto-invocation
    await start_cursor_auto_invocation([Path(".")])
    print("✅ Cursor auto-invocation started")
    
    # 2. Start knowledge integration
    await start_knowledge_auto_loading()
    print("✅ Knowledge integration started")
    
    # 3. Start mobile control
    await start_mobile_app()
    print("✅ Mobile control started")
    
    # 4. Start brain blocks integration
    await start_brain_blocks_integration()
    print("✅ Brain blocks integration started")
    
    # 5. Validate compliance
    compliance = validate_cursor_compliance()
    print(f"✅ Cursor compliance: {compliance}")
    
    print("🎉 CURSOR INTEGRATION ACTIVE!")
    return True

# MANDATORY: Run startup
asyncio.run(start_cursor_integration())
```

### **STEP 2: ENFORCE CURSOR USAGE FOR ALL CODING**
```python
# MANDATORY: Use this decorator for ALL coding functions
@require_cursor_agent(agent_type="FRONTEND")  # or BACKEND, QA, etc.
def generate_code():
    """All code generation must use Cursor agents."""
    pass

# MANDATORY: Validate before any coding task
def validate_cursor_usage():
    """Validate Cursor is being used."""
    try:
        enforce_cursor_integration()
        return True
    except Exception as e:
        print(f"❌ Cursor integration not active: {e}")
        return False
```

---

## 🎯 **CURSOR AGENT SELECTION PROTOCOL**

### **File Type → Agent Mapping:**
```python
# MANDATORY: Select correct agent based on file type
def select_cursor_agent(file_path: str) -> str:
    """Select Cursor agent based on file type."""
    
    if file_path.endswith(('.tsx', '.jsx', '.ts', '.js')):
        return "FRONTEND"
    elif file_path.endswith(('.py', '.pyx')):
        return "BACKEND"
    elif file_path.endswith(('.md', '.rst', '.txt')):
        return "KNOWLEDGE"
    elif file_path.endswith(('.yml', '.yaml', '.json')):
        return "CICD"
    elif 'test' in file_path.lower():
        return "QA"
    else:
        return "ARCHITECT"

# MANDATORY: Use agent selection
agent_type = select_cursor_agent(file_path)
@require_cursor_agent(agent_type=agent_type)
def process_file(file_path: str):
    """Process file with correct Cursor agent."""
    pass
```

---

## 📚 **KNOWLEDGE INTEGRATION PROTOCOL**

### **MANDATORY: Query Knowledge Systems**
```python
# MANDATORY: Query knowledge before coding
async def query_knowledge_for_context():
    """Query knowledge systems for context."""
    
    from src.knowledge.auto_loader import get_knowledge_entries
    from src.knowledge.brain_blocks_integration import query_brain_blocks
    
    # Query knowledge entries
    knowledge_entries = await get_knowledge_entries()
    print(f"📚 Loaded {len(knowledge_entries)} knowledge entries")
    
    # Query brain blocks
    brain_blocks = await query_brain_blocks()
    print(f"🧠 Loaded {len(brain_blocks)} brain blocks")
    
    return knowledge_entries, brain_blocks

# MANDATORY: Use knowledge context
knowledge_entries, brain_blocks = await query_knowledge_for_context()
```

---

## 📱 **MOBILE CONTROL PROTOCOL**

### **MANDATORY: Use Mobile Control for Goals**
```python
# MANDATORY: Use mobile control for goal management
async def manage_goals_with_mobile():
    """Manage goals through mobile control."""
    
    from src.mobile.mobile_app import create_goal, get_goals, approve_goal
    
    # Create goal
    goal = await create_goal(
        title="Code Generation Task",
        description="Generate code using Cursor IDE",
        priority="high"
    )
    
    # Get goals
    goals = await get_goals()
    print(f"📱 Active goals: {len(goals)}")
    
    # Approve goal
    await approve_goal(goal['id'])
    
    return goal
```

---

## 🧠 **BRAIN BLOCKS INTEGRATION PROTOCOL**

### **MANDATORY: Use Brain Blocks for Context**
```python
# MANDATORY: Query brain blocks for context
async def get_brain_blocks_context():
    """Get context from brain blocks."""
    
    from src.knowledge.brain_blocks_integration import (
        query_brain_blocks,
        get_sections,
        get_tags
    )
    
    # Query brain blocks
    blocks = await query_brain_blocks()
    
    # Get sections
    sections = await get_sections()
    
    # Get tags
    tags = await get_tags()
    
    print(f"🧠 Brain blocks: {len(blocks)}")
    print(f"📑 Sections: {len(sections)}")
    print(f"🏷️ Tags: {len(tags)}")
    
    return blocks, sections, tags
```

---

## 🔧 **PNPM INTEGRATION PROTOCOL**

### **MANDATORY: Use pnpm Commands**
```bash
# MANDATORY: Use pnpm commands for Cursor integration
pnpm run cursor:setup        # Setup Cursor integration
pnpm run cursor:start        # Start Cursor integration
pnpm run cursor:validate     # Validate Cursor integration
pnpm run cursor:test         # Test Cursor integration
pnpm run cursor:enforce      # Enforce Cursor usage
pnpm run cursor:auto         # Auto-setup Cursor integration
```

---

## 🚨 **ENFORCEMENT PROTOCOL**

### **MANDATORY: Enforce Cursor Usage**
```python
# MANDATORY: Enforce Cursor usage for all coding
def enforce_cursor_usage():
    """Enforce Cursor usage for all coding tasks."""
    
    # Check if Cursor is active
    if not validate_cursor_usage():
        raise Exception("❌ CURSOR INTEGRATION NOT ACTIVE!")
    
    # Check compliance
    compliance = validate_cursor_compliance()
    if compliance < 100:
        raise Exception(f"❌ CURSOR COMPLIANCE: {compliance}% - MUST BE 100%!")
    
    # Check agent usage
    if not require_cursor_agent():
        raise Exception("❌ CURSOR AGENT NOT SELECTED!")
    
    print("✅ CURSOR USAGE ENFORCED!")
    return True
```

---

## 📋 **COMPLETE TASK PROTOCOL**

### **MANDATORY: Follow This Protocol for Every Task**

#### **1. STARTUP (MANDATORY)**
```python
# MANDATORY: Start Cursor integration
await start_cursor_integration()
```

#### **2. KNOWLEDGE QUERY (MANDATORY)**
```python
# MANDATORY: Query knowledge systems
knowledge_entries, brain_blocks = await query_knowledge_for_context()
```

#### **3. MOBILE CONTROL (MANDATORY)**
```python
# MANDATORY: Use mobile control
goal = await manage_goals_with_mobile()
```

#### **4. BRAIN BLOCKS (MANDATORY)**
```python
# MANDATORY: Query brain blocks
blocks, sections, tags = await get_brain_blocks_context()
```

#### **5. CURSOR AGENT SELECTION (MANDATORY)**
```python
# MANDATORY: Select correct agent
agent_type = select_cursor_agent(file_path)
@require_cursor_agent(agent_type=agent_type)
def generate_code():
    pass
```

#### **6. ENFORCEMENT (MANDATORY)**
```python
# MANDATORY: Enforce Cursor usage
enforce_cursor_usage()
```

#### **7. CODING (MANDATORY)**
```python
# MANDATORY: All coding through Cursor
# Use Cursor agents for all code generation
# Use knowledge context for all decisions
# Use brain blocks for all context
# Use mobile control for all goals
```

---

## 🎯 **SUCCESS CRITERIA**

### **100% Cursor Integration Achieved When:**
- ✅ Cursor auto-invocation system active
- ✅ Knowledge systems queried and loaded
- ✅ Mobile control active and used
- ✅ Brain blocks integrated and queried
- ✅ Correct Cursor agent selected for each task
- ✅ Cursor usage enforced and validated
- ✅ All coding through Cursor IDE
- ✅ All context from knowledge systems
- ✅ All goals managed through mobile control
- ✅ All decisions informed by brain blocks

---

## 🚨 **CRITICAL REMINDERS**

### **NEVER:**
- ❌ Start coding without Cursor integration active
- ❌ Use any agent other than Cursor agents
- ❌ Skip knowledge system queries
- ❌ Skip mobile control usage
- ❌ Skip brain blocks integration
- ❌ Skip Cursor usage enforcement
- ❌ Skip compliance validation

### **ALWAYS:**
- ✅ Start with Cursor integration
- ✅ Query knowledge systems
- ✅ Use mobile control
- ✅ Query brain blocks
- ✅ Select correct Cursor agent
- ✅ Enforce Cursor usage
- ✅ Validate compliance
- ✅ Use Cursor for all coding

---

## 🚀 **FINAL IMPLEMENTATION**

### **Run This Command to Start Everything:**
```bash
python scripts/codex_cursor_startup.py
```

### **This Will:**
1. ✅ Setup all Cursor integration components
2. ✅ Start all systems automatically
3. ✅ Validate everything is working
4. ✅ Ensure 100% compliance
5. ✅ Make Cursor IDE the default for all coding tasks

---

**YOUR CURSOR INTEGRATION SYSTEM IS NOW READY! 🎉**

**EVERY TASK WILL AUTOMATICALLY USE CURSOR IDE INTEGRATION!**

**NO MORE MANUAL SETUP - EVERYTHING IS AUTOMATIC! 🚀**

**CURSOR IDE IS NOW YOUR PRIMARY DEVELOPMENT ENVIRONMENT! 💻**
