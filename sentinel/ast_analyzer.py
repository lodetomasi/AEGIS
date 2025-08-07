"""AST-based code analysis for deep vulnerability detection."""

import ast
import re
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import importlib.util
import sys


@dataclass
class SecurityPattern:
    """Represents a security pattern to detect."""
    
    name: str
    description: str
    severity: str  # low, medium, high, critical
    pattern_type: str  # ast_pattern, regex_pattern, flow_pattern
    detection_logic: Any  # Function or pattern
    mitigation: str
    cwe_id: Optional[str] = None


@dataclass
class CodeVulnerability:
    """Detected code vulnerability."""
    
    pattern: SecurityPattern
    file_path: str
    line_number: int
    code_snippet: str
    confidence: float  # 0-1 confidence in detection
    data_flow: Optional[List[str]] = None  # For taint analysis
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'pattern_name': self.pattern.name,
            'severity': self.pattern.severity,
            'description': self.pattern.description,
            'file': self.file_path,
            'line': self.line_number,
            'code': self.code_snippet,
            'confidence': self.confidence,
            'mitigation': self.pattern.mitigation,
            'cwe_id': self.pattern.cwe_id,
            'data_flow': self.data_flow
        }


class ASTSecurityVisitor(ast.NodeVisitor):
    """AST visitor for security pattern detection."""
    
    def __init__(self, patterns: List[SecurityPattern]):
        """Initialize visitor with patterns to detect."""
        self.patterns = patterns
        self.vulnerabilities: List[CodeVulnerability] = []
        self.current_file = ""
        self.source_lines: List[str] = []
        self.taint_sources: Set[str] = set()
        self.taint_sinks: Set[str] = set()
        self.data_flows: Dict[str, List[str]] = {}
        
    def analyze_file(self, file_path: str) -> List[CodeVulnerability]:
        """Analyze a Python file for vulnerabilities."""
        self.current_file = file_path
        self.vulnerabilities = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
                self.source_lines = source.splitlines()
            
            tree = ast.parse(source, filename=file_path)
            self.visit(tree)
            
        except Exception as e:
            # Log parsing error but continue
            pass
        
        return self.vulnerabilities
    
    def visit_Call(self, node: ast.Call) -> Any:
        """Visit function calls to detect dangerous patterns."""
        # Check for dangerous function calls
        dangerous_calls = {
            'eval': SecurityPattern(
                name='unsafe_eval',
                description='Use of eval() with user input',
                severity='critical',
                pattern_type='ast_pattern',
                detection_logic=None,
                mitigation='Use ast.literal_eval() or avoid eval entirely',
                cwe_id='CWE-95'
            ),
            'exec': SecurityPattern(
                name='unsafe_exec',
                description='Use of exec() with user input',
                severity='critical',
                pattern_type='ast_pattern',
                detection_logic=None,
                mitigation='Avoid exec or use restricted execution environment',
                cwe_id='CWE-95'
            ),
            'compile': SecurityPattern(
                name='unsafe_compile',
                description='Dynamic code compilation',
                severity='high',
                pattern_type='ast_pattern',
                detection_logic=None,
                mitigation='Avoid dynamic compilation',
                cwe_id='CWE-94'
            ),
            '__import__': SecurityPattern(
                name='dynamic_import',
                description='Dynamic module import',
                severity='medium',
                pattern_type='ast_pattern',
                detection_logic=None,
                mitigation='Use static imports or whitelist allowed modules',
                cwe_id='CWE-470'
            )
        }
        
        func_name = self._get_function_name(node.func)
        if func_name in dangerous_calls:
            # Check if input comes from user
            if self._is_tainted_input(node):
                self._add_vulnerability(
                    node,
                    dangerous_calls[func_name],
                    confidence=0.9
                )
        
        # Check for SQL injection patterns
        if func_name in ['execute', 'executemany', 'raw']:
            if self._has_string_formatting(node):
                pattern = SecurityPattern(
                    name='sql_injection',
                    description='Potential SQL injection vulnerability',
                    severity='critical',
                    pattern_type='ast_pattern',
                    detection_logic=None,
                    mitigation='Use parameterized queries',
                    cwe_id='CWE-89'
                )
                self._add_vulnerability(node, pattern, confidence=0.8)
        
        # Check for command injection
        if func_name in ['system', 'popen', 'call', 'run', 'Popen']:
            if self._has_user_input(node):
                pattern = SecurityPattern(
                    name='command_injection',
                    description='Potential command injection vulnerability',
                    severity='critical',
                    pattern_type='ast_pattern',
                    detection_logic=None,
                    mitigation='Use subprocess with shell=False and validate input',
                    cwe_id='CWE-78'
                )
                self._add_vulnerability(node, pattern, confidence=0.85)
        
        self.generic_visit(node)
    
    def visit_Import(self, node: ast.Import) -> Any:
        """Check for dangerous imports."""
        dangerous_modules = {
            'pickle': ('Insecure deserialization risk', 'CWE-502'),
            'marshal': ('Insecure deserialization risk', 'CWE-502'),
            'shelve': ('Insecure deserialization risk', 'CWE-502'),
            'ctypes': ('Memory corruption risk', 'CWE-119'),
        }
        
        for alias in node.names:
            if alias.name in dangerous_modules:
                desc, cwe = dangerous_modules[alias.name]
                pattern = SecurityPattern(
                    name=f'dangerous_import_{alias.name}',
                    description=f'{desc} from {alias.name} module',
                    severity='medium',
                    pattern_type='ast_pattern',
                    detection_logic=None,
                    mitigation=f'Avoid using {alias.name} or implement strict input validation',
                    cwe_id=cwe
                )
                self._add_vulnerability(node, pattern, confidence=0.7)
        
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        """Analyze function definitions for security issues."""
        # Check for hardcoded credentials
        for child in ast.walk(node):
            if isinstance(child, ast.Assign):
                for target in child.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id.lower()
                        if any(secret in var_name for secret in ['password', 'secret', 'key', 'token', 'api_key']):
                            if isinstance(child.value, ast.Constant):
                                pattern = SecurityPattern(
                                    name='hardcoded_credential',
                                    description='Hardcoded credential detected',
                                    severity='high',
                                    pattern_type='ast_pattern',
                                    detection_logic=None,
                                    mitigation='Use environment variables or secure key management',
                                    cwe_id='CWE-798'
                                )
                                self._add_vulnerability(child, pattern, confidence=0.95)
        
        # Check for missing input validation
        if node.name.startswith(('handle_', 'process_', 'parse_')):
            has_validation = self._has_input_validation(node)
            if not has_validation:
                pattern = SecurityPattern(
                    name='missing_input_validation',
                    description='Function processing input without validation',
                    severity='medium',
                    pattern_type='ast_pattern',
                    detection_logic=None,
                    mitigation='Add input validation and sanitization',
                    cwe_id='CWE-20'
                )
                self._add_vulnerability(node, pattern, confidence=0.6)
        
        self.generic_visit(node)
    
    def visit_Try(self, node: ast.Try) -> Any:
        """Check for poor exception handling."""
        for handler in node.handlers:
            # Check for bare except
            if handler.type is None:
                pattern = SecurityPattern(
                    name='bare_except',
                    description='Bare except clause that catches all exceptions',
                    severity='low',
                    pattern_type='ast_pattern',
                    detection_logic=None,
                    mitigation='Catch specific exceptions',
                    cwe_id='CWE-396'
                )
                self._add_vulnerability(handler, pattern, confidence=0.9)
            
            # Check for exception info leakage
            for child in ast.walk(handler):
                if isinstance(child, ast.Call):
                    func_name = self._get_function_name(child.func)
                    if func_name in ['print', 'write', 'send']:
                        # Check if exception details are being exposed
                        for arg in child.args:
                            if isinstance(arg, ast.Name) and handler.name and arg.id == handler.name:
                                pattern = SecurityPattern(
                                    name='exception_info_leak',
                                    description='Exception details exposed to user',
                                    severity='medium',
                                    pattern_type='ast_pattern',
                                    detection_logic=None,
                                    mitigation='Log exceptions internally, show generic error to users',
                                    cwe_id='CWE-209'
                                )
                                self._add_vulnerability(child, pattern, confidence=0.7)
        
        self.generic_visit(node)
    
    def _get_function_name(self, node: ast.AST) -> Optional[str]:
        """Extract function name from AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Call):
            return self._get_function_name(node.func)
        return None
    
    def _is_tainted_input(self, node: ast.Call) -> bool:
        """Check if function call uses potentially tainted input."""
        # Simplified taint analysis
        taint_sources = {'input', 'request', 'argv', 'environ', 'form', 'args', 'json', 'data'}
        
        for arg in node.args:
            arg_str = ast.dump(arg)
            if any(source in arg_str.lower() for source in taint_sources):
                return True
        
        return False
    
    def _has_string_formatting(self, node: ast.Call) -> bool:
        """Check if call uses string formatting with variables."""
        for arg in node.args:
            if isinstance(arg, ast.BinOp) and isinstance(arg.op, ast.Mod):
                return True
            elif isinstance(arg, ast.Call):
                func_name = self._get_function_name(arg.func)
                if func_name in ['format', 'join']:
                    return True
            elif isinstance(arg, ast.JoinedStr):  # f-string
                return True
        
        return False
    
    def _has_user_input(self, node: ast.Call) -> bool:
        """Check if call involves user input."""
        # Similar to tainted input but broader
        return self._is_tainted_input(node)
    
    def _has_input_validation(self, node: ast.FunctionDef) -> bool:
        """Check if function has input validation."""
        validation_patterns = [
            'validate', 'sanitize', 'check', 'verify',
            'isinstance', 'type', 'schema', 'filter'
        ]
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                func_name = self._get_function_name(child.func)
                if func_name and any(pattern in func_name.lower() for pattern in validation_patterns):
                    return True
            elif isinstance(child, ast.If):
                # Check for validation in conditionals
                condition_str = ast.dump(child.test)
                if any(pattern in condition_str.lower() for pattern in validation_patterns):
                    return True
        
        return False
    
    def _add_vulnerability(self, node: ast.AST, pattern: SecurityPattern, confidence: float):
        """Add detected vulnerability."""
        line_no = getattr(node, 'lineno', 0)
        code_snippet = self.source_lines[line_no - 1] if line_no > 0 and line_no <= len(self.source_lines) else ""
        
        vuln = CodeVulnerability(
            pattern=pattern,
            file_path=self.current_file,
            line_number=line_no,
            code_snippet=code_snippet.strip(),
            confidence=confidence
        )
        
        self.vulnerabilities.append(vuln)


class TaintAnalyzer:
    """Performs taint analysis for data flow tracking."""
    
    def __init__(self):
        """Initialize taint analyzer."""
        self.taint_sources = {
            'user_input': ['input', 'request.args', 'request.form', 'request.json', 'sys.argv'],
            'file_input': ['open', 'read', 'readlines', 'pickle.load'],
            'network_input': ['recv', 'recvfrom', 'request.data', 'socket.recv'],
            'env_input': ['os.environ', 'getenv'],
        }
        
        self.taint_sinks = {
            'code_execution': ['eval', 'exec', 'compile', '__import__'],
            'command_execution': ['os.system', 'subprocess.call', 'subprocess.run', 'os.popen'],
            'sql_execution': ['execute', 'executemany', 'raw'],
            'file_operations': ['open', 'write', 'unlink', 'remove'],
            'network_operations': ['send', 'sendto', 'urlopen'],
        }
        
        self.tainted_variables: Dict[str, Set[str]] = {}  # var_name -> taint_sources
        
    def analyze_data_flow(self, ast_tree: ast.AST) -> List[Tuple[str, str, List[str]]]:
        """
        Analyze data flow to find taint propagation.
        
        Returns:
            List of (source, sink, path) tuples
        """
        flows = []
        
        # Build control flow graph (simplified)
        cfg = self._build_cfg(ast_tree)
        
        # Track taint propagation
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.Assign):
                self._process_assignment(node)
            elif isinstance(node, ast.Call):
                sink_flow = self._check_sink(node)
                if sink_flow:
                    flows.append(sink_flow)
        
        return flows
    
    def _build_cfg(self, ast_tree: ast.AST) -> Dict[ast.AST, List[ast.AST]]:
        """Build simplified control flow graph."""
        # This is a simplified version - real CFG building is complex
        cfg = {}
        
        class CFGBuilder(ast.NodeVisitor):
            def __init__(self):
                self.current_block = []
                self.blocks = []
            
            def visit_FunctionDef(self, node):
                self.current_block = []
                self.generic_visit(node)
                if self.current_block:
                    self.blocks.append(self.current_block)
            
            def visit_If(self, node):
                if self.current_block:
                    self.blocks.append(self.current_block)
                self.current_block = []
                self.generic_visit(node)
        
        builder = CFGBuilder()
        builder.visit(ast_tree)
        
        return cfg
    
    def _process_assignment(self, node: ast.Assign):
        """Process assignment for taint tracking."""
        # Get assigned variables
        targets = []
        for target in node.targets:
            if isinstance(target, ast.Name):
                targets.append(target.id)
        
        # Check if value is tainted
        taint_sources = self._get_taint_sources(node.value)
        if taint_sources:
            for target in targets:
                self.tainted_variables[target] = taint_sources
    
    def _get_taint_sources(self, node: ast.AST) -> Set[str]:
        """Get taint sources from an expression."""
        sources = set()
        
        if isinstance(node, ast.Call):
            func_name = self._get_func_name(node)
            for source_type, source_funcs in self.taint_sources.items():
                if func_name in source_funcs:
                    sources.add(f"{source_type}:{func_name}")
        
        elif isinstance(node, ast.Name) and node.id in self.tainted_variables:
            sources.update(self.tainted_variables[node.id])
        
        return sources
    
    def _check_sink(self, node: ast.Call) -> Optional[Tuple[str, str, List[str]]]:
        """Check if call is a taint sink with tainted input."""
        func_name = self._get_func_name(node)
        
        # Check if it's a sink
        sink_type = None
        for sink_cat, sink_funcs in self.taint_sinks.items():
            if func_name in sink_funcs:
                sink_type = sink_cat
                break
        
        if not sink_type:
            return None
        
        # Check if any argument is tainted
        for arg in node.args:
            taint_sources = self._get_taint_sources(arg)
            if taint_sources:
                return (
                    ','.join(taint_sources),
                    f"{sink_type}:{func_name}",
                    []  # Simplified - no path tracking
                )
        
        return None
    
    def _get_func_name(self, node: ast.Call) -> str:
        """Extract function name from call."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""


class ASTAnalyzer:
    """Main AST analyzer for code vulnerability detection."""
    
    def __init__(self):
        """Initialize AST analyzer."""
        self.security_patterns = self._load_security_patterns()
        self.visitor = ASTSecurityVisitor(self.security_patterns)
        self.taint_analyzer = TaintAnalyzer()
    
    def analyze_code(self, code_path: str) -> Dict[str, Any]:
        """
        Analyze code for security vulnerabilities.
        
        Args:
            code_path: Path to code file or directory
            
        Returns:
            Analysis results with vulnerabilities
        """
        path = Path(code_path)
        vulnerabilities = []
        
        if path.is_file() and path.suffix == '.py':
            vulnerabilities.extend(self._analyze_file(str(path)))
        elif path.is_dir():
            for py_file in path.rglob("*.py"):
                vulnerabilities.extend(self._analyze_file(str(py_file)))
        
        # Categorize vulnerabilities
        by_severity = self._categorize_by_severity(vulnerabilities)
        by_type = self._categorize_by_type(vulnerabilities)
        
        return {
            'total_vulnerabilities': len(vulnerabilities),
            'vulnerabilities': [v.to_dict() for v in vulnerabilities],
            'by_severity': by_severity,
            'by_type': by_type,
            'risk_score': self._calculate_risk_score(vulnerabilities)
        }
    
    def _analyze_file(self, file_path: str) -> List[CodeVulnerability]:
        """Analyze single file."""
        vulnerabilities = []
        
        # AST-based analysis
        ast_vulns = self.visitor.analyze_file(file_path)
        vulnerabilities.extend(ast_vulns)
        
        # Additional pattern-based analysis
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check for regex patterns
        regex_vulns = self._check_regex_patterns(file_path, content)
        vulnerabilities.extend(regex_vulns)
        
        return vulnerabilities
    
    def _load_security_patterns(self) -> List[SecurityPattern]:
        """Load security patterns for detection."""
        patterns = []
        
        # Add more sophisticated patterns
        patterns.extend([
            SecurityPattern(
                name='jwt_none_algorithm',
                description='JWT none algorithm vulnerability',
                severity='critical',
                pattern_type='regex_pattern',
                detection_logic=re.compile(r'algorithm["\']?\s*:\s*["\']none["\']', re.I),
                mitigation='Never allow "none" algorithm in JWT',
                cwe_id='CWE-347'
            ),
            SecurityPattern(
                name='weak_random',
                description='Use of weak random number generator',
                severity='medium',
                pattern_type='ast_pattern',
                detection_logic=lambda node: isinstance(node, ast.Call) and 
                              any(name in str(node.func) for name in ['random.random', 'random.randint']),
                mitigation='Use secrets module for cryptographic randomness',
                cwe_id='CWE-330'
            ),
            SecurityPattern(
                name='path_traversal',
                description='Potential path traversal vulnerability',
                severity='high',
                pattern_type='regex_pattern',
                detection_logic=re.compile(r'open\s*\([^)]*\+[^)]*\)'),
                mitigation='Validate and sanitize file paths',
                cwe_id='CWE-22'
            ),
            SecurityPattern(
                name='xxe_vulnerability',
                description='XML External Entity vulnerability',
                severity='high',
                pattern_type='regex_pattern',
                detection_logic=re.compile(r'XMLParser\s*\([^)]*resolve_entities\s*=\s*True'),
                mitigation='Disable external entity resolution',
                cwe_id='CWE-611'
            ),
            SecurityPattern(
                name='insecure_ssl',
                description='Insecure SSL/TLS configuration',
                severity='medium',
                pattern_type='regex_pattern',
                detection_logic=re.compile(r'verify\s*=\s*False|ssl\._create_unverified_context'),
                mitigation='Always verify SSL certificates',
                cwe_id='CWE-295'
            )
        ])
        
        return patterns
    
    def _check_regex_patterns(self, file_path: str, content: str) -> List[CodeVulnerability]:
        """Check regex-based patterns."""
        vulnerabilities = []
        
        for pattern in self.security_patterns:
            if pattern.pattern_type == 'regex_pattern' and isinstance(pattern.detection_logic, re.Pattern):
                for match in pattern.detection_logic.finditer(content):
                    line_no = content[:match.start()].count('\n') + 1
                    line = content.splitlines()[line_no - 1] if line_no <= len(content.splitlines()) else ""
                    
                    vuln = CodeVulnerability(
                        pattern=pattern,
                        file_path=file_path,
                        line_number=line_no,
                        code_snippet=line.strip(),
                        confidence=0.8
                    )
                    vulnerabilities.append(vuln)
        
        return vulnerabilities
    
    def _categorize_by_severity(self, vulnerabilities: List[CodeVulnerability]) -> Dict[str, int]:
        """Categorize vulnerabilities by severity."""
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        
        for vuln in vulnerabilities:
            severity_counts[vuln.pattern.severity] += 1
        
        return severity_counts
    
    def _categorize_by_type(self, vulnerabilities: List[CodeVulnerability]) -> Dict[str, int]:
        """Categorize vulnerabilities by type."""
        type_counts = {}
        
        for vuln in vulnerabilities:
            vuln_type = vuln.pattern.name
            type_counts[vuln_type] = type_counts.get(vuln_type, 0) + 1
        
        return type_counts
    
    def _calculate_risk_score(self, vulnerabilities: List[CodeVulnerability]) -> float:
        """Calculate overall risk score based on vulnerabilities."""
        if not vulnerabilities:
            return 0.0
        
        severity_weights = {
            'critical': 10.0,
            'high': 7.0,
            'medium': 4.0,
            'low': 1.0
        }
        
        total_score = sum(
            severity_weights.get(v.pattern.severity, 0) * v.confidence
            for v in vulnerabilities
        )
        
        # Normalize to 0-10 scale
        return min(10.0, total_score / len(vulnerabilities) * 2)