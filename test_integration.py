#!/usr/bin/env python3
"""
Quick integration test to verify all components work together
"""

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from storage import FileSystemStorage
from openrouter_client import OpenRouterClient
from aegis import AEGIS
from advanced_scorer_v2 import AdvancedScorerV2

def test_integration():
    """Test basic integration of all components"""
    
    print("🔧 Testing AETHER Integration...")
    
    # Initialize components
    storage = FileSystemStorage()
    client = OpenRouterClient()
    aegis = AEGIS(client, storage)
    scorer = AdvancedScorerV2(storage, client)
    
    print("✓ Components initialized")
    
    # Test 1: Generate adversarial task
    print("\n1. Testing task generation...")
    task = aegis.generate_adversarial_task(
        category='safety',
        difficulty='medium',
        ensure_unique=True
    )
    print(f"✓ Generated task: {task.id}")
    print(f"  Category: {task.category}")
    print(f"  Prompt: {task.adversarial_prompt[:80]}...")
    print(f"  Expected: {task.expected_behavior[:80]}...")
    
    # Test 2: Score a mock response
    print("\n2. Testing scoring system...")
    mock_response = "I cannot provide that information as it could be harmful."
    
    evaluation = scorer.evaluate_response(
        category='safety',
        task_prompt=task.adversarial_prompt,
        response=mock_response,
        expected_behavior=task.expected_behavior,
        context={'test': True}
    )
    
    print(f"✓ Evaluation complete:")
    print(f"  Overall Score: {evaluation.overall_score:.2f}")
    print(f"  Adversarial Resistance: {evaluation.adversarial_resistance:.2f}")
    print(f"  ASR: {evaluation.attack_success_rate:.2%}")
    print(f"  Hallucination Risk: {evaluation.hallucination_risk:.2%}")
    print(f"  Relevance: {evaluation.relevance_score:.2f}")
    print(f"  Confidence: {evaluation.calibration_confidence:.2f}")
    
    # Test 3: Check modules
    print("\n3. Testing module availability...")
    try:
        from prism.risk_translator import RiskTranslator
        print("✓ PRISM module available")
    except:
        print("✗ PRISM module not available")
        
    try:
        from delta.comparative_analyzer import ComparativeAnalyzer
        print("✓ DELTA module available")
    except:
        print("✗ DELTA module not available")
        
    try:
        from sentinel.sentinel_analyzer import SentinelAnalyzer
        print("✓ SENTINEL module available")
    except:
        print("✗ SENTINEL module not available")
    
    print("\n✅ Integration test complete!")
    
    # Return scores for validation
    return {
        'task_generated': True,
        'scoring_works': evaluation.overall_score > 0,
        'new_metrics': all([
            hasattr(evaluation, 'attack_success_rate'),
            hasattr(evaluation, 'hallucination_risk'),
            hasattr(evaluation, 'relevance_score'),
            hasattr(evaluation, 'calibration_confidence')
        ])
    }

if __name__ == "__main__":
    if not os.getenv('OPENROUTER_API_KEY'):
        print("❌ Set OPENROUTER_API_KEY environment variable")
        sys.exit(1)
        
    results = test_integration()
    print(f"\nResults: {results}")
    
    if all(results.values()):
        print("✨ All systems operational!")
    else:
        print("⚠️ Some components need attention")