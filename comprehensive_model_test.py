"""
Comprehensive Model Testing with Real APIs
==========================================

Test all production models across multiple domains and categories.
Designed to run in background with progress monitoring and incremental results.
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any
import signal

# Add src to path
sys.path.append('src')

from aether_integrated import AETHERIntegrated


class ComprehensiveModelTest:
    """Comprehensive testing of all models with real API calls."""
    
    def __init__(self):
        """Initialize test configuration."""
        self.start_time = datetime.utcnow()
        self.test_id = self.start_time.strftime("%Y%m%d_%H%M%S")
        
        # Setup logging
        log_file = f"results/comprehensive_test_{self.test_id}.log"
        os.makedirs("results", exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Test configuration
        self.models = [
            "mistralai/mixtral-8x22b-instruct",
            "anthropic/claude-opus-4", 
            "meta-llama/llama-3.3-70b-instruct",
            "deepseek/deepseek-r1-0528",
            "google/gemini-2.5-pro"
        ]
        
        self.categories = ["safety", "harmful", "bias", "accuracy"]
        self.domains = ["healthcare", "finance", "legal", "general"]
        
        # Results storage
        self.results = {
            "test_metadata": {
                "test_id": self.test_id,
                "start_time": self.start_time.isoformat(),
                "models": self.models,
                "categories": self.categories,
                "domains": self.domains
            },
            "model_results": {},
            "summary": {},
            "errors": []
        }
        
        # Progress tracking
        self.total_tests = len(self.models) * len(self.categories) * 3  # 3 tasks per category
        self.completed_tests = 0
        
        # Graceful shutdown handling
        signal.signal(signal.SIGINT, self._save_and_exit)
        signal.signal(signal.SIGTERM, self._save_and_exit)
        
        self.logger.info(f"🚀 Starting comprehensive model test {self.test_id}")
        self.logger.info(f"📊 Total tests planned: {self.total_tests}")
        self.logger.info(f"🤖 Models: {len(self.models)}")
        self.logger.info(f"📝 Categories: {len(self.categories)}")
        
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """Run comprehensive test across all models and categories."""
        
        try:
            # Initialize AETHER framework
            self.logger.info("🔧 Initializing AETHER framework...")
            framework = AETHERIntegrated()
            
            # Test each model
            for model_idx, model in enumerate(self.models):
                self.logger.info(f"\n{'='*60}")
                self.logger.info(f"🤖 Testing Model {model_idx + 1}/{len(self.models)}: {model}")
                self.logger.info(f"{'='*60}")
                
                model_results = self._test_single_model(framework, model)
                self.results["model_results"][model] = model_results
                
                # Save incremental results
                self._save_incremental_results()
                
                # Progress update
                progress = (model_idx + 1) / len(self.models) * 100
                self.logger.info(f"📈 Overall Progress: {progress:.1f}%")
                
            # Generate final summary
            self.logger.info("\n🔍 Generating comprehensive summary...")
            self.results["summary"] = self._generate_summary()
            
            # Save final results
            self._save_final_results()
            
            self.logger.info(f"\n✅ Comprehensive test completed successfully!")
            self.logger.info(f"⏱️  Total time: {self._get_elapsed_time()}")
            
            return self.results
            
        except Exception as e:
            self.logger.error(f"❌ Test failed with error: {e}")
            self.results["errors"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "error": str(e),
                "completed_tests": self.completed_tests
            })
            self._save_final_results()
            raise
    
    def _test_single_model(self, framework: AETHERIntegrated, model: str) -> Dict[str, Any]:
        """Test a single model across all categories."""
        
        model_results = {
            "model": model,
            "start_time": datetime.utcnow().isoformat(),
            "category_results": {},
            "summary": {},
            "errors": []
        }
        
        for category in self.categories:
            self.logger.info(f"📝 Testing category: {category}")
            
            try:
                category_result = self._test_model_category(framework, model, category)
                model_results["category_results"][category] = category_result
                
                # Update progress
                self.completed_tests += 3  # 3 tasks per category
                progress = (self.completed_tests / self.total_tests) * 100
                self.logger.info(f"✅ {category} completed. Progress: {progress:.1f}%")
                
            except Exception as e:
                error_msg = f"Error testing {model} on {category}: {e}"
                self.logger.error(f"❌ {error_msg}")
                model_results["errors"].append(error_msg)
                
            # Rate limiting - 10 second delay between categories
            time.sleep(10)
        
        model_results["end_time"] = datetime.utcnow().isoformat()
        model_results["summary"] = self._summarize_model_results(model_results)
        
        return model_results
    
    def _test_model_category(self, framework: AETHERIntegrated, model: str, category: str) -> Dict[str, Any]:
        """Test a model on a specific category using comprehensive evaluation."""
        
        category_results = {
            "category": category,
            "model": model,
            "result": {},
            "summary": {}
        }
        
        try:
            self.logger.info(f"  🎯 Running comprehensive evaluation for {category}")
            
            # Use the framework's comprehensive evaluation
            start_time = time.time()
            
            result = framework.comprehensive_evaluation(
                models=[model],
                categories=[category],
                industry="general",
                analyze_architecture=False  # Skip for speed
            )
            
            execution_time = time.time() - start_time
            
            # Extract overall results and find this model's data
            detailed_results = result.get("detailed_results", [])
            model_results = [r for r in detailed_results if r.get("model") == model]
            
            # Calculate average scores for this model
            if model_results:
                avg_score = sum(r.get("overall_score", 0) for r in model_results) / len(model_results)
                total_time = execution_time
            else:
                avg_score = 0
                total_time = execution_time
            
            # Add timing and metadata
            category_results["result"] = {
                "evaluation_result": {"overall_score": avg_score, "detailed_results": model_results},
                "execution_time": total_time,
                "timestamp": datetime.utcnow().isoformat(),
                "summary_stats": result.get("summary", {})
            }
            
            # Extract score for logging
            self.logger.info(f"    ✅ Score: {avg_score:.3f}, Time: {total_time:.1f}s")
            
        except Exception as e:
            error_msg = f"Evaluation failed: {e}"
            self.logger.error(f"    ❌ {error_msg}")
            category_results["result"] = {
                "error": error_msg,
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Summarize category results
        category_results["summary"] = self._summarize_category_results(category_results)
        
        return category_results
    
    def _summarize_category_results(self, category_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize results for a single category."""
        
        result_data = category_results.get("result", {})
        
        # Check if there was an error
        if "error" in result_data:
            return {
                "success_rate": 0.0,
                "average_score": 0.0,
                "average_time": 0.0,
                "error_count": 1,
                "task_count": 1
            }
        
        # Extract evaluation result
        eval_result = result_data.get("evaluation_result", {})
        execution_time = result_data.get("execution_time", 0)
        overall_score = eval_result.get("overall_score", 0)
        
        return {
            "success_rate": 1.0,
            "average_score": overall_score,
            "average_time": execution_time,
            "error_count": 0,
            "task_count": 1
        }
    
    def _summarize_model_results(self, model_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize results for a single model."""
        
        category_summaries = [
            summary for summary in 
            [cr.get("summary", {}) for cr in model_results["category_results"].values()]
            if summary
        ]
        
        if not category_summaries:
            return {"overall_score": 0.0, "success_rate": 0.0}
        
        overall_score = sum(s.get("average_score", 0) for s in category_summaries) / len(category_summaries)
        success_rate = sum(s.get("success_rate", 0) for s in category_summaries) / len(category_summaries)
        
        return {
            "overall_score": overall_score,
            "success_rate": success_rate,
            "categories_tested": len(category_summaries),
            "total_errors": len(model_results["errors"])
        }
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate comprehensive test summary."""
        
        model_summaries = []
        for model, results in self.results["model_results"].items():
            summary = results.get("summary", {})
            if summary:
                summary["model"] = model
                model_summaries.append(summary)
        
        if not model_summaries:
            return {"status": "failed", "reason": "No successful model tests"}
        
        # Calculate overall statistics
        overall_scores = [s["overall_score"] for s in model_summaries]
        success_rates = [s["success_rate"] for s in model_summaries]
        
        # Find best performing model
        best_model = max(model_summaries, key=lambda x: x["overall_score"])
        
        return {
            "test_status": "completed",
            "models_tested": len(model_summaries),
            "total_tasks": self.completed_tests,
            "overall_average_score": sum(overall_scores) / len(overall_scores),
            "overall_success_rate": sum(success_rates) / len(success_rates),
            "best_model": {
                "name": best_model["model"],
                "score": best_model["overall_score"],
                "success_rate": best_model["success_rate"]
            },
            "model_rankings": sorted(model_summaries, key=lambda x: x["overall_score"], reverse=True),
            "total_time": self._get_elapsed_time(),
            "end_time": datetime.utcnow().isoformat()
        }
    
    def _save_incremental_results(self):
        """Save incremental results during test execution."""
        filename = f"results/comprehensive_test_{self.test_id}_incremental.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
    
    def _save_final_results(self):
        """Save final comprehensive results."""
        filename = f"results/comprehensive_test_{self.test_id}_final.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        # Also create a summary report
        self._create_summary_report()
    
    def _create_summary_report(self):
        """Create a human-readable summary report."""
        filename = f"results/comprehensive_test_{self.test_id}_report.md"
        
        with open(filename, 'w') as f:
            f.write(f"# Comprehensive Model Test Report\n\n")
            f.write(f"**Test ID**: {self.test_id}\n")
            f.write(f"**Date**: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC\n")
            f.write(f"**Duration**: {self._get_elapsed_time()}\n\n")
            
            if "summary" in self.results and self.results["summary"]:
                summary = self.results["summary"]
                f.write(f"## Overall Results\n\n")
                f.write(f"- **Models Tested**: {summary.get('models_tested', 0)}\n")
                f.write(f"- **Total Tasks**: {summary.get('total_tasks', 0)}\n")
                f.write(f"- **Average Score**: {summary.get('overall_average_score', 0):.3f}\n")
                f.write(f"- **Success Rate**: {summary.get('overall_success_rate', 0):.1%}\n\n")
                
                if "best_model" in summary:
                    best = summary["best_model"]
                    f.write(f"## Best Performing Model\n\n")
                    f.write(f"**{best['name']}**\n")
                    f.write(f"- Score: {best['score']:.3f}\n")
                    f.write(f"- Success Rate: {best['success_rate']:.1%}\n\n")
                
                if "model_rankings" in summary:
                    f.write(f"## Model Rankings\n\n")
                    for i, model in enumerate(summary["model_rankings"], 1):
                        f.write(f"{i}. **{model['model']}** - Score: {model['overall_score']:.3f}\n")
    
    def _get_elapsed_time(self) -> str:
        """Get elapsed time as formatted string."""
        elapsed = datetime.utcnow() - self.start_time
        hours, remainder = divmod(elapsed.total_seconds(), 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
    
    def _save_and_exit(self, signum, frame):
        """Graceful shutdown handler."""
        self.logger.info(f"\n⚠️  Received interrupt signal. Saving results...")
        self.results["summary"] = {
            "test_status": "interrupted", 
            "completed_tests": self.completed_tests,
            "total_planned": self.total_tests
        }
        self._save_final_results()
        self.logger.info(f"💾 Results saved. Exiting...")
        sys.exit(0)


def main():
    """Main execution function."""
    
    # Check API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set. Please export your API key.")
        return 1
    
    print("🚀 Starting comprehensive model testing...")
    print("📝 This will test all models across multiple categories")
    print("⏱️  Estimated time: 30-45 minutes")
    print("💾 Results will be saved incrementally")
    print("🛑 Press Ctrl+C to gracefully stop and save results\n")
    
    try:
        tester = ComprehensiveModelTest()
        results = tester.run_comprehensive_test()
        
        print(f"\n{'='*60}")
        print("✅ COMPREHENSIVE TEST COMPLETED")
        print(f"{'='*60}")
        
        if "summary" in results and results["summary"]:
            summary = results["summary"]
            print(f"📊 Models tested: {summary.get('models_tested', 0)}")
            print(f"📝 Total tasks: {summary.get('total_tasks', 0)}")
            print(f"🎯 Average score: {summary.get('overall_average_score', 0):.3f}")
            print(f"✅ Success rate: {summary.get('overall_success_rate', 0):.1%}")
            
            if "best_model" in summary:
                best = summary["best_model"]
                print(f"🏆 Best model: {best['name']} ({best['score']:.3f})")
        
        print(f"💾 Results saved to: results/comprehensive_test_{tester.test_id}_final.json")
        print(f"📄 Report saved to: results/comprehensive_test_{tester.test_id}_report.md")
        
        return 0
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)