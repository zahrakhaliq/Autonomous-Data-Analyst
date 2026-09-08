import json

from groq_client import GroqClient
from analysis_tools import execute_plan


PLANNER_SYSTEM = """
You are the planning component of an autonomous data analyst.

Your job is ONLY to create an analysis plan.

You must NOT calculate any numerical results.

You must NOT invent values.

You must select deterministic analysis operations that can be executed by Python.

Available actions:
- profile
- aggregate
- top_n
- correlation
- describe
- outliers

Rules:

1. Use ONLY columns that exist in the supplied dataset profiles.
2. Every step must have a valid dataset filename.
3. For a "why" question, create multiple focused analysis steps.
4. Do not claim causation.
5. Use Python/Pandas for all calculations.
6. Keep the plan concise.
7. Return only the fields defined by the JSON schema.
"""


PLANNER_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "goal": {
            "type": "string"
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "description": {
                        "type": "string"
                    },
                    "action": {
                        "type": "string",
                        "enum": [
                            "profile",
                            "aggregate",
                            "top_n",
                            "correlation",
                            "describe",
                            "outliers"
                        ]
                    },
                    "dataset": {
                        "type": "string"
                    },
                    "metric": {
                        "type": ["string", "null"]
                    },
                    "group_by": {
                        "type": ["string", "null"]
                    },
                    "date_column": {
                        "type": ["string", "null"]
                    },
                    "aggregation": {
                        "type": "string",
                        "enum": [
                            "sum",
                            "mean",
                            "count",
                            "median"
                        ]
                    },
                    "frequency": {
                        "type": "string",
                        "enum": [
                            "M",
                            "Q",
                            "Y"
                        ]
                    },
                    "columns": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        }
                    },
                    "n": {
                        "type": "integer"
                    },
                    "visualize": {
                        "type": "boolean"
                    },
                    "chart_title": {
                        "type": "string"
                    }
                },
                "required": [
                    "description",
                    "action",
                    "dataset",
                    "metric",
                    "group_by",
                    "date_column",
                    "aggregation",
                    "frequency",
                    "columns",
                    "n",
                    "visualize",
                    "chart_title"
                ]
            }
        },
        "assumptions": {
            "type": "array",
            "items": {
                "type": "string"
            }
        }
    },
    "required": [
        "goal",
        "steps",
        "assumptions"
    ]
}


REPORT_SYSTEM = """
You are the report generator for an autonomous data analyst.

Use ONLY the supplied verified analysis results.

Never invent numbers.

Never perform calculations yourself.

Clearly distinguish:
- Facts
- Interpretations
- Limitations

Do not claim causation unless the supplied evidence establishes it.

Return only the JSON structure defined by the schema.
"""


REPORT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "executive_summary": {
            "type": "string"
        },
        "key_findings": {
            "type": "array",
            "items": {
                "type": "string"
            }
        },
        "evidence": {
            "type": "string"
        },
        "methodology": {
            "type": "string"
        },
        "verification": {
            "type": "string"
        },
        "limitations": {
            "type": "string"
        }
    },
    "required": [
        "executive_summary",
        "key_findings",
        "evidence",
        "methodology",
        "verification",
        "limitations"
    ]
}


class AnalystAgent:

    def __init__(self, datasets, profiles, history=None):
        self.datasets = datasets
        self.profiles = profiles
        self.history = history or []
        self.llm = GroqClient()

    def _context(self):
        return {
            "datasets": self.profiles,
            "recent_history": self.history[-5:]
        }

    def plan(self, question):

        prompt = json.dumps(
            {
                "question": question,
                "available_data": self._context()
            },
            default=str
        )

        return self.llm.json_completion(
            PLANNER_SYSTEM,
            prompt,
            PLANNER_SCHEMA,
            "analysis_plan"
        )

    def run(self, question, progress=None):

        plan = self.plan(question)

        if progress:
            progress.write("🧩 Plan created.")

        results, figures = execute_plan(
            self.datasets,
            plan
        )

        if progress:
            progress.write(
                f"🧮 Completed {len(results)} analysis step(s)."
            )

        from verification import verify_results

        verification = verify_results(
            self.datasets,
            plan,
            results,
            question
        )

        if progress:
            progress.write(
                "🔐 Verification layer completed."
            )

        report_prompt = json.dumps(
            {
                "question": question,
                "plan": plan,
                "analysis_results": results,
                "verification": verification
            },
            default=str
        )

        report = self.llm.json_completion(
            REPORT_SYSTEM,
            report_prompt,
            REPORT_SCHEMA,
            "analysis_report"
        )

        return {
            "question": question,
            "plan": plan,
            "results": results,
            "verification": verification,
            "figures": figures,
            "report": report
        }
