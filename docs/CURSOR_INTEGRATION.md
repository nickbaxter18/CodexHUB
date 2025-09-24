# Cursor Integration Guide

## U-DIG IT WebsiteOS Meta-Intelligence v4.3+

This guide explains how to integrate the Cursor client with your existing Codex system for full AI-powered development leverage.

## Overview

The Cursor client provides comprehensive API integration that maps your JSON configuration into actual Cursor API calls, enabling:

- **Intelligent Code Generation**: Generate code with AI reasoning
- **Advanced Refactoring**: AI-powered code optimization and restructuring
- **Comprehensive Testing**: Automated test generation and coverage analysis
- **Knowledge Synthesis**: Process and synthesize complex knowledge blocks
- **Visual Refinement**: AI-powered visual design and elevation
- **Multi-Agent Coordination**: Orchestrate complex development workflows

## Integration Points

### 1. Agent System Integration

The Cursor client integrates seamlessly with your existing agent architecture:

```javascript
// Existing agent system
const metaAgent = new MetaAgent();

// Enhanced with Cursor integration
const cursorClient = new CursorClient();
const enhancedMetaAgent = cursorClient.getAgent('meta');

// Coordinate agents with AI assistance
const coordination = await enhancedMetaAgent.coordinateGeneration({
  task: 'Build user management system',
  agents: ['frontend', 'backend', 'qa'],
  aiAssistance: true,
});
```

### 2. Macro System Integration

Integrate with your existing macro system for intelligent code generation:

```javascript
// In your macro_system/engine.py
from src.cursor import CursorClient, AgentType

class EnhancedMacroEngine:
    def __init__(self):
        self.cursor_client = CursorClient()

    async def execute_macro_with_ai(self, macro_name, context):
        # Use AI to enhance macro execution
        backend_agent = self.cursor_client.get_agent(AgentType.BACKEND)

        result = await backend_agent.generate_boilerplate(
            macro_name,
            context.get('schema', {})
        )

        return result
```

### 3. QA Engine Integration

Enhance your QA engine with AI-powered analysis:

```python
# In your qa/qa_engine.py
from src.cursor import CursorClient, AgentType

class EnhancedQAEngine:
    def __init__(self):
        self.cursor_client = CursorClient()

    async def run_ai_enhanced_review(self, code, review_types):
        qa_agent = self.cursor_client.get_agent(AgentType.QA)

        return await qa_agent.run_automated_reviews(code, review_types)
```

## Configuration

### Environment Setup

Add to your `.env` file:

```bash
# Cursor API Configuration
CURSOR_API_URL=https://api.cursor.sh
CURSOR_API_KEY=your_cursor_api_key_here
CURSOR_TIMEOUT=30
CURSOR_MAX_RETRIES=3
CURSOR_RETRY_DELAY=1.0
```

### Docker Integration

Update your `docker-compose.yml`:

```yaml
services:
  codex-app:
    build: .
    environment:
      - CURSOR_API_URL=${CURSOR_API_URL}
      - CURSOR_API_KEY=${CURSOR_API_KEY}
    volumes:
      - ./src/cursor:/app/src/cursor
```

## Usage Patterns

### 1. Development Workflow Enhancement

```javascript
// Enhanced development workflow
class EnhancedDevelopmentWorkflow {
  constructor() {
    this.cursorClient = new CursorClient();
    this.visualRefinement = new VisualRefinementCursor(this.cursorClient);
  }

  async buildFeature(requirements) {
    // 1. Meta-Agent coordination
    const metaAgent = this.cursorClient.getAgent('meta');
    const plan = await metaAgent.coordinateGeneration({
      task: requirements.task,
      context: requirements.context,
    });

    // 2. Execute with AI assistance
    const results = {};
    for (const task of plan.agentTasks) {
      const agent = this.cursorClient.getAgent(task.agent);
      results[task.agent] = await this.executeWithAI(agent, task);
    }

    // 3. Visual refinement
    if (results.frontend) {
      results.frontend = await this.visualRefinement.elevationPass(
        results.frontend.code,
        'luxury_polish'
      );
    }

    return results;
  }
}
```

### 2. Code Generation Pipeline

```python
# Enhanced code generation pipeline
class EnhancedCodeGenerationPipeline:
    def __init__(self):
        self.cursor_client = CursorClient()

    async def generate_complete_feature(self, spec):
        # Generate backend API
        backend_agent = self.cursor_client.get_agent(AgentType.BACKEND)
        api_code = await backend_agent.generate_boilerplate(
            'rest_api',
            spec['api_schema']
        )

        # Generate frontend components
        frontend_agent = self.cursor_client.get_agent(AgentType.FRONTEND)
        components = await frontend_agent.generate_react_component(
            spec['component_spec'],
            spec['styling_requirements']
        )

        # Generate tests
        tests = await self.cursor_client.generate_tests({
            'sourceCode': api_code['code'] + components['code'],
            'testTypes': ['unit', 'integration', 'e2e'],
            'framework': 'jest'
        })

        return {
            'api': api_code,
            'components': components,
            'tests': tests
        }
```

### 3. Visual Refinement Integration

```javascript
// Visual refinement pipeline integration
class VisualRefinementPipeline {
  constructor(cursorClient) {
    this.visualRefinement = new VisualRefinementCursor(cursorClient);
  }

  async refineUserInterface(code, brandGuidelines) {
    const pipeline = [
      () => this.visualRefinement.compliancePass(code, brandGuidelines),
      (result) => this.visualRefinement.missedOpportunitiesAudit(result.code),
      (result) => this.visualRefinement.refinementPass(result.code, ['palette', 'spacing']),
      (result) => this.visualRefinement.elevationPass(result.code, 'luxury_polish'),
    ];

    let current = { code };
    for (const step of pipeline) {
      current = await step(current);
    }

    return current;
  }
}
```

## API Reference

### Core Methods

#### `generateCode(request)`

Generate code with intelligent reasoning.

**Parameters:**

- `requirements`: Array of code requirements
- `language`: Programming language (default: 'javascript')
- `framework`: Framework to use
- `context`: Additional context object

#### `refactorCode(request)`

Refactor existing code with AI assistance.

**Parameters:**

- `sourceCode`: Code to refactor
- `refactoringType`: Type of refactoring ('optimization', 'security', etc.)
- `preserveBehavior`: Whether to preserve existing behavior

#### `coordinateAgents(task, context)`

Coordinate multiple agents for complex tasks.

**Parameters:**

- `task`: Task description
- `context`: Context for coordination

### Agent Methods

Each agent type has specialized methods:

- **Architect Agent**: `integrateOmniLaws()`, `scaffoldSystem()`
- **Frontend Agent**: `generateReactComponent()`, `optimizeUI()`
- **Backend Agent**: `generateBoilerplate()`, `generateTypeDefinitions()`
- **QA Agent**: `runAutomatedReviews()`, `proposeAccessibilityFixes()`
- **Knowledge Agent**: `traverseBrainBlocks()`, `summarizeNdjsonScaffolds()`
- **Meta Agent**: `accelerateReasoning()`, `coordinateGeneration()`

## Best Practices

### 1. Error Handling

```javascript
async function robustCursorOperation() {
  try {
    const result = await cursorClient.generateCode(request);
    return result;
  } catch (error) {
    if (error.message.includes('API error 429')) {
      // Rate limit - implement backoff
      await new Promise((resolve) => setTimeout(resolve, 5000));
      return robustCursorOperation(); // Retry
    } else {
      throw error;
    }
  }
}
```

### 2. Configuration Management

```javascript
// Use environment variables for configuration
const config = {
  apiBaseUrl: process.env.CURSOR_API_URL,
  apiKey: process.env.CURSOR_API_KEY,
  timeout: parseInt(process.env.CURSOR_TIMEOUT) || 30,
  maxRetries: parseInt(process.env.CURSOR_MAX_RETRIES) || 3,
};

const client = new CursorClient(config);
```

### 3. Performance Optimization

```python
# Use connection pooling for high-throughput applications
import asyncio
from aiohttp import ClientSession

class OptimizedCursorClient(CursorClient):
    def __init__(self, config):
        super().__init__(config)
        self.session_pool = None

    async def __aenter__(self):
        # Create connection pool
        connector = aiohttp.TCPConnector(limit=100, limit_per_host=30)
        self.session = aiohttp.ClientSession(connector=connector)
        return self
```

## Troubleshooting

### Common Issues

1. **API Key Issues**: Ensure `CURSOR_API_KEY` is set correctly
2. **Rate Limiting**: Implement exponential backoff for retries
3. **Timeout Issues**: Increase `CURSOR_TIMEOUT` for large requests
4. **Connection Issues**: Check network connectivity and API URL

### Debug Mode

Enable debug logging:

```javascript
// JavaScript
process.env.DEBUG = 'cursor:*';
const client = new CursorClient();
```

```python
# Python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Migration Guide

### From Existing Systems

1. **Install Dependencies**: Add cursor client dependencies to your project
2. **Set Environment Variables**: Configure Cursor API credentials
3. **Update Agent Classes**: Integrate cursor client methods into existing agents
4. **Test Integration**: Run tests to ensure compatibility
5. **Deploy**: Update deployment configuration with new environment variables

### Gradual Migration

Start with specific use cases:

1. **Code Generation**: Begin with simple code generation tasks
2. **Refactoring**: Add AI-powered refactoring to existing workflows
3. **Testing**: Integrate automated test generation
4. **Visual Refinement**: Add visual refinement pipeline
5. **Full Integration**: Complete multi-agent coordination

## Support

For issues and questions:

1. Check the comprehensive examples in `docs/cursor_client_examples.md`
2. Review the API reference in this document
3. Check environment configuration and API credentials
4. Enable debug logging for detailed error information

The Cursor client integration provides powerful AI capabilities while maintaining compatibility with your existing Codex system architecture.
