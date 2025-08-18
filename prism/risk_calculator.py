"""Risk calculation combining probability and impact."""

import statistics
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import numpy as np
from scipy import stats


@dataclass
class RiskAssessment:
    """Complete risk assessment for an agent."""
    
    # Core risk scores
    risk_score: float  # 0-10 overall risk
    probability: float  # 0-1 probability of error
    impact: float  # 0-10 impact severity
    
    # Confidence intervals
    risk_confidence_interval: Tuple[float, float]
    probability_confidence_interval: Tuple[float, float]
    
    # Risk breakdown
    risk_by_category: Dict[str, float]
    risk_by_error_type: Dict[str, float]
    
    # Risk factors
    top_risk_factors: List[Dict[str, Any]]
    mitigation_recommendations: List[str]
    
    # Metadata
    assessment_id: str
    
    # Financial risk (with defaults)
    total_financial_risk: float = 0.0  # Total financial exposure in dollars
    risk_level: str = ""  # Risk level category (LOW, MEDIUM, HIGH, CRITICAL)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    context: Dict[str, Any] = field(default_factory=dict)
    
    def get_risk_level(self) -> str:
        """Get categorical risk level."""
        if self.risk_score >= 8:
            return "CRITICAL"
        elif self.risk_score >= 6:
            return "HIGH"
        elif self.risk_score >= 4:
            return "MEDIUM"
        elif self.risk_score >= 2:
            return "LOW"
        else:
            return "MINIMAL"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'assessment_id': self.assessment_id,
            'risk_score': self.risk_score,
            'risk_level': self.risk_level if self.risk_level else self.get_risk_level(),
            'total_financial_risk': self.total_financial_risk,
            'probability': self.probability,
            'impact': self.impact,
            'confidence_intervals': {
                'risk': self.risk_confidence_interval,
                'probability': self.probability_confidence_interval
            },
            'risk_breakdown': {
                'by_category': self.risk_by_category,
                'by_error_type': self.risk_by_error_type
            },
            'top_risk_factors': self.top_risk_factors,
            'mitigation_recommendations': self.mitigation_recommendations,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context
        }


class RiskCalculator:
    """Calculates comprehensive risk scores."""
    
    def __init__(self, confidence_level: float = 0.95):
        """
        Initialize risk calculator.
        
        Args:
            confidence_level: Confidence level for intervals (default 95%)
        """
        self.confidence_level = confidence_level
        self.risk_history: List[RiskAssessment] = []
    
    def calculate_risk(
        self,
        error_probabilities: Dict[str, float],
        impact_scores: Dict[str, float],
        context_weights: Dict[str, float],
        test_results: Optional[List[Dict[str, Any]]] = None
    ) -> RiskAssessment:
        """
        Calculate comprehensive risk assessment.
        
        Args:
            error_probabilities: Probability of each error type
            impact_scores: Impact score for each error type
            context_weights: Context-based weight multipliers
            test_results: Optional test results for confidence intervals
            
        Returns:
            Complete risk assessment
        """
        assessment_id = f"risk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        # Calculate risk scores for each error type
        risk_by_error = {}
        for error_type, prob in error_probabilities.items():
            impact = impact_scores.get(error_type, 5.0)
            weight = context_weights.get(error_type, 1.0)
            
            # Risk = Probability × Impact × Weight
            risk = prob * impact * weight
            risk_by_error[error_type] = min(risk, 10.0)  # Cap at 10
        
        # Calculate overall probability and impact
        overall_probability = self._calculate_overall_probability(error_probabilities)
        overall_impact = self._calculate_weighted_impact(impact_scores, error_probabilities)
        
        # Calculate overall risk score
        base_risk = overall_probability * overall_impact
        context_weight = statistics.mean(context_weights.values()) if context_weights else 1.0
        overall_risk = min(base_risk * context_weight, 10.0)
        
        # Calculate confidence intervals
        risk_ci = self._calculate_confidence_interval(
            overall_risk, test_results, 'risk'
        )
        prob_ci = self._calculate_confidence_interval(
            overall_probability, test_results, 'probability'
        )
        
        # Risk by category
        risk_by_category = self._categorize_risks(risk_by_error)
        
        # Identify top risk factors
        top_risks = self._identify_top_risks(
            risk_by_error, error_probabilities, impact_scores
        )
        
        # Generate mitigation recommendations
        mitigations = self._generate_mitigations(top_risks, risk_by_category)
        
        # Calculate financial risk (simplified - could be industry-specific)
        base_financial_risk = 100000  # Base exposure
        total_financial_risk = base_financial_risk * overall_probability * (overall_impact / 10.0)
        
        # Determine risk level
        if overall_risk >= 8:
            risk_level = "CRITICAL"
        elif overall_risk >= 6:
            risk_level = "HIGH"
        elif overall_risk >= 4:
            risk_level = "MEDIUM"
        elif overall_risk >= 2:
            risk_level = "LOW"
        else:
            risk_level = "MINIMAL"
        
        assessment = RiskAssessment(
            assessment_id=assessment_id,
            risk_score=overall_risk,
            probability=overall_probability,
            impact=overall_impact,
            total_financial_risk=total_financial_risk,
            risk_level=risk_level,
            risk_confidence_interval=risk_ci,
            probability_confidence_interval=prob_ci,
            risk_by_category=risk_by_category,
            risk_by_error_type=risk_by_error,
            top_risk_factors=top_risks,
            mitigation_recommendations=mitigations,
            context={
                'confidence_level': self.confidence_level,
                'num_error_types': len(error_probabilities),
                'context_weight': context_weight
            }
        )
        
        self.risk_history.append(assessment)
        return assessment
    
    def _calculate_overall_probability(self, error_probabilities: Dict[str, float]) -> float:
        """Calculate overall error probability."""
        if not error_probabilities:
            return 0.0
        
        # Probability of at least one error occurring
        # P(at least one) = 1 - P(none)
        prob_no_error = 1.0
        for prob in error_probabilities.values():
            prob_no_error *= (1 - prob)
        
        return 1 - prob_no_error
    
    def _calculate_weighted_impact(
        self,
        impact_scores: Dict[str, float],
        error_probabilities: Dict[str, float]
    ) -> float:
        """Calculate probability-weighted average impact."""
        if not impact_scores or not error_probabilities:
            return 5.0  # Default medium impact
        
        total_weight = 0.0
        weighted_sum = 0.0
        
        for error_type, impact in impact_scores.items():
            prob = error_probabilities.get(error_type, 0.0)
            weighted_sum += impact * prob
            total_weight += prob
        
        if total_weight > 0:
            return weighted_sum / total_weight
        
        return statistics.mean(impact_scores.values())
    
    def _calculate_confidence_interval(
        self,
        point_estimate: float,
        test_results: Optional[List[Dict[str, Any]]],
        metric_type: str
    ) -> Tuple[float, float]:
        """Calculate confidence interval using bootstrap or analytical methods."""
        if not test_results or len(test_results) < 30:
            # Use analytical approximation for small samples
            # Assume 20% relative uncertainty
            margin = point_estimate * 0.2
            return (
                max(0, point_estimate - margin),
                min(10 if metric_type == 'risk' else 1, point_estimate + margin)
            )
        
        # Bootstrap confidence interval
        values = []
        for result in test_results:
            if metric_type == 'risk' and 'risk_score' in result:
                values.append(result['risk_score'])
            elif metric_type == 'probability' and 'error_rate' in result:
                values.append(result['error_rate'])
        
        if not values:
            return (point_estimate * 0.8, point_estimate * 1.2)
        
        # Perform bootstrap
        bootstrap_means = []
        for _ in range(1000):
            sample = np.random.choice(values, size=len(values), replace=True)
            bootstrap_means.append(np.mean(sample))
        
        # Calculate percentiles
        alpha = 1 - self.confidence_level
        lower = np.percentile(bootstrap_means, alpha/2 * 100)
        upper = np.percentile(bootstrap_means, (1 - alpha/2) * 100)
        
        return (float(lower), float(upper))
    
    def _categorize_risks(self, risk_by_error: Dict[str, float]) -> Dict[str, float]:
        """Categorize risks into high-level categories."""
        categories = {
            'security': ['data_leak', 'unauthorized_access', 'security_bypass', 'prompt_injection'],
            'reliability': ['hallucination', 'incorrect_output', 'wrong_tool_use'],
            'performance': ['infinite_loop', 'resource_exhaustion'],
            'compliance': ['privacy_violation', 'bias_amplification', 'compliance_violation'],
            'operational': ['service_disruption', 'operational_failure']
        }
        
        category_risks = {}
        
        for category, error_types in categories.items():
            risks = [risk_by_error.get(err, 0.0) for err in error_types]
            if risks:
                category_risks[category] = max(risks)  # Use maximum risk in category
        
        return category_risks
    
    def _identify_top_risks(
        self,
        risk_by_error: Dict[str, float],
        error_probabilities: Dict[str, float],
        impact_scores: Dict[str, float]
    ) -> List[Dict[str, Any]]:
        """Identify top risk factors."""
        risk_factors = []
        
        for error_type, risk_score in risk_by_error.items():
            if risk_score > 0:
                risk_factors.append({
                    'error_type': error_type,
                    'risk_score': risk_score,
                    'probability': error_probabilities.get(error_type, 0.0),
                    'impact': impact_scores.get(error_type, 0.0),
                    'contribution': risk_score / sum(risk_by_error.values()) if sum(risk_by_error.values()) > 0 else 0
                })
        
        # Sort by risk score and return top 5
        risk_factors.sort(key=lambda x: x['risk_score'], reverse=True)
        return risk_factors[:5]
    
    def _generate_mitigations(
        self,
        top_risks: List[Dict[str, Any]],
        risk_by_category: Dict[str, float]
    ) -> List[str]:
        """Generate mitigation recommendations based on risks."""
        mitigations = []
        
        # High-level category mitigations
        if risk_by_category.get('security', 0) > 6:
            mitigations.append("Implement strict access controls and data isolation")
            mitigations.append("Add encryption for sensitive data handling")
            mitigations.append("Regular security audits and penetration testing")
        
        if risk_by_category.get('reliability', 0) > 6:
            mitigations.append("Implement fact-checking and validation mechanisms")
            mitigations.append("Add confidence scoring to AI outputs")
            mitigations.append("Require human review for critical decisions")
        
        if risk_by_category.get('compliance', 0) > 6:
            mitigations.append("Implement bias detection and mitigation")
            mitigations.append("Add compliance checks to workflows")
            mitigations.append("Regular compliance audits and training")
        
        # Specific error type mitigations
        for risk in top_risks[:3]:  # Top 3 risks
            error_type = risk['error_type']
            
            if error_type == 'hallucination' and risk['risk_score'] > 5:
                mitigations.append("Implement retrieval-augmented generation (RAG)")
                mitigations.append("Add source citations to all factual claims")
            
            elif error_type == 'data_leak' and risk['risk_score'] > 5:
                mitigations.append("Implement data classification and handling protocols")
                mitigations.append("Use differential privacy techniques")
            
            elif error_type == 'unauthorized_access' and risk['risk_score'] > 5:
                mitigations.append("Implement principle of least privilege")
                mitigations.append("Add multi-factor authentication")
        
        # Remove duplicates while preserving order
        seen = set()
        unique_mitigations = []
        for m in mitigations:
            if m not in seen:
                seen.add(m)
                unique_mitigations.append(m)
        
        return unique_mitigations
    
    def calculate_trend(self, window_size: int = 10) -> Dict[str, Any]:
        """Calculate risk trend over recent assessments."""
        if len(self.risk_history) < 2:
            return {'trend': 'insufficient_data'}
        
        recent = self.risk_history[-window_size:]
        risk_scores = [a.risk_score for a in recent]
        timestamps = [(a.timestamp - recent[0].timestamp).total_seconds() for a in recent]
        
        # Calculate linear regression
        if len(risk_scores) >= 3:
            slope, intercept, r_value, p_value, std_err = stats.linregress(timestamps, risk_scores)
            
            trend = 'increasing' if slope > 0.01 else 'decreasing' if slope < -0.01 else 'stable'
            
            return {
                'trend': trend,
                'slope': slope,
                'r_squared': r_value ** 2,
                'p_value': p_value,
                'current_risk': risk_scores[-1],
                'average_risk': statistics.mean(risk_scores),
                'risk_volatility': statistics.stdev(risk_scores) if len(risk_scores) > 1 else 0
            }
        
        return {
            'trend': 'stable',
            'current_risk': risk_scores[-1],
            'average_risk': statistics.mean(risk_scores)
        }