"""Main risk translation orchestrator for PRISM module."""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path

from .risk_mapper import RiskMapper, ErrorType
from .context_weigher import ContextWeigher, Industry, Sensitivity
from .risk_calculator import RiskCalculator, RiskAssessment
from .industry_risk_models import IndustryRiskModelFactory
# Removed logger dependency for integration testing


@dataclass
class RiskTranslationInput:
    """Input data for risk translation."""
    
    # Error analysis
    errors: List[str]  # Error descriptions
    error_rates: Dict[str, float]  # Error type -> probability
    
    # Context information
    industry: str
    sensitivity_level: str
    use_case_description: str
    
    # Test results (optional)
    test_results: Optional[List[Dict[str, Any]]] = None
    
    # Additional context
    metadata: Dict[str, Any] = None


@dataclass
class RiskTranslationOutput:
    """Output from risk translation."""
    
    # Risk assessment
    risk_assessment: RiskAssessment
    
    # Business impact summary
    business_impacts: Dict[str, Any]
    
    # Regulatory concerns
    regulatory_requirements: List[str]
    compliance_risks: List[str]
    
    # Executive summary
    executive_summary: str
    risk_narrative: str
    
    # Visualizations data
    risk_matrix: Dict[str, Any]
    risk_breakdown_chart: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'risk_assessment': self.risk_assessment.to_dict(),
            'business_impacts': self.business_impacts,
            'regulatory_requirements': self.regulatory_requirements,
            'compliance_risks': self.compliance_risks,
            'executive_summary': self.executive_summary,
            'risk_narrative': self.risk_narrative,
            'risk_matrix': self.risk_matrix,
            'risk_breakdown_chart': self.risk_breakdown_chart
        }


class RiskTranslator:
    """Translates technical metrics to business risk assessments."""
    
    def __init__(
        self,
        risk_mappings_file: Optional[str] = None,
        context_config_file: Optional[str] = None
    ):
        """
        Initialize risk translator.
        
        Args:
            risk_mappings_file: Custom risk mappings file
            context_config_file: Custom context weights file
        """
        self.risk_mapper = RiskMapper(risk_mappings_file)
        self.context_weigher = ContextWeigher(context_config_file)
        self.risk_calculator = RiskCalculator()
        self.industry_calculators = {}
    
    def translate(self, input_data: RiskTranslationInput) -> RiskTranslationOutput:
        """
        Translate technical metrics to business risk assessment.
        
        Args:
            input_data: Risk translation input data
            
        Returns:
            Complete risk translation output
        """
        # Translating risks for {input_data.industry} context
        
        # Parse context
        industry = self._parse_industry(input_data.industry)
        sensitivity = self._parse_sensitivity(input_data.sensitivity_level)
        
        # Analyze errors
        error_analysis = self._analyze_errors(input_data.errors)
        
        # Calculate error probabilities
        error_probabilities = self._calculate_error_probabilities(
            error_analysis, input_data.error_rates
        )
        
        # Get impact scores
        impact_scores = self._get_impact_scores(error_analysis)
        
        # Get context weights
        context_weights = self._get_context_weights(
            error_analysis, industry, sensitivity
        )
        
        # Calculate risk assessment
        risk_assessment = self.risk_calculator.calculate_risk(
            error_probabilities,
            impact_scores,
            context_weights,
            input_data.test_results
        )
        
        # Generate business impacts
        business_impacts = self._generate_business_impacts(
            risk_assessment, error_analysis, industry
        )
        
        # Get regulatory requirements
        regulatory_requirements = self.context_weigher.get_regulatory_requirements(industry)
        compliance_risks = self._identify_compliance_risks(
            error_analysis, regulatory_requirements
        )
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(
            risk_assessment, business_impacts, industry
        )
        
        # Generate risk narrative
        risk_narrative = self._generate_risk_narrative(
            risk_assessment, business_impacts, compliance_risks
        )
        
        # Create visualization data
        risk_matrix = self._create_risk_matrix(risk_assessment)
        risk_breakdown_chart = self._create_risk_breakdown_chart(risk_assessment)
        
        return RiskTranslationOutput(
            risk_assessment=risk_assessment,
            business_impacts=business_impacts,
            regulatory_requirements=regulatory_requirements,
            compliance_risks=compliance_risks,
            executive_summary=executive_summary,
            risk_narrative=risk_narrative,
            risk_matrix=risk_matrix,
            risk_breakdown_chart=risk_breakdown_chart
        )
    
    def _parse_industry(self, industry_str: str) -> Industry:
        """Parse industry from string."""
        try:
            return Industry(industry_str.lower())
        except ValueError:
            # Try to infer from description
            return self.context_weigher.analyze_context(industry_str)
    
    def _parse_sensitivity(self, sensitivity_str: str) -> Sensitivity:
        """Parse sensitivity level from string."""
        try:
            return Sensitivity(sensitivity_str.lower())
        except ValueError:
            # Default to internal
            return Sensitivity.INTERNAL
    
    def _analyze_errors(self, errors: List[str]) -> Dict[ErrorType, List[str]]:
        """Analyze and categorize errors."""
        error_analysis = {}
        
        for error in errors:
            error_type = self.risk_mapper.analyze_error(error)
            if error_type not in error_analysis:
                error_analysis[error_type] = []
            error_analysis[error_type].append(error)
        
        return error_analysis
    
    def _calculate_error_probabilities(
        self,
        error_analysis: Dict[ErrorType, List[str]],
        error_rates: Dict[str, float]
    ) -> Dict[str, float]:
        """Calculate error probabilities."""
        probabilities = {}
        
        for error_type, errors in error_analysis.items():
            # Use provided rate if available
            if error_type.value in error_rates:
                probabilities[error_type.value] = error_rates[error_type.value]
            else:
                # Estimate based on error count
                probabilities[error_type.value] = len(errors) / 100.0  # Rough estimate
        
        return probabilities
    
    def _get_impact_scores(self, error_analysis: Dict[ErrorType, List[str]]) -> Dict[str, float]:
        """Get impact scores for error types."""
        impact_scores = {}
        
        for error_type in error_analysis:
            severity = self.risk_mapper.get_severity(error_type)
            impact_scores[error_type.value] = severity
        
        return impact_scores
    
    def _get_context_weights(
        self,
        error_analysis: Dict[ErrorType, List[str]],
        industry: Industry,
        sensitivity: Sensitivity
    ) -> Dict[str, float]:
        """Get context weights for errors."""
        weights = {}
        
        for error_type in error_analysis:
            weight = self.context_weigher.get_weight(
                industry, sensitivity, error_type.value
            )
            weights[error_type.value] = weight
        
        return weights
    
    def _generate_business_impacts(
        self,
        risk_assessment: RiskAssessment,
        error_analysis: Dict[ErrorType, List[str]],
        industry: Industry
    ) -> Dict[str, Any]:
        """Generate business impact analysis with industry-specific calculations."""
        # Get or create industry calculator
        if industry not in self.industry_calculators:
            self.industry_calculators[industry] = IndustryRiskModelFactory.create_calculator(industry)
        
        industry_calc = self.industry_calculators[industry]
        
        impacts = {
            'financial': {
                'potential_loss': self._estimate_financial_impact(risk_assessment),
                'risk_factors': [],
                'industry_specific': {}
            },
            'reputation': {
                'impact_level': self._assess_reputation_impact(risk_assessment),
                'risk_factors': []
            },
            'operational': {
                'disruption_risk': self._assess_operational_impact(risk_assessment),
                'risk_factors': []
            },
            'compliance': {
                'violation_risk': self._assess_compliance_impact(risk_assessment, industry),
                'risk_factors': []
            }
        }
        
        # Add industry-specific financial calculations
        total_industry_impact = 0
        for error_type, errors in error_analysis.items():
            error_rate = risk_assessment.risk_by_error_type.get(error_type.value, 0.0) / 10.0  # Convert from risk score to rate
            
            # Use appropriate calculator method based on industry
            if hasattr(industry_calc, 'calculate_financial_impact'):
                industry_impact = industry_calc.calculate_financial_impact(
                    error_type.value,
                    error_rate
                )
                impacts['financial']['industry_specific'][error_type.value] = industry_impact
                total_industry_impact += industry_impact.get('total_financial_impact', 0)
            
            # Healthcare-specific calculations
            if industry == Industry.HEALTHCARE and hasattr(industry_calc, 'calculate_regulatory_risk_score'):
                regulatory_score = industry_calc.calculate_regulatory_risk_score(
                    {error_type.value: error_rate}
                )
                impacts['compliance']['healthcare_regulatory_score'] = regulatory_score
            
            # Finance-specific calculations
            elif industry == Industry.FINANCE and hasattr(industry_calc, 'calculate_basel_risk_score'):
                basel_scores = industry_calc.calculate_basel_risk_score(
                    {error_type.value: error_rate}
                )
                impacts['compliance']['basel_risk_scores'] = basel_scores
            
            # Legal-specific calculations
            elif industry == Industry.LEGAL:
                if hasattr(industry_calc, 'calculate_malpractice_exposure'):
                    malpractice = industry_calc.calculate_malpractice_exposure(
                        error_type.value,
                        error_rate
                    )
                    impacts['financial']['malpractice_exposure'] = malpractice
                
                if hasattr(industry_calc, 'calculate_ethical_risk_score'):
                    ethical_score = industry_calc.calculate_ethical_risk_score(
                        {error_type.value: error_rate}
                    )
                    impacts['compliance']['ethical_risk_score'] = ethical_score
        
        # Update total financial impact with industry-specific calculations
        if total_industry_impact > 0:
            impacts['financial']['industry_adjusted_loss'] = f"${total_industry_impact:,.0f}"
        
        # Add specific risk factors
        for error_type in error_analysis:
            mappings = self.risk_mapper.get_impacts(error_type)
            for mapping in mappings:
                impact_type = mapping.impact_type.value
                
                if 'financial' in impact_type:
                    impacts['financial']['risk_factors'].append(mapping.description)
                elif 'reputation' in impact_type:
                    impacts['reputation']['risk_factors'].append(mapping.description)
                elif 'operational' in impact_type or 'service' in impact_type:
                    impacts['operational']['risk_factors'].append(mapping.description)
                elif 'compliance' in impact_type or 'legal' in impact_type:
                    impacts['compliance']['risk_factors'].append(mapping.description)
        
        return impacts
    
    def _estimate_financial_impact(self, risk_assessment: RiskAssessment) -> str:
        """Estimate financial impact based on risk score."""
        if risk_assessment.risk_score >= 8:
            return "Very High (>$10M potential loss)"
        elif risk_assessment.risk_score >= 6:
            return "High ($1M-$10M potential loss)"
        elif risk_assessment.risk_score >= 4:
            return "Medium ($100K-$1M potential loss)"
        elif risk_assessment.risk_score >= 2:
            return "Low ($10K-$100K potential loss)"
        else:
            return "Minimal (<$10K potential loss)"
    
    def _assess_reputation_impact(self, risk_assessment: RiskAssessment) -> str:
        """Assess reputation impact."""
        if risk_assessment.risk_score >= 8:
            return "Critical (potential for viral negative coverage)"
        elif risk_assessment.risk_score >= 6:
            return "High (likely negative media coverage)"
        elif risk_assessment.risk_score >= 4:
            return "Medium (possible customer complaints)"
        elif risk_assessment.risk_score >= 2:
            return "Low (minor user dissatisfaction)"
        else:
            return "Minimal (negligible impact)"
    
    def _assess_operational_impact(self, risk_assessment: RiskAssessment) -> str:
        """Assess operational impact."""
        if risk_assessment.risk_score >= 8:
            return "Critical (complete service disruption)"
        elif risk_assessment.risk_score >= 6:
            return "High (major feature unavailability)"
        elif risk_assessment.risk_score >= 4:
            return "Medium (performance degradation)"
        elif risk_assessment.risk_score >= 2:
            return "Low (minor inconvenience)"
        else:
            return "Minimal (no noticeable impact)"
    
    def _assess_compliance_impact(self, risk_assessment: RiskAssessment, industry: Industry) -> str:
        """Assess compliance impact."""
        # Industry-specific compliance sensitivity
        high_compliance_industries = [
            Industry.HEALTHCARE, Industry.FINANCE, Industry.LEGAL, Industry.GOVERNMENT
        ]
        
        multiplier = 1.5 if industry in high_compliance_industries else 1.0
        adjusted_score = risk_assessment.risk_score * multiplier
        
        if adjusted_score >= 8:
            return "Critical (likely regulatory action)"
        elif adjusted_score >= 6:
            return "High (potential fines and audits)"
        elif adjusted_score >= 4:
            return "Medium (compliance warnings likely)"
        elif adjusted_score >= 2:
            return "Low (minor compliance issues)"
        else:
            return "Minimal (within compliance bounds)"
    
    def _identify_compliance_risks(
        self,
        error_analysis: Dict[ErrorType, List[str]],
        regulatory_requirements: List[str]
    ) -> List[str]:
        """Identify specific compliance risks."""
        compliance_risks = []
        
        # Map error types to compliance concerns
        compliance_mapping = {
            ErrorType.DATA_LEAK: ["GDPR violation", "HIPAA breach", "Data protection violation"],
            ErrorType.PRIVACY_VIOLATION: ["Privacy law violation", "Consumer protection violation"],
            ErrorType.BIAS_AMPLIFICATION: ["Fair lending violation", "Equal opportunity violation"],
            ErrorType.SECURITY_BYPASS: ["Security compliance failure", "SOC 2 violation"]
        }
        
        for error_type in error_analysis:
            if error_type in compliance_mapping:
                for risk in compliance_mapping[error_type]:
                    # Check if risk is relevant to regulatory requirements
                    if any(req in risk for req in regulatory_requirements):
                        compliance_risks.append(risk)
        
        return list(set(compliance_risks))  # Remove duplicates
    
    def _generate_executive_summary(
        self,
        risk_assessment: RiskAssessment,
        business_impacts: Dict[str, Any],
        industry: Industry
    ) -> str:
        """Generate executive summary with industry-specific insights."""
        risk_level = risk_assessment.get_risk_level()
        
        summary = f"AI Agent Risk Assessment Summary\n\n"
        summary += f"Overall Risk Level: {risk_level} ({risk_assessment.risk_score:.1f}/10)\n"
        summary += f"Industry Context: {industry.value.title()}\n\n"
        
        summary += "Key Findings:\n"
        summary += f"• Probability of Error: {risk_assessment.probability:.1%}\n"
        summary += f"• Impact Severity: {risk_assessment.impact:.1f}/10\n"
        summary += f"• Financial Risk: {business_impacts['financial']['potential_loss']}\n"
        
        # Add industry-specific financial impact if available
        if 'industry_adjusted_loss' in business_impacts['financial']:
            summary += f"• Industry-Specific Impact: {business_impacts['financial']['industry_adjusted_loss']}\n"
        
        summary += f"• Reputation Risk: {business_impacts['reputation']['impact_level']}\n"
        
        # Add industry-specific compliance insights
        if industry == Industry.HEALTHCARE and 'healthcare_regulatory_score' in business_impacts['compliance']:
            summary += f"• Healthcare Regulatory Risk Score: {business_impacts['compliance']['healthcare_regulatory_score']:.1f}/10\n"
        elif industry == Industry.FINANCE and 'basel_risk_scores' in business_impacts['compliance']:
            basel = business_impacts['compliance']['basel_risk_scores']
            summary += f"• Basel III Capital Impact: {basel.get('operational_risk_capital', 0):.1%}\n"
        elif industry == Industry.LEGAL and 'ethical_risk_score' in business_impacts['compliance']:
            summary += f"• Legal Ethics Risk Score: {business_impacts['compliance']['ethical_risk_score']:.1f}/10\n"
        
        if risk_assessment.top_risk_factors:
            summary += "\nTop Risk Factors:\n"
            for i, factor in enumerate(risk_assessment.top_risk_factors[:3], 1):
                summary += f"{i}. {factor['error_type']} (Risk: {factor['risk_score']:.1f})\n"
        
        # Add industry-specific warnings
        if industry == Industry.HEALTHCARE and risk_level in ["CRITICAL", "HIGH"]:
            summary += "\n⚠️ WARNING: Patient safety and HIPAA compliance at risk\n"
        elif industry == Industry.FINANCE and risk_level in ["CRITICAL", "HIGH"]:
            summary += "\n⚠️ WARNING: Regulatory violations may trigger SEC/FINRA investigations\n"
        elif industry == Industry.LEGAL and risk_level in ["CRITICAL", "HIGH"]:
            summary += "\n⚠️ WARNING: Malpractice exposure exceeds professional liability coverage\n"
        
        return summary
    
    def _generate_risk_narrative(
        self,
        risk_assessment: RiskAssessment,
        business_impacts: Dict[str, Any],
        compliance_risks: List[str]
    ) -> str:
        """Generate detailed risk narrative."""
        narrative = "Risk Analysis Narrative\n\n"
        
        # Overall assessment
        risk_level = risk_assessment.get_risk_level()
        if risk_level in ["CRITICAL", "HIGH"]:
            narrative += f"This AI agent presents {risk_level} risk that requires immediate attention. "
            narrative += "The combination of high error probability and severe potential impacts "
            narrative += "creates an unacceptable risk profile for production deployment.\n\n"
        elif risk_level == "MEDIUM":
            narrative += "This AI agent presents moderate risk that should be carefully managed. "
            narrative += "While not immediately critical, the identified risks require "
            narrative += "mitigation strategies before widespread deployment.\n\n"
        else:
            narrative += "This AI agent presents acceptable risk levels with proper monitoring. "
            narrative += "The identified risks are manageable with standard controls.\n\n"
        
        # Specific concerns
        if business_impacts['financial']['risk_factors']:
            narrative += "Financial Risks:\n"
            for factor in business_impacts['financial']['risk_factors'][:3]:
                narrative += f"• {factor}\n"
            narrative += "\n"
        
        if compliance_risks:
            narrative += "Compliance Concerns:\n"
            for risk in compliance_risks[:3]:
                narrative += f"• {risk}\n"
            narrative += "\n"
        
        # Recommendations
        if risk_assessment.mitigation_recommendations:
            narrative += "Priority Recommendations:\n"
            for i, rec in enumerate(risk_assessment.mitigation_recommendations[:5], 1):
                narrative += f"{i}. {rec}\n"
        
        return narrative
    
    def _create_risk_matrix(self, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Create risk matrix visualization data."""
        matrix = {
            'axes': {
                'x': {'label': 'Probability', 'range': [0, 1]},
                'y': {'label': 'Impact', 'range': [0, 10]}
            },
            'risks': []
        }
        
        for factor in risk_assessment.top_risk_factors:
            matrix['risks'].append({
                'name': factor['error_type'],
                'x': factor['probability'],
                'y': factor['impact'],
                'size': factor['risk_score'],
                'color': self._risk_color(factor['risk_score'])
            })
        
        return matrix
    
    def _create_risk_breakdown_chart(self, risk_assessment: RiskAssessment) -> Dict[str, Any]:
        """Create risk breakdown chart data."""
        return {
            'type': 'bar',
            'data': {
                'categories': list(risk_assessment.risk_by_category.keys()),
                'values': list(risk_assessment.risk_by_category.values())
            },
            'colors': [self._risk_color(v) for v in risk_assessment.risk_by_category.values()]
        }
    
    def _risk_color(self, risk_score: float) -> str:
        """Get color for risk score."""
        if risk_score >= 8:
            return '#d32f2f'  # Red
        elif risk_score >= 6:
            return '#f57c00'  # Orange
        elif risk_score >= 4:
            return '#fbc02d'  # Yellow
        elif risk_score >= 2:
            return '#388e3c'  # Green
        else:
            return '#1976d2'  # Blue