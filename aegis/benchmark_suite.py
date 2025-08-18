"""Benchmark suite orchestration for AEGIS."""

import json
import time
import logging
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from contextlib import contextmanager
import random
import concurrent.futures
from pathlib import Path

from .task_generator import TaskGenerator, TaskInstance
from .environment_simulator import EnvironmentSimulator, MockEnvironment
from .reliability_calculator import ReliabilityCalculator, TestRun

# Setup logger
logger = logging.getLogger(__name__)


# Mock classes for missing dependencies
class LLMClient:
    """Mock LLM client for typing purposes"""

    pass


class MetricsCollector:
    """Mock metrics collector"""

    def __init__(self):
        pass

    def collect_metrics(self, *args, **kwargs):
        return {}


@contextmanager
def timer_context(name: str):
    """Simple timer context manager"""
    start = time.time()
    yield
    end = time.time()
    logger.debug(f"{name} took {end - start:.2f}s")


@dataclass
class BenchmarkConfig:
    """Configuration for benchmark execution."""

    num_tasks: int = 10
    runs_per_task: int = 3
    categories: Optional[List[str]] = None
    difficulties: Optional[List[str]] = None
    parallel_execution: bool = False
    max_workers: int = 4
    timeout_seconds: int = 300
    randomize_order: bool = True
    seed: Optional[int] = None
    environment_reset: bool = True
    save_results: bool = True
    results_dir: str = "./benchmark_results"


@dataclass
class BenchmarkResult:
    """Result of a complete benchmark run."""

    benchmark_id: str
    config: BenchmarkConfig
    tasks: List[TaskInstance]
    test_runs: List[TestRun]
    reliability_metrics: Dict[str, Any]
    aggregate_metrics: Dict[str, Any]
    start_time: datetime
    end_time: datetime
    duration: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "benchmark_id": self.benchmark_id,
            "config": self.config.__dict__,
            "tasks": [t.to_dict() for t in self.tasks],
            "test_runs": [
                {
                    "task_id": r.task_id,
                    "run_number": r.run_number,
                    "success": r.success,
                    "score": r.score,
                    "execution_time": r.execution_time,
                    "errors": r.errors,
                    "timestamp": r.timestamp.isoformat(),
                }
                for r in self.test_runs
            ],
            "reliability_metrics": self.reliability_metrics,
            "aggregate_metrics": self.aggregate_metrics,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration": self.duration,
            "metadata": self.metadata,
        }


class BenchmarkSuite:
    """Orchestrates benchmark execution for agent evaluation."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize benchmark suite.

        Args:
            llm_client: LLM client for agent evaluation
        """
        self.task_generator = TaskGenerator()
        self.env_simulator = EnvironmentSimulator()
        self.reliability_calc = ReliabilityCalculator()
        self.metrics_collector = MetricsCollector()
        self.llm_client = llm_client or LLMClient()

        # Initialize default environments
        self._setup_default_environments()

    def _setup_default_environments(self):
        """Setup default test environments."""
        self.env_simulator.create_environment("database", "test_db")
        self.env_simulator.create_environment("filesystem", "test_fs")
        self.env_simulator.create_environment("api", "test_api")

    def run_benchmark(
        self,
        agent_executor: Callable[[str, Dict[str, Any]], Dict[str, Any]],
        config: Optional[BenchmarkConfig] = None,
    ) -> BenchmarkResult:
        """
        Run complete benchmark suite.

        Args:
            agent_executor: Function that executes agent on a task
            config: Benchmark configuration

        Returns:
            Benchmark results
        """
        config = config or BenchmarkConfig()
        benchmark_id = f"benchmark_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        logger.info(f"Starting benchmark {benchmark_id}")
        start_time = datetime.utcnow()

        # Set random seed if specified
        if config.seed is not None:
            random.seed(config.seed)

        # Generate tasks
        with timer_context("task_generation"):
            tasks = self._generate_tasks(config)

        # Randomize order if requested
        if config.randomize_order:
            random.shuffle(tasks)

        # Run tests
        test_runs = []

        if config.parallel_execution:
            with timer_context("parallel_execution"):
                test_runs = self._run_parallel(tasks, agent_executor, config)
        else:
            with timer_context("sequential_execution"):
                test_runs = self._run_sequential(tasks, agent_executor, config)

        # Calculate metrics
        with timer_context("metrics_calculation"):
            reliability_metrics = self._calculate_reliability_metrics(test_runs)
            aggregate_metrics = self.reliability_calc.get_aggregate_metrics()

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Create result
        result = BenchmarkResult(
            benchmark_id=benchmark_id,
            config=config,
            tasks=tasks,
            test_runs=test_runs,
            reliability_metrics=reliability_metrics,
            aggregate_metrics=aggregate_metrics,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            metadata={"metrics": self.metrics_collector.export_json()},
        )

        # Save results if requested
        if config.save_results:
            self._save_results(result)

        logger.info(f"Benchmark {benchmark_id} completed in {duration:.2f}s")

        return result

    def _generate_tasks(self, config: BenchmarkConfig) -> List[TaskInstance]:
        """Generate tasks for benchmark."""
        tasks = []

        # Determine how many tasks per category/difficulty
        categories = config.categories or self.task_generator.get_categories()
        difficulties = config.difficulties or self.task_generator.get_difficulties()

        tasks_per_combo = max(
            1, config.num_tasks // (len(categories) * len(difficulties))
        )

        for category in categories:
            for difficulty in difficulties:
                batch = self.task_generator.generate_batch(
                    count=tasks_per_combo,
                    category=category,
                    difficulty=difficulty,
                    seed=config.seed,
                )
                tasks.extend(batch)

        # Ensure we have exactly the requested number
        if len(tasks) > config.num_tasks:
            tasks = tasks[: config.num_tasks]
        elif len(tasks) < config.num_tasks:
            # Generate additional random tasks
            additional = self.task_generator.generate_batch(
                count=config.num_tasks - len(tasks), seed=config.seed
            )
            tasks.extend(additional)

        return tasks

    def _run_sequential(
        self,
        tasks: List[TaskInstance],
        agent_executor: Callable,
        config: BenchmarkConfig,
    ) -> List[TestRun]:
        """Run tests sequentially."""
        test_runs = []

        for task in tasks:
            logger.info(f"Running task {task.id}")

            for run_num in range(config.runs_per_task):
                if config.environment_reset:
                    self.env_simulator.reset_all()

                run = self._execute_single_test(
                    task, run_num, agent_executor, config.timeout_seconds
                )
                test_runs.append(run)
                self.reliability_calc.add_run(run)

        return test_runs

    def _run_parallel(
        self,
        tasks: List[TaskInstance],
        agent_executor: Callable,
        config: BenchmarkConfig,
    ) -> List[TestRun]:
        """Run tests in parallel."""
        test_runs = []

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=config.max_workers
        ) as executor:
            futures = []

            for task in tasks:
                for run_num in range(config.runs_per_task):
                    future = executor.submit(
                        self._execute_single_test,
                        task,
                        run_num,
                        agent_executor,
                        config.timeout_seconds,
                    )
                    futures.append(future)

            for future in concurrent.futures.as_completed(futures):
                try:
                    run = future.result()
                    test_runs.append(run)
                    self.reliability_calc.add_run(run)
                except Exception as e:
                    logger.error(f"Test execution failed: {e}")

        return test_runs

    def _execute_single_test(
        self,
        task: TaskInstance,
        run_number: int,
        agent_executor: Callable,
        timeout: int,
    ) -> TestRun:
        """Execute a single test run."""
        start_time = time.time()
        errors = []
        success = False
        score = 0.0

        try:
            # Prepare environment context
            env_context = self._prepare_environment_context(task)

            # Execute agent
            agent_result = agent_executor(task.task_text, env_context)

            # Evaluate result
            evaluation = self._evaluate_result(task, agent_result)

            success = evaluation["success"]
            score = evaluation["score"]
            errors = evaluation.get("errors", [])

        except Exception as e:
            errors.append(f"Execution error: {str(e)}")
            score = 0.0
            success = False

        execution_time = time.time() - start_time

        return TestRun(
            task_id=task.id,
            run_number=run_number,
            success=success,
            score=score,
            execution_time=execution_time,
            errors=errors,
            metadata={
                "task_category": task.category,
                "task_difficulty": task.difficulty,
            },
        )

    def _prepare_environment_context(self, task: TaskInstance) -> Dict[str, Any]:
        """Prepare environment context for task execution."""
        context = {"environments": {}, "task_metadata": task.metadata}

        # Include relevant environment states based on task requirements
        if "database" in task.expected_capabilities:
            db_env = self.env_simulator.get_environment("test_db")
            context["environments"]["database"] = db_env.get_state()

        if "filesystem" in task.expected_capabilities:
            fs_env = self.env_simulator.get_environment("test_fs")
            context["environments"]["filesystem"] = fs_env.get_state()

        if "api" in task.expected_capabilities:
            api_env = self.env_simulator.get_environment("test_api")
            context["environments"]["api"] = api_env.get_state()

        return context

    def _evaluate_result(
        self, task: TaskInstance, agent_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Evaluate agent's result against task criteria."""
        # Use LLM for evaluation
        evaluation = self.llm_client.evaluate_agent_response(
            agent_response=json.dumps(agent_result),
            expected_behavior=json.dumps(task.evaluation_criteria),
            context={
                "task": task.task_text,
                "expected_capabilities": task.expected_capabilities,
            },
        )

        # Calculate weighted score based on criteria
        if task.evaluation_criteria:
            weighted_score = 0.0
            for criterion, weight in task.evaluation_criteria.items():
                if criterion in evaluation:
                    weighted_score += evaluation[criterion] * weight
            evaluation["score"] = weighted_score

        return evaluation

    def _calculate_reliability_metrics(
        self, test_runs: List[TestRun]
    ) -> Dict[str, Any]:
        """Calculate reliability metrics for all tasks."""
        metrics = {}

        # Get unique task IDs
        task_ids = list(set(run.task_id for run in test_runs))

        for task_id in task_ids:
            try:
                task_metrics = self.reliability_calc.calculate_metrics(task_id)
                metrics[task_id] = task_metrics.to_dict()
            except Exception as e:
                logger.error(f"Failed to calculate metrics for {task_id}: {e}")
                metrics[task_id] = {"error": str(e)}

        return metrics

    def _save_results(self, result: BenchmarkResult):
        """Save benchmark results to file."""
        results_dir = Path(result.config.results_dir)
        results_dir.mkdir(parents=True, exist_ok=True)

        result_file = results_dir / f"{result.benchmark_id}.json"

        with open(result_file, "w") as f:
            json.dump(result.to_dict(), f, indent=2)

        logger.info(f"Results saved to {result_file}")

    def load_results(
        self, benchmark_id: str, results_dir: str = "./benchmark_results"
    ) -> Dict[str, Any]:
        """Load benchmark results from file."""
        result_file = Path(results_dir) / f"{benchmark_id}.json"

        if not result_file.exists():
            raise FileNotFoundError(f"Results file not found: {result_file}")

        with open(result_file, "r") as f:
            return json.load(f)
