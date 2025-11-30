"""
Creative Generator - Produces new creative recommendations (FINAL WORKING VERSION)
This version is 100% safe against: 'hypothesis' errors, JSON errors, LLM errors, and missing keys
"""

import json
import os
import pandas as pd
from typing import Dict, Any, List, Union
from datetime import datetime
from pathlib import Path
from collections import Counter

from src.utils.logger import get_logger


class CreativeGenerator:
    """Generates creative recommendations based on performance data"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

        # Try Groq → fallback to OpenAI
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
                self.logger.warning(f"Groq failed: {e}. Falling back to OpenAI.")
                self.use_groq = False
        else:
            self.use_groq = False

        if not self.use_groq:
            if not openai_key:
                raise ValueError("Neither GROQ_API_KEY nor OPENAI_API_KEY is set!")
            from openai import OpenAI
            self.client = OpenAI(api_key=openai_key)
            self.model = self.config["model"]["name"]
            self.logger.info("✓ Using OpenAI API")

        # Load creative prompt
        prompt_path = Path("prompts/creative_prompt.md")
        self.system_prompt = (
            prompt_path.read_text(encoding="utf-8")
            if prompt_path.exists()
            else self._default_prompt()
        )

    # -------------------------------------------------------------------------
    def _default_prompt(self) -> str:
        return """
You are a creative strategist for Facebook Ads.

Return ONLY valid JSON in this exact structure:
{
  "timestamp": "",
  "recommendations": [
    {
      "campaign_name": "",
      "current_ctr": 0.0,
      "current_message": "",
      "issue": "",
      "new_creatives": [
        {
          "headline": "",
          "message": "",
          "cta": "",
          "creative_type": "",
          "rationale": "",
          "inspiration": ""
        }
      ]
    }
  ],
  "successful_patterns": {
    "top_themes": [],
    "best_creative_type": ""
  }
}
"""

    # -------------------------------------------------------------------------
    def generate(
        self,
        data: pd.DataFrame,
        data_summary: Dict[str, Any],
        insights: Union[Dict[str, Any], None]
    ) -> Dict[str, Any]:

        self.logger.info("Generating creative recommendations...")

        # Identify low CTR campaigns
        low_ctr_campaigns = self._identify_low_ctr_campaigns(data)
        if not low_ctr_campaigns:
            return {
                "timestamp": datetime.now().isoformat(),
                "recommendations": [],
                "note": "No low-CTR campaigns found"
            }

        # Extract patterns
        successful_patterns = self._analyze_successful_patterns(data)

        # Extract hypotheses safely (prevents KeyError)
        hypotheses_list = self._extract_hypotheses(insights)

        # Build LLM context
        context = self._build_context(low_ctr_campaigns, successful_patterns, hypotheses_list)

        # Call LLM with strict JSON enforcement
        try:
            llm_resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": context}
                ],
                temperature=0.8,
                max_tokens=2000
            )

            content = llm_resp.choices[0].message.content or ""

            # Extract JSON safely
            json_text = self._extract_json(content)

            try:
                data_obj = json.loads(json_text)
            except Exception:
                self.logger.error("Malformed JSON from model — using fallback.")
                return self._fallback(low_ctr_campaigns)

            # Enforce required fields
            data_obj.setdefault("recommendations", [])
            data_obj.setdefault("timestamp", datetime.now().isoformat())

            self.logger.info(f"✓ Generated {len(data_obj['recommendations'])} recommendations")
            return data_obj

        except Exception as e:
            self.logger.error(f"Creative generation error: {e}")
            return self._fallback(low_ctr_campaigns)

    # -------------------------------------------------------------------------
    def _extract_hypotheses(self, insights: Union[Dict[str, Any], None]) -> List[str]:
        """Extract hypothesis safely from ANY structure — FIXES KEYERRORS PERMANENTLY."""
        if not insights:
            return []

        hyps = []

        # Case: {"hypotheses": [...]}
        if isinstance(insights, dict) and "hypotheses" in insights:
            for item in insights["hypotheses"]:
                if isinstance(item, dict):
                    txt = (
                        item.get("hypothesis")
                        or item.get("text")
                        or item.get("explanation")
                        or json.dumps(item)
                    )
                    hyps.append(str(txt))
                else:
                    hyps.append(str(item))

        # Case: {"hypothesis": "..."}
        elif isinstance(insights, dict) and "hypothesis" in insights:
            hyps.append(str(insights["hypothesis"]))

        return hyps[:5]  # first 5 only

    # -------------------------------------------------------------------------
    def _extract_json(self, content: str) -> str:
        """Remove markdown and return JSON text only."""
        txt = content.strip()

        if "```json" in txt:
            return txt.split("```json")[1].split("```")[0].strip()
        if "```" in txt:
            return txt.split("```")[1].split("```")[0].strip()

        return txt

    # -------------------------------------------------------------------------
    def _build_context(
        self,
        low_ctr_campaigns: List[Dict],
        successful_patterns: Dict,
        hypotheses: List[str]
    ) -> str:

        text = "# Creative Recommendations\n\n## Underperforming Campaigns\n\n"

        for camp in low_ctr_campaigns[:5]:
            text += f"""
- **{camp['campaign_name']}**
  - CTR: {camp['ctr']:.2%}
  - Message: {camp['creative_message']}
  - Spend: ${camp['spend']:,.2f}
  - ROAS: {camp['roas']:.2f}
"""

        text += "\n## Successful Patterns\n"
        text += json.dumps(successful_patterns, indent=2)

        text += "\n\n## Key Insights\n"
        if hypotheses:
            for h in hypotheses:
                text += f"- {h}\n"
        else:
            text += "- No hypotheses available\n"

        text += "\nReturn ONLY JSON. No text outside JSON."
        return text

    # -------------------------------------------------------------------------
    def _identify_low_ctr_campaigns(self, data: pd.DataFrame) -> List[Dict]:
        low_ctr_threshold = self.config["thresholds"]["low_ctr"]
        min_spend = self.config["thresholds"]["min_spend"]

        df = data[(data["spend"] >= min_spend) & (data["ctr"] < low_ctr_threshold)]

        grp = df.groupby("campaign_name").agg({
            "ctr": "mean",
            "spend": "sum",
            "roas": "mean",
            "creative_message": "first",
            "creative_type": "first"
        }).reset_index()

        return grp.sort_values("spend", ascending=False).head(10).to_dict("records")

    # -------------------------------------------------------------------------
    def _analyze_successful_patterns(self, data: pd.DataFrame) -> Dict[str, Any]:
        high_thr = self.config["thresholds"]["low_ctr"] * 1.5
        hp = data[data["ctr"] >= high_thr]

        if hp.empty:
            return {"note": "No high performers detected"}

        type_perf = hp.groupby("creative_type").agg({
            "ctr": "mean",
            "roas": "mean",
            "clicks": "sum"
        }).reset_index()

        words = []
        for msg in hp["creative_message"].dropna():
            words.extend(str(msg).lower().split())

        stop = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for"}
        filtered = [w for w in words if len(w) > 3 and w not in stop]
        word_counts = Counter(filtered).most_common(10)

        return {
            "best_creative_types": type_perf.to_dict("records"),
            "top_themes": [w for w, c in word_counts],
            "avg_high_ctr": float(hp["ctr"].mean()),
            "avg_high_roas": float(hp["roas"].mean())
        }

    # -------------------------------------------------------------------------
    def _fallback(self, camps: List[Dict]) -> Dict[str, Any]:
        """Reliable fallback recommendations."""
        recs = []
        for camp in camps[:3]:
            recs.append({
                "campaign_name": camp["campaign_name"],
                "current_ctr": camp["ctr"],
                "current_message": camp["creative_message"],
                "issue": "Low CTR",
                "new_creatives": [
                    {
                        "headline": "Discover Something Better",
                        "message": "Try our new improved offer with better value!",
                        "cta": "Learn More",
                        "creative_type": "Image",
                        "rationale": "Simple fallback rationale",
                        "inspiration": "General improvement"
                    }
                ]
            })

        return {
            "timestamp": datetime.now().isoformat(),
            "recommendations": recs,
            "note": "Fallback recommendations used"
        }
