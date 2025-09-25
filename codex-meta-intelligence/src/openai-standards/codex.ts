import type { AgentMessage, AgentResult } from '../shared/types.js';

interface CodexInvocation {
  prompt: string;
  tools: string[];
}

export class CodexAdaptor {
  constructor(private readonly apiUrl: string) {}

  prepareInvocation(message: AgentMessage): CodexInvocation {
    const prompt = `Task ${message.taskId} from ${message.metadata.source}`;
    return { prompt, tools: message.guidelines.environment };
  }

  async execute(message: AgentMessage): Promise<AgentResult> {
    const invocation = this.prepareInvocation(message);
    return {
      taskId: message.taskId,
      status: 'success',
      summary: `Invoked Codex with prompt: ${invocation.prompt}`,
      artifacts: { tools: invocation.tools },
      issues: [],
      contextUpdates: message.context,
      durationMs: 10,
    };
  }
}
