# AGENTS CURSOR INTEGRATION GUIDE
## Complete Guide for All Agents Using Cursor IDE

### 🎯 **PURPOSE**
This guide ensures all Codex agents are aware of and properly use Cursor IDE integration for every task.

---

## 🚨 **MANDATORY PROTOCOL FOR ALL AGENTS**

### **STEP 1: ALWAYS START WITH CURSOR INTEGRATION**
```python
# MANDATORY: Every agent must start with this
import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(".") / "src"))

# Import Cursor components
from src.cursor import (
    start_cursor_auto_invocation,
    get_auto_invoker,
    validate_cursor_compliance,
    enforce_cursor_integration,
    require_cursor_agent
)

# MANDATORY: Start Cursor integration
async def start_cursor_integration():
    await start_cursor_auto_invocation([Path(".")])
    print("✅ Cursor integration started")

# Run startup
asyncio.run(start_cursor_integration())
```

### **STEP 2: SELECT CORRECT CURSOR AGENT**
```python
# MANDATORY: Select agent based on task type
def select_cursor_agent(task_type: str, file_path: str = None) -> str:
    """Select correct Cursor agent for task."""
    
    if task_type == "frontend" or (file_path and file_path.endswith(('.tsx', '.jsx', '.ts', '.js'))):
        return "FRONTEND"
    elif task_type == "backend" or (file_path and file_path.endswith(('.py', '.pyx'))):
        return "BACKEND"
    elif task_type == "knowledge" or (file_path and file_path.endswith(('.md', '.rst', '.txt'))):
        return "KNOWLEDGE"
    elif task_type == "qa" or (file_path and 'test' in file_path.lower()):
        return "QA"
    elif task_type == "cicd" or (file_path and file_path.endswith(('.yml', '.yaml', '.json'))):
        return "CICD"
    elif task_type == "architect":
        return "ARCHITECT"
    else:
        return "ARCHITECT"  # Default fallback

# MANDATORY: Use agent selection
agent_type = select_cursor_agent(task_type, file_path)
@require_cursor_agent(agent_type=agent_type)
def execute_task():
    pass
```

---

## 🎨 **FRONTEND AGENT CURSOR INTEGRATION**

### **Agent Type**: `FRONTEND`
### **File Types**: `.tsx`, `.jsx`, `.ts`, `.js`
### **Cursor Agent**: `FRONTEND`

```python
# MANDATORY: Frontend agent protocol
@require_cursor_agent(agent_type="FRONTEND")
def generate_react_component(component_name: str, props: dict):
    """Generate React component using Cursor FRONTEND agent."""
    
    # 1. Query knowledge systems for React patterns
    from src.knowledge.auto_loader import get_knowledge_entries
    knowledge_entries = await get_knowledge_entries()
    
    # 2. Query brain blocks for component context
    from src.knowledge.brain_blocks_integration import query_brain_blocks
    brain_blocks = await query_brain_blocks()
    
    # 3. Use mobile control for goal management
    from src.mobile.mobile_app import create_goal
    goal = await create_goal(
        title=f"Generate {component_name} Component",
        description="Generate React component using Cursor IDE",
        priority="high"
    )
    
    # 4. Generate component using Cursor FRONTEND agent
    # (This will be handled by the Cursor integration system)
    
    return {
        "component": component_name,
        "props": props,
        "knowledge_context": knowledge_entries,
        "brain_blocks_context": brain_blocks,
        "goal": goal
    }
```

### **Frontend Agent Responsibilities:**
- ✅ Generate React components using Cursor FRONTEND agent
- ✅ Use Tailwind CSS for styling
- ✅ Follow functional component patterns
- ✅ Query knowledge systems for React patterns
- ✅ Use brain blocks for component context
- ✅ Manage goals through mobile control

---

## 🐍 **BACKEND AGENT CURSOR INTEGRATION**

### **Agent Type**: `BACKEND`
### **File Types**: `.py`, `.pyx`
### **Cursor Agent**: `BACKEND`

```python
# MANDATORY: Backend agent protocol
@require_cursor_agent(agent_type="BACKEND")
def generate_python_api(endpoint: str, methods: list):
    """Generate Python API using Cursor BACKEND agent."""
    
    # 1. Query knowledge systems for Python patterns
    from src.knowledge.auto_loader import get_knowledge_entries
    knowledge_entries = await get_knowledge_entries()
    
    # 2. Query brain blocks for API context
    from src.knowledge.brain_blocks_integration import query_brain_blocks
    brain_blocks = await query_brain_blocks()
    
    # 3. Use mobile control for goal management
    from src.mobile.mobile_app import create_goal
    goal = await create_goal(
        title=f"Generate {endpoint} API",
        description="Generate Python API using Cursor IDE",
        priority="high"
    )
    
    # 4. Generate API using Cursor BACKEND agent
    # (This will be handled by the Cursor integration system)
    
    return {
        "endpoint": endpoint,
        "methods": methods,
        "knowledge_context": knowledge_entries,
        "brain_blocks_context": brain_blocks,
        "goal": goal
    }
```

### **Backend Agent Responsibilities:**
- ✅ Generate Python APIs using Cursor BACKEND agent
- ✅ Follow Python best practices
- ✅ Query knowledge systems for Python patterns
- ✅ Use brain blocks for API context
- ✅ Manage goals through mobile control

---

## 📚 **KNOWLEDGE AGENT CURSOR INTEGRATION**

### **Agent Type**: `KNOWLEDGE`
### **File Types**: `.md`, `.rst`, `.txt`
### **Cursor Agent**: `KNOWLEDGE`

```python
# MANDATORY: Knowledge agent protocol
@require_cursor_agent(agent_type="KNOWLEDGE")
def generate_documentation(topic: str, content_type: str):
    """Generate documentation using Cursor KNOWLEDGE agent."""
    
    # 1. Query knowledge systems for documentation patterns
    from src.knowledge.auto_loader import get_knowledge_entries
    knowledge_entries = await get_knowledge_entries()
    
    # 2. Query brain blocks for documentation context
    from src.knowledge.brain_blocks_integration import query_brain_blocks
    brain_blocks = await query_brain_blocks()
    
    # 3. Use mobile control for goal management
    from src.mobile.mobile_app import create_goal
    goal = await create_goal(
        title=f"Generate {topic} Documentation",
        description="Generate documentation using Cursor IDE",
        priority="high"
    )
    
    # 4. Generate documentation using Cursor KNOWLEDGE agent
    # (This will be handled by the Cursor integration system)
    
    return {
        "topic": topic,
        "content_type": content_type,
        "knowledge_context": knowledge_entries,
        "brain_blocks_context": brain_blocks,
        "goal": goal
    }
```

### **Knowledge Agent Responsibilities:**
- ✅ Generate documentation using Cursor KNOWLEDGE agent
- ✅ Query knowledge systems for documentation patterns
- ✅ Use brain blocks for documentation context
- ✅ Manage goals through mobile control

---

## 🧪 **QA AGENT CURSOR INTEGRATION**

### **Agent Type**: `QA`
### **File Types**: Test files, quality assurance
### **Cursor Agent**: `QA`

```python
# MANDATORY: QA agent protocol
@require_cursor_agent(agent_type="QA")
def generate_tests(test_type: str, coverage_requirements: dict):
    """Generate tests using Cursor QA agent."""
    
    # 1. Query knowledge systems for testing patterns
    from src.knowledge.auto_loader import get_knowledge_entries
    knowledge_entries = await get_knowledge_entries()
    
    # 2. Query brain blocks for testing context
    from src.knowledge.brain_blocks_integration import query_brain_blocks
    brain_blocks = await query_brain_blocks()
    
    # 3. Use mobile control for goal management
    from src.mobile.mobile_app import create_goal
    goal = await create_goal(
        title=f"Generate {test_type} Tests",
        description="Generate tests using Cursor IDE",
        priority="high"
    )
    
    # 4. Generate tests using Cursor QA agent
    # (This will be handled by the Cursor integration system)
    
    return {
        "test_type": test_type,
        "coverage_requirements": coverage_requirements,
        "knowledge_context": knowledge_entries,
        "brain_blocks_context": brain_blocks,
        "goal": goal
    }
```

### **QA Agent Responsibilities:**
- ✅ Generate tests using Cursor QA agent
- ✅ Ensure test coverage requirements
- ✅ Query knowledge systems for testing patterns
- ✅ Use brain blocks for testing context
- ✅ Manage goals through mobile control

---

## 🏗️ **ARCHITECT AGENT CURSOR INTEGRATION**

### **Agent Type**: `ARCHITECT`
### **File Types**: Architecture decisions, system design
### **Cursor Agent**: `ARCHITECT`

```python
# MANDATORY: Architect agent protocol
@require_cursor_agent(agent_type="ARCHITECT")
def design_system_architecture(requirements: dict, constraints: list):
    """Design system architecture using Cursor ARCHITECT agent."""
    
    # 1. Query knowledge systems for architecture patterns
    from src.knowledge.auto_loader import get_knowledge_entries
    knowledge_entries = await get_knowledge_entries()
    
    # 2. Query brain blocks for architecture context
    from src.knowledge.brain_blocks_integration import query_brain_blocks
    brain_blocks = await query_brain_blocks()
    
    # 3. Use mobile control for goal management
    from src.mobile.mobile_app import create_goal
    goal = await create_goal(
        title="Design System Architecture",
        description="Design system architecture using Cursor IDE",
        priority="high"
    )
    
    # 4. Design architecture using Cursor ARCHITECT agent
    # (This will be handled by the Cursor integration system)
    
    return {
        "requirements": requirements,
        "constraints": constraints,
        "knowledge_context": knowledge_entries,
        "brain_blocks_context": brain_blocks,
        "goal": goal
    }
```

### **Architect Agent Responsibilities:**
- ✅ Design system architecture using Cursor ARCHITECT agent
- ✅ Query knowledge systems for architecture patterns
- ✅ Use brain blocks for architecture context
- ✅ Manage goals through mobile control

---

## 🚀 **CICD AGENT CURSOR INTEGRATION**

### **Agent Type**: `CICD`
### **File Types**: `.yml`, `.yaml`, `.json`
### **Cursor Agent**: `CICD`

```python
# MANDATORY: CI/CD agent protocol
@require_cursor_agent(agent_type="CICD")
def generate_pipeline(pipeline_type: str, stages: list):
    """Generate CI/CD pipeline using Cursor CICD agent."""
    
    # 1. Query knowledge systems for CI/CD patterns
    from src.knowledge.auto_loader import get_knowledge_entries
    knowledge_entries = await get_knowledge_entries()
    
    # 2. Query brain blocks for CI/CD context
    from src.knowledge.brain_blocks_integration import query_brain_blocks
    brain_blocks = await query_brain_blocks()
    
    # 3. Use mobile control for goal management
    from src.mobile.mobile_app import create_goal
    goal = await create_goal(
        title=f"Generate {pipeline_type} Pipeline",
        description="Generate CI/CD pipeline using Cursor IDE",
        priority="high"
    )
    
    # 4. Generate pipeline using Cursor CICD agent
    # (This will be handled by the Cursor integration system)
    
    return {
        "pipeline_type": pipeline_type,
        "stages": stages,
        "knowledge_context": knowledge_entries,
        "brain_blocks_context": brain_blocks,
        "goal": goal
    }
```

### **CI/CD Agent Responsibilities:**
- ✅ Generate CI/CD pipelines using Cursor CICD agent
- ✅ Query knowledge systems for CI/CD patterns
- ✅ Use brain blocks for CI/CD context
- ✅ Manage goals through mobile control

---

## 🚨 **CRITICAL REQUIREMENTS FOR ALL AGENTS**

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

## 🎯 **SUCCESS CRITERIA**

### **100% Cursor Integration Achieved When:**
- ✅ All agents use Cursor IDE integration
- ✅ Knowledge systems are queried by all agents
- ✅ Mobile control is used by all agents
- ✅ Brain blocks are integrated by all agents
- ✅ Correct Cursor agent is selected for each task
- ✅ Cursor usage is enforced by all agents
- ✅ All coding through Cursor IDE
- ✅ All context from knowledge systems
- ✅ All goals managed through mobile control
- ✅ All decisions informed by brain blocks

---

**ALL AGENTS ARE NOW AWARE OF CURSOR IDE INTEGRATION! 🎉**

**EVERY AGENT WILL USE CURSOR IDE FOR EVERY TASK!**

**NO MORE MANUAL SETUP - EVERYTHING IS AUTOMATIC! 🚀**

**CURSOR IDE IS NOW THE PRIMARY DEVELOPMENT ENVIRONMENT FOR ALL AGENTS! 💻**
