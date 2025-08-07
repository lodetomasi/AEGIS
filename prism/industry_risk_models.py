"""Industry-specific risk calculation models for PRISM."""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np
from scipy import stats

from .context_weigher import Industry


@dataclass
class IndustryRiskModel:
    """Industry-specific risk calculation model."""
    
    industry: Industry
    risk_multipliers: Dict[str, float]
    cost_models: Dict[str, Any]
    regulatory_penalties: Dict[str, float]
    reputation_impact_factors: Dict[str, float]
    operational_thresholds: Dict[str, float]
    

class HealthcareRiskCalculator:
    """Healthcare-specific risk calculations."""
    
    def __init__(self):
        """Initialize healthcare risk calculator."""
        self.model = IndustryRiskModel(
            industry=Industry.HEALTHCARE,
            risk_multipliers={
                'patient_safety': 3.0,
                'privacy_violation': 2.5,
                'misdiagnosis': 2.8,
                'treatment_error': 3.0,
                'data_breach': 2.2
            },
            cost_models={
                'malpractice_claim_avg': 500000,  # $500K average
                'hipaa_violation_min': 100,
                'hipaa_violation_max': 50000000,  # $50M max
                'patient_harm_compensation': 250000,
                'regulatory_audit_cost': 100000
            },
            regulatory_penalties={
                'hipaa_breach_per_record': 1913,  # 2024 rate
                'false_claims_act_min': 13946,
                'false_claims_act_max': 27894,
                'stark_law_violation': 29873
            },
            reputation_impact_factors={
                'patient_trust_loss': 0.15,  # 15% patient loss
                'referral_reduction': 0.20,   # 20% referral reduction
                'staff_turnover_increase': 0.10  # 10% increase
            },
            operational_thresholds={
                'critical_safety_threshold': 0.001,  # 0.1% error rate
                'privacy_breach_threshold': 0.0001,  # 0.01% breach rate
                'diagnostic_accuracy_min': 0.95      # 95% accuracy required
            }
        )
    
    def calculate_financial_impact(
        self,
        error_type: str,
        error_rate: float,
        volume: int = 10000
    ) -> Dict[str, float]:
        """Calculate healthcare-specific financial impact."""
        impacts = {}
        
        if 'privacy' in error_type.lower() or 'data' in error_type.lower():
            # HIPAA violation calculation
            breach_probability = min(error_rate, 1.0)
            expected_records = volume * breach_probability * 0.1  # Assume 10% contain PHI
            
            impacts['hipaa_fines'] = expected_records * self.model.regulatory_penalties['hipaa_breach_per_record']
            impacts['breach_response_cost'] = expected_records * 200  # $200 per record for response
            impacts['litigation_risk'] = breach_probability * self.model.cost_models['malpractice_claim_avg'] * 0.3
            
        elif 'diagnosis' in error_type.lower() or 'treatment' in error_type.lower():
            # Medical malpractice calculation
            harm_probability = error_rate * 0.1  # 10% of errors cause harm
            claims_expected = volume * harm_probability * 0.05  # 5% result in claims
            
            impacts['malpractice_claims'] = claims_expected * self.model.cost_models['malpractice_claim_avg']
            impacts['defensive_medicine_cost'] = volume * error_rate * 500  # Extra tests/procedures
            impacts['insurance_premium_increase'] = impacts['malpractice_claims'] * 0.2
        
        elif 'billing' in error_type.lower() or 'coding' in error_type.lower():
            # False Claims Act calculation
            false_claim_rate = error_rate * 0.3  # 30% of errors are false claims
            false_claims = volume * false_claim_rate
            
            avg_penalty = (self.model.regulatory_penalties['false_claims_act_min'] + 
                          self.model.regulatory_penalties['false_claims_act_max']) / 2
            impacts['fca_penalties'] = false_claims * avg_penalty
            impacts['audit_costs'] = self.model.cost_models['regulatory_audit_cost']
        
        # Reputation impact (affects all error types)
        reputation_loss = self._calculate_reputation_impact(error_type, error_rate)
        impacts['revenue_loss_reputation'] = volume * 1000 * reputation_loss  # $1000 per patient avg
        
        impacts['total_financial_impact'] = sum(impacts.values())
        return impacts
    
    def _calculate_reputation_impact(self, error_type: str, error_rate: float) -> float:
        """Calculate reputation impact factor."""
        base_impact = 0.05  # 5% base impact
        
        if 'safety' in error_type.lower() or 'harm' in error_type.lower():
            base_impact *= 3.0  # Triple for safety issues
        elif 'privacy' in error_type.lower():
            base_impact *= 2.0  # Double for privacy issues
        
        # Scale by error rate
        return min(base_impact * (error_rate / 0.01), 0.5)  # Cap at 50% loss
    
    def calculate_regulatory_risk_score(self, error_rates: Dict[str, float]) -> float:
        """Calculate healthcare regulatory risk score (0-10)."""
        score = 0.0
        
        # Check against thresholds
        for error_type, rate in error_rates.items():
            if 'safety' in error_type.lower():
                if rate > self.model.operational_thresholds['critical_safety_threshold']:
                    score += 3.0 * (rate / self.model.operational_thresholds['critical_safety_threshold'])
            
            elif 'privacy' in error_type.lower():
                if rate > self.model.operational_thresholds['privacy_breach_threshold']:
                    score += 2.5 * (rate / self.model.operational_thresholds['privacy_breach_threshold'])
            
            elif 'diagnosis' in error_type.lower():
                accuracy = 1 - rate
                if accuracy < self.model.operational_thresholds['diagnostic_accuracy_min']:
                    score += 2.0 * (1 - accuracy / self.model.operational_thresholds['diagnostic_accuracy_min'])
        
        return min(score, 10.0)


class FinanceRiskCalculator:
    """Finance-specific risk calculations."""
    
    def __init__(self):
        """Initialize finance risk calculator."""
        self.model = IndustryRiskModel(
            industry=Industry.FINANCE,
            risk_multipliers={
                'transaction_error': 2.5,
                'fraud_detection_failure': 3.0,
                'compliance_violation': 2.8,
                'market_manipulation': 3.5,
                'insider_trading': 4.0
            },
            cost_models={
                'transaction_reversal': 150,
                'fraud_loss_avg': 5000,
                'sec_investigation': 5000000,
                'compliance_audit': 250000,
                'litigation_defense': 1000000
            },
            regulatory_penalties={
                'sec_violation_min': 100000,
                'sec_violation_max': 25000000,
                'finra_fine_avg': 500000,
                'aml_violation': 1000000,
                'sox_violation': 5000000
            },
            reputation_impact_factors={
                'client_attrition': 0.10,  # 10% client loss
                'aum_reduction': 0.15,     # 15% AUM reduction
                'trading_volume_decrease': 0.20  # 20% volume decrease
            },
            operational_thresholds={
                'transaction_error_rate_max': 0.0001,  # 0.01%
                'fraud_detection_rate_min': 0.95,      # 95% detection
                'compliance_accuracy_min': 0.99        # 99% compliance
            }
        )
    
    def calculate_financial_impact(
        self,
        error_type: str,
        error_rate: float,
        transaction_volume: float = 1000000000  # $1B default
    ) -> Dict[str, float]:
        """Calculate finance-specific financial impact."""
        impacts = {}
        
        if 'transaction' in error_type.lower():
            # Transaction error costs
            error_count = (transaction_volume / 1000) * error_rate  # Per $1000
            impacts['direct_losses'] = error_count * self.model.cost_models['transaction_reversal']
            impacts['reconciliation_costs'] = error_count * 50  # $50 per error to reconcile
            
        elif 'fraud' in error_type.lower():
            # Fraud detection failure
            undetected_fraud_rate = error_rate
            fraud_losses = transaction_volume * 0.001 * undetected_fraud_rate  # 0.1% fraud baseline
            impacts['fraud_losses'] = fraud_losses
            impacts['insurance_premium_increase'] = fraud_losses * 0.15
            impacts['additional_controls_cost'] = transaction_volume * 0.00001  # Basis points
            
        elif 'compliance' in error_type.lower() or 'regulatory' in error_type.lower():
            # Compliance violations
            violation_probability = error_rate * 0.1  # 10% of errors lead to violations
            impacts['regulatory_fines'] = violation_probability * self.model.regulatory_penalties['finra_fine_avg']
            impacts['legal_costs'] = violation_probability * self.model.cost_models['litigation_defense']
            impacts['compliance_remediation'] = self.model.cost_models['compliance_audit']
            
        elif 'market' in error_type.lower() or 'trading' in error_type.lower():
            # Market manipulation risk
            manipulation_risk = error_rate * 0.01  # 1% of errors could be manipulation
            impacts['sec_penalties'] = manipulation_risk * self.model.regulatory_penalties['sec_violation_max']
            impacts['trading_suspension_loss'] = transaction_volume * 0.001 * manipulation_risk * 30  # 30 days
        
        # Reputation and business impact
        reputation_factor = self._calculate_reputation_impact(error_type, error_rate)
        impacts['aum_loss'] = transaction_volume * reputation_factor * 0.1  # 10% of volume is AUM
        impacts['revenue_loss'] = impacts['aum_loss'] * 0.015  # 1.5% management fee
        
        impacts['total_financial_impact'] = sum(impacts.values())
        return impacts
    
    def _calculate_reputation_impact(self, error_type: str, error_rate: float) -> float:
        """Calculate reputation impact for financial services."""
        base_impact = 0.02  # 2% base
        
        multipliers = {
            'fraud': 3.0,
            'compliance': 2.5,
            'market': 4.0,
            'insider': 5.0,
            'transaction': 1.5
        }
        
        for keyword, multiplier in multipliers.items():
            if keyword in error_type.lower():
                base_impact *= multiplier
                break
        
        return min(base_impact * (error_rate / 0.001), 0.3)  # Cap at 30%
    
    def calculate_basel_risk_score(self, error_rates: Dict[str, float]) -> Dict[str, float]:
        """Calculate Basel III operational risk scores."""
        scores = {
            'operational_risk_capital': 0.0,
            'risk_weighted_assets': 0.0,
            'tier1_impact': 0.0
        }
        
        # Simplified Basel calculation
        for error_type, rate in error_rates.items():
            if rate > self.model.operational_thresholds.get(f'{error_type}_max', 0.001):
                impact = rate / 0.001  # Normalize to basis points
                scores['operational_risk_capital'] += impact * 0.15  # 15% capital charge
                scores['risk_weighted_assets'] += impact * 1.0
                scores['tier1_impact'] += impact * 0.08  # 8% Tier 1 requirement
        
        return scores


class LegalRiskCalculator:
    """Legal industry-specific risk calculations."""
    
    def __init__(self):
        """Initialize legal risk calculator."""
        self.model = IndustryRiskModel(
            industry=Industry.LEGAL,
            risk_multipliers={
                'malpractice': 3.5,
                'confidentiality_breach': 3.0,
                'conflict_of_interest': 2.8,
                'missed_deadline': 2.5,
                'incorrect_advice': 3.2
            },
            cost_models={
                'malpractice_claim_avg': 250000,
                'malpractice_defense': 100000,
                'client_settlement': 150000,
                'bar_investigation': 50000,
                'reputation_recovery': 200000
            },
            regulatory_penalties={
                'bar_discipline_fine': 25000,
                'suspension_revenue_loss_daily': 5000,
                'disbarment_lifetime_loss': 5000000
            },
            reputation_impact_factors={
                'client_loss': 0.25,  # 25% client loss
                'referral_loss': 0.30,  # 30% referral loss
                'rate_reduction': 0.15  # 15% rate reduction
            },
            operational_thresholds={
                'error_rate_max': 0.001,  # 0.1% error rate
                'deadline_miss_rate_max': 0.0001,  # 0.01%
                'confidentiality_breach_max': 0.00001  # 0.001%
            }
        )
    
    def calculate_malpractice_exposure(
        self,
        error_type: str,
        error_rate: float,
        case_volume: int = 1000,
        avg_case_value: float = 500000
    ) -> Dict[str, float]:
        """Calculate legal malpractice exposure."""
        exposure = {}
        
        if 'advice' in error_type.lower() or 'counsel' in error_type.lower():
            # Incorrect legal advice
            claim_probability = error_rate * 0.2  # 20% of errors lead to claims
            exposure['direct_claims'] = case_volume * claim_probability * self.model.cost_models['malpractice_claim_avg']
            exposure['defense_costs'] = case_volume * claim_probability * self.model.cost_models['malpractice_defense']
            
        elif 'deadline' in error_type.lower() or 'filing' in error_type.lower():
            # Missed deadlines
            miss_rate = error_rate
            cases_affected = case_volume * miss_rate
            exposure['client_damages'] = cases_affected * avg_case_value * 0.5  # 50% of case value
            exposure['malpractice_claims'] = cases_affected * 0.8 * self.model.cost_models['client_settlement']
            
        elif 'confidential' in error_type.lower() or 'privilege' in error_type.lower():
            # Confidentiality breaches
            breach_incidents = case_volume * error_rate
            exposure['client_settlements'] = breach_incidents * self.model.cost_models['client_settlement'] * 2
            exposure['bar_penalties'] = breach_incidents * self.model.regulatory_penalties['bar_discipline_fine']
            exposure['reputation_damage'] = self.model.cost_models['reputation_recovery']
        
        # Professional liability insurance impact
        total_exposure = sum(exposure.values())
        exposure['insurance_premium_increase'] = total_exposure * 0.1  # 10% of exposure
        
        exposure['total_malpractice_exposure'] = sum(exposure.values())
        return exposure
    
    def calculate_ethical_risk_score(self, error_rates: Dict[str, float]) -> float:
        """Calculate legal ethics risk score."""
        score = 0.0
        
        ethics_weights = {
            'confidentiality': 3.0,
            'conflict': 2.5,
            'competence': 2.0,
            'diligence': 1.5,
            'communication': 1.0
        }
        
        for error_type, rate in error_rates.items():
            for ethics_area, weight in ethics_weights.items():
                if ethics_area in error_type.lower():
                    threshold = self.model.operational_thresholds.get(
                        f'{ethics_area}_breach_max', 0.001
                    )
                    if rate > threshold:
                        score += weight * (rate / threshold)
        
        return min(score, 10.0)


class RetailRiskCalculator:
    """Retail industry-specific risk calculations."""
    
    def __init__(self):
        """Initialize retail risk calculator."""
        self.model = IndustryRiskModel(
            industry=Industry.RETAIL,
            risk_multipliers={
                'inventory_error': 1.5,
                'pricing_error': 2.0,
                'customer_data_breach': 2.5,
                'supply_chain_disruption': 2.2,
                'fraud_detection': 1.8
            },
            cost_models={
                'inventory_shrinkage_rate': 0.015,  # 1.5% industry avg
                'price_match_cost': 50,
                'data_breach_per_record': 150,
                'customer_acquisition': 200,
                'fraud_chargeback': 100
            },
            regulatory_penalties={
                'pci_violation': 100000,
                'gdpr_violation_max': 20000000,
                'ftc_fine_avg': 500000,
                'ada_violation': 75000
            },
            reputation_impact_factors={
                'customer_churn': 0.15,  # 15% churn
                'brand_damage': 0.10,     # 10% brand value loss
                'social_media_impact': 0.20  # 20% negative impact
            },
            operational_thresholds={
                'inventory_accuracy_min': 0.98,  # 98% accuracy
                'pricing_error_rate_max': 0.001,  # 0.1%
                'fraud_rate_max': 0.01,  # 1%
                'stockout_rate_max': 0.05  # 5%
            }
        )
    
    def calculate_operational_impact(
        self,
        error_type: str,
        error_rate: float,
        annual_revenue: float = 10000000,  # $10M default
        transaction_count: int = 100000
    ) -> Dict[str, float]:
        """Calculate retail operational impact."""
        impacts = {}
        
        if 'inventory' in error_type.lower():
            # Inventory management errors
            shrinkage_increase = error_rate * 0.5  # 50% of errors cause shrinkage
            impacts['additional_shrinkage'] = annual_revenue * shrinkage_increase
            impacts['stockout_losses'] = annual_revenue * error_rate * 0.03  # 3% lost sales
            impacts['markdown_costs'] = annual_revenue * error_rate * 0.02  # 2% markdowns
            
        elif 'pricing' in error_type.lower():
            # Pricing errors
            pricing_errors = transaction_count * error_rate
            impacts['direct_losses'] = pricing_errors * self.model.cost_models['price_match_cost']
            impacts['margin_erosion'] = annual_revenue * error_rate * 0.01  # 1% margin impact
            
        elif 'customer' in error_type.lower() and 'data' in error_type.lower():
            # Customer data issues
            records_at_risk = transaction_count * error_rate * 0.3  # 30% have PII
            impacts['breach_costs'] = records_at_risk * self.model.cost_models['data_breach_per_record']
            impacts['gdpr_risk'] = error_rate * 0.01 * self.model.regulatory_penalties['gdpr_violation_max']
            impacts['customer_loss'] = records_at_risk * self.model.cost_models['customer_acquisition']
        
        # Brand and reputation impact
        reputation_loss = self._calculate_reputation_impact(error_type, error_rate)
        impacts['revenue_loss_reputation'] = annual_revenue * reputation_loss
        
        impacts['total_operational_impact'] = sum(impacts.values())
        return impacts
    
    def _calculate_reputation_impact(self, error_type: str, error_rate: float) -> float:
        """Calculate retail reputation impact."""
        base_impact = 0.01  # 1% base
        
        if 'data' in error_type.lower() or 'privacy' in error_type.lower():
            base_impact *= 3.0
        elif 'customer' in error_type.lower():
            base_impact *= 2.0
        elif 'fraud' in error_type.lower():
            base_impact *= 1.5
        
        # Social media amplification factor
        social_multiplier = 1 + (error_rate * 10)  # Up to 2x for high error rates
        
        return min(base_impact * social_multiplier, 0.2)  # Cap at 20%


class IndustryRiskModelFactory:
    """Factory for creating industry-specific risk calculators."""
    
    _calculators = {
        Industry.HEALTHCARE: HealthcareRiskCalculator,
        Industry.FINANCE: FinanceRiskCalculator,
        Industry.LEGAL: LegalRiskCalculator,
        Industry.RETAIL: RetailRiskCalculator
    }
    
    @classmethod
    def create_calculator(cls, industry: Industry):
        """Create appropriate risk calculator for industry."""
        calculator_class = cls._calculators.get(industry)
        if calculator_class:
            return calculator_class()
        
        # Return generic calculator for unsupported industries
        return GenericRiskCalculator(industry)


class GenericRiskCalculator:
    """Generic risk calculator for industries without specific models."""
    
    def __init__(self, industry: Industry):
        """Initialize generic calculator."""
        self.industry = industry
        self.base_multiplier = 1.0
    
    def calculate_financial_impact(
        self,
        error_type: str,
        error_rate: float,
        volume: float = 1000000
    ) -> Dict[str, float]:
        """Generic financial impact calculation."""
        base_impact = volume * error_rate * 0.01  # 1% of volume
        
        return {
            'estimated_losses': base_impact,
            'mitigation_costs': base_impact * 0.2,
            'total_financial_impact': base_impact * 1.2
        }