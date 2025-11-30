"""
Planner Agent - Bulletproof Version with Aggressive JSON Fixing
GUARANTEED to return valid structure - NO EXCEPTIONS
"""

import json
import os
import re
from typing import Dict, Any
from pathlib import Path

from src.utils.logger import get_logger


class PlannerAgent:
    """Decomposes user queries into structured analysis plan with guaranteed schema"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = get_logger(__name__)

        groq_key = os.getenv("GROQ_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        # Prefer Groq API
        if groq_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=groq_key)
                self.use_groq = True
                self.model = "llama-3.3-70b-versatile"
                self.logger.info("✓ Using Groq API (FREE)")
            except Exception as e:
                self.logger.warning(f"Groq init failed: {e}")
                self.use_groq = False
        else:
            self.use_groq = False

        # Fallback to OpenAI
        if not self.use_groq:
            if not openai_key:
                raise ValueError("Missing API keys!")
            from openai import OpenAI
            self.client = OpenAI(api_key=openai_key)
            self.model = self.config["model"]["name"]
            self.logger.info("✓ Using OpenAI API")

        # Load prompt
        prompt_path = Path("prompts/planner_prompt.md")
        if prompt_path.exists():
            self.system_prompt = prompt_path.read_text()
        else:
            self.system_prompt = self._default_prompt()

    def _default_prompt(self) -> str:
        return """You are a Facebook Ads strategic planner. 

You MUST return a JSON object with this EXACT structure - do not change the key names:

{
  "query": "the user's question",
  "intent": "diagnose_drop",
  "tasks": [
    {
      "task_id": "T1",
      "description": "what to analyze",
      "data_requirements": ["column_name"],
      "expected_output": "expected result"
    }
  ],
  "success_criteria": "how to measure success"
}

CRITICAL: The array MUST be called "tasks" not "steps" or "actions".

EXAMPLE for "Why did ROAS drop?":
{
  "query": "Why did ROAS drop?",
  "intent": "diagnose_drop",
  "tasks": [
    {
      "task_id": "T1",
      "description": "Analyze ROAS time trend",
      "data_requirements": ["date", "roas", "spend"],
      "expected_output": "Week over week ROAS change"
    },
    {
      "task_id": "T2",
      "description": "Compare campaign performance",
      "data_requirements": ["campaign_name", "roas", "ctr"],
      "expected_output": "Top and bottom performers"
    }
  ],
  "success_criteria": "Identify root cause of ROAS decline"
}

Return ONLY this JSON structure. No markdown, no backticks, no extra text."""

    def create_plan(self, query: str) -> Dict[str, Any]:
        """Create plan with aggressive error recovery"""
        self.logger.info(f"Planning for query: {query}")

        try:
            # Call LLM with JSON formatting hints
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Create a plan for: {query}\n\nReturn ONLY JSON, no other text."}
            ]
            
            # Build API call params
            api_params = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.1,
                "max_tokens": 1000
            }
            
            # Try to force JSON mode for compatible models
            if self.use_groq:
                # Groq doesn't support response_format yet, but lower temp helps
                api_params["temperature"] = 0.05
            else:
                # OpenAI supports JSON mode
                try:
                    api_params["response_format"] = {"type": "json_object"}
                except:
                    pass
            
            response = self.client.chat.completions.create(**api_params)

            raw = response.choices[0].message.content or ""
            self.logger.info(f"Raw LLM response: {raw[:200]}...")

            # Step 1: Extract JSON from any wrapping
            cleaned = self._extract_json(raw)
            
            # Step 2: Try parsing
            try:
                plan = json.loads(cleaned)
                self.logger.info("✓ JSON parsed successfully")
                
                # FIX: Handle nested structure {"plan": {...}}
                if "plan" in plan and isinstance(plan["plan"], dict):
                    self.logger.info("Auto-fixing: Unwrapping nested 'plan' object")
                    plan = plan["plan"]
                
            except json.JSONDecodeError as e:
                self.logger.warning(f"JSON parse error: {e}")
                plan = self._aggressive_repair(cleaned, query)

            # Step 3: Validate structure
            if self._is_valid_plan(plan):
                self.logger.info(f"✓ Valid plan with {len(plan['tasks'])} tasks")
                return plan
            else:
                self.logger.warning("Plan structure invalid after parsing")
                return self._fallback_plan(query)

        except Exception as e:
            self.logger.error(f"Planner error: {e}")
            return self._fallback_plan(query)

    def _extract_json(self, text: str) -> str:
        """Aggressively extract JSON from text"""
        txt = text.strip()
        
        # Remove markdown code blocks
        if "```json" in txt:
            txt = txt.split("```json")[1].split("```")[0].strip()
        elif "```" in txt:
            txt = txt.split("```")[1].split("```")[0].strip()
        
        # Find JSON object boundaries
        start = txt.find('{')
        end = txt.rfind('}')
        
        if start >= 0 and end > start:
            txt = txt[start:end+1]
        
        return txt

    def _aggressive_repair(self, broken_json: str, query: str) -> Dict[str, Any]:
        """Try multiple repair strategies"""
        
        # Strategy 1: Fix common issues
        repaired = broken_json
        repaired = repaired.replace("'", '"')  # Single to double quotes
        repaired = re.sub(r',\s*}', '}', repaired)  # Remove trailing commas in objects
        repaired = re.sub(r',\s*]', ']', repaired)  # Remove trailing commas in arrays
        
        try:
            return json.loads(repaired)
        except:
            pass
        
        # Strategy 2: Try to extract key parts with regex
        try:
            # Extract query
            query_match = re.search(r'"query"\s*:\s*"([^"]+)"', broken_json)
            query_val = query_match.group(1) if query_match else query
            
            # Extract tasks array
            tasks_match = re.search(r'"tasks"\s*:\s*\[(.*?)\]', broken_json, re.DOTALL)
            
            if tasks_match:
                tasks_str = tasks_match.group(1)
                # Try to parse individual tasks
                task_objects = re.findall(r'\{[^}]+\}', tasks_str)
                
                tasks = []
                for i, task_str in enumerate(task_objects[:5], 1):
                    try:
                        task = json.loads(task_str.replace("'", '"'))
                        if 'task_id' not in task:
                            task['task_id'] = f"T{i}"
                        tasks.append(task)
                    except:
                        continue
                
                if tasks:
                    return {
                        "query": query_val,
                        "intent": "diagnose_drop",
                        "tasks": tasks,
                        "success_criteria": "Identify root cause"
                    }
        except:
            pass
        
        # Strategy 3: Return empty valid structure
        self.logger.warning("All repair strategies failed")
        return {}

    def _is_valid_plan(self, plan: Any) -> bool:
        """Strict validation with auto-correction"""
        if not isinstance(plan, dict):
            self.logger.warning("Plan is not a dictionary")
            return False
        
        # Auto-fix: Unwrap nested structures
        if "plan" in plan and isinstance(plan["plan"], dict):
            self.logger.info("Auto-fixing: Unwrapping nested 'plan' object")
            plan = plan["plan"]
        
        # Auto-fix: Handle "steps" that contains list of objects with "tasks" arrays
        if "steps" in plan and isinstance(plan["steps"], list):
            # Check if steps[0] has a "tasks" array
            if len(plan["steps"]) > 0 and isinstance(plan["steps"][0], dict):
                if "tasks" in plan["steps"][0]:
                    # Flatten: extract tasks from nested structure
                    self.logger.info("Auto-fixing: Flattening nested steps->tasks structure")
                    all_tasks = []
                    for step_obj in plan["steps"]:
                        if "tasks" in step_obj and isinstance(step_obj["tasks"], list):
                            # Convert task strings to proper task objects
                            for i, task in enumerate(step_obj["tasks"], 1):
                                if isinstance(task, str):
                                    all_tasks.append({
                                        "task_id": f"T{len(all_tasks)+1}",
                                        "description": task,
                                        "data_requirements": ["spend", "revenue", "roas"],
                                        "expected_output": "Analysis results"
                                    })
                                elif isinstance(task, dict):
                                    all_tasks.append(task)
                    plan["tasks"] = all_tasks
                    del plan["steps"]
                else:
                    # Direct conversion: steps -> tasks
                    self.logger.info("Auto-fixing: Converting 'steps' to 'tasks'")
                    plan["tasks"] = plan["steps"]
                    del plan["steps"]
        
        # Auto-fix: Convert "actions" to "tasks" if present
        if "actions" in plan and "tasks" not in plan:
            self.logger.info("Auto-fixing: Converting 'actions' to 'tasks'")
            plan["tasks"] = plan["actions"]
            del plan["actions"]
        
        if "tasks" not in plan:
            self.logger.warning("Missing 'tasks' key (and no 'steps' or 'actions' to convert)")
            return False
        
        if not isinstance(plan["tasks"], list):
            self.logger.warning("'tasks' is not a list")
            return False
        
        if len(plan["tasks"]) == 0:
            self.logger.warning("'tasks' array is empty")
            return False
        
        # Validate and fix each task
        valid_tasks = []
        for i, task in enumerate(plan["tasks"]):
            if not isinstance(task, dict):
                # Try to convert string to dict
                if isinstance(task, str):
                    task = {
                        "task_id": f"T{i+1}",
                        "description": task,
                        "data_requirements": ["spend", "revenue", "roas"],
                        "expected_output": "Analysis results"
                    }
                    self.logger.info(f"Auto-fixing: Converted string task to dict")
                else:
                    self.logger.warning(f"Task {i} is not a dictionary, skipping")
                    continue
            
            # Auto-fix: Add missing task_id
            if "task_id" not in task:
                task["task_id"] = f"T{i+1}"
                self.logger.info(f"Auto-fixing: Added task_id T{i+1}")
            
            # Auto-fix: Add missing description
            if "description" not in task:
                # Try to use other fields
                task["description"] = task.get("action", task.get("task", task.get("step", "Analysis task")))
                self.logger.info(f"Auto-fixing: Added description from other fields")
            
            # Auto-fix: Add missing data_requirements
            if "data_requirements" not in task:
                task["data_requirements"] = ["spend", "revenue", "roas"]
                self.logger.info(f"Auto-fixing: Added default data_requirements")
            
            # Auto-fix: Add missing expected_output
            if "expected_output" not in task:
                task["expected_output"] = "Analysis results"
                self.logger.info(f"Auto-fixing: Added default expected_output")
            
            valid_tasks.append(task)
        
        # Replace with fixed tasks
        plan["tasks"] = valid_tasks
        
        if len(plan["tasks"]) == 0:
            self.logger.warning("No valid tasks after cleanup")
            return False
        
        # Auto-fix: Add missing query
        if "query" not in plan:
            plan["query"] = "Analysis query"
        
        # Auto-fix: Add missing intent
        if "intent" not in plan:
            plan["intent"] = "general_analysis"
        
        # Auto-fix: Add missing success_criteria
        if "success_criteria" not in plan:
            plan["success_criteria"] = "Complete analysis"
        
        self.logger.info(f"✓ Plan validated with {len(plan['tasks'])} tasks after auto-fixes")
        return True

    def _fallback_plan(self, query: str) -> Dict[str, Any]:
        """Guaranteed valid fallback plan"""
        self.logger.warning("[PlannerAgent] Using fallback plan.")

        # Detect query intent
        query_lower = query.lower()
        
        if "drop" in query_lower or "decline" in query_lower or "decrease" in query_lower:
            intent = "diagnose_drop"
            tasks = [
                {
                    "task_id": "T1",
                    "description": "Analyze ROAS trend over time",
                    "data_requirements": ["date", "roas", "spend", "revenue"],
                    "expected_output": "Time-based ROAS pattern showing decline"
                },
                {
                    "task_id": "T2",
                    "description": "Identify underperforming campaigns",
                    "data_requirements": ["campaign_name", "roas", "ctr", "spend"],
                    "expected_output": "List of campaigns with low ROAS"
                },
                {
                    "task_id": "T3",
                    "description": "Analyze creative performance",
                    "data_requirements": ["creative_type", "creative_message", "ctr", "roas"],
                    "expected_output": "Creative types and messages causing decline"
                }
            ]
        elif "improve" in query_lower or "increase" in query_lower or "optimize" in query_lower:
            intent = "optimize_performance"
            tasks = [
                {
                    "task_id": "T1",
                    "description": "Find top performing campaigns",
                    "data_requirements": ["campaign_name", "roas", "ctr", "spend"],
                    "expected_output": "Best performing campaigns to scale"
                },
                {
                    "task_id": "T2",
                    "description": "Identify winning creative patterns",
                    "data_requirements": ["creative_type", "creative_message", "ctr"],
                    "expected_output": "Creative elements that drive performance"
                }
            ]
        else:
            intent = "general_analysis"
            tasks = [
                {
                    "task_id": "T1",
                    "description": "Overall performance analysis",
                    "data_requirements": ["spend", "revenue", "roas", "ctr"],
                    "expected_output": "Summary of key metrics"
                },
                {
                    "task_id": "T2",
                    "description": "Campaign comparison",
                    "data_requirements": ["campaign_name", "roas", "spend"],
                    "expected_output": "Campaign performance breakdown"
                }
            ]

        return {
            "query": query,
            "intent": intent,
            "tasks": tasks,
            "success_criteria": f"Provide actionable insights for: {query}"
        }