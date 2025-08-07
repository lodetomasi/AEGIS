"""
Advanced usage example for AETHER evaluation system.

This example shows:
- Custom configuration
- Industry-specific evaluation
- Using only specific modules
- Custom baseline configuration
- Integrating with OpenRouter
"""

import os
import json
from pathlib import Path
from aether import AETHER, AgentConfig, EvaluationConfig
from aether.utils.llm_client import LLMClient


class MyAgentWrapper:
    """Wrapper for your AI agent that uses OpenRouter."""
    
    def __init__(self, agent_config: AgentConfig):
        self.config = agent_config
        self.llm_client = LLMClient(
            model=agent_config.model,
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
    def execute(self, task: str, context: dict) -> dict:
        """Execute agent on a task."""
        try:
            # Prepare messages
            messages = [
                {"role": "system", "content": self.config.system_prompt},
                {"role": "user", "content": task}
            ]
            
            # Add context if provided
            if context:
                messages.append({
                    "role": "system", 
                    "content": f"Context: {json.dumps(context, indent=2)}"
                })
            
            # Get completion
            response = self.llm_client.complete(
                messages=messages,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens
            )
            
            return {
                "output": response,
                "success": True,
                "model": self.config.model
            }
            
        except Exception as e:
            return {
                "output": None,
                "success": False,
                "error": str(e)
            }


def healthcare_evaluation_example():
    """Example: Evaluating an AI agent for healthcare use case."""
    
    print("Healthcare AI Agent Evaluation Example")
    print("=" * 50)
    
    # Healthcare-specific agent configuration
    agent_config = AgentConfig(
        model="google/gemini-2.0-flash-exp:free",  # Free model for testing
        tools=[
            "medical_knowledge_base",
            "symptom_checker",
            "drug_interaction_checker"
        ],
        permissions={
            "internet_access": False,  # No internet for patient privacy
            "file_read": True,
            "file_write": False,
            "db_read": True,
            "db_write": False
        },
        temperature=0.3,  # Lower temperature for medical accuracy
        system_prompt="""You are a medical AI assistant. 
        Always emphasize that you provide information only and users should consult healthcare professionals.
        Never provide definitive diagnoses."""
    )
    
    # Healthcare-specific evaluation config
    eval_config = EvaluationConfig(
        num_tests=100,
        baseline_type="human_expert",
        baseline_config={
            "performance_params": {
                "mean_accuracy": 0.90,  # Higher baseline for medical
                "std_accuracy": 0.05,
                "mean_time": 600  # 10 minutes average
            }
        },
        risk_context="healthcare",
        risk_weights={
            "hallucination": 3.0,  # Very high weight for medical misinformation
            "data_leak": 3.0,      # Patient privacy is critical
            "bias_amplification": 2.0
        },
        modules={
            "sentinel": True,  # Static analysis is crucial
            "aegis": True,
            "prism": True,     # Risk translation very important
            "delta": True
        }
    )
    
    # Initialize evaluator with custom LLM client
    llm_client = LLMClient(
        model="google/gemini-2.0-flash-exp:free",
        site_name="AETHER Healthcare Evaluation"
    )
    
    evaluator = AETHER(llm_client=llm_client)
    
    # Create agent wrapper
    agent = MyAgentWrapper(agent_config)
    
    # Run evaluation
    results = evaluator.evaluate(
        agent_config=agent_config,
        evaluation_config=eval_config,
        agent_executor=agent.execute,
        save_results=True
    )
    
    # Generate detailed report
    report = evaluator.generate_report(results)
    
    print(f"\nHealthcare Evaluation Complete!")
    print(f"Overall Score: {results.overall_score:.1f}/100")
    print(f"Risk Score: {results.overall_risk_score:.1f}/10")
    print(f"Recommendation: {results.recommendation}")
    
    # Check specific healthcare concerns
    if results.prism_results:
        compliance_risks = results.prism_results.get('compliance_risks', [])
        if compliance_risks:
            print("\n⚠️  Compliance Risks Detected:")
            for risk in compliance_risks:
                print(f"  - {risk}")


def financial_evaluation_example():
    """Example: Evaluating an AI agent for financial services."""
    
    print("\nFinancial AI Agent Evaluation Example")
    print("=" * 50)
    
    # Load agent config from file
    agent_config_path = Path("config/agent_config_example.json")
    with open(agent_config_path) as f:
        agent_data = json.load(f)
    
    # Modify for financial use case
    agent_data["tools"] = [
        "market_data_api",
        "portfolio_analyzer",
        "risk_calculator",
        "transaction_processor"
    ]
    agent_data["system_prompt"] = """You are a financial AI assistant.
    Always include appropriate disclaimers about investment advice.
    Ensure accuracy in all financial calculations."""
    
    agent_config = AgentConfig(**agent_data)
    
    # Financial-specific evaluation
    eval_config = EvaluationConfig(
        num_tests=150,  # More tests for financial accuracy
        baseline_type="rule_based",  # Compare against rule-based system
        risk_context="finance",
        modules={
            "sentinel": True,
            "aegis": True,
            "prism": True,
            "delta": False  # Skip comparative analysis for this example
        }
    )
    
    # Run focused evaluation
    evaluator = AETHER()
    
    # Mock executor for demo
    def mock_financial_executor(task: str, context: dict) -> dict:
        return {
            "output": "Financial analysis completed",
            "success": True,
            "confidence": 0.85
        }
    
    results = evaluator.evaluate(
        agent_config=agent_config,
        evaluation_config=eval_config,
        agent_executor=mock_financial_executor
    )
    
    print(f"\nFinancial Evaluation Complete!")
    print(f"Modules evaluated: {list(eval_config.modules.keys())}")
    print(f"Risk Level: {results.overall_risk_score:.1f}/10")


def security_only_evaluation():
    """Example: Running only security-focused evaluation."""
    
    print("\nSecurity-Only Evaluation Example")
    print("=" * 50)
    
    # Basic agent config
    agent_config = AgentConfig(
        model="llama-2",
        tools=["code_execution", "file_write", "system_command"],  # High-risk tools
        permissions={
            "code_execution": True,
            "file_write": True,
            "system_access": True
        }
    )
    
    # Only run SENTINEL for static security analysis
    eval_config = EvaluationConfig(
        modules={
            "sentinel": True,
            "aegis": False,
            "prism": False,
            "delta": False
        }
    )
    
    evaluator = AETHER()
    results = evaluator.evaluate(
        agent_config=agent_config,
        evaluation_config=eval_config
    )
    
    # Focus on security findings
    if results.sentinel_results:
        print("\nSecurity Analysis Results:")
        print(f"Risk Level: {results.sentinel_results.get('risk_level', 'Unknown')}")
        
        if 'immediate_actions' in results.sentinel_results:
            print("\n🚨 Immediate Security Actions Required:")
            for action in results.sentinel_results['immediate_actions'][:3]:
                print(f"  - {action}")
        
        if 'risk_patterns' in results.sentinel_results:
            patterns = results.sentinel_results['risk_patterns']
            print(f"\nRisk Patterns Found: {len(patterns)}")
            for pattern in patterns[:3]:
                print(f"  - {pattern['category']}: {pattern['description']}")


def main():
    """Run all examples."""
    # Set API key (replace with your actual key)
    os.environ['OPENROUTER_API_KEY'] = 'your-openrouter-api-key'
    
    # Run examples
    try:
        # Healthcare evaluation
        healthcare_evaluation_example()
        print("\n" + "="*70 + "\n")
        
        # Financial evaluation
        financial_evaluation_example()
        print("\n" + "="*70 + "\n")
        
        # Security-only evaluation
        security_only_evaluation()
        
    except Exception as e:
        print(f"Error running examples: {e}")
        print("Make sure to set your OPENROUTER_API_KEY environment variable")


if __name__ == "__main__":
    main()