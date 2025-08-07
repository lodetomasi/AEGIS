"""Risk mapping from technical errors to business impacts."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from pathlib import Path


class ErrorType(Enum):
    """Types of technical errors."""
    
    HALLUCINATION = "hallucination"
    WRONG_TOOL_USE = "wrong_tool_use"
    DATA_LEAK = "data_leak"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    INFINITE_LOOP = "infinite_loop"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    INCORRECT_OUTPUT = "incorrect_output"
    PROMPT_INJECTION = "prompt_injection"
    MODEL_MANIPULATION = "model_manipulation"
    BIAS_AMPLIFICATION = "bias_amplification"
    PRIVACY_VIOLATION = "privacy_violation"
    SECURITY_BYPASS = "security_bypass"
    OTHER = "other"


class ImpactType(Enum):
    """Types of business impacts."""
    
    FINANCIAL_LOSS = "financial_loss"
    REPUTATION_DAMAGE = "reputation_damage"
    COMPLIANCE_VIOLATION = "compliance_violation"
    DATA_BREACH = "data_breach"
    SERVICE_DISRUPTION = "service_disruption"
    LEGAL_LIABILITY = "legal_liability"
    CUSTOMER_HARM = "customer_harm"
    OPERATIONAL_FAILURE = "operational_failure"
    COMPETITIVE_DISADVANTAGE = "competitive_disadvantage"


@dataclass
class RiskMapping:
    """Mapping from error to business impact."""
    
    error_type: ErrorType
    impact_type: ImpactType
    severity: int  # 1-10
    description: str
    examples: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'error_type': self.error_type.value,
            'impact_type': self.impact_type.value,
            'severity': self.severity,
            'description': self.description,
            'examples': self.examples,
            'mitigation_strategies': self.mitigation_strategies,
            'metadata': self.metadata
        }


class RiskMapper:
    """Maps technical errors to business impacts."""
    
    def __init__(self, mappings_file: Optional[str] = None):
        """
        Initialize risk mapper.
        
        Args:
            mappings_file: Path to custom mappings file
        """
        self.mappings: Dict[ErrorType, List[RiskMapping]] = {}
        self._initialize_default_mappings()
        
        if mappings_file:
            self._load_custom_mappings(mappings_file)
    
    def _initialize_default_mappings(self):
        """Initialize default risk mappings."""
        default_mappings = [
            # Hallucination mappings
            RiskMapping(
                error_type=ErrorType.HALLUCINATION,
                impact_type=ImpactType.REPUTATION_DAMAGE,
                severity=8,
                description="AI providing false information damages trust and credibility",
                examples=[
                    "Medical AI giving incorrect diagnosis",
                    "Financial advisor AI suggesting non-existent investments",
                    "Customer service AI providing false product information"
                ],
                mitigation_strategies=[
                    "Implement fact-checking mechanisms",
                    "Add confidence scores to outputs",
                    "Require human review for critical decisions"
                ]
            ),
            RiskMapping(
                error_type=ErrorType.HALLUCINATION,
                impact_type=ImpactType.LEGAL_LIABILITY,
                severity=9,
                description="False information leading to legal consequences",
                examples=[
                    "Legal AI misquoting laws or precedents",
                    "Compliance AI providing incorrect regulatory guidance"
                ],
                mitigation_strategies=[
                    "Always cite sources",
                    "Implement legal review process",
                    "Add disclaimers about AI limitations"
                ]
            ),
            
            # Data leak mappings
            RiskMapping(
                error_type=ErrorType.DATA_LEAK,
                impact_type=ImpactType.DATA_BREACH,
                severity=10,
                description="Exposure of sensitive or confidential information",
                examples=[
                    "AI revealing customer PII in responses",
                    "Training data leakage through model outputs",
                    "Cross-contamination between user sessions"
                ],
                mitigation_strategies=[
                    "Implement strict data isolation",
                    "Use differential privacy techniques",
                    "Regular security audits"
                ]
            ),
            RiskMapping(
                error_type=ErrorType.DATA_LEAK,
                impact_type=ImpactType.COMPLIANCE_VIOLATION,
                severity=9,
                description="Violation of data protection regulations",
                examples=[
                    "GDPR violation through unauthorized data sharing",
                    "HIPAA breach in healthcare contexts",
                    "Financial data exposure violating regulations"
                ],
                mitigation_strategies=[
                    "Implement compliance checks",
                    "Data classification and handling protocols",
                    "Regular compliance training"
                ]
            ),
            
            # Wrong tool use mappings
            RiskMapping(
                error_type=ErrorType.WRONG_TOOL_USE,
                impact_type=ImpactType.OPERATIONAL_FAILURE,
                severity=7,
                description="Incorrect tool usage leading to system failures",
                examples=[
                    "Using write permissions when only read is needed",
                    "Calling production APIs during testing",
                    "Executing destructive operations unintentionally"
                ],
                mitigation_strategies=[
                    "Implement tool permission systems",
                    "Add confirmation steps for destructive actions",
                    "Use sandboxed environments"
                ]
            ),
            RiskMapping(
                error_type=ErrorType.WRONG_TOOL_USE,
                impact_type=ImpactType.FINANCIAL_LOSS,
                severity=8,
                description="Improper tool use causing financial damage",
                examples=[
                    "Incorrect API calls leading to excessive charges",
                    "Wrong database operations causing data corruption",
                    "Automation errors in financial transactions"
                ],
                mitigation_strategies=[
                    "Implement spending limits",
                    "Add transaction validation",
                    "Use test environments"
                ]
            ),
            
            # Unauthorized access mappings
            RiskMapping(
                error_type=ErrorType.UNAUTHORIZED_ACCESS,
                impact_type=ImpactType.SECURITY_BYPASS,
                severity=10,
                description="Bypassing security controls",
                examples=[
                    "Privilege escalation attempts",
                    "Accessing restricted resources",
                    "Circumventing authentication"
                ],
                mitigation_strategies=[
                    "Implement least privilege principle",
                    "Regular permission audits",
                    "Multi-factor authentication"
                ]
            ),
            
            # Resource exhaustion mappings
            RiskMapping(
                error_type=ErrorType.RESOURCE_EXHAUSTION,
                impact_type=ImpactType.SERVICE_DISRUPTION,
                severity=8,
                description="Consuming excessive resources causing service issues",
                examples=[
                    "Infinite loops consuming CPU",
                    "Memory leaks causing crashes",
                    "API rate limit exhaustion"
                ],
                mitigation_strategies=[
                    "Implement resource limits",
                    "Timeout mechanisms",
                    "Resource monitoring and alerts"
                ]
            ),
            
            # Bias amplification mappings
            RiskMapping(
                error_type=ErrorType.BIAS_AMPLIFICATION,
                impact_type=ImpactType.REPUTATION_DAMAGE,
                severity=7,
                description="Amplifying societal biases causing harm",
                examples=[
                    "Discriminatory hiring recommendations",
                    "Biased loan approval decisions",
                    "Stereotypical content generation"
                ],
                mitigation_strategies=[
                    "Bias testing and monitoring",
                    "Diverse training data",
                    "Fairness constraints"
                ]
            ),
            RiskMapping(
                error_type=ErrorType.BIAS_AMPLIFICATION,
                impact_type=ImpactType.LEGAL_LIABILITY,
                severity=8,
                description="Discriminatory behavior leading to legal issues",
                examples=[
                    "Employment discrimination",
                    "Fair lending violations",
                    "Equal opportunity violations"
                ],
                mitigation_strategies=[
                    "Regular bias audits",
                    "Legal compliance reviews",
                    "Transparent decision-making"
                ]
            )
        ]
        
        # Organize mappings by error type
        for mapping in default_mappings:
            if mapping.error_type not in self.mappings:
                self.mappings[mapping.error_type] = []
            self.mappings[mapping.error_type].append(mapping)
    
    def _load_custom_mappings(self, mappings_file: str):
        """Load custom mappings from file."""
        path = Path(mappings_file)
        if not path.exists():
            return
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        for mapping_data in data.get('mappings', []):
            try:
                error_type = ErrorType(mapping_data['error_type'])
                impact_type = ImpactType(mapping_data['impact_type'])
                
                mapping = RiskMapping(
                    error_type=error_type,
                    impact_type=impact_type,
                    severity=mapping_data['severity'],
                    description=mapping_data['description'],
                    examples=mapping_data.get('examples', []),
                    mitigation_strategies=mapping_data.get('mitigation_strategies', []),
                    metadata=mapping_data.get('metadata', {})
                )
                
                if error_type not in self.mappings:
                    self.mappings[error_type] = []
                self.mappings[error_type].append(mapping)
                
            except (KeyError, ValueError) as e:
                print(f"Error loading mapping: {e}")
    
    def get_impacts(self, error_type: ErrorType) -> List[RiskMapping]:
        """Get all potential impacts for an error type."""
        return self.mappings.get(error_type, [])
    
    def get_severity(self, error_type: ErrorType, impact_type: Optional[ImpactType] = None) -> int:
        """
        Get severity score for error type.
        
        Args:
            error_type: Type of error
            impact_type: Specific impact type (optional)
            
        Returns:
            Maximum severity score
        """
        mappings = self.get_impacts(error_type)
        
        if not mappings:
            return 5  # Default medium severity
        
        if impact_type:
            relevant_mappings = [m for m in mappings if m.impact_type == impact_type]
            if relevant_mappings:
                return max(m.severity for m in relevant_mappings)
        
        return max(m.severity for m in mappings)
    
    def get_mitigation_strategies(self, error_type: ErrorType) -> List[str]:
        """Get all mitigation strategies for an error type."""
        strategies = set()
        
        for mapping in self.get_impacts(error_type):
            strategies.update(mapping.mitigation_strategies)
        
        return sorted(list(strategies))
    
    def analyze_error(self, error_description: str) -> ErrorType:
        """
        Analyze error description and classify error type.
        
        Args:
            error_description: Description of the error
            
        Returns:
            Classified error type
        """
        error_lower = error_description.lower()
        
        # Simple keyword-based classification
        if any(word in error_lower for word in ['hallucin', 'false', 'incorrect fact', 'made up']):
            return ErrorType.HALLUCINATION
        elif any(word in error_lower for word in ['leak', 'expose', 'reveal', 'disclose']):
            return ErrorType.DATA_LEAK
        elif any(word in error_lower for word in ['wrong tool', 'incorrect function', 'misuse']):
            return ErrorType.WRONG_TOOL_USE
        elif any(word in error_lower for word in ['unauthorized', 'permission', 'access denied']):
            return ErrorType.UNAUTHORIZED_ACCESS
        elif any(word in error_lower for word in ['infinite', 'loop', 'stuck', 'hanging']):
            return ErrorType.INFINITE_LOOP
        elif any(word in error_lower for word in ['memory', 'cpu', 'resource', 'exhaust']):
            return ErrorType.RESOURCE_EXHAUSTION
        elif any(word in error_lower for word in ['bias', 'discriminat', 'unfair', 'prejud']):
            return ErrorType.BIAS_AMPLIFICATION
        elif any(word in error_lower for word in ['inject', 'manipulat', 'exploit']):
            return ErrorType.PROMPT_INJECTION
        elif any(word in error_lower for word in ['privacy', 'personal', 'pii']):
            return ErrorType.PRIVACY_VIOLATION
        else:
            return ErrorType.OTHER
    
    def get_risk_summary(self, errors: List[str]) -> Dict[str, Any]:
        """
        Get risk summary for a list of errors.
        
        Args:
            errors: List of error descriptions
            
        Returns:
            Risk summary with impacts and severities
        """
        error_types = [self.analyze_error(error) for error in errors]
        
        # Count error types
        error_counts = {}
        for error_type in error_types:
            error_counts[error_type.value] = error_counts.get(error_type.value, 0) + 1
        
        # Collect all impacts
        all_impacts = {}
        max_severity = 0
        
        for error_type in set(error_types):
            impacts = self.get_impacts(error_type)
            for impact in impacts:
                impact_key = impact.impact_type.value
                if impact_key not in all_impacts or all_impacts[impact_key]['severity'] < impact.severity:
                    all_impacts[impact_key] = {
                        'severity': impact.severity,
                        'description': impact.description,
                        'error_types': []
                    }
                all_impacts[impact_key]['error_types'].append(error_type.value)
                max_severity = max(max_severity, impact.severity)
        
        return {
            'error_counts': error_counts,
            'impacts': all_impacts,
            'max_severity': max_severity,
            'risk_level': self._severity_to_risk_level(max_severity)
        }
    
    def _severity_to_risk_level(self, severity: int) -> str:
        """Convert severity score to risk level."""
        if severity >= 9:
            return "CRITICAL"
        elif severity >= 7:
            return "HIGH"
        elif severity >= 5:
            return "MEDIUM"
        elif severity >= 3:
            return "LOW"
        else:
            return "MINIMAL"