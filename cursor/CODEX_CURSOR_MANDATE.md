# CODEX CURSOR MANDATE

## ABSOLUTE REQUIREMENT FOR ALL CODING TASKS

### 🚨 THIS IS A NON-NEGOTIABLE MANDATE 🚨

**EVERY SINGLE LINE OF CODE MUST BE GENERATED THROUGH CURSOR IDE INTEGRATION**
**NO EXCEPTIONS. NO BYPASSES. NO FALLBACKS.**

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

### **Configuration Files:**

- `config/cursor_environment_template.env` - Environment template
- `config/cursor_integration_config.json` - Integration configuration

### **Documentation Files:**

- `CODEX_CURSOR_MANDATE.md` - This file
- `CURSOR_INTEGRATION_INSTRUCTIONS.md` - Technical instructions
- `CURSOR_INTEGRATION_README.md` - System overview
- `CURSOR_INTEGRATION_COMPLETE_GUIDE.md` - Complete guide

---

## 1. MANDATORY CURSOR INTEGRATION PROTOCOL

### Before ANY coding task, you MUST:

```python
# STEP 1: ALWAYS start with Cursor integration
import asyncio
from src.cursor.auto_invocation import get_auto_invoker, start_cursor_auto_invocation
from src.cursor.enforcement import enforce_cursor_integration, require_cursor_agent

# STEP 2: Start Cursor auto-invocation
await start_cursor_auto_invocation([Path(".")])

# STEP 3: Get auto-invoker
auto_invoker = get_auto_invoker()

# STEP 4: Determine agent type based on file
def determine_agent_type(file_path: str) -> str:
    if file_path.endswith('.tsx') or file_path.endswith('.jsx'):
        return 'FRONTEND'
    elif file_path.endswith('.py'):
        return 'BACKEND'
    elif file_path.endswith('.md'):
        return 'ARCHITECT'
    elif 'test' in file_path:
        return 'QA'
    elif 'workflow' in file_path or 'pipeline' in file_path:
        return 'CICD'
    elif file_path.endswith('.ndjson'):
        return 'KNOWLEDGE'
    else:
        return 'META'

# STEP 5: Get Cursor client and agent
cursor_client = auto_invoker.cursor_client
agent_type = determine_agent_type(file_path)
agent = cursor_client.get_agent(agent_type)

# STEP 6: ALWAYS use agent for coding
result = await agent.perform_task({
    "action": get_action_for_agent(agent_type),
    "payload": {
        "file_path": file_path,
        "requirements": requirements,
        "context": await get_knowledge_context()
    }
})
```

---

## 2. MANDATORY KNOWLEDGE INTEGRATION

### Every coding task MUST query ALL knowledge systems:

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

---

## 3. MANDATORY CURSOR AGENT USAGE

### Use the appropriate Cursor agent for EVERY task:

```python
# MANDATORY: Agent-specific coding tasks
@require_cursor_agent('FRONTEND')
async def generate_frontend_code(requirements):
    # This will automatically use Cursor FRONTEND agent
    pass

@require_cursor_agent('BACKEND')
async def generate_backend_code(requirements):
    # This will automatically use Cursor BACKEND agent
    pass

@require_cursor_agent('QA')
async def generate_tests(requirements):
    # This will automatically use Cursor QA agent
    pass

@require_cursor_agent('ARCHITECT')
async def generate_architecture(requirements):
    # This will automatically use Cursor ARCHITECT agent
    pass

@require_cursor_agent('CICD')
async def generate_pipeline(requirements):
    # This will automatically use Cursor CI/CD agent
    pass

@require_cursor_agent('KNOWLEDGE')
async def query_knowledge(requirements):
    # This will automatically use Cursor KNOWLEDGE agent
    pass

@require_cursor_agent('META')
async def coordinate_agents(requirements):
    # This will automatically use Cursor META agent
    pass
```

---

## 4. MANDATORY QUALITY ASSURANCE

### Every code change MUST go through Cursor QA:

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

## 5. MANDATORY ERROR HANDLING

### If Cursor integration fails, STOP and retry:

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

## 6. MANDATORY COMPLIANCE CHECKLIST

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

## 7. MANDATORY TESTING PROTOCOL

### Every implementation MUST be tested:

```python
# MANDATORY: Test Cursor integration
async def test_cursor_integration():
    # 1. Test auto-invocation
    auto_invoker = get_auto_invoker()
    assert auto_invoker is not None

    # 2. Test agent selection
    agent_type = determine_agent_type("test.py")
    assert agent_type == 'BACKEND'

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

## 8. MANDATORY DOCUMENTATION PROTOCOL

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

## 9. MANDATORY PERFORMANCE MONITORING

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

## 10. MANDATORY EMERGENCY PROTOCOL

### If you find yourself writing code without Cursor integration:

1. **STOP IMMEDIATELY**
2. **RESTART** with Cursor integration
3. **DELETE** any code written without Cursor
4. **REWRITE** using proper Cursor integration

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

---

## 🎯 IMPLEMENTATION EXAMPLE

Here's how to implement a coding task with 100% Cursor integration:

```python
# MANDATORY: Complete coding task with Cursor integration
async def implement_feature_with_cursor(feature_name: str, requirements: list):
    # 1. Start Cursor auto-invocation
    await start_cursor_auto_invocation([Path(".")])

    # 2. Get auto-invoker
    auto_invoker = get_auto_invoker()

    # 3. Determine agent type
    agent_type = determine_agent_type("feature.py")

    # 4. Get Cursor client and agent
    cursor_client = auto_invoker.cursor_client
    agent = cursor_client.get_agent(agent_type)

    # 5. Query knowledge systems
    knowledge_context = await get_knowledge_context()

    # 6. Use Cursor agent for coding
    result = await agent.perform_task({
        "action": "generate_feature",
        "payload": {
            "feature_name": feature_name,
            "requirements": requirements,
            "context": knowledge_context
        }
    })

    # 7. Quality assurance
    qa_result = await quality_assurance_workflow(result, "feature.py")

    # 8. Monitor performance
    await monitor_cursor_performance()

    # 9. Document usage
    document_cursor_usage()

    return result
```

---

**REMEMBER: CURSOR INTEGRATION IS NOT OPTIONAL. IT IS MANDATORY.**
**EVERY SINGLE CODING TASK MUST USE CURSOR IDE INTEGRATION.**
**NO EXCEPTIONS. NO DRIFTING. NO FALLBACKS.**
