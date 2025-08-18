"""Context-based risk weight calculation."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
import yaml
from pathlib import Path


class Industry(Enum):
    """Industry/context categories."""

    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    LEGAL = "legal"
    EDUCATION = "education"
    ENTERTAINMENT = "entertainment"
    RETAIL = "retail"
    GOVERNMENT = "government"
    TECHNOLOGY = "technology"
    MANUFACTURING = "manufacturing"
    TRANSPORTATION = "transportation"
    ENERGY = "energy"
    GENERAL = "general"


class Sensitivity(Enum):
    """Data sensitivity levels."""

    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    SECRET = "secret"
    TOP_SECRET = "top_secret"


@dataclass
class ContextWeight:
    """Weight multiplier for specific context."""

    industry: Industry
    base_multiplier: float
    sensitivity_multipliers: Dict[Sensitivity, float]
    error_type_adjustments: Dict[str, float] = field(default_factory=dict)
    description: str = ""
    regulatory_requirements: List[str] = field(default_factory=list)

    def get_multiplier(
        self, sensitivity: Sensitivity, error_type: Optional[str] = None
    ) -> float:
        """
        Get total multiplier for given sensitivity and error type.

        Args:
            sensitivity: Data sensitivity level
            error_type: Optional error type for adjustment

        Returns:
            Total multiplier value
        """
        multiplier = self.base_multiplier

        # Apply sensitivity multiplier
        if sensitivity in self.sensitivity_multipliers:
            multiplier *= self.sensitivity_multipliers[sensitivity]

        # Apply error type adjustment if specified
        if error_type and error_type in self.error_type_adjustments:
            multiplier *= self.error_type_adjustments[error_type]

        return multiplier


class ContextWeigher:
    """Calculates risk weights based on context."""

    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize context weigher.

        Args:
            config_file: Path to configuration file
        """
        self.weights: Dict[Industry, ContextWeight] = {}
        self._initialize_default_weights()

        if config_file:
            self._load_config(config_file)

    def _initialize_default_weights(self):
        """Initialize default context weights."""
        default_weights = [
            ContextWeight(
                industry=Industry.HEALTHCARE,
                base_multiplier=3.0,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.5,
                    Sensitivity.CONFIDENTIAL: 2.0,
                    Sensitivity.SECRET: 3.0,
                    Sensitivity.TOP_SECRET: 5.0,
                },
                error_type_adjustments={
                    "hallucination": 2.0,  # Medical misinformation is extremely dangerous
                    "data_leak": 2.5,  # HIPAA violations
                    "bias_amplification": 1.8,  # Healthcare discrimination
                },
                description="Healthcare context with strict privacy and accuracy requirements",
                regulatory_requirements=["HIPAA", "HITECH", "FDA regulations"],
            ),
            ContextWeight(
                industry=Industry.FINANCE,
                base_multiplier=2.5,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.3,
                    Sensitivity.CONFIDENTIAL: 2.0,
                    Sensitivity.SECRET: 3.0,
                    Sensitivity.TOP_SECRET: 4.0,
                },
                error_type_adjustments={
                    "hallucination": 1.8,  # Financial misinformation
                    "data_leak": 2.2,  # Financial data exposure
                    "unauthorized_access": 2.5,  # Financial fraud risk
                    "bias_amplification": 1.5,  # Fair lending concerns
                },
                description="Financial services with regulatory compliance requirements",
                regulatory_requirements=["SOX", "PCI-DSS", "GDPR", "Fair Lending Act"],
            ),
            ContextWeight(
                industry=Industry.LEGAL,
                base_multiplier=2.8,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.5,
                    Sensitivity.CONFIDENTIAL: 2.5,
                    Sensitivity.SECRET: 4.0,
                    Sensitivity.TOP_SECRET: 5.0,
                },
                error_type_adjustments={
                    "hallucination": 3.0,  # Legal misinformation is critical
                    "data_leak": 2.0,  # Attorney-client privilege
                    "incorrect_output": 2.5,  # Legal accuracy is crucial
                },
                description="Legal context requiring high accuracy and confidentiality",
                regulatory_requirements=[
                    "Attorney-client privilege",
                    "Legal ethics rules",
                ],
            ),
            ContextWeight(
                industry=Industry.GOVERNMENT,
                base_multiplier=2.2,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.5,
                    Sensitivity.CONFIDENTIAL: 2.5,
                    Sensitivity.SECRET: 4.0,
                    Sensitivity.TOP_SECRET: 6.0,
                },
                error_type_adjustments={
                    "data_leak": 3.0,  # National security concerns
                    "unauthorized_access": 3.0,
                    "security_bypass": 3.5,
                },
                description="Government operations with security classifications",
                regulatory_requirements=[
                    "FISMA",
                    "FedRAMP",
                    "Security clearance requirements",
                ],
            ),
            ContextWeight(
                industry=Industry.EDUCATION,
                base_multiplier=1.5,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.2,
                    Sensitivity.CONFIDENTIAL: 1.8,
                    Sensitivity.SECRET: 2.5,
                    Sensitivity.TOP_SECRET: 3.0,
                },
                error_type_adjustments={
                    "hallucination": 1.5,  # Educational misinformation
                    "bias_amplification": 1.8,  # Educational equity
                    "data_leak": 1.5,  # FERPA compliance
                },
                description="Educational context with student privacy concerns",
                regulatory_requirements=["FERPA", "COPPA (for minors)"],
            ),
            ContextWeight(
                industry=Industry.ENTERTAINMENT,
                base_multiplier=0.5,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.1,
                    Sensitivity.CONFIDENTIAL: 1.3,
                    Sensitivity.SECRET: 1.5,
                    Sensitivity.TOP_SECRET: 2.0,
                },
                error_type_adjustments={
                    "hallucination": 0.5,  # Less critical in entertainment
                    "bias_amplification": 1.2,  # Still important for representation
                },
                description="Entertainment context with lower risk tolerance",
                regulatory_requirements=["Copyright", "Content ratings"],
            ),
            ContextWeight(
                industry=Industry.RETAIL,
                base_multiplier=1.0,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.2,
                    Sensitivity.CONFIDENTIAL: 1.5,
                    Sensitivity.SECRET: 2.0,
                    Sensitivity.TOP_SECRET: 2.5,
                },
                error_type_adjustments={
                    "data_leak": 1.5,  # Customer data protection
                    "financial_loss": 1.3,  # Transaction errors
                },
                description="Retail operations with customer data concerns",
                regulatory_requirements=["PCI-DSS", "Consumer protection laws"],
            ),
            ContextWeight(
                industry=Industry.TECHNOLOGY,
                base_multiplier=1.2,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.3,
                    Sensitivity.CONFIDENTIAL: 1.8,
                    Sensitivity.SECRET: 2.5,
                    Sensitivity.TOP_SECRET: 3.0,
                },
                error_type_adjustments={
                    "security_bypass": 2.0,
                    "unauthorized_access": 1.8,
                    "resource_exhaustion": 1.5,
                },
                description="Technology sector with security focus",
                regulatory_requirements=["SOC 2", "ISO 27001"],
            ),
            ContextWeight(
                industry=Industry.GENERAL,
                base_multiplier=1.0,
                sensitivity_multipliers={
                    Sensitivity.PUBLIC: 1.0,
                    Sensitivity.INTERNAL: 1.2,
                    Sensitivity.CONFIDENTIAL: 1.5,
                    Sensitivity.SECRET: 2.0,
                    Sensitivity.TOP_SECRET: 3.0,
                },
                description="General purpose context with standard weights",
                regulatory_requirements=["GDPR", "CCPA"],
            ),
        ]

        for weight in default_weights:
            self.weights[weight.industry] = weight

    def _load_config(self, config_file: str):
        """Load configuration from file."""
        path = Path(config_file)
        if not path.exists():
            return

        with open(path, "r") as f:
            if path.suffix in [".yaml", ".yml"]:
                data = yaml.safe_load(f)
            else:
                data = json.load(f)

        for industry_name, weight_data in data.get("weights", {}).items():
            try:
                industry = Industry(industry_name)

                # Parse sensitivity multipliers
                sensitivity_multipliers = {}
                for sens_name, mult in weight_data.get(
                    "sensitivity_multipliers", {}
                ).items():
                    sensitivity = Sensitivity(sens_name)
                    sensitivity_multipliers[sensitivity] = float(mult)

                weight = ContextWeight(
                    industry=industry,
                    base_multiplier=float(weight_data["base_multiplier"]),
                    sensitivity_multipliers=sensitivity_multipliers,
                    error_type_adjustments=weight_data.get(
                        "error_type_adjustments", {}
                    ),
                    description=weight_data.get("description", ""),
                    regulatory_requirements=weight_data.get(
                        "regulatory_requirements", []
                    ),
                )

                self.weights[industry] = weight

            except (KeyError, ValueError) as e:
                print(f"Error loading weight config for {industry_name}: {e}")

    def get_weight(
        self,
        industry: Industry,
        sensitivity: Sensitivity = Sensitivity.INTERNAL,
        error_type: Optional[str] = None,
    ) -> float:
        """
        Get risk weight for given context.

        Args:
            industry: Industry context
            sensitivity: Data sensitivity level
            error_type: Optional error type

        Returns:
            Risk weight multiplier
        """
        if industry not in self.weights:
            industry = Industry.GENERAL

        weight = self.weights[industry]
        return weight.get_multiplier(sensitivity, error_type)

    def get_regulatory_requirements(self, industry: Industry) -> List[str]:
        """Get regulatory requirements for industry."""
        if industry in self.weights:
            return self.weights[industry].regulatory_requirements
        return []

    def analyze_context(self, context_description: str) -> Industry:
        """
        Analyze context description and determine industry.

        Args:
            context_description: Description of use case context

        Returns:
            Identified industry
        """
        context_lower = context_description.lower()

        # Keyword-based industry detection
        industry_keywords = {
            Industry.HEALTHCARE: [
                "medical",
                "health",
                "patient",
                "doctor",
                "hospital",
                "clinical",
                "diagnosis",
            ],
            Industry.FINANCE: [
                "financial",
                "banking",
                "investment",
                "trading",
                "payment",
                "transaction",
                "credit",
            ],
            Industry.LEGAL: [
                "legal",
                "law",
                "attorney",
                "court",
                "litigation",
                "contract",
                "compliance",
            ],
            Industry.GOVERNMENT: [
                "government",
                "federal",
                "state",
                "municipal",
                "agency",
                "public sector",
            ],
            Industry.EDUCATION: [
                "education",
                "school",
                "university",
                "student",
                "teacher",
                "learning",
                "academic",
            ],
            Industry.ENTERTAINMENT: [
                "entertainment",
                "gaming",
                "media",
                "content",
                "streaming",
                "social",
            ],
            Industry.RETAIL: [
                "retail",
                "ecommerce",
                "shopping",
                "customer",
                "product",
                "inventory",
            ],
            Industry.TECHNOLOGY: [
                "software",
                "technology",
                "IT",
                "development",
                "infrastructure",
                "cloud",
            ],
        }

        # Count keyword matches
        industry_scores = {}
        for industry, keywords in industry_keywords.items():
            score = sum(1 for keyword in keywords if keyword in context_lower)
            if score > 0:
                industry_scores[industry] = score

        # Return industry with highest score
        if industry_scores:
            return max(industry_scores.items(), key=lambda x: x[1])[0]

        return Industry.GENERAL

    def calculate_weighted_risk(
        self,
        base_risk: float,
        industry: Industry,
        sensitivity: Sensitivity = Sensitivity.INTERNAL,
        error_types: Optional[List[str]] = None,
    ) -> float:
        """
        Calculate weighted risk score.

        Args:
            base_risk: Base risk score (0-10)
            industry: Industry context
            sensitivity: Data sensitivity level
            error_types: List of error types present

        Returns:
            Weighted risk score
        """
        # Get base weight
        weight = self.get_weight(industry, sensitivity)

        # Apply additional weights for each error type
        if error_types:
            for error_type in error_types:
                error_weight = self.get_weight(industry, sensitivity, error_type)
                weight = max(weight, error_weight)  # Use maximum weight

        # Calculate weighted risk (capped at 10)
        weighted_risk = min(base_risk * weight, 10.0)

        return weighted_risk

    def get_context_summary(self, industry: Industry) -> Dict[str, Any]:
        """Get summary of context weights and requirements."""
        if industry not in self.weights:
            industry = Industry.GENERAL

        weight = self.weights[industry]

        return {
            "industry": industry.value,
            "base_multiplier": weight.base_multiplier,
            "description": weight.description,
            "regulatory_requirements": weight.regulatory_requirements,
            "sensitivity_impact": {
                sens.value: mult
                for sens, mult in weight.sensitivity_multipliers.items()
            },
            "error_type_adjustments": weight.error_type_adjustments,
        }
