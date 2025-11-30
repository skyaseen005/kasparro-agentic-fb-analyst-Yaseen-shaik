"""
Insight Agent - Generates hypotheses explaining performance patterns
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

from src.utils.logger import get_logger


class InsightAgent:
    """Generates data-driven hypotheses about FB Ads performance"""

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
        prompt_path = Path("prompts/insight_prompt.md")
        if prompt_path.exists():
            self.system_prompt = prompt_path.read_text()
        else:
            self.system_prompt = self._default_prompt()

    def _default_prompt(self) -> str:
        return """You are an expert Facebook Ads analyst specializing in ROAS optimization.

Return valid JSON ONLY:
{
  "timestamp": "ISO",
  "query": "user query",
  "hypotheses": [
    {
      "id": "H1",
      "hypothesis": "Clear statement of what happened and why",
      "confidence": 0.8,
      "evidence": ["Specific data point 1", "Specific data point 2"],
      "recommendation": "Actionable next step",
      "category": "creative_fatigue | audience_saturation | seasonal | technical"
    }
  ],
  "reasoning": "Your thought process"
}

Generate 3-5 evidence-based hypotheses. Be specific with numbers."""

    def generate_insights(
        self,
        query: str,
        data_summary: Dict[str, Any],
        plan: Dict[str, Any],
        previous_attempt: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:

        self.logger.info("Generating insights...")
        context = self._build_context(query, data_summary, plan, previous_attempt)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context},
                ],
                max_tokens=2000,
                temperature=0.7,
            )

            raw = response.choices[0].message.content.strip()
            insights = self._extract_json(raw)

            if not insights:
                raise ValueError("Invalid JSON output")

            # Enforce fields
            if "timestamp" not in insights:
                insights["timestamp"] = datetime.now().isoformat()
            if "query" not in insights:
                insights["query"] = query
            if "hypotheses" not in insights:
                insights["hypotheses"] = []

            self.logger.info(f"✓ Generated {len(insights['hypotheses'])} hypotheses.")
            return insights

        except Exception as e:
            self.logger.error(f"Error generating insights: {e}")
            return self._fallback_insights(query)

    def _extract_json(self, content: str) -> Optional[Dict[str, Any]]:
        """Removes code fences and extracts JSON safely."""
        try:
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception as e:
            self.logger.warning(f"JSON parsing failed: {e}")
            return None

    def _build_context(
        self,
        query: str,
        data_summary: Dict[str, Any],
        plan: Dict[str, Any],
        previous_attempt: Optional[Dict[str, Any]] = None
    ) -> str:

        ctx = f"# FB Ads Analytics\n\nQuery: {query}\n\n"

        # Performance metrics
        perf = data_summary.get("performance_metrics", {})
        if perf:
            ctx += "## Overall Metrics\n"
            ctx += f"- Total Spend: ${perf.get('total_spend', 0):,.2f}\n"
            ctx += f"- Total Revenue: ${perf.get('total_revenue', 0):,.2f}\n"
            ctx += f"- Average ROAS: {perf.get('avg_roas', 0):.2f}\n"
            ctx += f"- Average CTR: {perf.get('avg_ctr', 0):.2%}\n"
            ctx += f"- Median ROAS: {perf.get('median_roas', 0):.2f}\n\n"

        # Time analysis
        time = data_summary.get("time_analysis", {})
        recent = time.get("recent_week")
        prev = time.get("previous_week")
        changes = time.get("changes")

        if recent and prev:
            ctx += "## Week-over-Week\n"
            ctx += f"- Recent ROAS: {recent.get('avg_roas', 0):.2f}\n"
            ctx += f"- Previous ROAS: {prev.get('avg_roas', 0):.2f}\n"
            ctx += f"- Recent CTR: {recent.get('avg_ctr', 0):.2%}\n"
            ctx += f"- Previous CTR: {prev.get('avg_ctr', 0):.2%}\n"

            if changes:
                ctx += f"- ROAS Change: {changes.get('roas_change_pct', 0):.1f}%\n"
                ctx += f"- CTR Change: {changes.get('ctr_change_pct', 0):.1f}%\n"
            ctx += "\n"

        # Creative performance
        creative = data_summary.get("creative_analysis")
        if creative and "by_type" in creative:
            ctx += "## Creative Performance\n"
            for c in creative["by_type"]:
                ctx += (
                    f"- {c.get('creative_type')}: "
                    f"ROAS {c.get('roas', 0):.2f}, "
                    f"CTR {c.get('ctr', 0):.2%}\n"
                )
            ctx += "\n"

        # Underperformers
        under = data_summary.get("underperformers")
        if under:
            ctx += "## Underperforming Segments\n"
            ctx += f"- Low CTR campaigns: {under.get('count_low_ctr', 0)}\n"
            ctx += f"- Low ROAS campaigns: {under.get('count_low_roas', 0)}\n\n"

        # Previous attempt
        if previous_attempt:
            ctx += "## Previous Attempt (Low Confidence)\n"
            ctx += "Improve depth + evidence\n"
            ctx += json.dumps(previous_attempt.get("hypotheses", []), indent=2)
            ctx += "\n\n"

        ctx += "Generate 3-5 evidence-based hypotheses. Return ONLY JSON.\n"
        return ctx

    def _fallback_insights(self, query: str) -> Dict[str, Any]:
        self.logger.warning("[InsightAgent] Using fallback insights")
        return {
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "hypotheses": [
                {
                    "id": "H1",
                    "hypothesis": "Performance metrics require detailed analysis",
                    "confidence": 0.3,
                    "evidence": ["Automated analysis unavailable"],
                    "recommendation": "Manual review recommended",
                    "category": "technical",
                }
            ],
            "reasoning": "Fallback triggered due to API error"
        }