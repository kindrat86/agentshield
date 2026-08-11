// AgentShield Plugin for OpenClaw
// Per-transaction spend rules enforced before model dispatch
//
// Architecture:
//   OpenClaw gateway → AgentShield plugin → model dispatch
//   Each call evaluated against 7 composable rules in <1ms
//
// Config in openclaw.json:
//   "plugins": {
//     "agentshield": {
//       "endpoint": "https://agentshield.fly.dev",
//       "apiKey": "${AGENTSHIELD_API_KEY}",
//       "rules": {
//         "transactionLimit": 100,
//         "dailyCap": 2000,
//         "velocityThreshold": 10,
//         "merchantAllowlist": ["openai-api", "anthropic-api"],
//         "categoryBlocks": []
//       }
//     }
//   }

export interface AgentShieldConfig {
  endpoint: string;
  apiKey: string;
  rules: {
    transactionLimit?: number;
    dailyCap?: number;
    velocityThreshold?: number;
    merchantAllowlist?: string[];
    categoryBlocks?: string[];
  };
}

interface AgentShieldDecision {
  decision: 'ALLOW' | 'BLOCK' | 'FLAGGED';
  rule: string;
  evaluation_ms: number;
}

export class AgentShieldPlugin {
  private config: AgentShieldConfig;

  constructor(config: AgentShieldConfig) {
    this.config = config;
  }

  async evaluate(transaction: {
    amount: number;
    merchant: string;
    agent_id: string;
    category?: string;
  }): Promise<AgentShieldDecision> {
    const response = await fetch(
      `${this.config.endpoint}/v1/transactions/evaluate`,
      {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${this.config.apiKey}`,
        },
        body: JSON.stringify({
          amount: transaction.amount,
          merchant: transaction.merchant,
          agent_id: transaction.agent_id,
          rules: this.config.rules,
        }),
      }
    );

    if (!response.ok) {
      throw new Error(`AgentShield evaluation failed: ${response.status}`);
    }

    return response.json();
  }

  // Hook into OpenClaw's model dispatch pipeline
  // Intercepts before each LLM call, evaluates rules, returns allow/block
  async beforeModelDispatch(params: {
    model: string;
    estimatedTokens: number;
    provider: string;
    sessionCost: number;
  }): Promise<{ allowed: boolean; reason?: string }> {
    const estimatedCost = this.estimateCost(params.model, params.estimatedTokens);
    
    const decision = await this.evaluate({
      amount: estimatedCost,
      merchant: params.provider,
      agent_id: 'openclaw-session',
      category: 'llm-api',
    });

    if (decision.decision === 'BLOCK') {
      return {
        allowed: false,
        reason: `Blocked by ${decision.rule} (${decision.evaluation_ms}ms)`,
      };
    }

    return { allowed: true };
  }

  private estimateCost(model: string, tokens: number): number {
    const rates: Record<string, number> = {
      'claude-opus': 15.0,
      'claude-sonnet': 3.0,
      'claude-haiku': 0.25,
      'gpt-4o': 2.5,
      'gpt-4': 30.0,
      'gpt-3.5-turbo': 0.5,
    };

    const rate = rates[model] || 5.0;
    return (tokens / 1_000_000) * rate;
  }
}
