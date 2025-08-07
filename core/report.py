"""Report generation for AETHER evaluation results."""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Report:
    """Evaluation report container."""
    
    evaluation_id: str
    agent_name: str
    evaluation_date: datetime
    
    # Module results
    sentinel_results: Optional[Dict[str, Any]] = None
    aegis_results: Optional[Dict[str, Any]] = None
    delta_results: Optional[Dict[str, Any]] = None
    prism_results: Optional[Dict[str, Any]] = None
    
    # Overall assessment
    overall_score: float = 0.0
    overall_risk: float = 0.0
    recommendation: str = ""
    confidence: float = 0.0
    
    # Summary
    executive_summary: str = ""
    key_findings: List[str] = None
    critical_issues: List[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.key_findings is None:
            self.key_findings = []
        if self.critical_issues is None:
            self.critical_issues = []
        if self.metadata is None:
            self.metadata = {}


class ReportGenerator:
    """Generates comprehensive evaluation reports."""
    
    def __init__(self, output_dir: str = "./reports"):
        """
        Initialize report generator.
        
        Args:
            output_dir: Directory to save reports
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, report: Report) -> str:
        """
        Generate comprehensive evaluation report.
        
        Args:
            report: Report data
            
        Returns:
            Path to generated report
        """
        # Generate markdown report
        markdown_content = self._generate_markdown(report)
        
        # Save markdown
        report_name = f"{report.evaluation_id}_report.md"
        report_path = self.output_dir / report_name
        
        with open(report_path, 'w') as f:
            f.write(markdown_content)
        
        # Also save JSON version
        json_path = self.output_dir / f"{report.evaluation_id}_report.json"
        self._save_json_report(report, json_path)
        
        return str(report_path)
    
    def _generate_markdown(self, report: Report) -> str:
        """Generate markdown report."""
        md = []
        
        # Header
        md.append(f"# AETHER Evaluation Report: {report.agent_name}")
        md.append(f"\n**Date:** {report.evaluation_date.strftime('%Y-%m-%d %H:%M:%S')}")
        md.append(f"**Evaluation ID:** {report.evaluation_id}")
        md.append("")
        
        # Executive Summary
        md.append("## Executive Summary")
        md.append("")
        if report.executive_summary:
            md.append(report.executive_summary)
        else:
            md.append(self._generate_executive_summary(report))
        md.append("")
        
        # Overall Assessment
        md.append("## Overall Assessment")
        md.append("")
        md.append(f"- **Overall Score:** {report.overall_score:.1f}/100")
        md.append(f"- **Risk Level:** {self._score_to_risk_level(report.overall_risk)}")
        md.append(f"- **Recommendation:** {report.recommendation}")
        md.append(f"- **Confidence:** {report.confidence:.0%}")
        md.append("")
        
        # Key Findings
        if report.key_findings:
            md.append("## Key Findings")
            md.append("")
            for finding in report.key_findings:
                md.append(f"- {finding}")
            md.append("")
        
        # Critical Issues
        if report.critical_issues:
            md.append("## ⚠️ Critical Issues")
            md.append("")
            for issue in report.critical_issues:
                md.append(f"- **{issue}**")
            md.append("")
        
        # SENTINEL Results
        if report.sentinel_results:
            md.extend(self._generate_sentinel_section(report.sentinel_results))
        
        # AEGIS Results
        if report.aegis_results:
            md.extend(self._generate_aegis_section(report.aegis_results))
        
        # DELTA Results
        if report.delta_results:
            md.extend(self._generate_delta_section(report.delta_results))
        
        # PRISM Results
        if report.prism_results:
            md.extend(self._generate_prism_section(report.prism_results))
        
        # Recommendations
        md.append("## Recommendations")
        md.append("")
        md.extend(self._generate_recommendations(report))
        md.append("")
        
        # Technical Details
        md.append("## Technical Details")
        md.append("")
        md.append("<details>")
        md.append("<summary>Click to expand technical details</summary>")
        md.append("")
        md.append("```json")
        md.append(json.dumps({
            'evaluation_id': report.evaluation_id,
            'metadata': report.metadata,
            'module_summaries': {
                'sentinel': self._get_module_summary(report.sentinel_results),
                'aegis': self._get_module_summary(report.aegis_results),
                'delta': self._get_module_summary(report.delta_results),
                'prism': self._get_module_summary(report.prism_results)
            }
        }, indent=2))
        md.append("```")
        md.append("</details>")
        
        return "\n".join(md)
    
    def _generate_executive_summary(self, report: Report) -> str:
        """Generate executive summary if not provided."""
        risk_level = self._score_to_risk_level(report.overall_risk)
        
        summary = f"The AI agent '{report.agent_name}' has been evaluated using the AETHER framework. "
        
        if report.overall_score >= 80:
            summary += f"The agent demonstrates strong performance with an overall score of {report.overall_score:.0f}/100. "
        elif report.overall_score >= 60:
            summary += f"The agent shows acceptable performance with an overall score of {report.overall_score:.0f}/100. "
        else:
            summary += f"The agent exhibits concerning performance with an overall score of {report.overall_score:.0f}/100. "
        
        summary += f"The risk assessment indicates {risk_level} risk. "
        
        if report.critical_issues:
            summary += f"Critical issues requiring immediate attention were identified. "
        
        summary += f"The evaluation confidence is {report.confidence:.0%}."
        
        return summary
    
    def _generate_sentinel_section(self, results: Dict[str, Any]) -> List[str]:
        """Generate SENTINEL results section."""
        md = []
        md.append("## SENTINEL - Static Analysis Results")
        md.append("")
        
        # Architecture summary
        md.append("### Architecture Analysis")
        md.append(f"- **Architecture Type:** {results.get('architecture_type', 'Unknown')}")
        md.append(f"- **Risk Score:** {results.get('overall_risk_score', 0):.1f}/10")
        md.append(f"- **Risk Level:** {results.get('risk_level', 'Unknown')}")
        md.append("")
        
        # Risk patterns
        if 'risk_summary' in results:
            summary = results['risk_summary']
            md.append("### Risk Patterns Detected")
            md.append(f"- **Total Patterns:** {summary.get('total_patterns', 0)}")
            
            if 'by_severity' in summary:
                md.append("- **By Severity:**")
                for severity, count in summary['by_severity'].items():
                    if count > 0:
                        md.append(f"  - {severity.capitalize()}: {count}")
            md.append("")
        
        # Vulnerabilities
        if 'vulnerability_summary' in results:
            vuln_summary = results['vulnerability_summary']
            md.append("### Vulnerabilities")
            md.append(f"- **Total Vulnerabilities:** {vuln_summary.get('total_vulnerabilities', 0)}")
            
            if vuln_summary.get('total_vulnerabilities', 0) > 0:
                md.append(f"- **Average CVSS Score:** {vuln_summary.get('average_score', 0):.1f}")
                if 'by_severity' in vuln_summary:
                    for severity, count in vuln_summary['by_severity'].items():
                        if count > 0:
                            md.append(f"  - {severity.capitalize()}: {count}")
            md.append("")
        
        # Immediate actions
        if 'immediate_actions' in results:
            md.append("### Immediate Actions Required")
            for action in results['immediate_actions'][:5]:  # Top 5
                md.append(f"- {action}")
            md.append("")
        
        return md
    
    def _generate_aegis_section(self, results: Dict[str, Any]) -> List[str]:
        """Generate AEGIS results section."""
        md = []
        md.append("## AEGIS - Dynamic Testing Results")
        md.append("")
        
        # Test summary
        if 'aggregate_metrics' in results:
            metrics = results['aggregate_metrics']
            md.append("### Test Execution Summary")
            md.append(f"- **Total Tests:** {metrics.get('total_runs', 0)}")
            md.append(f"- **Success Rate:** {metrics.get('avg_success_rate', 0):.1%}")
            md.append(f"- **Consistency Score:** {metrics.get('avg_consistency', 0):.2f}")
            md.append(f"- **Performance Degradation:** {metrics.get('avg_degradation', 0):.1%}")
            md.append("")
        
        # Reliability metrics
        if 'reliability_metrics' in results:
            md.append("### Reliability Analysis")
            
            # Find most reliable and least reliable tasks
            task_scores = []
            for task_id, metrics in results['reliability_metrics'].items():
                if isinstance(metrics, dict) and 'success_rate' in metrics:
                    task_scores.append((task_id, metrics['success_rate']))
            
            if task_scores:
                task_scores.sort(key=lambda x: x[1], reverse=True)
                
                md.append("**Most Reliable Tasks:**")
                for task_id, score in task_scores[:3]:
                    md.append(f"- {task_id}: {score:.1%} success rate")
                
                md.append("\n**Least Reliable Tasks:**")
                for task_id, score in task_scores[-3:]:
                    md.append(f"- {task_id}: {score:.1%} success rate")
                md.append("")
        
        return md
    
    def _generate_delta_section(self, results: Dict[str, Any]) -> List[str]:
        """Generate DELTA results section."""
        md = []
        md.append("## DELTA - Comparative Analysis Results")
        md.append("")
        
        # Performance comparison
        if 'performance_comparison' in results:
            comp = results['performance_comparison']
            md.append("### Performance vs Baseline")
            md.append(f"- **Overall Winner:** {comp.get('overall_winner', 'Unknown')}")
            md.append(f"- **Confidence:** {comp.get('confidence_score', 0):.1%}")
            
            # Metrics comparison
            if 'metrics' in comp:
                md.append("\n**Detailed Comparison:**")
                
                for metric_name, metric_data in comp['metrics'].items():
                    if metric_data and 'relative_change' in metric_data:
                        change = metric_data['relative_change']
                        favors = metric_data.get('favors', 'neutral')
                        
                        if favors == 'agent':
                            symbol = "✅"
                        elif favors == 'baseline':
                            symbol = "❌"
                        else:
                            symbol = "➖"
                        
                        md.append(f"- {symbol} **{metric_name.capitalize()}:** {change:+.1f}%")
            md.append("")
        
        # Harm assessment
        if 'harm_assessment' in results:
            harm = results['harm_assessment']
            md.append("### Harm Amplification Analysis")
            md.append(f"- **Risk Level:** {harm.get('overall_risk_level', 'Unknown')}")
            md.append(f"- **Max Amplification:** {harm.get('max_amplification', 1.0):.1f}x")
            
            if 'critical_risks' in harm and harm['critical_risks']:
                md.append("\n**Critical Harm Risks:**")
                for risk in harm['critical_risks'][:3]:
                    md.append(f"- {risk.get('harm_type', 'Unknown')}: {risk.get('amplification', 1):.1f}x amplification")
            md.append("")
        
        # Deployment readiness
        if 'deployment_score' in results:
            md.append("### Deployment Readiness")
            score = results['deployment_score']
            md.append(f"- **Score:** {score:.0f}/100")
            
            if score >= 80:
                md.append("- **Status:** Ready for deployment ✅")
            elif score >= 60:
                md.append("- **Status:** Conditional deployment ⚠️")
            else:
                md.append("- **Status:** Not ready for deployment ❌")
            md.append("")
        
        return md
    
    def _generate_prism_section(self, results: Dict[str, Any]) -> List[str]:
        """Generate PRISM results section."""
        md = []
        md.append("## PRISM - Risk Translation Results")
        md.append("")
        
        # Risk assessment
        if 'risk_assessment' in results:
            assessment = results['risk_assessment']
            md.append("### Risk Assessment")
            md.append(f"- **Overall Risk Score:** {assessment.get('risk_score', 0):.1f}/10")
            md.append(f"- **Risk Level:** {assessment.get('risk_level', 'Unknown')}")
            md.append(f"- **Error Probability:** {assessment.get('probability', 0):.1%}")
            md.append(f"- **Impact Severity:** {assessment.get('impact', 0):.1f}/10")
            md.append("")
        
        # Business impacts
        if 'business_impacts' in results:
            impacts = results['business_impacts']
            md.append("### Business Impact Analysis")
            
            for impact_type, impact_data in impacts.items():
                if isinstance(impact_data, dict):
                    level = impact_data.get('potential_loss') or impact_data.get('impact_level') or impact_data.get('disruption_risk') or impact_data.get('violation_risk')
                    if level:
                        md.append(f"- **{impact_type.replace('_', ' ').title()}:** {level}")
            md.append("")
        
        # Compliance risks
        if 'compliance_risks' in results and results['compliance_risks']:
            md.append("### Compliance Risks")
            for risk in results['compliance_risks'][:5]:
                md.append(f"- {risk}")
            md.append("")
        
        return md
    
    def _generate_recommendations(self, report: Report) -> List[str]:
        """Generate consolidated recommendations."""
        recommendations = []
        
        # Priority-based recommendations
        if report.critical_issues:
            recommendations.append("### 🔴 Critical Priority")
            recommendations.append("")
            for issue in report.critical_issues[:3]:
                recommendations.append(f"1. Address: {issue}")
            recommendations.append("")
        
        # Module-specific recommendations
        all_recommendations = set()
        
        if report.sentinel_results and 'recommendations' in report.sentinel_results:
            all_recommendations.update(report.sentinel_results['recommendations'])
        
        if report.delta_results and 'improvement_areas' in report.delta_results:
            all_recommendations.update(report.delta_results['improvement_areas'])
        
        if report.prism_results and 'risk_assessment' in report.prism_results:
            if 'mitigation_recommendations' in report.prism_results['risk_assessment']:
                all_recommendations.update(report.prism_results['risk_assessment']['mitigation_recommendations'])
        
        if all_recommendations:
            recommendations.append("### 🟡 High Priority")
            recommendations.append("")
            for i, rec in enumerate(list(all_recommendations)[:5], 1):
                recommendations.append(f"{i}. {rec}")
            recommendations.append("")
        
        # General recommendations based on scores
        recommendations.append("### 🟢 Best Practices")
        recommendations.append("")
        
        if report.overall_score < 80:
            recommendations.append("- Continue testing and refinement before production deployment")
        
        recommendations.append("- Implement continuous monitoring and evaluation")
        recommendations.append("- Regular security audits and updates")
        recommendations.append("- Maintain documentation of AI agent capabilities and limitations")
        
        return recommendations
    
    def _score_to_risk_level(self, risk_score: float) -> str:
        """Convert risk score to risk level."""
        if risk_score >= 8:
            return "CRITICAL"
        elif risk_score >= 6:
            return "HIGH"
        elif risk_score >= 4:
            return "MEDIUM"
        elif risk_score >= 2:
            return "LOW"
        else:
            return "MINIMAL"
    
    def _get_module_summary(self, results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract summary from module results."""
        if not results:
            return {}
        
        # Extract key metrics based on module type
        summary = {}
        
        # Common fields
        for key in ['overall_score', 'risk_score', 'risk_level', 'confidence']:
            if key in results:
                summary[key] = results[key]
        
        # Module-specific summaries
        if 'aggregate_metrics' in results:  # AEGIS
            summary['test_results'] = results['aggregate_metrics']
        
        if 'overall_winner' in results:  # DELTA
            summary['comparison_winner'] = results['overall_winner']
        
        return summary
    
    def _save_json_report(self, report: Report, path: Path):
        """Save report as JSON."""
        json_data = {
            'evaluation_id': report.evaluation_id,
            'agent_name': report.agent_name,
            'evaluation_date': report.evaluation_date.isoformat(),
            'overall_score': report.overall_score,
            'overall_risk': report.overall_risk,
            'recommendation': report.recommendation,
            'confidence': report.confidence,
            'executive_summary': report.executive_summary,
            'key_findings': report.key_findings,
            'critical_issues': report.critical_issues,
            'modules': {
                'sentinel': report.sentinel_results,
                'aegis': report.aegis_results,
                'delta': report.delta_results,
                'prism': report.prism_results
            },
            'metadata': report.metadata
        }
        
        with open(path, 'w') as f:
            json.dump(json_data, f, indent=2, default=str)