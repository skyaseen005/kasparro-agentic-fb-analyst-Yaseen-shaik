"""
Agentic Workflow Orchestrator - FULLY FIXED VERSION
Coordinates the multi-agent system for Facebook Ads analysis
Handles all edge cases and prevents KeyError crashes
"""

import yaml
from pathlib import Path
from typing import Dict, Any
import pandas as pd

from src.agents.planner import PlannerAgent
from src.agents.data_agent import DataAgent
from src.agents.insight_agent import InsightAgent
from src.agents.evaluator import EvaluatorAgent
from src.agents.creative_generator import CreativeGenerator
from src.utils.logger import get_logger


class AgenticWorkflow:
    """Orchestrates the multi-agent workflow for FB Ads analysis"""
    
    def __init__(self, config_path: str = "config/config.yaml"):
        self.logger = get_logger(__name__)
        self.config = self._load_config(config_path)
        
        # Initialize all agents
        self.planner = PlannerAgent(self.config)
        self.data_agent = DataAgent(self.config)
        self.insight_agent = InsightAgent(self.config)
        self.evaluator = EvaluatorAgent(self.config)
        self.creative_generator = CreativeGenerator(self.config)
        
        self.logger.info("AgenticWorkflow initialized with all agents")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    
    def run(self, query: str, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Execute the full agentic workflow
        
        Args:
            query: User's analysis question
            data: Facebook Ads DataFrame
            
        Returns:
            Dictionary containing insights, creatives, and report
        """
        self.logger.info(f"\n{'='*80}")
        self.logger.info("STARTING AGENTIC WORKFLOW")
        self.logger.info(f"{'='*80}\n")
        
        try:
            # STEP 1: Planning
            self.logger.info("[AGENT: PLANNER] Decomposing query into subtasks...")
            plan = self.planner.create_plan(query)
            
            # FIX: Ensure plan has tasks key
            if not isinstance(plan, dict):
                plan = {'tasks': [], 'query': query}
            if 'tasks' not in plan:
                plan['tasks'] = []
            
            self.logger.info(f"Plan created with {len(plan['tasks'])} tasks")
            
            # STEP 2: Data Analysis
            self.logger.info("\n[AGENT: DATA] Analyzing dataset...")
            data_summary = self.data_agent.analyze(data)
            self.logger.info(f"Data summary generated: {len(data_summary)} metrics")
            
            # STEP 3: Generate Insights
            self.logger.info("\n[AGENT: INSIGHT] Generating hypotheses...")
            insights = self.insight_agent.generate_insights(
                query=query,
                data_summary=data_summary,
                plan=plan
            )
            
            # FIX: Ensure insights has hypotheses key
            if not isinstance(insights, dict):
                insights = {'hypotheses': [], 'query': query}
            if 'hypotheses' not in insights:
                insights['hypotheses'] = []
            
            self.logger.info(f"Generated {len(insights['hypotheses'])} hypotheses")
            
            # STEP 4: Evaluate Insights
            self.logger.info("\n[AGENT: EVALUATOR] Validating hypotheses...")
            validated_insights = self.evaluator.evaluate(
                hypotheses=insights['hypotheses'],
                data=data,
                data_summary=data_summary
            )
            
            # FIX: Ensure validated_insights has required keys
            if not isinstance(validated_insights, dict):
                validated_insights = {
                    'hypotheses': insights['hypotheses'],
                    'overall_confidence': 0.0,
                    'validation_summary': 'Validation failed'
                }
            if 'hypotheses' not in validated_insights:
                validated_insights['hypotheses'] = insights['hypotheses']
            if 'overall_confidence' not in validated_insights:
                # Calculate from hypotheses if missing
                if validated_insights['hypotheses']:
                    avg_conf = sum(h.get('confidence', 0) for h in validated_insights['hypotheses']) / len(validated_insights['hypotheses'])
                    validated_insights['overall_confidence'] = avg_conf
                else:
                    validated_insights['overall_confidence'] = 0.0
            
            self.logger.info(f"Validated {len(validated_insights['hypotheses'])} hypotheses")
            
            # Check if we need to retry with low confidence
            if self._needs_reflection(validated_insights):
                self.logger.warning("Low confidence detected. Running reflection loop...")
                validated_insights = self._reflection_loop(
                    query, data, data_summary, plan, validated_insights
                )
            
            # STEP 5: Generate Creative Recommendations
            self.logger.info("\n[AGENT: CREATIVE] Generating recommendations...")
            creatives = self.creative_generator.generate(
                data=data,
                data_summary=data_summary,
                insights=validated_insights
            )
            
            # FIX: Ensure creatives has recommendations key
            if not isinstance(creatives, dict):
                creatives = {'recommendations': []}
            if 'recommendations' not in creatives:
                creatives['recommendations'] = []
            
            self.logger.info(f"Generated {len(creatives['recommendations'])} creative ideas")
            
            # STEP 6: Create Final Report
            self.logger.info("\n[FINAL STEP] Compiling report...")
            report = self._create_report(
                query=query,
                insights=validated_insights,
                creatives=creatives,
                plan=plan
            )
            
            self.logger.info(f"\n{'='*80}")
            self.logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
            self.logger.info(f"{'='*80}\n")
            
            return {
                'insights': validated_insights,
                'creatives': creatives,
                'report': report,
                'plan': plan
            }
            
        except Exception as e:
            self.logger.error(f"❌ Workflow failed: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            
            # Return safe fallback structure
            return {
                'insights': {
                    'hypotheses': [],
                    'overall_confidence': 0.0,
                    'validation_summary': f'Analysis failed: {str(e)}'
                },
                'creatives': {'recommendations': []},
                'report': f"Analysis failed: {str(e)}",
                'plan': {'tasks': [], 'query': query}
            }
    
    def _needs_reflection(self, insights: Dict[str, Any]) -> bool:
        """Check if insights need reflection/retry"""
        # FIX: Safe access with defaults
        config_reflection = self.config.get('agents', {}).get('reflection_enabled', True)
        
        if not config_reflection:
            return False
        
        hypotheses = insights.get('hypotheses', [])
        if not hypotheses:
            return True
        
        # Use overall_confidence if available, otherwise calculate
        if 'overall_confidence' in insights:
            avg_confidence = insights['overall_confidence']
        else:
            avg_confidence = sum(h.get('confidence', 0) for h in hypotheses) / len(hypotheses)
        
        min_confidence = self.config.get('agents', {}).get('min_confidence', 0.6)
        
        return avg_confidence < min_confidence
    
    def _reflection_loop(
        self,
        query: str,
        data: pd.DataFrame,
        data_summary: Dict,
        plan: Dict,
        previous_insights: Dict
    ) -> Dict[str, Any]:
        """Re-analyze with reflection on previous low-confidence results"""
        self.logger.info("Reflection: Re-generating insights with context...")
        
        try:
            refined_insights = self.insight_agent.generate_insights(
                query=query,
                data_summary=data_summary,
                plan=plan,
                previous_attempt=previous_insights
            )
            
            # FIX: Ensure structure
            if not isinstance(refined_insights, dict):
                refined_insights = {'hypotheses': []}
            if 'hypotheses' not in refined_insights:
                refined_insights['hypotheses'] = []
            
            validated_insights = self.evaluator.evaluate(
                hypotheses=refined_insights['hypotheses'],
                data=data,
                data_summary=data_summary
            )
            
            # FIX: Ensure structure
            if not isinstance(validated_insights, dict):
                return previous_insights  # Return previous if reflection fails
            if 'hypotheses' not in validated_insights:
                validated_insights['hypotheses'] = refined_insights['hypotheses']
            if 'overall_confidence' not in validated_insights:
                if validated_insights['hypotheses']:
                    avg_conf = sum(h.get('confidence', 0) for h in validated_insights['hypotheses']) / len(validated_insights['hypotheses'])
                    validated_insights['overall_confidence'] = avg_conf
                else:
                    validated_insights['overall_confidence'] = 0.0
            
            return validated_insights
            
        except Exception as e:
            self.logger.error(f"Reflection loop failed: {e}")
            # Return previous insights if reflection fails
            return previous_insights
    
    def _create_report(
        self,
        query: str,
        insights: Dict,
        creatives: Dict,
        plan: Dict
    ) -> str:
        """Generate markdown report for marketers"""
        
        # FIX: Safe access to all fields
        hypotheses = insights.get('hypotheses', [])
        recommendations = creatives.get('recommendations', [])
        timestamp = insights.get('timestamp', 'N/A')
        
        report = f"""# Facebook Ads Performance Analysis Report

## Query
{query}

## Executive Summary

This analysis examined Facebook Ads performance data to identify drivers of ROAS fluctuation and provide actionable recommendations.

### Key Findings
"""
        
        if not hypotheses:
            report += "\n*No hypotheses were generated. Please check the data quality and try again.*\n"
        else:
            # Add top insights
            for i, h in enumerate(hypotheses[:3], 1):
                confidence = h.get('confidence', 0)
                confidence_emoji = "🟢" if confidence >= 0.75 else "🟡" if confidence >= 0.5 else "🔴"
                
                report += f"""
#### {i}. {h.get('hypothesis', 'Unknown hypothesis')} {confidence_emoji}
**Confidence:** {confidence:.0%}

**Evidence:**
"""
                evidence_list = h.get('evidence', [])
                if evidence_list:
                    for evidence in evidence_list:
                        report += f"- {evidence}\n"
                else:
                    report += "- No evidence available\n"
                
                report += f"\n**Recommendation:** {h.get('recommendation', 'No recommendation available')}\n"
        
        # Add creative recommendations
        report += f"""

## Creative Recommendations

"""
        
        if not recommendations:
            report += "*No creative recommendations were generated.*\n"
        else:
            report += f"We identified {len(recommendations)} campaigns that would benefit from creative refresh:\n\n"
            
            for rec in recommendations[:5]:
                campaign_name = rec.get('campaign_name', 'Unknown Campaign')
                current_ctr = rec.get('current_ctr', 0)
                current_message = rec.get('current_message', 'N/A')
                new_creatives_list = rec.get('new_creatives', [])
                
                report += f"""
### Campaign: {campaign_name}
- **Current CTR:** {current_ctr:.2%}
- **Current Message:** "{current_message}"

**New Creative Ideas:**
"""
                if new_creatives_list:
                    for i, creative in enumerate(new_creatives_list[:2], 1):
                        report += f"""
{i}. **Headline:** {creative.get('headline', 'N/A')}
   - **Message:** {creative.get('message', 'N/A')}
   - **CTA:** {creative.get('cta', 'N/A')}
   - **Rationale:** {creative.get('rationale', 'N/A')}
"""
                else:
                    report += "*No new creatives generated for this campaign.*\n"
        
        report += f"""

## Next Steps

1. Implement creative refreshes for campaigns with declining CTR
2. Monitor performance daily for the next week
3. A/B test new creative concepts against current winners
4. Review audience targeting for fatigued segments

---
*Report generated by Kasparro Agentic FB Analyst*
*Timestamp: {timestamp}*
"""
        
        return report