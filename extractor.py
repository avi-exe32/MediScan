"""
Agent 1: Extractor
Extracts visual information from medical scans using AMD MI300X GPU with Qwen2-VL model.
"""

import os
import base64
import requests
from typing import Dict, Any
from dotenv import load_dotenv
import google.genai as genai
from google.genai import types

# Load environment variables
load_dotenv()


def extract_image(image_bytes: bytes) -> str:
    """
    Extract information using AMD MI300X endpoint with Qwen2-VL model.
    """
    # Convert image to base64
    image_b64 = base64.b64encode(image_bytes).decode("utf-8")
    
    endpoint = os.getenv("AMD_ENDPOINT", "http://134.199.200.40:8000")
    
    payload = {
        "model": "Qwen/Qwen2-VL-7B-Instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_b64}"
                        }
                    },
                    {
                        "type": "text",
                        "text": """You are a medical imaging analysis AI with 
expertise in radiology and diagnostic imaging.

Analyze this medical image thoroughly and describe 
EVERYTHING you observe.

Describe:
1. Image type and quality (X-ray, MRI, CT scan, ultrasound)
2. Body region visible
3. Any visible structures — bones, organs, tissue, vessels
4. Any anomalies — masses, shadows, opacities, lesions, 
   irregularities, calcifications
5. Size estimates if visible
6. Location of anomalies (left/right, upper/lower)
7. Texture and density of suspicious areas
8. Anything abnormal compared to healthy anatomy

Be extremely detailed. Do not diagnose — only observe.
Output as plain paragraph text."""
                    }
                ]
            }
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    
    response = requests.post(
        f"{endpoint}/v1/chat/completions",
        json=payload,
        timeout=60
    )
    
    result = response.json()
    return result["choices"][0]["message"]["content"]


def extract_from_image(image_bytes: bytes) -> Dict[str, Any]:
    """
    Wrapper for app.py compatibility.
    """
    try:
        extracted_text = extract_image(image_bytes)
        return {
            "success": True,
            "extracted_text": extracted_text,
            "model_used": "Qwen/Qwen2-VL-7B-Instruct",
            "vision_mode": "amd"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model_used": None,
            "vision_mode": "amd"
        }


def extract_from_pdf(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Extract clinical values from PDF (Blood Reports, Pathology) using Gemini 2.0 Flash.
    Enhanced for hematology and oncology data extraction.
    """
    try:
        client = genai.Client(
            vertexai=True,
            project='electvoice',
            location='us-central1'
        )
        pdf_part = types.Part.from_bytes(
            data=pdf_bytes,
            mime_type="application/pdf"
        )
        prompt = """You are a medical data extraction specialist with expertise in hematology and pathology reports.

Extract ALL key clinical values from this blood work/pathology report. Focus on:

HEMATOLOGY VALUES:
- Complete Blood Count (CBC): WBC, RBC, Hemoglobin, Hematocrit, Platelets
- Differential: Neutrophils, Lymphocytes, Monocytes, Eosinophils, Basophils
- Blast Cells percentage (critical for leukemia detection)
- Abnormal cell morphology

CHEMISTRY PANEL:
- Liver function: ALT, AST, Bilirubin
- Kidney function: Creatinine, BUN
- Electrolytes: Sodium, Potassium, Chloride

TUMOR MARKERS (if present):
- CEA, CA 19-9, CA 125, PSA, AFP, etc.

OTHER FINDINGS:
- Any flagged abnormal values (marked with H/L or *)
- Reference ranges and deviations
- Critical values or panic values

Provide a structured text summary with:
1. All numeric values with units
2. Highlight abnormal values and their severity
3. Any diagnostic impressions or notes from the report
4. Date of test if available

Format as clear, organized text (not JSON). Be thorough and precise."""
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=[pdf_part, prompt]
        )
        
        extracted = response.text.strip() if response.text else "No data extracted"
        
        return {
            "success": True,
            "extracted_text": extracted,
            "model_used": "gemini-2.5-flash",
            "vision_mode": "gemini-pdf",
            "file_type": "blood_report_pdf"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "model_used": "gemini-2.5-flash",
            "vision_mode": "gemini-pdf",
            "file_type": "blood_report_pdf"
        }

if __name__ == "__main__":
    # Quick connection test
    import requests
    endpoint = "http://134.199.200.40:8000"
    try:
        r = requests.get(f"{endpoint}/v1/models", timeout=10)
        print("[SUCCESS] AMD MI300X connected:", r.json())
    except Exception as e:
        print("[ERROR] Connection failed:", e)

# Made with Bob
