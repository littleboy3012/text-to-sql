"""
sql_generator.py
Interacts with Sarvam AI Chat Completion API to translate natural language into SQL and visualization specs.
"""

import json
import re
import requests
from typing import Dict, Any

DEFAULT_SYSTEM_PROMPT = """You are an expert MySQL Architect and Business Intelligence Analyst.
Your task is to convert the user's natural language question into an optimized, valid MySQL SELECT query based on the provided schema, and recommend the best visualization.

Rules:
1. ONLY produce valid MySQL queries. Use MySQL syntax (e.g. backticks for table/column names if needed, DATE_FORMAT, YEAR, MONTH, CURDATE, etc.).
2. ONLY generate SELECT or WITH statements. NEVER use DROP, DELETE, INSERT, UPDATE, ALTER, or TRUNCATE.
3. ALWAYS give clean column aliases for aggregated calculations (e.g., `SELECT SUM(unit_price * quantity) AS total_revenue`).
4. Apply appropriate JOINs using the provided Foreign Key relations.
5. If the query asks for top/bottom items without a specific count, use LIMIT 10.
6. When comparing or aggregating time/dates, group by appropriate date intervals.
7. Output MUST BE strictly a valid JSON object with the following keys:
{
  "sql_query": "SELECT ...",
  "explanation": "Brief 1-2 sentence explanation of what this query calculates.",
  "visualization": {
    "recommended": true,
    "chart_type": "bar" | "line" | "pie" | "donut" | "scatter" | "metric" | "none",
    "x_axis": "column_name_for_categories_or_dates",
    "y_axis": "column_name_for_numeric_metrics",
    "color": null or "grouping_column",
    "title": "Descriptive Chart Title"
  }
}
8. IMPORTANT: Keep your internal thinking very brief and concise. Do NOT generate lengthy internal reasoning. Directly provide the JSON answer.
"""

class SarvamSQLGenerator:
    def __init__(self, api_key: str, model_name: str = "sarvam-105b", api_version: str = "v1"):
        self.api_key = api_key.strip() if api_key else ""
        self.model_name = model_name
        self.api_version = api_version
        self.endpoint = f"https://api.sarvam.ai/{api_version}/chat/completions"

    def clean_json_response(self, text: Any) -> Dict[str, Any]:
        """Strips markdown fences and parses JSON safely with null-safety."""
        if text is None:
            text = ""
        text = str(text).strip()
        
        # Strip <think>...</think> tags if reasoning tokens leaked into text
        text = re.sub(r"<think>[\s\S]*?</think>", "", text).strip()

        # Remove ```json or ``` markdown blocks
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        clean_text = match.group(1).strip() if match else text
            
        try:
            parsed = json.loads(clean_text)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass

        # Fallback: regex search for sql_query
        sql_match = re.search(r"SELECT\s+[\s\S]+?(?=;|\n```|$)", text, re.IGNORECASE)
        if sql_match:
            sql_found = sql_match.group(0).strip()
            return {
                "sql_query": sql_found,
                "explanation": "Extracted query from model response.",
                "visualization": {
                    "recommended": True,
                    "chart_type": "bar",
                    "x_axis": None,
                    "y_axis": None,
                    "title": "Query Results"
                }
            }
        raise ValueError(f"Could not parse valid JSON or SQL from model response:\n{text}")

    def generate(self, user_prompt: str, schema_text: str) -> Dict[str, Any]:
        """
        Sends the user question and schema to Sarvam AI and returns structured SQL + viz payload.
        """
        if not self.api_key:
            raise ValueError("Sarvam AI API key is not provided. Please enter your API key in the sidebar.")

        headers = {
            "Content-Type": "application/json",
            "api-subscription-key": self.api_key,
            "Authorization": f"Bearer {self.api_key}"
        }

        user_content = f"""Database Schema:
{schema_text}

User Question:
{user_prompt}

Generate the JSON response containing the MySQL query and visualization recommendations:"""

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": DEFAULT_SYSTEM_PROMPT},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.1,
            "max_tokens": 4096,
            "reasoning_effort": "low"
        }

        try:
            response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)
            
            # If 400 Bad Request, possibly due to unsupported reasoning_effort parameter, retry without it
            if response.status_code == 400 and "reasoning_effort" in response.text:
                payload.pop("reasoning_effort", None)
                response = requests.post(self.endpoint, headers=headers, json=payload, timeout=60)

            # If v1 returns 404 or unsupported model, try fallback to v2
            if response.status_code == 404 and self.api_version == "v1":
                fallback_url = "https://api.sarvam.ai/v2/chat/completions"
                response = requests.post(fallback_url, headers=headers, json=payload, timeout=60)

            if response.status_code != 200:
                error_msg = response.text
                try:
                    err_json = response.json()
                    error_msg = err_json.get("error", {}).get("message", error_msg)
                except Exception:
                    pass
                raise RuntimeError(f"Sarvam API Error (HTTP {response.status_code}): {error_msg}")

            data = response.json()
            choice = data.get("choices", [{}])[0]
            message = choice.get("message", {})
            finish_reason = choice.get("finish_reason")
            
            content = message.get("content")
            reasoning = message.get("reasoning_content")
            
            # If length finish_reason occurred and output was empty, retry with 8192 tokens
            if finish_reason == "length" and not (content or reasoning):
                payload["max_tokens"] = 8192
                retry_resp = requests.post(self.endpoint, headers=headers, json=payload, timeout=75)
                if retry_resp.status_code == 200:
                    data = retry_resp.json()
                    choice = data.get("choices", [{}])[0]
                    message = choice.get("message", {})
                    content = message.get("content")
                    reasoning = message.get("reasoning_content")

            # Prioritize content; if empty, fallback to reasoning_content
            raw_text = content if (content is not None and str(content).strip() != "") else reasoning
            if not raw_text:
                raise ValueError(
                    f"Model reached token limit during reasoning (finish_reason: '{choice.get('finish_reason')}'). "
                    "Try switching to 'sarvam-105b-conversations' in the sidebar or ask a simpler prompt."
                )

            result = self.clean_json_response(raw_text)

            # Ensure valid sql_query string
            sql_query = result.get("sql_query")
            if not sql_query or not isinstance(sql_query, str):
                sql_match = re.search(r"SELECT\s+[\s\S]+?(?=;|\n```|$)", str(raw_text), re.IGNORECASE)
                if sql_match:
                    sql_query = sql_match.group(0).strip()
                else:
                    raise ValueError(f"Model response did not contain a valid SQL query:\n{raw_text}")

            result["sql_query"] = str(sql_query).strip().rstrip(";")
            if reasoning:
                result["reasoning"] = reasoning

            if not result.get("explanation"):
                result["explanation"] = "Generated SQL based on question."
            if "visualization" not in result or not isinstance(result["visualization"], dict):
                result["visualization"] = {"recommended": True, "chart_type": "bar"}

            return result

        except requests.exceptions.RequestException as e:
            raise ConnectionError(f"Failed to communicate with Sarvam AI API: {str(e)}")
