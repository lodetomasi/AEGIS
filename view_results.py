#!/usr/bin/env python3
"""
Display AETHER test results in formatted output
"""
import json
from pathlib import Path
from datetime import datetime

def view_latest_results():
    """Display the most recent evaluation results"""
    
    # Find the latest results directory
    results_dir = Path("data/results/evaluations")
    if not results_dir.exists():
        print("❌ No results found.")
        return
    
    # Get all result files
    result_files = list(results_dir.glob("*.json"))
    if not result_files:
        print("❌ No result files found.")
        return
    
    # Group by suite
    suites = {}
    for file in result_files:
        suite_name = file.stem.split('_results')[0]
        if 'google' in suite_name or 'meta-llama' in suite_name or 'deepseek' in suite_name:
            # Extract suite name from model files
            parts = file.stem.split('_')
            suite_name = '_'.join(parts[:4])  # real_test_YYYYMMDD_HHMMSS
        
        if suite_name not in suites:
            suites[suite_name] = []
        suites[suite_name].append(file)
    
    # Get the latest suite
    latest_suite = sorted(suites.keys())[-1]
    print(f"📊 Evaluation results: {latest_suite}")
    print("=" * 60)
    
    # Load and show results for each model
    total_results = {}
    
    for result_file in suites[latest_suite]:
        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        model = data['model']
        results = data.get('results', [])
        
        # Calculate statistics
        successful = [r for r in results if 'error' not in r]
        failed = [r for r in results if 'error' in r]
        
        if successful:
            avg_score = sum(r.get('score', 0) for r in successful) / len(successful)
            avg_latency = sum(r.get('latency_ms', 0) for r in successful) / len(successful)
            total_tokens = sum(r.get('tokens', {}).get('total_tokens', 0) for r in successful)
        else:
            avg_score = 0
            avg_latency = 0
            total_tokens = 0
        
        total_results[model] = {
            'successful': len(successful),
            'failed': len(failed),
            'avg_score': avg_score,
            'avg_latency': avg_latency,
            'total_tokens': total_tokens,
            'results': results
        }
    
    # Show summary
    print("\n🎯 RESULTS SUMMARY")
    print("-" * 60)
    
    for model, stats in total_results.items():
        print(f"\n📦 Model: {model}")
        print(f"   ✅ Tasks completed: {stats['successful']}/{stats['successful'] + stats['failed']}")
        print(f"   📈 Average score: {stats['avg_score']:.2%}")
        print(f"   ⏱️  Average latency: {stats['avg_latency']:.0f}ms")
        print(f"   🔢 Total tokens: {stats['total_tokens']}")
        
        if stats['failed'] > 0:
            print(f"   ❌ Failed tasks: {stats['failed']}")
    
    # Show details per task
    print("\n\n📝 TASK DETAILS")
    print("-" * 60)
    
    # Group by task
    tasks_results = {}
    for model, data in total_results.items():
        for result in data['results']:
            task_id = result.get('task_id', 'unknown')
            if task_id not in tasks_results:
                tasks_results[task_id] = {}
            tasks_results[task_id][model] = result
    
    # Show results for each task
    for task_id, model_results in sorted(tasks_results.items()):
        print(f"\n🎯 Task: {task_id}")
        
        for model, result in model_results.items():
            if 'error' in result:
                print(f"   {model}: ❌ Error - {result['error']}")
            else:
                score = result.get('score', 0)
                correct = result.get('correct', None)
                latency = result.get('latency_ms', 0)
                
                status = "✅" if score >= 0.8 else "⚠️"
                print(f"   {model}: {status} Score: {score:.2f}, Latency: {latency:.0f}ms")
                
                if correct is not None:
                    print(f"      → Correct: {'✅' if correct else '❌'}")
    
    # Show best model
    print("\n\n🏆 MODEL RANKINGS")
    print("-" * 60)
    
    ranked_models = sorted(
        [(model, stats) for model, stats in total_results.items() if stats['successful'] > 0],
        key=lambda x: (x[1]['avg_score'], -x[1]['avg_latency']),
        reverse=True
    )
    
    for i, (model, stats) in enumerate(ranked_models, 1):
        print(f"{i}. {model}")
        print(f"   Score: {stats['avg_score']:.2%} | Latency: {stats['avg_latency']:.0f}ms")

if __name__ == "__main__":
    print("🔍 AETHER - Results Viewer")
    print("=" * 60)
    view_latest_results()