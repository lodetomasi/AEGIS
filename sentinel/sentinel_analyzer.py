"""Main SENTINEL static analysis orchestrator."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from .architecture_parser import ArchitectureParser, AgentArchitecture
from .risk_scanner import RiskPatternScanner, RiskPattern
from .vulnerability_detector import VulnerabilityDetector, Vulnerability
from .ast_analyzer import ASTAnalyzer
# Removed logger dependency for integration


@dataclass
class SentinelInput:
    """Input for SENTINEL analysis."""
    
    # Agent configuration
    agent_config: Dict[str, Any]
    
    # Optional: Configuration file path
    config_file: Optional[str] = None
    
    # Optional: Code path for AST analysis
    code_path: Optional[str] = None
    
    # Optional: Custom vulnerability database
    vuln_db_path: Optional[str] = None
    
    # Analysis options
    check_vulnerabilities: bool = True
    check_risk_patterns: bool = True
    check_code_vulnerabilities: bool = True
    deep_analysis: bool = False
    
    # Metadata
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class SentinelOutput:
    """Output from SENTINEL analysis."""
    
    # Parsed architecture
    architecture: AgentArchitecture
    architecture_type: str
    
    # Risk patterns detected
    risk_patterns: List[RiskPattern]
    risk_summary: Dict[str, Any]
    
    # Vulnerabilities detected
    vulnerabilities: List[Vulnerability]
    vulnerability_summary: Dict[str, Any]
    
    # Overall assessment
    overall_risk_score: float  # 0-10
    risk_level: str  # low, medium, high, critical
    
    # Recommendations
    immediate_actions: List[str]
    recommendations: List[str]
    
    # Detailed findings
    findings: Dict[str, Any]
    
    # Code vulnerabilities detected (if applicable)
    code_vulnerabilities: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = {
            'architecture': self.architecture.to_dict(),
            'architecture_type': self.architecture_type,
            'risk_patterns': [p.to_dict() for p in self.risk_patterns],
            'risk_summary': self.risk_summary,
            'vulnerabilities': [v.to_dict() for v in self.vulnerabilities],
            'vulnerability_summary': self.vulnerability_summary,
            'overall_risk_score': self.overall_risk_score,
            'risk_level': self.risk_level,
            'immediate_actions': self.immediate_actions,
            'recommendations': self.recommendations,
            'findings': self.findings
        }
        
        if self.code_vulnerabilities:
            result['code_vulnerabilities'] = self.code_vulnerabilities
            
        return result


class SentinelAnalyzer:
    """Orchestrates SENTINEL static analysis."""
    
    def __init__(self):
        """Initialize SENTINEL analyzer."""
        self.architecture_parser = ArchitectureParser()
        self.risk_scanner = RiskPatternScanner()
        self.vulnerability_detector = None  # Initialized on demand
        self.ast_analyzer = ASTAnalyzer()
        
        # Initialize risk pattern database
        self._initialize_risk_patterns()
    
    def analyze(self, input_data: SentinelInput) -> SentinelOutput:
        """
        Perform complete SENTINEL analysis.
        
        Args:
            input_data: Analysis input data
            
        Returns:
            Complete analysis output
        """
        # Starting SENTINEL static analysis
        
        # Parse architecture
        if input_data.config_file:
            architecture = self.architecture_parser.parse_from_file(input_data.config_file)
        else:
            architecture = self.architecture_parser.parse(input_data.agent_config)
        
        # Detect architecture type
        architecture_type = self.architecture_parser.detect_architecture_type(architecture)
        # Detected architecture type: {architecture_type}
        
        # Scan for risk patterns
        risk_patterns = []
        if input_data.check_risk_patterns:
            risk_patterns = self.risk_scanner.scan(architecture)
            # Found {len(risk_patterns)} risk patterns
        
        # Detect vulnerabilities
        vulnerabilities = []
        if input_data.check_vulnerabilities:
            if self.vulnerability_detector is None:
                self.vulnerability_detector = VulnerabilityDetector(input_data.vuln_db_path)
            vulnerabilities = self.vulnerability_detector.detect(architecture)
            # Found {len(vulnerabilities)} vulnerabilities
        
        # Analyze code vulnerabilities if code path provided
        code_vulnerabilities = None
        if input_data.check_code_vulnerabilities and input_data.code_path:
            # Analyzing code at {input_data.code_path}
            code_vulnerabilities = self.ast_analyzer.analyze_code(input_data.code_path)
            # Found {code_vulnerabilities['total_vulnerabilities']} code vulnerabilities
        
        # Calculate overall risk score
        overall_risk_score, risk_level = self._calculate_overall_risk(
            risk_patterns, vulnerabilities, architecture, code_vulnerabilities
        )
        
        # Generate summaries
        risk_summary = self._generate_risk_summary(risk_patterns)
        vulnerability_summary = self._generate_vulnerability_summary(vulnerabilities)
        
        # Generate recommendations
        immediate_actions = self._generate_immediate_actions(
            risk_patterns, vulnerabilities, risk_level, code_vulnerabilities
        )
        recommendations = self._generate_recommendations(
            risk_patterns, vulnerabilities, architecture_type, code_vulnerabilities
        )
        
        # Compile detailed findings
        findings = self._compile_findings(
            architecture, risk_patterns, vulnerabilities, input_data.deep_analysis
        )
        
        return SentinelOutput(
            architecture=architecture,
            architecture_type=architecture_type,
            risk_patterns=risk_patterns,
            risk_summary=risk_summary,
            vulnerabilities=vulnerabilities,
            vulnerability_summary=vulnerability_summary,
            code_vulnerabilities=code_vulnerabilities,
            overall_risk_score=overall_risk_score,
            risk_level=risk_level,
            immediate_actions=immediate_actions,
            recommendations=recommendations,
            findings=findings
        )
    
    def _calculate_overall_risk(
        self,
        risk_patterns: List[RiskPattern],
        vulnerabilities: List[Vulnerability],
        architecture: AgentArchitecture,
        code_vulnerabilities: Optional[Dict[str, Any]] = None
    ) -> tuple[float, str]:
        """Calculate overall risk score and level."""
        # Base score from risk patterns
        pattern_score = 0.0
        if risk_patterns:
            # Weighted by severity and confidence
            total_weight = 0.0
            for pattern in risk_patterns:
                weight = pattern.confidence
                pattern_score += pattern.severity * weight
                total_weight += weight
            
            if total_weight > 0:
                pattern_score = pattern_score / total_weight
        
        # Vulnerability score
        vuln_score = 0.0
        if vulnerabilities:
            # Average CVSS score
            vuln_score = sum(v.score for v in vulnerabilities) / len(vulnerabilities)
        
        # Architecture complexity factor
        complexity_factor = 1.0
        if len(architecture.tools) > 10:
            complexity_factor = 1.2
        elif len(architecture.tools) > 5:
            complexity_factor = 1.1
        
        # Permission risk factor
        permission_factor = 1.0
        high_risk_perms = ['admin', 'root', 'write', 'exec', 'delete']
        permission_count = sum(
            1 for comp in architecture.components
            for perm in comp.permissions
            if any(risk in perm.lower() for risk in high_risk_perms)
        )
        if permission_count > 5:
            permission_factor = 1.5
        elif permission_count > 2:
            permission_factor = 1.2
        
        # Combine scores
        overall_score = (pattern_score * 0.4 + vuln_score * 0.4 + 2.0) * complexity_factor * permission_factor
        overall_score = min(10.0, overall_score)  # Cap at 10
        
        # Determine risk level
        if overall_score >= 8.0:
            risk_level = "critical"
        elif overall_score >= 6.0:
            risk_level = "high"
        elif overall_score >= 4.0:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return overall_score, risk_level
    
    def _initialize_risk_patterns(self):
        """Initialize common risk patterns for detection."""
        self.common_risk_patterns = [
            {
                'name': 'unrestricted_tool_access',
                'description': 'Agent has unrestricted access to external tools',
                'indicators': ['*', 'all', 'any', 'unrestricted'],
                'severity': 8.0
            },
            {
                'name': 'no_input_validation',
                'description': 'No input validation on user prompts',
                'indicators': ['raw_input', 'direct_execution', 'no_sanitize'],
                'severity': 7.0
            },
            {
                'name': 'memory_persistence',
                'description': 'Persistent memory without access controls',
                'indicators': ['persistent_memory', 'unlimited_storage', 'no_expiry'],
                'severity': 6.0
            },
            {
                'name': 'recursive_loops',
                'description': 'Potential for unbounded recursive execution',
                'indicators': ['self_invoke', 'recursive', 'loop_unlimited'],
                'severity': 7.5
            },
            {
                'name': 'credential_storage',
                'description': 'Stores or processes credentials',
                'indicators': ['password', 'api_key', 'credential', 'secret'],
                'severity': 9.0
            }
        ]
    
    def _generate_risk_summary(self, risk_patterns: List[RiskPattern]) -> Dict[str, Any]:
        """Generate risk pattern summary."""
        if not risk_patterns:
            return {
                'total_patterns': 0,
                'by_category': {},
                'by_severity': {},
                'top_risks': []
            }
        
        # Count by category
        by_category = {}
        for pattern in risk_patterns:
            category = pattern.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {
            'critical': sum(1 for p in risk_patterns if p.severity >= 9),
            'high': sum(1 for p in risk_patterns if 7 <= p.severity < 9),
            'medium': sum(1 for p in risk_patterns if 4 <= p.severity < 7),
            'low': sum(1 for p in risk_patterns if p.severity < 4)
        }
        
        # Top risks
        top_risks = sorted(risk_patterns, key=lambda p: p.severity, reverse=True)[:5]
        
        return {
            'total_patterns': len(risk_patterns),
            'by_category': by_category,
            'by_severity': by_severity,
            'top_risks': [
                {
                    'category': p.category.value,
                    'severity': p.severity,
                    'description': p.description
                }
                for p in top_risks
            ]
        }
    
    def _generate_vulnerability_summary(self, vulnerabilities: List[Vulnerability]) -> Dict[str, Any]:
        """Generate vulnerability summary."""
        if not vulnerabilities:
            return {
                'total_vulnerabilities': 0,
                'by_severity': {},
                'by_component': {},
                'average_score': 0.0
            }
        
        # Use vulnerability detector's summary method
        if self.vulnerability_detector:
            by_severity = self.vulnerability_detector.get_severity_summary(vulnerabilities)
        else:
            by_severity = {
                'critical': sum(1 for v in vulnerabilities if v.severity == 'critical'),
                'high': sum(1 for v in vulnerabilities if v.severity == 'high'),
                'medium': sum(1 for v in vulnerabilities if v.severity == 'medium'),
                'low': sum(1 for v in vulnerabilities if v.severity == 'low')
            }
        
        # Count by component
        by_component = {}
        for vuln in vulnerabilities:
            by_component[vuln.component] = by_component.get(vuln.component, 0) + 1
        
        # Average score
        avg_score = sum(v.score for v in vulnerabilities) / len(vulnerabilities)
        
        return {
            'total_vulnerabilities': len(vulnerabilities),
            'by_severity': by_severity,
            'by_component': by_component,
            'average_score': avg_score
        }
    
    def _generate_immediate_actions(
        self,
        risk_patterns: List[RiskPattern],
        vulnerabilities: List[Vulnerability],
        risk_level: str,
        code_vulnerabilities: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate immediate action items."""
        actions = []
        
        # Critical vulnerabilities
        critical_vulns = [v for v in vulnerabilities if v.severity == 'critical']
        if critical_vulns:
            actions.append(
                f"URGENT: Patch {len(critical_vulns)} critical vulnerabilities immediately"
            )
            for vuln in critical_vulns[:2]:  # Top 2
                actions.append(f"- Update {vuln.component} to {vuln.fixed_versions[0] if vuln.fixed_versions else 'latest version'}")
        
        # Critical risk patterns
        critical_patterns = [p for p in risk_patterns if p.severity >= 9]
        if critical_patterns:
            for pattern in critical_patterns[:2]:  # Top 2
                actions.append(f"- {pattern.mitigation}")
        
        # High-level actions based on risk level
        if risk_level == "critical":
            actions.insert(0, "DO NOT DEPLOY - Critical security issues detected")
            actions.append("Conduct immediate security review")
        elif risk_level == "high":
            actions.insert(0, "Address high-priority issues before deployment")
            actions.append("Schedule security assessment")
        
        # Specific high-risk findings
        if any(p.category.value == 'privilege_escalation' for p in risk_patterns):
            actions.append("Review and restrict permission model immediately")
        
        if any(p.category.value == 'data_exposure' for p in risk_patterns):
            actions.append("Implement data access controls and filtering")
        
        # Code vulnerability actions
        if code_vulnerabilities and code_vulnerabilities.get('total_vulnerabilities', 0) > 0:
            by_severity = code_vulnerabilities.get('by_severity', {})
            
            if by_severity.get('critical', 0) > 0:
                actions.append(f"FIX IMMEDIATELY: {by_severity['critical']} critical code vulnerabilities")
                
                # Add specific critical vulnerabilities
                for vuln in code_vulnerabilities.get('vulnerabilities', [])[:3]:
                    if vuln.get('severity') == 'critical':
                        actions.append(f"- {vuln['pattern_name']} at {vuln['file']}:{vuln['line']}")
            
            if by_severity.get('high', 0) > 0:
                actions.append(f"Address {by_severity['high']} high-severity code vulnerabilities")
        
        return actions
    
    def _generate_recommendations(
        self,
        risk_patterns: List[RiskPattern],
        vulnerabilities: List[Vulnerability],
        architecture_type: str,
        code_vulnerabilities: Optional[Dict[str, Any]] = None
    ) -> List[str]:
        """Generate detailed recommendations."""
        recommendations = []
        
        # Architecture-specific recommendations
        arch_recommendations = {
            'multi_agent_system': [
                "Implement inter-agent communication security",
                "Add agent isolation boundaries",
                "Deploy centralized monitoring"
            ],
            'code_assistant': [
                "Use sandboxed code execution environment",
                "Implement code review before execution",
                "Add resource limits for code execution"
            ],
            'research_assistant': [
                "Validate all external data sources",
                "Implement content filtering for web results",
                "Add citation tracking"
            ],
            'tool_augmented': [
                "Implement tool usage auditing",
                "Add rate limiting for tool calls",
                "Validate tool outputs"
            ]
        }
        
        if architecture_type in arch_recommendations:
            recommendations.extend(arch_recommendations[architecture_type])
        
        # Pattern-based recommendations
        pattern_categories = set(p.category.value for p in risk_patterns)
        
        if 'infinite_loop' in pattern_categories:
            recommendations.append("Implement timeout mechanisms for all operations")
            recommendations.append("Add recursion depth limits")
        
        if 'prompt_injection' in pattern_categories:
            recommendations.append("Implement input sanitization layer")
            recommendations.append("Use structured prompts with validation")
        
        if 'resource_exhaustion' in pattern_categories:
            recommendations.append("Implement resource quotas and monitoring")
            recommendations.append("Add circuit breakers for resource-intensive operations")
        
        # Vulnerability-based recommendations
        if vulnerabilities:
            recommendations.append("Establish regular dependency update schedule")
            recommendations.append("Implement vulnerability scanning in CI/CD pipeline")
        
        # Code-specific recommendations
        if code_vulnerabilities and code_vulnerabilities.get('total_vulnerabilities', 0) > 0:
            by_type = code_vulnerabilities.get('by_type', {})
            
            if 'sql_injection' in by_type:
                recommendations.append("Use parameterized queries for all database operations")
                recommendations.append("Implement SQL query validation layer")
            
            if 'command_injection' in by_type:
                recommendations.append("Use subprocess with shell=False")
                recommendations.append("Implement command whitelist validation")
            
            if 'hardcoded_credential' in by_type:
                recommendations.append("Migrate all credentials to environment variables")
                recommendations.append("Implement secure secret management system")
            
            if 'unsafe_eval' in by_type or 'unsafe_exec' in by_type:
                recommendations.append("Remove all eval/exec usage or implement sandboxing")
                recommendations.append("Use ast.literal_eval for safe evaluation")
            
            # General code security
            recommendations.append("Implement static code analysis in CI/CD pipeline")
            recommendations.append("Enable security linting rules (bandit, semgrep)")
        
        # General security recommendations
        recommendations.extend([
            "Implement comprehensive logging and monitoring",
            "Regular security audits and penetration testing",
            "Incident response plan for AI-specific scenarios",
            "User education on AI agent limitations and risks"
        ])
        
        # Remove duplicates while preserving order
        seen = set()
        unique_recommendations = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def _compile_findings(
        self,
        architecture: AgentArchitecture,
        risk_patterns: List[RiskPattern],
        vulnerabilities: List[Vulnerability],
        deep_analysis: bool
    ) -> Dict[str, Any]:
        """Compile detailed findings."""
        findings = {
            'architecture_analysis': {
                'total_models': len(architecture.models),
                'total_tools': len(architecture.tools),
                'total_permissions': len(architecture.get_all_permissions()),
                'has_dangerous_tools': any(
                    t.risk_level == 'high' for t in architecture.tools
                ),
                'complexity_score': self._calculate_complexity_score(architecture)
            },
            'security_posture': {
                'has_input_validation': any(
                    'validat' in t.name.lower() for t in architecture.tools
                ),
                'has_output_filtering': any(
                    'filter' in t.name.lower() or 'sanitiz' in t.name.lower()
                    for t in architecture.tools
                ),
                'has_rate_limiting': any(
                    'rate' in str(t.parameters) or 'limit' in str(t.parameters)
                    for t in architecture.tools
                ),
                'has_authentication': 'auth' in str(architecture.metadata).lower()
            }
        }
        
        if deep_analysis:
            # Additional deep analysis
            findings['deep_analysis'] = {
                'dependency_cycles': self._find_dependency_cycles(architecture),
                'permission_chains': self._analyze_permission_chains(architecture),
                'attack_surface': self._calculate_attack_surface(architecture),
                'data_flow_risks': self._analyze_data_flow(architecture)
            }
        
        return findings
    
    def _calculate_complexity_score(self, architecture: AgentArchitecture) -> float:
        """Calculate architecture complexity score."""
        score = 0.0
        
        # Model complexity
        score += len(architecture.models) * 1.0
        
        # Tool complexity
        score += len(architecture.tools) * 0.5
        high_risk_tools = sum(1 for t in architecture.tools if t.risk_level == 'high')
        score += high_risk_tools * 2.0
        
        # Permission complexity
        score += len(architecture.get_all_permissions()) * 0.3
        
        # Workflow complexity
        score += len(architecture.workflow_steps) * 0.2
        
        # Dependency complexity
        total_deps = sum(len(deps) for deps in architecture.dependencies.values())
        score += total_deps * 0.1
        
        return min(10.0, score)
    
    def _find_dependency_cycles(self, architecture: AgentArchitecture) -> List[List[str]]:
        """Find dependency cycles (simplified)."""
        # This would use the same cycle detection as in risk scanner
        # For now, return empty
        return []
    
    def _analyze_permission_chains(self, architecture: AgentArchitecture) -> List[Dict[str, Any]]:
        """Analyze permission chains that could be exploited."""
        chains = []
        
        # Look for dangerous permission combinations
        permissions = list(architecture.get_all_permissions())
        
        # Read + Write + Execute chain
        if all(p in permissions for p in ['file_read', 'file_write', 'code_exec']):
            chains.append({
                'chain': ['file_read', 'file_write', 'code_exec'],
                'risk': 'Potential for reading sensitive data and executing it',
                'severity': 'high'
            })
        
        return chains
    
    def _calculate_attack_surface(self, architecture: AgentArchitecture) -> Dict[str, Any]:
        """Calculate attack surface metrics."""
        return {
            'external_inputs': len(architecture.tools) + len(architecture.api_access),
            'data_sources': len(architecture.data_access),
            'execution_points': sum(1 for t in architecture.tools if 'exec' in t.name.lower()),
            'total_surface_area': len(architecture.tools) + len(architecture.data_access) + len(architecture.api_access)
        }
    
    def _analyze_data_flow(self, architecture: AgentArchitecture) -> List[Dict[str, Any]]:
        """Analyze data flow risks."""
        risks = []
        
        # Check for data flows from sensitive sources to external sinks
        sensitive_sources = [d for d in architecture.data_access if any(
            s in d.lower() for s in ['password', 'secret', 'key', 'token']
        )]
        
        external_sinks = [t for t in architecture.tools if any(
            s in t.name.lower() for s in ['api', 'http', 'web', 'email']
        )]
        
        if sensitive_sources and external_sinks:
            risks.append({
                'risk': 'Potential for sensitive data exfiltration',
                'sources': sensitive_sources[:3],  # Top 3
                'sinks': [t.name for t in external_sinks[:3]],
                'severity': 'high'
            })
        
        return risks