import json
from groq_client import GroqClient
from analysis_tools import execute_plan

PLANNER_SYSTEM = """
You are the planning component of an autonomous data analyst.
You DO NOT calculate results. You create a safe, explicit plan for deterministic
Python/Pandas tools.

Return valid JSON with:
{
  "goal": "...",
  "steps": [
    {
      "description": "...",
      "action": "profile|aggregate|top_n|correlation|describe|outliers",
      "dataset": "exact filename",
      "metric": "column or null",
      "group_by": "column or null",
      "date_column": "column or null",
      "aggregation": "sum|mean|count|median",
      "frequency": "M|Q|Y",
      "columns": [],
      "n": 10,
      "visualize": true,
      "chart_title": "..."
    }
  ],
  "assumptions": ["..."]
}

Use only columns present in the supplied profiles. Prefer multiple focused steps
for "why" questions. Do not claim causation unless the data supports it.
"""

REPORT_SYSTEM = """
You are the report generator for an autonomous data analyst.
Use ONLY the supplied verified results. Never invent numbers.
Return JSON:
{
 "executive_summary": "...",
 "key_findings": ["..."],
 "evidence": "...",
 "methodology": "...",
 "verification": "...",
 "limitations": "..."
}
Clearly label facts versus interpretations. If causation is not established,
say so.
"""

class AnalystAgent:
    def __init__(self, datasets, profiles, history=None):
        self.datasets = datasets
        self.profiles = profiles
        self.history = history or []
        self.llm = GroqClient()

    def _context(self):
        return {
            "datasets": self.profiles,
            "recent_history": self.history[-5:],
        }

    def plan(self, question):
        prompt = json.dumps({
            "question": question,
            "available_data": self._context(),
        }, default=str)
        return self.llm.json_completion(PLANNER_SYSTEM, prompt)

    def run(self, question, progress=None):
        plan = self.plan(question)
        if progress:
            progress.write("🧩 Plan created.")

        results, figures = execute_plan(self.datasets, plan)
        if progress:
            progress.write(f"🧮 Completed {len(results)} analysis step(s).")

        from verification import verify_results
        verification = verify_results(self.datasets, plan, results, question)
        if progress:
            progress.write("🔐 Verification layer completed.")

        report_prompt = json.dumps({
            "question": question,
            "plan": plan,
            "analysis_results": results,
            "verification": verification,
        }, default=str)

        report = self.llm.json_completion(REPORT_SYSTEM, report_prompt)

        return {
            "question": question,
            "plan": plan,
            "results": results,
            "verification": verification,
            "figures": figures,
            "report": report,
        }
