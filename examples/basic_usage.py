"""
Basic usage example for AETHER evaluation system.
"""

import os
from aether import AETHER, AgentConfig, EvaluationConfig


def main():
    """Run basic AETHER evaluation."""
    
    # Set OpenRouter API key
    os.environ['OPENROUTER_API_KEY'] = 'your-api-key-here'
    
    # 1. Configure the agent to evaluate
    agent_config = AgentConfig(
        model="gpt-4",
        tools=["web_search", "calculator", "file_reader"],
        permissions={
            "internet_access": True,
            "file_read": True,
            "file_write": False,
            "code_execution": False
        },
        temperature=0.7,
        max_tokens=2048,
        system_prompt="You are a helpful AI assistant."
    )
    
    # 2. Configure the evaluation
    eval_config = EvaluationConfig(
        num_tests=50,
        baseline_type="human_expert",
        risk_context="general",
        report_format=["markdown", "json"]
    )
    
    # 3. Initialize AETHER
    evaluator = AETHER(config_file="config/evaluation_config.yaml")
    
    # 4. Define agent executor (wrapper around your agent)
    def agent_executor(task: str, context: dict) -> dict:
        """
        Execute the agent on a task.
        
        This should call your actual agent implementation.
        For this example, we'll simulate a response.
        """
        # In real usage, this would call your agent
        # response = your_agent.execute(task, context)
        
        # Simulated response
        return {
            "output": f"Simulated response to: {task}",
            "success": True,
            "execution_time": 1.5
        }
    
    # 5. Run evaluation
    print("Starting AETHER evaluation...")
    results = evaluator.evaluate(
        agent_config=agent_config,
        evaluation_config=eval_config,
        agent_executor=agent_executor,
        save_results=True
    )
    
    # 6. Generate report
    print("\nGenerating evaluation report...")
    report = evaluator.generate_report(results)
    
    # 7. Print summary
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    print(f"Overall Score: {results.overall_score:.1f}/100")
    print(f"Risk Level: {results.overall_risk_score:.1f}/10")
    print(f"Recommendation: {results.recommendation}")
    print(f"\nReport saved to: reports/{results.evaluation_id}_report.md")


if __name__ == "__main__":
    main()