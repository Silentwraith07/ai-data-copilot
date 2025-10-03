import openai
import httpx
import json
import pandas as pd
from typing import Dict, Any

class LLMQueryModule:
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(
            api_key=api_key,
            timeout=httpx.Timeout(60.0, connect=10.0),
            max_retries=3
        )
    
    def process_query(self, question: str, df: pd.DataFrame, schema: Dict[str, str], summary: Dict[str, Any]) -> Dict[str, Any]:
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(question, df, schema, summary)
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            result = json.loads(response.choices[0].message.content)
            return self._validate_response(result)
        except Exception as e:
            return {
                "answer_text": f"Error: {str(e)}",
                "chart_type": None,
                "chart_data": None,
                "recommendations": None,
                "sql_query": None
            }
    
    def _build_system_prompt(self) -> str:
        return """You are DataCopilot, an AI assistant specialized in analyzing tabular data.
Always respond with valid JSON containing: answer_text, chart_type, chart_data, recommendations, sql_query."""
    
    def _build_user_prompt(self, question: str, df: pd.DataFrame, schema: Dict[str, str], summary: Dict[str, Any]) -> str:
        schema_str = "\n".join([f"  - {col}: {dtype}" for col, dtype in schema.items()])
        sample_rows = df.head(3).to_dict(orient='records')
        return f"""Schema:\n{schema_str}\n\nSample Data:\n{json.dumps(sample_rows, default=str)}\n\nQuestion: {question}"""
    
    def _validate_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and normalize LLM response.
        """
        # Get recommendations and ensure it's a list
        recommendations = result.get("recommendations", [])
        if isinstance(recommendations, str):
            # If LLM returned a string instead of list, convert it
            recommendations = [recommendations] if recommendations else []
        elif not isinstance(recommendations, list):
            recommendations = []
        
        validated = {
            "answer_text": result.get("answer_text", "No answer provided"),
            "chart_type": result.get("chart_type"),
            "chart_data": result.get("chart_data"),
            "recommendations": recommendations,
            "sql_query": result.get("sql_query")
        }
        
        # Validate chart_type
        valid_chart_types = {"bar", "line", "pie", "scatter", "none", None}
        if validated["chart_type"] not in valid_chart_types:
            validated["chart_type"] = None
        
        return validated

