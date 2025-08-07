#!/usr/bin/env python3
"""
Quick test with reduced scope for final verification
"""

import os
import sys
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage import FileSystemStorage
from openrouter_client import OpenRouterClient
from aegis import AEGIS
from advanced_scorer_v2 import AdvancedScorerV2

def quick_test():
    """Run quick test with 1 task per category"""
    
    print("🚀 AETHER Quick Test - Final Verification")
    print("=" * 60)
    
    # Initialize
    storage = FileSystemStorage()
    client = OpenRouterClient()
    aegis = AEGIS(client, storage)
    scorer = AdvancedScorerV2(storage, client)
    
    models = ['mistralai/mixtral-8x22b-instruct']
    categories = ['safety', 'harmful', 'accuracy']
    
    results = []
    
    for category in categories:
        print(f"\n📁 Testing {category}...")
        
        # Generate task
        task = aegis.generate_adversarial_task(category, 'medium', True)
        print(f"Task: {task.adversarial_prompt[:60]}...")
        
        # Get response
        response = client.chat_completion(
            model=models[0],
            messages=[{"role": "user", "content": task.adversarial_prompt}],
            temperature=0.0,
            max_tokens=200
        )
        
        # Evaluate
        eval_result = scorer.evaluate_response(
            category=category,
            task_prompt=task.adversarial_prompt,
            response=response.content,
            expected_behavior=task.expected_behavior,
            context={'model': models[0], 'category': category}
        )
        
        results.append({
            'category': category,
            'overall_score': eval_result.overall_score,
            'adversarial_resistance': eval_result.adversarial_resistance,
            'asr': eval_result.attack_success_rate,
            'hallucination_risk': eval_result.hallucination_risk,
            'relevance': eval_result.relevance_score,
            'confidence': eval_result.calibration_confidence
        })
        
        print(f"Score: {eval_result.overall_score:.2f} | ASR: {eval_result.attack_success_rate:.0%} | Relevance: {eval_result.relevance_score:.2f} | Confidence: {eval_result.calibration_confidence:.2f}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    print("=" * 60)
    
    avg_score = sum(r['overall_score'] for r in results) / len(results)
    avg_relevance = sum(r['relevance'] for r in results) / len(results)
    avg_confidence = sum(r['confidence'] for r in results) / len(results)
    
    print(f"Average Overall Score: {avg_score:.2f}")
    print(f"Average Relevance: {avg_relevance:.2f}")
    print(f"Average Confidence: {avg_confidence:.2f}")
    print(f"All ASRs: {[r['asr'] for r in results]}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"results/quick_test_{timestamp}.json"
    os.makedirs('results', exist_ok=True)
    
    with open(filename, 'w') as f:
        json.dump({
            'timestamp': timestamp,
            'results': results,
            'summary': {
                'avg_score': avg_score,
                'avg_relevance': avg_relevance,
                'avg_confidence': avg_confidence
            }
        }, f, indent=2)
    
    print(f"\n💾 Results saved to {filename}")
    print("✅ Test complete!")

if __name__ == "__main__":
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ Set OPENROUTER_API_KEY")
        sys.exit(1)
    
    quick_test()