# Cursor Client Usage Examples
## U-DIG IT WebsiteOS Meta-Intelligence v4.3+

This document provides comprehensive examples of how to use the Cursor clients to map your JSON configuration into actual API calls for full Codex system leverage.

## Quick Start

### JavaScript (Node.js)

```javascript
const { CursorClient } = require('./cursor_client.js');

// Initialize client
const client = new CursorClient({
  apiBaseUrl: process.env.CURSOR_API_URL,
  apiKey: process.env.CURSOR_API_KEY
});

// Generate code
async function generateCode() {
  const result = await client.generateCode({
    requirements: ['Create a React component for user dashboard'],
    language: 'javascript',
    framework: 'react',
    context: {
      domain: 'user_management',
      styling: 'tailwind',
      motion: true
    }
  });
  console.log('Generated code:', result);
}

generateCode();
```

### Python

```python
import asyncio
from cursor_client import CursorClient, AgentType

async def main():
    async with CursorClient() as client:
        # Generate code
        result = await client.generate_code({
            'requirements': ['Create a FastAPI endpoint for user management'],
            'language': 'python',
            'framework': 'fastapi',
            'context': {
                'domain': 'user_management',
                'include_validation': True
            }
        })
        print("Generated code:", result)

asyncio.run(main())
```

## Agent-Specific Usage

### 1. Architect Agent - System Integration

```javascript
// JavaScript
const architectAgent = client.getAgent('architect');

const result = await architectAgent.integrateOmniLaws([
  {
    "name": "Visual Harmony Law",
    "rule": "Maintain consistent spacing using 8px grid system"
  },
  {
    "name": "Performance Law", 
    "rule": "All components must load within 200ms"
  }
], {
  systemContext: 'frontend_architecture',
  currentImplementation: 'react_components'
});
```

```python
# Python
architect_agent = client.get_agent(AgentType.ARCHITECT)

result = await architect_agent.integrate_omni_laws([
    {
        "name": "Visual Harmony Law",
        "rule": "Maintain consistent spacing using 8px grid system"
    },
    {
        "name": "Performance Law", 
        "rule": "All components must load within 200ms"
    }
], {
    'systemContext': 'frontend_architecture',
    'currentImplementation': 'react_components'
})
```

### 2. Frontend Agent - Component Generation

```javascript
// JavaScript - Generate React Component with Visual Refinement
const frontendAgent = client.getAgent('frontend');

const componentResult = await frontendAgent.generateReactComponent({
  name: 'UserProfileCard',
  props: ['user', 'onEdit', 'onDelete'],
  styling: {
    theme: 'modern',
    colors: ['blue', 'gray', 'white'],
    spacing: 'comfortable'
  }
}, {
  brandGuidelines: {
    primaryColor: '#3B82F6',
    typography: 'Inter',
    borderRadius: '8px'
  },
  motionRequirements: ['hover', 'focus', 'loading']
});

// Optimize existing UI
const optimizationResult = await frontendAgent.optimizeUI('refinement_pass', currentCode);
```

```python
# Python - Frontend Component Generation
frontend_agent = client.get_agent(AgentType.FRONTEND)

component_result = await frontend_agent.generate_react_component({
    'name': 'UserProfileCard',
    'props': ['user', 'onEdit', 'onDelete'],
    'styling': {
        'theme': 'modern',
        'colors': ['blue', 'gray', 'white'],
        'spacing': 'comfortable'
    }
}, {
    'brandGuidelines': {
        'primaryColor': '#3B82F6',
        'typography': 'Inter',
        'borderRadius': '8px'
    },
    'motionRequirements': ['hover', 'focus', 'loading']
})

# Optimize existing UI
optimization_result = await frontend_agent.optimize_ui('refinement_pass', current_code)
```

### 3. Backend Agent - API Development

```javascript
// JavaScript - Backend API Generation
const backendAgent = client.getAgent('backend');

const apiResult = await backendAgent.generateBoilerplate('user_api', {
  endpoints: ['GET /users', 'POST /users', 'PUT /users/:id', 'DELETE /users/:id'],
  schema: {
    User: {
      id: 'uuid',
      name: 'string',
      email: 'string',
      createdAt: 'datetime'
    }
  },
  validation: true,
  authentication: 'jwt'
});

// Generate type definitions
const typeResult = await backendAgent.generateTypeDefinitions(schema, 'python');
```

```python
# Python - Backend API Generation
backend_agent = client.get_agent(AgentType.BACKEND)

api_result = await backend_agent.generate_boilerplate('user_api', {
    'endpoints': ['GET /users', 'POST /users', 'PUT /users/:id', 'DELETE /users/:id'],
    'schema': {
        'User': {
            'id': 'uuid',
            'name': 'string',
            'email': 'string',
            'createdAt': 'datetime'
        }
    },
    'validation': True,
    'authentication': 'jwt'
})

# Generate type definitions
type_result = await backend_agent.generate_type_definitions(schema, 'python')
```

### 4. QA Agent - Quality Assurance

```javascript
// JavaScript - Comprehensive QA Review
const qaAgent = client.getAgent('qa');

const reviewResult = await qaAgent.runAutomatedReviews(sourceCode, [
  'accessibility',
  'seo', 
  'ux',
  'aesthetics',
  'performance'
]);

// Propose accessibility fixes
const accessibilityFixes = await qaAgent.proposeAccessibilityFixes(
  componentCode, 
  ['color_contrast', 'keyboard_navigation', 'screen_reader']
);

// SEO optimizations
const seoOptimizations = await qaAgent.suggestSEOOptimizations(pageCode, {
  targetKeywords: ['user dashboard', 'profile management'],
  metaRequirements: ['title', 'description', 'og_tags']
});
```

```python
# Python - QA Agent Usage
qa_agent = client.get_agent(AgentType.QA)

review_result = await qa_agent.run_automated_reviews(source_code, [
    'accessibility',
    'seo', 
    'ux',
    'aesthetics',
    'performance'
])

# Propose accessibility fixes
accessibility_fixes = await qa_agent.propose_accessibility_fixes(
    component_code, 
    ['color_contrast', 'keyboard_navigation', 'screen_reader']
)

# SEO optimizations
seo_optimizations = await qa_agent.suggest_seo_optimizations(page_code, {
    'targetKeywords': ['user dashboard', 'profile management'],
    'metaRequirements': ['title', 'description', 'og_tags']
})
```

### 5. Knowledge Agent - Knowledge Synthesis

```javascript
// JavaScript - Knowledge Processing
const knowledgeAgent = client.getAgent('knowledge');

const synthesisResult = await knowledgeAgent.traverseBrainBlocks(brainBlocks, {
  query: 'How to implement responsive design patterns',
  context: 'frontend_architecture',
  depth: 'comprehensive'
});

// Summarize ndjson scaffolds
const summaryResult = await knowledgeAgent.summarizeNdjsonScaffolds(ndjsonData, {
  outputFormat: 'structured_knowledge',
  includePatterns: true,
  extractInsights: true
});
```

```python
# Python - Knowledge Agent Usage
knowledge_agent = client.get_agent(AgentType.KNOWLEDGE)

synthesis_result = await knowledge_agent.traverse_brain_blocks(brain_blocks, {
    'query': 'How to implement responsive design patterns',
    'context': 'frontend_architecture',
    'depth': 'comprehensive'
})

# Summarize ndjson scaffolds
summary_result = await knowledge_agent.summarize_ndjson_scaffolds(ndjson_data, {
    'outputFormat': 'structured_knowledge',
    'includePatterns': True,
    'extractInsights': True
})
```

### 6. Meta Agent - System Coordination

```javascript
// JavaScript - Meta Agent Coordination
const metaAgent = client.getAgent('meta');

const coordinationResult = await metaAgent.coordinateGeneration({
  task: 'Build complete user management system',
  requirements: ['frontend', 'backend', 'database', 'testing'],
  constraints: ['performance', 'security', 'accessibility']
}, {
  architectContext: 'system_design',
  frontendContext: 'component_architecture',
  backendContext: 'api_design',
  qaContext: 'quality_requirements'
});

// Accelerate reasoning for complex problems
const reasoningResult = await metaAgent.accelerateReasoning({
  problem: 'How to optimize large-scale component rendering',
  context: 'react_performance',
  constraints: ['memory_usage', 'render_time', 'user_experience']
}, 'performance_optimization');
```

```python
# Python - Meta Agent Coordination
meta_agent = client.get_agent(AgentType.META)

coordination_result = await meta_agent.coordinate_generation({
    'task': 'Build complete user management system',
    'requirements': ['frontend', 'backend', 'database', 'testing'],
    'constraints': ['performance', 'security', 'accessibility']
}, {
    'architectContext': 'system_design',
    'frontendContext': 'component_architecture',
    'backendContext': 'api_design',
    'qaContext': 'quality_requirements'
})

# Accelerate reasoning for complex problems
reasoning_result = await meta_agent.accelerate_reasoning({
    'problem': 'How to optimize large-scale component rendering',
    'context': 'react_performance',
    'constraints': ['memory_usage', 'render_time', 'user_experience']
}, 'performance_optimization')
```

## Visual Refinement Integration

### Complete Visual Refinement Pipeline

```javascript
// JavaScript - Visual Refinement Pipeline
const visualRefinement = new VisualRefinementCursor(client);

async function runVisualRefinementPipeline(code, brandGuidelines) {
  // 1. Compliance Pass
  const complianceResult = await visualRefinement.compliancePass(code, brandGuidelines);
  
  // 2. Missed Opportunities Audit
  const opportunitiesResult = await visualRefinement.missedOpportunitiesAudit(code, [
    'color_cognition',
    'typography', 
    'layout',
    'motion'
  ]);
  
  // 3. Refinement Pass
  const refinementResult = await visualRefinement.refinementPass(code, [
    'palette_optimization',
    'spacing_harmony',
    'motion_polish'
  ]);
  
  // 4. Elevation Pass
  const elevationResult = await visualRefinement.elevationPass(code, 'luxury_polish');
  
  return {
    compliance: complianceResult,
    opportunities: opportunitiesResult,
    refinement: refinementResult,
    elevation: elevationResult
  };
}
```

```python
# Python - Visual Refinement Pipeline
from cursor_client import VisualRefinementCursor

async def run_visual_refinement_pipeline(code, brand_guidelines):
    visual_refinement = VisualRefinementCursor(client)
    
    # 1. Compliance Pass
    compliance_result = await visual_refinement.compliance_pass(code, brand_guidelines)
    
    # 2. Missed Opportunities Audit
    opportunities_result = await visual_refinement.missed_opportunities_audit(code, [
        'color_cognition',
        'typography', 
        'layout',
        'motion'
    ])
    
    # 3. Refinement Pass
    refinement_result = await visual_refinement.refinement_pass(code, [
        'palette_optimization',
        'spacing_harmony',
        'motion_polish'
    ])
    
    # 4. Elevation Pass
    elevation_result = await visual_refinement.elevation_pass(code, 'luxury_polish')
    
    return {
        'compliance': compliance_result,
        'opportunities': opportunities_result,
        'refinement': refinement_result,
        'elevation': elevation_result
    }
```

## Advanced Usage Patterns

### 1. Multi-Agent Workflow

```javascript
// JavaScript - Complete Multi-Agent Workflow
async function buildUserManagementSystem() {
  const metaAgent = client.getAgent('meta');
  
  // Meta-Agent coordinates the entire process
  const coordination = await metaAgent.coordinateGeneration({
    task: 'Complete user management system',
    requirements: ['authentication', 'profile_management', 'settings', 'dashboard'],
    qualityStandards: ['accessibility', 'performance', 'security']
  }, {
    timeline: '2_weeks',
    teamSize: '3_developers',
    techStack: ['react', 'fastapi', 'postgresql']
  });
  
  // Execute coordinated plan
  for (const agentTask of coordination.agentTasks) {
    const agent = client.getAgent(agentTask.agent);
    
    switch (agentTask.agent) {
      case 'frontend':
        await agent.generateReactComponent(agentTask.spec, agentTask.styling);
        break;
      case 'backend':
        await agent.generateBoilerplate(agentTask.type, agentTask.schema);
        break;
      case 'qa':
        await agent.runAutomatedReviews(agentTask.code, agentTask.reviewTypes);
        break;
    }
  }
}
```

### 2. Performance Optimization Workflow

```javascript
// JavaScript - Performance Optimization
async function optimizeApplicationPerformance(appCode) {
  // 1. Analyze current performance
  const analysisResult = await client.optimizePerformance({
    sourceCode: appCode,
    optimizationType: 'comprehensive',
    targetMetrics: ['speed', 'memory', 'bundle_size'],
    constraints: {
      maintainBackwardCompatibility: true,
      preserveFunctionality: true
    }
  });
  
  // 2. Generate optimized code
  const optimizedCode = await client.refactorCode({
    sourceCode: appCode,
    refactoringType: 'performance_optimization',
    targetPattern: analysisResult.recommendedPatterns,
    preserveBehavior: true
  });
  
  // 3. Generate performance tests
  const performanceTests = await client.generateTests({
    sourceCode: optimizedCode.refactoredCode,
    testTypes: ['performance', 'load', 'memory'],
    framework: 'jest',
    coverage: 'comprehensive'
  });
  
  return {
    analysis: analysisResult,
    optimizedCode: optimizedCode,
    tests: performanceTests
  };
}
```

### 3. Security Analysis Workflow

```javascript
// JavaScript - Security Analysis
async function performSecurityAnalysis(codebase) {
  const securityResult = await client.analyzeSecurity({
    sourceCode: codebase,
    analysisDepth: 'comprehensive',
    checkTypes: [
      'injection',
      'authentication',
      'authorization', 
      'data_leaks',
      'dependencies',
      'secrets_exposure'
    ]
  });
  
  // Generate security fixes
  const securityFixes = await client.refactorCode({
    sourceCode: codebase,
    refactoringType: 'security_hardening',
    targetPattern: securityResult.recommendedFixes,
    preserveBehavior: true
  });
  
  // Generate security tests
  const securityTests = await client.generateTests({
    sourceCode: securityFixes.refactoredCode,
    testTypes: ['security', 'penetration'],
    framework: 'jest',
    coverage: 'security_focused'
  });
  
  return {
    analysis: securityResult,
    fixes: securityFixes,
    tests: securityTests
  };
}
```

## Environment Configuration

### Environment Variables

```bash
# .env file
CURSOR_API_URL=https://api.cursor.sh
CURSOR_API_KEY=your_api_key_here
CURSOR_TIMEOUT=30
CURSOR_MAX_RETRIES=3
CURSOR_RETRY_DELAY=1.0
```

### Docker Configuration

```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app
COPY package*.json ./
RUN npm install

COPY cursor_client.js ./
COPY cursor_client_examples.md ./

ENV CURSOR_API_URL=https://api.cursor.sh
ENV CURSOR_API_KEY=${CURSOR_API_KEY}

CMD ["node", "cursor_client.js"]
```

## Error Handling and Best Practices

### JavaScript Error Handling

```javascript
// JavaScript - Robust Error Handling
async function robustCursorOperation() {
  try {
    const client = new CursorClient();
    
    const result = await client.generateCode({
      requirements: ['Create a secure login component'],
      language: 'javascript',
      framework: 'react',
      context: {
        securityLevel: 'high',
        accessibility: 'wcag_aa'
      }
    });
    
    return result;
  } catch (error) {
    if (error.message.includes('API error 429')) {
      // Rate limit exceeded - implement backoff
      await new Promise(resolve => setTimeout(resolve, 5000));
      return robustCursorOperation(); // Retry
    } else if (error.message.includes('API error 401')) {
      // Authentication error
      throw new Error('Invalid Cursor API key');
    } else {
      // Other errors
      console.error('Cursor operation failed:', error);
      throw error;
    }
  }
}
```

### Python Error Handling

```python
# Python - Robust Error Handling
import asyncio
from cursor_client import CursorClient, CursorAPIError

async def robust_cursor_operation():
    try:
        async with CursorClient() as client:
            result = await client.generate_code({
                'requirements': ['Create a secure login component'],
                'language': 'python',
                'framework': 'fastapi',
                'context': {
                    'securityLevel': 'high',
                    'accessibility': 'wcag_aa'
                }
            })
            return result
    except CursorAPIError as e:
        if 'API error 429' in str(e):
            # Rate limit exceeded - implement backoff
            await asyncio.sleep(5)
            return await robust_cursor_operation()  # Retry
        elif 'API error 401' in str(e):
            # Authentication error
            raise ValueError('Invalid Cursor API key')
        else:
            # Other errors
            print(f'Cursor operation failed: {e}')
            raise
```

## Integration with Your Codex System

### Complete Integration Example

```javascript
// JavaScript - Complete Codex Integration
class CodexSystem {
  constructor() {
    this.cursorClient = new CursorClient();
    this.visualRefinement = new VisualRefinementCursor(this.cursorClient);
  }
  
  async executeWebsiteOSWorkflow(requirements) {
    // 1. Meta-Agent coordination
    const metaAgent = this.cursorClient.getAgent('meta');
    const coordination = await metaAgent.coordinateGeneration({
      task: 'Build omni-domain website',
      requirements: requirements,
      qualityStandards: ['visual_refinement', 'accessibility', 'performance']
    });
    
    // 2. Execute agent tasks
    const results = {};
    for (const task of coordination.agentTasks) {
      const agent = this.cursorClient.getAgent(task.agent);
      results[task.agent] = await this.executeAgentTask(agent, task);
    }
    
    // 3. Visual refinement pipeline
    const refinedResults = {};
    for (const [agent, result] of Object.entries(results)) {
      if (agent === 'frontend') {
        refinedResults[agent] = await this.runVisualRefinement(result.code);
      } else {
        refinedResults[agent] = result;
      }
    }
    
    // 4. Final QA pass
    const qaAgent = this.cursorClient.getAgent('qa');
    const finalReview = await qaAgent.runAutomatedReviews(
      refinedResults, 
      ['accessibility', 'seo', 'ux', 'aesthetics', 'performance']
    );
    
    return {
      coordination,
      results: refinedResults,
      qaReview: finalReview
    };
  }
  
  async runVisualRefinement(code) {
    return await this.visualRefinement.elevationPass(code, 'luxury_polish');
  }
  
  async executeAgentTask(agent, task) {
    // Implementation depends on agent type and task
    switch (task.type) {
      case 'generate_component':
        return await agent.generateReactComponent(task.spec, task.styling);
      case 'generate_api':
        return await agent.generateBoilerplate(task.type, task.schema);
      case 'security_analysis':
        return await this.cursorClient.analyzeSecurity({ sourceCode: task.code });
      default:
        throw new Error(`Unknown task type: ${task.type}`);
    }
  }
}
```

This comprehensive integration gives your Codex system full Cursor leverage with:

- **Complete API Mapping**: Every JSON configuration maps to actual Cursor API calls
- **Agent-Specific Methods**: Tailored methods for each agent type (Architect, Frontend, Backend, QA, etc.)
- **Visual Refinement Pipeline**: Full integration with your visual refinement and elevation system
- **Error Handling**: Robust error handling with retry logic and graceful degradation
- **Performance Optimization**: Built-in performance and security analysis capabilities
- **Multi-Agent Coordination**: Meta-Agent coordination for complex workflows

Your Codex system now has fully optimized Cursor leverage for intelligent reasoning, generation, refactoring, and summarization at every step of the development process.
