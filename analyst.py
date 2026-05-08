"""
Agent 2: Analyst
Generates clinical reports from extracted information and patient data using Gemini API.
"""

import os
import json
from typing import Dict, Any, Optional
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv(
    'GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json'
)

client = genai.Client(
    vertexai=True,
    project='electvoice',
    location='us-central1'
)

def analyze_report(image_bytes: bytes, extractor_text: str, patient_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Multi-Modal Analysis function for generating medical reports.
    Handles BOTH imaging scans AND blood work/pathology data.
    Can detect Leukemia (from blood values) or Solid Tumors (from scans).
    """
    try:
        patient_context = ""
        if patient_data:
            patient_context = json.dumps(patient_data, indent=2)
        else:
            patient_context = "No patient data provided."
            
        prompt = f"""
You are MediScan AI, an expert medical imaging analyst, hematologist, and oncologist.
Analyze the provided medical data, which may include visual descriptions from imaging scans, blood work/pathology data, or both.
Focus on detecting SOLID TUMORS, HEMATOLOGICAL MALIGNANCIES (like Leukemia), and structural abnormalities.

Extracted Data / Vision AI raw description:
{extractor_text}

Patient context:
{patient_context}

CRITICAL FOR BLOOD WORK:
- Look for elevated WBC count (>11,000/μL), presence of blast cells, low hemoglobin, and low platelets.
CRITICAL FOR SCANS:
- Look for tumors, lesions, or aggressive structural abnormalities.

Generate a comprehensive clinical report in valid JSON format ONLY. Do not include markdown formatting or backticks.
The JSON must adhere to this exact structure:

{{
  "image_type": "string (e.g. X-Ray / Blood Work / Combined)",
  "body_region": "string",
  "image_quality": "string (Clear/Blurry/N/A)",
  "findings": [
    {{
      "category": "string",
      "description": "string",
      "severity": "string (Normal/Mild/Moderate/Severe/Critical)"
    }}
  ],
  "cancer_risk": {{
    "risk_score": integer (0-100),
    "risk_level": "string (Low/Moderate/High/Critical)",
    "suspected_type": "string (e.g., Lung Cancer, Leukemia, or None)",
    "stage": "string (if applicable, or None)",
    "reasoning": "string"
  }},
  "conditions": [
    {{
      "name": "string",
      "confidence": "string (low/medium/high)",
      "reasoning": "string"
    }}
  ],
  "next_steps": [
    {{
      "action": "string",
      "reason": "string",
      "urgency": "string (Routine/Soon/Urgent/Immediate)"
    }}
  ],
  "nearby_specialists": [],
  "treatment_pathway": null
}}
"""
        contents = []
        if image_bytes and len(image_bytes) > 0:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg")
            contents.append(image_part)
            
        contents.append(prompt)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents
        )
        
        report_text = response.text.strip() if response.text else "{}"
        
        # Strip markdown formatting if the model still includes it
        if report_text.startswith("```json"):
            report_text = report_text[7:]
        if report_text.endswith("```"):
            report_text = report_text[:-3]
            
        report_text = report_text.strip()
        
        # Parse the JSON
        try:
            report_data = json.loads(report_text)
            
            # Ensure future-proofing fields exist
            if "nearby_specialists" not in report_data:
                report_data["nearby_specialists"] = []
            if "treatment_pathway" not in report_data:
                report_data["treatment_pathway"] = None
                
        except json.JSONDecodeError as e:
            # Fallback if json parsing fails
            raise ValueError(f"Failed to parse generated report as JSON. Raw output: {report_text[:100]}... Error: {str(e)}")
            
        return {
            "success": True,
            "report": report_data,
            "model_used": "gemini-2.5-flash",
            "analysis_type": "multimodal"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model_used": "gemini-2.5-flash"
        }

# Wrapper for app.py
def analyze_scan(image_bytes: bytes, extracted_text: str, patient_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    return analyze_report(image_bytes, extracted_text, patient_data)

# Made with Bob
