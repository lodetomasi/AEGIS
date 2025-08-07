#!/usr/bin/env python3
"""
AETHER Test Runner - Properly handles rate limits and generates dynamic tasks
"""

import os
import sys
import json
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage import FileSystemStorage
from openrouter_client import OpenRouterClient
from aegis import AEGIS
from advanced_scorer import AdvancedScorer

def wait_with_countdown(seconds):
    """Show countdown while waiting"""
    for i in range(seconds, 0, -1):
        print(f"\rWaiting {i} seconds to respect rate limits...", end='', flush=True)
        time.sleep(1)
    print("\r" + " " * 50 + "\r", end='', flush=True)

def main():
    print("=== AETHER Framework Test ===")
    print("Dynamic Adversarial AI Evaluation\n")
    
    # Check API key
    api_key = os.environ.get('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ Error: Set OPENROUTER_API_KEY environment variable")
        print("export OPENROUTER_API_KEY=your_key")
        return
        
    print(f"✅ API Key configured")
    
    # Initialize
    storage = FileSystemStorage()
    client = OpenRouterClient()
    aegis = AEGIS(client, storage)
    advanced_scorer = AdvancedScorer(storage, client)
    
    # Configuration
    categories = ['safety', 'accuracy', 'bias', 'harmful', 'reasoning']
    models = [
        'mistralai/mixtral-8x22b-instruct',
        'anthropic/claude-opus-4',
        'meta-llama/llama-3.3-70b-instruct',
        'deepseek/deepseek-r1-0528',
        'google/gemini-2.5-pro'
    ]
    
    # Results storage
    suite_name = f"aether_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    results = []
    
    print(f"\nTest Configuration:")
    print(f"- Categories: {len(categories)}")
    print(f"- Models: {len(models)}")
    print(f"- Total evaluations: {len(categories) * len(models)}")
    print(f"- Estimated time: {(len(categories) + len(categories) * len(models)) * 30 / 60:.1f} minutes")
    print(f"\nStarting in 5 seconds...\n")
    time.sleep(5)
    
    # Generate and evaluate tasks
    generated_tasks = {}
    
    # Phase 1: Generate all tasks first (with delays)
    print("=== Phase 1: Generating Dynamic Tasks ===\n")
    
    for i, category in enumerate(categories):
        print(f"[{i+1}/{len(categories)}] Generating {category} task...")
        
        if i > 0:
            wait_with_countdown(30)
            
        try:
            # Generate task
            task = aegis.generate_adversarial_task(category)
            generated_tasks[category] = task
            
            print(f"✅ Generated {category} task:")
            print(f"   Prompt: {task.adversarial_prompt[:80]}...")
            print(f"   Expected: {task.expected_behavior[:80]}...")
            print("")
            
        except Exception as e:
            print(f"❌ Error generating {category} task: {e}")
            # Create fallback task
            generated_tasks[category] = type('Task', (), {
                'adversarial_prompt': f"Test {category} capabilities of the AI system.",
                'expected_behavior': "Respond appropriately and safely.",
                'category': category,
                'id': f"{category}_fallback"
            })()
    
    # Phase 2: Evaluate tasks with models
    print("\n=== Phase 2: Model Evaluation ===\n")
    
    evaluation_count = 0
    total_evaluations = len(generated_tasks) * len(models)
    
    for category, task in generated_tasks.items():
        print(f"\n--- Evaluating {category} task ---")
        print(f"Task: {task.adversarial_prompt[:100]}...")
        
        for model in models:
            evaluation_count += 1
            print(f"\n[{evaluation_count}/{total_evaluations}] Testing {model}")
            
            # Always wait between API calls
            wait_with_countdown(30)
            
            try:
                # Make API call
                start_time = time.time()
                response = client.chat_completion(
                    model=model,
                    messages=[{"role": "user", "content": task.adversarial_prompt}],
                    temperature=0.0,
                    max_tokens=1000
                )
                latency = (time.time() - start_time) * 1000
                
                # Score response with advanced scorer
                evaluation = advanced_scorer.evaluate_response(
                    category=category,
                    task_prompt=task.adversarial_prompt,
                    response=response.content,
                    expected_behavior=task.expected_behavior
                )
                
                print(f"✅ Success!")
                print(f"   Overall Score: {evaluation.overall_score:.2f}")
                print(f"   Adversarial Resistance: {evaluation.adversarial_resistance:.2f}")
                print(f"   Contextual Appropriateness: {evaluation.contextual_appropriateness:.2f}")
                print(f"   Business Risk Score: {evaluation.business_risk_score:.2f}")
                print(f"   Latency: {latency:.0f}ms")
                print(f"   Response: {response.content[:100]}...")
                
                # Store result
                results.append({
                    'task_id': task.id,
                    'category': category,
                    'model': model,
                    'prompt': task.adversarial_prompt,
                    'expected': task.expected_behavior,
                    'response': response.content,
                    'score': evaluation.overall_score,
                    'base_score': evaluation.base_score,
                    'adversarial_resistance': evaluation.adversarial_resistance,
                    'contextual_appropriateness': evaluation.contextual_appropriateness,
                    'business_risk_score': evaluation.business_risk_score,
                    'risk_metrics': evaluation.details['risk_metrics'],
                    'adversarial_tactics_detected': evaluation.details['adversarial_tactics_detected'],
                    'context_alignment': evaluation.details['context_alignment'],
                    'latency_ms': latency,
                    'success': True,
                    'timestamp': datetime.now().isoformat()
                })
                
            except Exception as e:
                print(f"❌ Error: {e}")
                results.append({
                    'task_id': task.id,
                    'category': category,
                    'model': model,
                    'prompt': task.adversarial_prompt,
                    'error': str(e),
                    'success': False,
                    'timestamp': datetime.now().isoformat()
                })
    
    # Save results
    results_dir = 'data/results/evaluations'
    os.makedirs(results_dir, exist_ok=True)
    
    results_file = os.path.join(results_dir, f'{suite_name}_results.json')
    
    with open(results_file, 'w') as f:
        json.dump({
            'suite_name': suite_name,
            'timestamp': datetime.now().isoformat(),
            'categories': categories,
            'models': models,
            'results': results
        }, f, indent=2)
    
    print(f"\n\n✅ Results saved to: {results_file}")
    
    # Summary
    successful = sum(1 for r in results if r.get('success', False))
    print(f"\n=== SUMMARY ===")
    print(f"Total evaluations: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    
    if successful > 0:
        avg_score = sum(r['score'] for r in results if r.get('success')) / successful
        avg_latency = sum(r['latency_ms'] for r in results if r.get('success')) / successful
        avg_adversarial = sum(r['adversarial_resistance'] for r in results if r.get('success')) / successful
        avg_contextual = sum(r['contextual_appropriateness'] for r in results if r.get('success')) / successful
        avg_risk = sum(r['business_risk_score'] for r in results if r.get('success')) / successful
        
        print(f"Average overall score: {avg_score:.2f}")
        print(f"Average adversarial resistance: {avg_adversarial:.2f}")
        print(f"Average contextual appropriateness: {avg_contextual:.2f}")
        print(f"Average business risk score: {avg_risk:.2f}")
        print(f"Average latency: {avg_latency:.0f}ms")
        
        # Per model summary
        print("\nModel Performance:")
        for model in models:
            model_results = [r for r in results if r.get('model') == model and r.get('success')]
            if model_results:
                model_avg = sum(r['score'] for r in model_results) / len(model_results)
                model_adv = sum(r['adversarial_resistance'] for r in model_results) / len(model_results)
                model_ctx = sum(r['contextual_appropriateness'] for r in model_results) / len(model_results)
                print(f"\n  {model}:")
                print(f"    Overall: {model_avg:.2f}")
                print(f"    Adversarial: {model_adv:.2f}")
                print(f"    Contextual: {model_ctx:.2f}")


if __name__ == "__main__":
    main()