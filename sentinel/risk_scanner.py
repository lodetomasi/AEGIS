"""Risk pattern scanning for agent architectures."""

import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum

from .architecture_parser import AgentArchitecture, ToolInfo


class RiskCategory(Enum):
    """Categories of architectural risks."""

    INFINITE_LOOP = "infinite_loop"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXPOSURE = "data_exposure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    UNCONTROLLED_RECURSION = "uncontrolled_recursion"
    EXTERNAL_CONTROL = "external_control"
    PROMPT_INJECTION = "prompt_injection"
    MODEL_CONFUSION = "model_confusion"
    TOOL_ABUSE = "tool_abuse"
    PERMISSION_BYPASS = "permission_bypass"


@dataclass
class RiskPattern:
    """A detected risk pattern."""

    category: RiskCategory
    severity: int  # 1-10
    description: str
    location: str  # Where in architecture
    evidence: List[str]
    mitigation: str
    confidence: float  # 0-1

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "category": self.category.value,
            "severity": self.severity,
            "description": self.description,
            "location": self.location,
            "evidence": self.evidence,
            "mitigation": self.mitigation,
            "confidence": self.confidence,
        }


class RiskPatternScanner:
    """Scans agent architectures for risk patterns."""

    def __init__(self):
        """Initialize risk scanner."""
        self.patterns = self._initialize_patterns()

    def _initialize_patterns(self) -> Dict[RiskCategory, Dict[str, Any]]:
        """Initialize risk detection patterns."""
        return {
            RiskCategory.INFINITE_LOOP: {
                "indicators": [
                    "recursive_call_without_limit",
                    "while_true_without_break",
                    "cyclic_dependency",
                    "unbounded_iteration",
                ],
                "severity_base": 8,
                "check_functions": [
                    self._check_recursive_patterns,
                    self._check_cyclic_dependencies,
                ],
            },
            RiskCategory.PRIVILEGE_ESCALATION: {
                "indicators": [
                    "permission_modification",
                    "role_elevation",
                    "sudo_access",
                    "admin_tools",
                ],
                "severity_base": 9,
                "check_functions": [
                    self._check_permission_escalation,
                    self._check_dangerous_tools,
                ],
            },
            RiskCategory.DATA_EXPOSURE: {
                "indicators": [
                    "unrestricted_data_access",
                    "no_data_filtering",
                    "broad_permissions",
                    "sensitive_data_tools",
                ],
                "severity_base": 8,
                "check_functions": [
                    self._check_data_access_patterns,
                    self._check_output_filtering,
                ],
            },
            RiskCategory.RESOURCE_EXHAUSTION: {
                "indicators": [
                    "no_rate_limiting",
                    "unbounded_resource_use",
                    "parallel_execution",
                    "large_context_window",
                ],
                "severity_base": 7,
                "check_functions": [
                    self._check_resource_limits,
                    self._check_parallel_execution,
                ],
            },
            RiskCategory.PROMPT_INJECTION: {
                "indicators": [
                    "user_input_in_system_prompt",
                    "dynamic_prompt_construction",
                    "unvalidated_input",
                    "prompt_concatenation",
                ],
                "severity_base": 8,
                "check_functions": [
                    self._check_prompt_construction,
                    self._check_input_validation,
                ],
            },
            RiskCategory.TOOL_ABUSE: {
                "indicators": [
                    "dangerous_tool_combinations",
                    "tool_chaining_without_validation",
                    "external_tool_execution",
                    "unverified_tool_output",
                ],
                "severity_base": 7,
                "check_functions": [
                    self._check_tool_combinations,
                    self._check_tool_validation,
                ],
            },
        }

    def scan(self, architecture: AgentArchitecture) -> List[RiskPattern]:
        """
        Scan architecture for risk patterns.

        Args:
            architecture: Agent architecture to scan

        Returns:
            List of detected risk patterns
        """
        detected_patterns = []

        for category, pattern_info in self.patterns.items():
            # Run all check functions for this category
            for check_func in pattern_info["check_functions"]:
                patterns = check_func(architecture, pattern_info)
                detected_patterns.extend(patterns)

        # Sort by severity
        detected_patterns.sort(key=lambda p: p.severity, reverse=True)

        return detected_patterns

    def _check_recursive_patterns(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for recursive patterns that could cause infinite loops."""
        patterns = []

        # Check workflow for recursive calls
        recursive_steps = set()
        for i, step in enumerate(architecture.workflow_steps):
            if isinstance(step, dict):
                if step.get("type") == "loop" and not step.get("max_iterations"):
                    patterns.append(
                        RiskPattern(
                            category=RiskCategory.INFINITE_LOOP,
                            severity=pattern_info["severity_base"],
                            description="Unbounded loop detected in workflow",
                            location=f"workflow_step_{i}",
                            evidence=[f"Loop without max_iterations: {step}"],
                            mitigation="Add max_iterations limit to all loops",
                            confidence=0.9,
                        )
                    )

                # Check for self-referential steps
                if step.get("next_step") == step.get("name"):
                    recursive_steps.add(step.get("name", f"step_{i}"))

        if recursive_steps:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.INFINITE_LOOP,
                    severity=pattern_info["severity_base"] + 1,
                    description="Self-referential workflow steps detected",
                    location="workflow",
                    evidence=[f"Recursive steps: {list(recursive_steps)}"],
                    mitigation="Break recursive references with exit conditions",
                    confidence=0.95,
                )
            )

        # Check system prompt for recursive instructions
        if architecture.system_prompt:
            recursive_keywords = [
                "repeat until",
                "keep trying",
                "try again",
                "continue indefinitely",
            ]
            for keyword in recursive_keywords:
                if keyword in architecture.system_prompt.lower():
                    patterns.append(
                        RiskPattern(
                            category=RiskCategory.INFINITE_LOOP,
                            severity=pattern_info["severity_base"] - 1,
                            description=f"Potentially recursive instruction in system prompt",
                            location="system_prompt",
                            evidence=[f"Found '{keyword}' in system prompt"],
                            mitigation="Add explicit termination conditions",
                            confidence=0.7,
                        )
                    )

        return patterns

    def _check_cyclic_dependencies(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for cyclic dependencies."""
        patterns = []

        # Get dependency graph
        dep_graph = architecture.get_dependency_graph()

        # Find cycles using DFS
        cycles = self._find_cycles(dep_graph)

        if cycles:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.INFINITE_LOOP,
                    severity=pattern_info["severity_base"],
                    description="Cyclic dependencies detected",
                    location="dependencies",
                    evidence=[f"Cycles: {cycles}"],
                    mitigation="Refactor to remove circular dependencies",
                    confidence=1.0,
                )
            )

        return patterns

    def _find_cycles(self, graph: Dict[str, Set[str]]) -> List[List[str]]:
        """Find cycles in dependency graph using DFS."""
        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycles.append(path[cycle_start:] + [neighbor])

            rec_stack.remove(node)

        for node in graph:
            if node not in visited:
                dfs(node, [])

        return cycles

    def _check_permission_escalation(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for privilege escalation risks."""
        patterns = []

        # Check for dangerous permission combinations
        all_permissions = architecture.get_all_permissions()

        dangerous_combos = [
            (
                ["file_read", "file_write", "code_exec"],
                "Read-Write-Execute combination",
            ),
            (["db_read", "db_write", "api_access"], "Database and API access"),
            (["email_access", "file_read"], "Email with file access"),
        ]

        for combo, description in dangerous_combos:
            if all(perm in all_permissions for perm in combo):
                patterns.append(
                    RiskPattern(
                        category=RiskCategory.PRIVILEGE_ESCALATION,
                        severity=pattern_info["severity_base"] - 1,
                        description=f"Dangerous permission combination: {description}",
                        location="permissions",
                        evidence=[f"Has permissions: {combo}"],
                        mitigation="Apply principle of least privilege",
                        confidence=0.8,
                    )
                )

        # Check for tools that can modify permissions
        for tool in architecture.tools:
            if any(
                keyword in tool.name.lower()
                for keyword in ["chmod", "chown", "permission", "grant"]
            ):
                patterns.append(
                    RiskPattern(
                        category=RiskCategory.PRIVILEGE_ESCALATION,
                        severity=pattern_info["severity_base"],
                        description=f"Tool can modify permissions: {tool.name}",
                        location=f"tool:{tool.name}",
                        evidence=[f"Permission-modifying tool detected"],
                        mitigation="Remove or restrict permission-modifying tools",
                        confidence=0.9,
                    )
                )

        return patterns

    def _check_dangerous_tools(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for dangerous tool access."""
        patterns = []

        dangerous_tools = {
            "shell_exec": 9,
            "system_command": 9,
            "eval": 10,
            "exec": 10,
            "compile": 8,
            "subprocess": 8,
            "os_command": 9,
        }

        for tool in architecture.tools:
            tool_lower = tool.name.lower()

            for dangerous, severity in dangerous_tools.items():
                if dangerous in tool_lower:
                    patterns.append(
                        RiskPattern(
                            category=RiskCategory.PRIVILEGE_ESCALATION,
                            severity=severity,
                            description=f"Dangerous tool detected: {tool.name}",
                            location=f"tool:{tool.name}",
                            evidence=[f"Tool allows {dangerous} operations"],
                            mitigation="Replace with safer alternative or add strict validation",
                            confidence=0.95,
                        )
                    )
                    break

        return patterns

    def _check_data_access_patterns(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for risky data access patterns."""
        patterns = []

        # Check for overly broad data access
        if "*" in architecture.data_access or "all" in architecture.data_access:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.DATA_EXPOSURE,
                    severity=pattern_info["severity_base"],
                    description="Unrestricted data access detected",
                    location="data_access",
                    evidence=["Wildcard or 'all' in data access patterns"],
                    mitigation="Specify exact data sources needed",
                    confidence=0.9,
                )
            )

        # Check for sensitive data patterns
        sensitive_patterns = ["password", "ssn", "credit_card", "private_key", "secret"]
        for data_source in architecture.data_access:
            for pattern in sensitive_patterns:
                if pattern in data_source.lower():
                    patterns.append(
                        RiskPattern(
                            category=RiskCategory.DATA_EXPOSURE,
                            severity=pattern_info["severity_base"] + 1,
                            description=f"Access to sensitive data: {data_source}",
                            location="data_access",
                            evidence=[f"Sensitive pattern '{pattern}' found"],
                            mitigation="Implement data masking and access controls",
                            confidence=0.85,
                        )
                    )

        return patterns

    def _check_output_filtering(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for output filtering mechanisms."""
        patterns = []

        # Check if there's any output filtering mentioned
        has_filtering = False

        # Check in tools
        for tool in architecture.tools:
            if any(
                keyword in tool.name.lower()
                for keyword in ["filter", "sanitize", "redact", "mask"]
            ):
                has_filtering = True
                break

        # Check in workflow
        for step in architecture.workflow_steps:
            if isinstance(step, dict) and step.get("type") in [
                "filter",
                "validate",
                "sanitize",
            ]:
                has_filtering = True
                break

        if not has_filtering and architecture.data_access:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.DATA_EXPOSURE,
                    severity=pattern_info["severity_base"] - 1,
                    description="No output filtering detected",
                    location="architecture",
                    evidence=["No filtering tools or workflow steps found"],
                    mitigation="Add output validation and filtering layer",
                    confidence=0.7,
                )
            )

        return patterns

    def _check_resource_limits(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for resource limit configurations."""
        patterns = []

        # Check token limits
        if architecture.max_tokens > 4096:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.RESOURCE_EXHAUSTION,
                    severity=pattern_info["severity_base"] - 2,
                    description="Very high token limit configured",
                    location="configuration",
                    evidence=[f"max_tokens: {architecture.max_tokens}"],
                    mitigation="Consider reducing max_tokens to prevent excessive resource use",
                    confidence=0.6,
                )
            )

        # Check for rate limiting in tools
        has_rate_limiting = any(
            "rate_limit" in tool.parameters or "throttle" in tool.parameters
            for tool in architecture.tools
        )

        if not has_rate_limiting and len(architecture.tools) > 5:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.RESOURCE_EXHAUSTION,
                    severity=pattern_info["severity_base"],
                    description="No rate limiting on tools",
                    location="tools",
                    evidence=["Multiple tools without rate limiting"],
                    mitigation="Implement rate limiting for tool usage",
                    confidence=0.8,
                )
            )

        return patterns

    def _check_parallel_execution(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for uncontrolled parallel execution."""
        patterns = []

        # Check workflow for parallel steps
        parallel_count = 0
        for step in architecture.workflow_steps:
            if isinstance(step, dict) and step.get("parallel", False):
                parallel_count += 1

        if parallel_count > 3:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.RESOURCE_EXHAUSTION,
                    severity=pattern_info["severity_base"],
                    description="Multiple parallel execution steps",
                    location="workflow",
                    evidence=[f"Found {parallel_count} parallel steps"],
                    mitigation="Limit concurrent executions",
                    confidence=0.75,
                )
            )

        return patterns

    def _check_prompt_construction(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for prompt injection vulnerabilities."""
        patterns = []

        # Check system prompt for user input placeholders
        if architecture.system_prompt:
            dangerous_patterns = ["{user_input}", "${input}", "{{message}}"]
            for pattern in dangerous_patterns:
                if pattern in architecture.system_prompt:
                    patterns.append(
                        RiskPattern(
                            category=RiskCategory.PROMPT_INJECTION,
                            severity=pattern_info["severity_base"],
                            description="User input directly in system prompt",
                            location="system_prompt",
                            evidence=[f"Found pattern: {pattern}"],
                            mitigation="Sanitize user input before prompt insertion",
                            confidence=0.9,
                        )
                    )

        return patterns

    def _check_input_validation(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for input validation mechanisms."""
        patterns = []

        # Check if validation tools exist
        validation_tools = [
            tool
            for tool in architecture.tools
            if any(
                keyword in tool.name.lower()
                for keyword in ["validate", "sanitize", "check"]
            )
        ]

        if not validation_tools and len(architecture.tools) > 3:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.PROMPT_INJECTION,
                    severity=pattern_info["severity_base"] - 1,
                    description="No input validation tools detected",
                    location="tools",
                    evidence=["No validation mechanisms found"],
                    mitigation="Add input validation layer",
                    confidence=0.7,
                )
            )

        return patterns

    def _check_tool_combinations(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for dangerous tool combinations."""
        patterns = []

        tool_names = [tool.name.lower() for tool in architecture.tools]

        # Dangerous combinations
        dangerous_combos = [
            (["web_search", "code_execution"], "Web content to code execution"),
            (["email_send", "database_write"], "Email to database pipeline"),
            (["file_read", "api_call"], "File data to external API"),
        ]

        for combo, description in dangerous_combos:
            if all(any(c in tool for tool in tool_names) for c in combo):
                patterns.append(
                    RiskPattern(
                        category=RiskCategory.TOOL_ABUSE,
                        severity=pattern_info["severity_base"],
                        description=f"Dangerous tool combination: {description}",
                        location="tools",
                        evidence=[f"Has tools: {combo}"],
                        mitigation="Add validation between tool calls",
                        confidence=0.8,
                    )
                )

        return patterns

    def _check_tool_validation(
        self, architecture: AgentArchitecture, pattern_info: Dict[str, Any]
    ) -> List[RiskPattern]:
        """Check for tool output validation."""
        patterns = []

        # Check for tools without output validation
        unvalidated_tools = []
        for tool in architecture.tools:
            if tool.risk_level == "high" and "validate_output" not in tool.parameters:
                unvalidated_tools.append(tool.name)

        if unvalidated_tools:
            patterns.append(
                RiskPattern(
                    category=RiskCategory.TOOL_ABUSE,
                    severity=pattern_info["severity_base"],
                    description="High-risk tools without output validation",
                    location="tools",
                    evidence=[f"Unvalidated tools: {unvalidated_tools}"],
                    mitigation="Add output validation for high-risk tools",
                    confidence=0.85,
                )
            )

        return patterns
