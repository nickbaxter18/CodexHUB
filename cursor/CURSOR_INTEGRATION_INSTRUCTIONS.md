# CURSOR INTEGRATION INSTRUCTIONS

## MANDATORY CODEX BEHAVIOR PROTOCOL

### 🚨 CRITICAL: THESE INSTRUCTIONS ARE NON-NEGOTIABLE 🚨

**EVERY SINGLE CODING TASK MUST USE CURSOR IDE INTEGRATION**
**NO EXCEPTIONS. NO DRIFTING. NO FALLBACKS.**

---

## 📁 **REQUIRED FILES REFERENCE**

### **Core Cursor Integration Files:**

- `src/cursor/__init__.py` - Main package exports
- `src/cursor/cursor_client.py` - Core Cursor API client
- `src/cursor/auto_invocation.py` - Auto-invocation system
- `src/cursor/enforcement.py` - Usage enforcement
- `src/knowledge/auto_loader.py` - Knowledge auto-loading
- `src/mobile/mobile_app.py` - Mobile control interface
- `src/knowledge/brain_blocks_integration.py` - Brain Blocks integration

### **Setup & Management Scripts:**

- `scripts/setup_cursor_integration.py` - Complete setup
- `scripts/start_cursor_integration.py` - Start all systems
- `scripts/validate_cursor_integration.py` - Validate integration
- `scripts/test_cursor_integration.py` - Test all components
- `scripts/bootstrap_integration.py` - Bootstrap all systems
- `scripts/enforce_cursor_usage.py` - Enforce compliance
- `scripts/bootstrap_cursor_integration.py` - Bootstrap Cursor integration
- `scripts/bootstrap_knowledge.py` - Bootstrap Knowledge agent

### **Configuration Files:**

- `config/cursor_environment_template.env` - Environment template
- `config/cursor_integration_config.json` - Integration configuration

### **Documentation Files:**

- `CODEX_CURSOR_MANDATE.md` - MANDATORY instructions
- `CURSOR_INTEGRATION_INSTRUCTIONS.md` - This file
- `CURSOR_INTEGRATION_README.md` - System overview
- `CURSOR_INTEGRATION_COMPLETE_GUIDE.md` - Complete guide
- `CURSOR_INTEGRATION_FILES.md` - Complete file reference

---

## 1. MANDATORY CURSOR USAGE PROTOCOL

### Before ANY coding task:

1. **ALWAYS** invoke Cursor auto-invocation system
2. **ALWAYS** check which agent is appropriate for the task
3. **ALWAYS** use the Cursor API integration we built
4. **NEVER** write code without Cursor agent assistance

### Required Cursor Integration Flow:

```python
# MANDATORY: Every coding task MUST start with this
from src.cursor.auto_invocation import get_auto_invoker, start_cursor_auto_invocation
from src.cursor.enforcement import require_cursor_agent, validate_cursor_compliance
from src.knowledge.auto_loader import get_auto_loader
from src.mobile.mobile_app import get_mobile_app
from src.knowledge.brain_blocks_integration import get_brain_blocks_integration

# 1. Get the auto-invoker
auto_invoker = get_auto_invoker()

# 2. Determine appropriate agent based on file type
if file_path.endswith('.tsx') or file_path.endswith('.jsx'):
    agent_type = AgentType.FRONTEND
elif file_path.endswith('.py'):
    agent_type = AgentType.BACKEND
elif file_path.endswith('.md'):
    agent_type = AgentType.ARCHITECT
elif 'test' in file_path:
    agent_type = AgentType.QA
elif 'workflow' in file_path or 'pipeline' in file_path:
    agent_type = AgentType.CICD
else:
    agent_type = AgentType.META

# 3. ALWAYS invoke the agent
agent = cursor_client.get_agent(agent_type)
result = await agent.perform_task(task_payload)
```

---

## 2. MANDATORY SYSTEM INTEGRATION PROTOCOL

### Every task MUST utilize ALL built systems:

#### A. Knowledge Agent Integration (MANDATORY)

```python
# ALWAYS query knowledge before coding
from src.knowledge.auto_loader import get_auto_loader

auto_loader = get_auto_loader()
knowledge_result = await auto_loader.query_knowledge("relevant context for task")
# Use knowledge_result to inform coding decisions
```

#### B. Brain Blocks Integration (MANDATORY)

```python
# ALWAYS check brain blocks for relevant information
from src.knowledge.brain_blocks_integration import get_brain_blocks_integration

brain_blocks = get_brain_blocks_integration()
brain_results = await brain_blocks.query_brain_blocks(BrainBlockQuery(
    query="task context",
    limit=5
))
# Use brain_results to enhance code quality
```

#### C. Mobile Control Integration (MANDATORY)

```python
# ALWAYS check for mobile control requirements
from src.mobile.mobile_app import get_mobile_app

mobile_app = get_mobile_app()
dashboard = await mobile_app.get_dashboard()
# Use dashboard data to inform mobile-first decisions
```

---

## 3. CURSOR AGENT SELECTION MATRIX

### MANDATORY Agent Selection Rules:

| File Type       | Agent     | Cursor Action           | Required Integration     |
| --------------- | --------- | ----------------------- | ------------------------ |
| `.tsx`, `.jsx`  | FRONTEND  | `generate_components`   | Knowledge + Brain Blocks |
| `.py`           | BACKEND   | `generate_apis`         | Knowledge + Brain Blocks |
| `.md`           | ARCHITECT | `generate_blueprint`    | Knowledge + Brain Blocks |
| `test_*.py`     | QA        | `run_automated_reviews` | Knowledge + Brain Blocks |
| `.yml`, `.yaml` | CI/CD     | `optimize_pipeline`     | Knowledge + Brain Blocks |
| `.ndjson`       | KNOWLEDGE | `traverse_brain_blocks` | Brain Blocks + Mobile    |
| Any other       | META      | `arbitrate_qa_signals`  | All systems              |

---

## 4. MANDATORY CODING WORKFLOW

### Step 1: ALWAYS Start with Cursor Integration

```python
# MANDATORY: This is the FIRST thing you do
import asyncio
from src.cursor.auto_invocation import get_auto_invoker, start_cursor_auto_invocation

async def execute_coding_task():
    # 1. Start Cursor auto-invocation
    await start_cursor_auto_invocation([Path(".")])

    # 2. Get auto-invoker
    auto_invoker = get_auto_invoker()

    # 3. Determine agent type
    agent_type = determine_agent_type(file_path)

    # 4. Get Cursor client and agent
    cursor_client = auto_invoker.cursor_client
    agent = cursor_client.get_agent(agent_type)

    # 5. ALWAYS use agent for coding
    result = await agent.perform_task({
        "action": get_action_for_agent(agent_type),
        "payload": {
            "file_path": file_path,
            "requirements": requirements,
            "context": await get_knowledge_context()
        }
    })

    return result
```

### Step 2: ALWAYS Integrate Knowledge Systems

```python
# MANDATORY: Query all knowledge sources
async def get_knowledge_context():
    # 1. Query Knowledge Agent
    from src.knowledge.auto_loader import get_auto_loader
    auto_loader = get_auto_loader()
    knowledge_result = await auto_loader.query_knowledge("task context")

    # 2. Query Brain Blocks
    from src.knowledge.brain_blocks_integration import get_brain_blocks_integration
    brain_blocks = get_brain_blocks_integration()
    brain_result = await brain_blocks.query_brain_blocks(BrainBlockQuery(
        query="task context",
        limit=5
    ))

    # 3. Check Mobile Requirements
    from src.mobile.mobile_app import get_mobile_app
    mobile_app = get_mobile_app()
    dashboard = await mobile_app.get_dashboard()

    return {
        "knowledge": knowledge_result,
        "brain_blocks": brain_result,
        "mobile": dashboard
    }
```

### Step 3: ALWAYS Use Cursor Agent for Code Generation

```python
# MANDATORY: Never write code without Cursor agent
async def generate_code_with_cursor(agent_type, requirements, context):
    cursor_client = get_cursor_client()
    agent = cursor_client.get_agent(agent_type)

    # ALWAYS use the agent's specific method
    if agent_type == AgentType.FRONTEND:
        result = await agent.generate_components(requirements)
    elif agent_type == AgentType.BACKEND:
        result = await agent.generate_apis(requirements)
    elif agent_type == AgentType.QA:
        result = await agent.run_automated_reviews(requirements)
    elif agent_type == AgentType.ARCHITECT:
        result = await agent.generate_blueprint(requirements)
    elif agent_type == AgentType.CICD:
        result = await agent.optimize_pipeline(requirements)
    elif agent_type == AgentType.KNOWLEDGE:
        result = await agent.traverse_brain_blocks(requirements)
    elif agent_type == AgentType.META:
        result = await agent.arbitrate_qa_signals(requirements)

    return result
```

---

## 5. MANDATORY QUALITY ASSURANCE PROTOCOL

### Every code change MUST go through:

1. **Cursor Agent Review** - Use QA agent for code review
2. **Knowledge Validation** - Check against knowledge base
3. **Brain Blocks Validation** - Verify against brain blocks
4. **Mobile Compatibility** - Ensure mobile control compatibility

```python
# MANDATORY: Quality assurance workflow
async def quality_assurance_workflow(code, file_path):
    # 1. Cursor QA Agent Review
    qa_agent = cursor_client.get_agent(AgentType.QA)
    qa_result = await qa_agent.run_automated_reviews(code, [
        "security", "performance", "accessibility", "code_quality"
    ])

    # 2. Knowledge Validation
    knowledge_result = await auto_loader.query_knowledge("code validation")

    # 3. Brain Blocks Validation
    brain_result = await brain_blocks.query_brain_blocks(BrainBlockQuery(
        query="code best practices",
        limit=3
    ))

    # 4. Mobile Compatibility Check
    mobile_result = await mobile_app.get_dashboard()

    return {
        "qa": qa_result,
        "knowledge": knowledge_result,
        "brain_blocks": brain_result,
        "mobile": mobile_result
    }
```

---

## 6. MANDATORY ERROR HANDLING PROTOCOL

### If Cursor integration fails:

1. **STOP** - Do not proceed without Cursor
2. **DEBUG** - Check Cursor client connection
3. **RETRY** - Attempt Cursor integration again
4. **ESCALATE** - If still failing, report the issue

```python
# MANDATORY: Error handling for Cursor integration
async def safe_cursor_integration():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Attempt Cursor integration
            result = await execute_cursor_integration()
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                # Final attempt failed - STOP
                raise Exception(f"Cursor integration failed after {max_retries} attempts: {e}")
            else:
                # Retry with backoff
                await asyncio.sleep(2 ** attempt)
                continue
```

---

## 7. MANDATORY PERFORMANCE MONITORING

### Track Cursor usage:

```python
# MANDATORY: Performance monitoring
async def monitor_cursor_performance():
    auto_invoker = get_auto_invoker()
    stats = auto_invoker.get_rule_stats()

    # Log performance metrics
    logger.info(f"Cursor integration stats: {stats}")

    # Ensure we're using Cursor
    if stats['total_triggers'] == 0:
        raise Exception("Cursor integration not being used!")

    return stats
```

---

## 8. MANDATORY TESTING PROTOCOL

### Every implementation MUST be tested:

```python
# MANDATORY: Test Cursor integration
async def test_cursor_integration():
    # 1. Test auto-invocation
    auto_invoker = get_auto_invoker()
    assert auto_invoker is not None

    # 2. Test agent selection
    agent_type = determine_agent_type("test.py")
    assert agent_type == AgentType.BACKEND

    # 3. Test Cursor client
    cursor_client = auto_invoker.cursor_client
    agent = cursor_client.get_agent(AgentType.BACKEND)
    assert agent is not None

    # 4. Test agent execution
    result = await agent.generate_apis({"test": "data"})
    assert result is not None

    return True
```

---

## 9. MANDATORY DOCUMENTATION PROTOCOL

### Every code change MUST document Cursor usage:

```python
# MANDATORY: Document Cursor integration
def document_cursor_usage():
    return """
    CURSOR INTEGRATION USED:
    - Agent Type: {agent_type}
    - Cursor Action: {action}
    - Knowledge Queried: {knowledge_used}
    - Brain Blocks Queried: {brain_blocks_used}
    - Mobile Control: {mobile_used}
    - Performance: {performance_metrics}
    """
```

---

## 10. MANDATORY COMPLIANCE CHECKLIST

### Before ANY code change, verify:

- [ ] Cursor auto-invocation is active
- [ ] Appropriate agent is selected
- [ ] Knowledge Agent is queried
- [ ] Brain Blocks are queried
- [ ] Mobile control is checked
- [ ] QA agent reviews the code
- [ ] Performance is monitored
- [ ] Documentation includes Cursor usage

---

## 🚨 CRITICAL REMINDERS

1. **NEVER** write code without Cursor integration
2. **ALWAYS** use the auto-invocation system
3. **ALWAYS** query knowledge systems
4. **ALWAYS** use appropriate Cursor agents
5. **ALWAYS** monitor performance
6. **ALWAYS** document Cursor usage

---

## 📞 EMERGENCY PROTOCOL

If you find yourself writing code without Cursor integration:

1. **STOP IMMEDIATELY**
2. **RESTART** with Cursor integration
3. **DELETE** any code written without Cursor
4. **REWRITE** using proper Cursor integration

---

**THESE INSTRUCTIONS ARE NON-NEGOTIABLE. FOLLOW THEM EXACTLY.**
**NO EXCEPTIONS. NO DRIFTING. NO FALLBACKS.**
**CURSOR INTEGRATION IS MANDATORY FOR ALL CODING TASKS.**
