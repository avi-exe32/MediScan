"""
Agent 3: Validator
Provides a safety, reliability, and sanity check on the generated clinical report.
"""

import os
import json
from typing import Dict, Any
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv(
    'GOOGLE_APPLICATION_CREDENTIALS', 'credentials/gcp-key.json'
)

client = genai.Client(
    vertexai=True,
    project='electvoice',
    location='us-central1'
)

VALIDATOR_PROMPT = """You are CancerLens AI's Chief Medical Officer (Agent 3 - Validator).
Your job is to independently review the AI-generated medical report for safety, consistency, and reliability before it is shown to the user.

Review the JSON report provided and perform the following checks:
1. Contradictions: Do the findings contradict the final diagnosis?
2. Severity mismatch: Is a critical finding marked as low risk, or a benign finding marked as high risk?
3. Unrealistic confidence: Are diagnoses too confident without definitive proof?
4. Missing disclaimers: Does the report suggest taking action without consulting a doctor?
5. Formatting: Is the JSON structure exactly correct?

Generate your validation report in valid JSON format ONLY. Do not include markdown formatting.
Adhere to this exact structure:

{
  "reliability_score": integer (0-10, where 10 is perfect/safe),
  "verdict": "string (Pass / Pass with Warning / Fail - Needs Review)",
  "validator_note": "string (A brief summary of your review)",
  "flags": [
    "string (Any specific contradictions or safety warnings found)"
  ]
}
"""


def validate_report(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validates the generated medical report.
    """
    try:
        report_json = json.dumps(report_data, indent=2)
        full_prompt = f"{VALIDATOR_PROMPT}\n\n=== MEDICAL REPORT TO VALIDATE ===\n{report_json}\n\nGenerate the validation report in JSON format:"
        
        # Generate the validation
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        
        validation_text = response.text.strip()
        
        # Strip markdown
        if validation_text.startswith("```json"):
            validation_text = validation_text[7:]
        if validation_text.endswith("```"):
            validation_text = validation_text[:-3]
            
        validation_text = validation_text.strip()
        
        try:
            validation_data = json.loads(validation_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse validation as JSON: {str(e)}")
            
        return {
            "success": True,
            "validation": validation_data,
            "model_used": "gemini-2.5-flash"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model_used": "gemini-2.5-flash"
        }


def quick_validate(report_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Fallback structural validation if AI validation fails.
    """
    flags = []
    score = 10
    verdict = "Pass"
    
    if not isinstance(report_data, dict):
        return {
            "success": True,
            "validation": {
                "reliability_score": 0,
                "verdict": "Fail - Invalid Format",
                "validator_note": "Report is not a valid object.",
                "flags": ["Format Error"]
            }
        }
        
    if "cancer_risk" not in report_data:
        flags.append("Missing cancer risk assessment")
        score -= 5
        verdict = "Fail - Needs Review"
        
    if "findings" not in report_data or not report_data["findings"]:
        flags.append("No findings reported")
        score -= 3
        if verdict == "Pass": verdict = "Pass with Warning"
        
    if score < 5:
        verdict = "Fail - Needs Review"
        
    return {
        "success": True,
        "validation": {
            "reliability_score": score,
            "verdict": verdict,
            "validator_note": "Validation performed via structural fallback. AI validation was unavailable.",
            "flags": flags
        }
    }

# Made with Bob
