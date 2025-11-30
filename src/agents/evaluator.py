"""
Evaluator Agent - Validates hypotheses with quantitative analysis
"""

import json
import os
import pandas as pd
from typing import Dict, Any, List
from pathlib import Path

from src.utils.logger import get_logger


class EvaluatorAgent:
    """Validates hypotheses using quantitative data checks"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)
        
        # Try Groq first (FREE), fallback to OpenAI
        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=groq_key)
                self.use_groq = True
                self.model = "llama-3.3-70b-versatile"
                self.logger.info("✓ Using Groq API (FREE)")
            except Exception as e:
                self.logger.warning(f"Groq initialization failed: {e}. Using OpenAI fallback")
                self.use_groq = False
        else:
            self.use_groq = False
        
        if not self.use_groq:
            if openai_key:
                from openai import OpenAI
                self.client = OpenAI(api_key=openai_key)
                self.model = self.config['model']['name']
                self.logger.info("✓ Using OpenAI API")
            else:
                raise ValueError("Neither GROQ_API_KEY nor OPENAI_API_KEY is set")
        
        # Load prompt template
        prompt_path = Path("prompts/evaluator_prompt.md")
        if prompt_path.exists():
            with open(prompt_path, 'r') as f:
                self.system_prompt = f.read()
        else:
            self.system_prompt = self._default_prompt()
    
    def _default_prompt(self) -> str:
        return """You are a quantitative analyst validating hypotheses.

Review hypotheses and adjust confidence scores based on evidence quality.

Return JSON:
{
  "timestamp": "ISO",
  "hypotheses": [
    {
      "id": "H1",
      "hypothesis": "...",
      "confidence": 0.85,
      "original_confidence": 0.8,
      "evidence": [...],
      "recommendation": "...",
      "category": "...",
      "validation": {
        "supports": ["what confirms"],
        "contradicts": ["what contradicts"],
        "data_gaps": ["missing data"]
      }
    }
  ],
  "overall_confidence": 0.78,
  "validation_summary": "Assessment"
}

Confidence:
- High (0.75-1.0): Strong evidence
- Medium (0.5-0.74): Moderate evidence
- Low (0.0-0.49): Weak evidence"""
    
    def evaluate(
        self,
        hypotheses: List[Dict[str, Any]],
        data: pd.DataFrame,
        data_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate hypotheses against actual data"""
        
        self.logger.info(f"Evaluating {len(hypotheses)} hypotheses...")
        
        # Perform quantitative validation
        quantitative_checks = self._perform_quantitative_checks(data, data_summary)
        
        # Build context
        context = self._build_validation_context(
            hypotheses, data_summary, quantitative_checks
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.3,
                max_tokens=2000
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            
            validated = json.loads(content)
            
            # Calculate overall confidence
            if 'hypotheses' in validated and len(validated['hypotheses']) > 0:
                avg_conf = sum(h['confidence'] for h in validated['hypotheses']) / len(validated['hypotheses'])
                validated['overall_confidence'] = avg_conf
            
            self.logger.info(f"✓ Validation complete. Confidence: {validated.get('overall_confidence', 0):.2f}")
            return validated
            
        except Exception as e:
            self.logger.error(f"Error in evaluation: {str(e)}")
            return {
                "hypotheses": hypotheses,
                "overall_confidence": 0.5,
                "validation_summary": "Automated validation failed"
            }
    
    def _perform_quantitative_checks(
        self,
        data: pd.DataFrame,
        data_summary: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Perform statistical validation checks"""
        
        checks = {
            "sample_size_adequate": len(data) >= 30,
            "date_range_adequate": True,
            "metrics_complete": True
        }
        
        # Check for significant changes
        if 'time_analysis' in data_summary:
            time = data_summary['time_analysis']
            if 'changes' in time:
                checks['significant_roas_change'] = abs(time['changes'].get('roas_change_pct', 0)) > 10
                checks['significant_ctr_change'] = abs(time['changes'].get('ctr_change_pct', 0)) > 10
        
        # Check creative performance variance
        if 'creative_analysis' in data_summary:
            creative = data_summary['creative_analysis']
            if 'by_type' in creative and len(creative['by_type']) > 1:
                roas_values = [c.get('roas', 0) for c in creative['by_type']]
                checks['creative_variance'] = max(roas_values) / min(roas_values) if min(roas_values) > 0 else 1
        
        # Check for underperformers
        if 'underperformers' in data_summary:
            under = data_summary['underperformers']
            checks['has_low_ctr_campaigns'] = under.get('count_low_ctr', 0) > 0
            checks['has_low_roas_campaigns'] = under.get('count_low_roas', 0) > 0
        
        return checks
    
    def _build_validation_context(
        self,
        hypotheses: List[Dict],
        data_summary: Dict,
        quantitative_checks: Dict
    ) -> str:
        """Build context for LLM validation"""
        
        context = "# Hypothesis Validation\n\n## Hypotheses to Validate\n\n"
        
        for h in hypotheses:
            context += f"""
### {h.get('id', 'H?')}: {h.get('hypothesis', 'Unknown')}
- Confidence: {h.get('confidence', 0.5)}
- Evidence: {json.dumps(h.get('evidence', []))}
- Category: {h.get('category', 'unknown')}
"""
        
        context += f"\n## Quantitative Checks\n{json.dumps(quantitative_checks, indent=2)}\n"
        
        # Add data summary
        if 'performance_metrics' in data_summary:
            context += f"\n## Performance\n{json.dumps(data_summary['performance_metrics'], indent=2)}\n"
        
        if 'time_analysis' in data_summary:
            context += f"\n## Time Analysis\n{json.dumps(data_summary['time_analysis'], indent=2)}\n"
        
        context += "\nValidate each hypothesis and return JSON with adjusted confidence scores."
        
        return context