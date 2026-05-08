"""
MediScan AI - Flask Backend
Main application server with REST API endpoints for medical scan analysis.
"""

import os
import json
from flask import Flask, request, jsonify, send_from_directory, Response
from flask_cors import CORS
import traceback
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

# Import our agents
from extractor import extract_from_image, extract_from_pdf
from analyst import analyze_scan
from validator import validate_report, quick_validate

# Load environment variables
load_dotenv()
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.getenv(
    'GOOGLE_APPLICATION_CREDENTIALS', 'credentials.json'
)

client = genai.Client(
    vertexai=True,
    project='electvoice',
    location='us-central1'
)

# Initialize Flask app
app = Flask(__name__, static_folder='static')
CORS(app)  # Enable CORS for all routes

# Configuration
FLASK_PORT = int(os.getenv('FLASK_PORT', 5000))
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
VISION_MODE = os.getenv('VISION_MODE', 'amd')

# Allowed file extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff', 'pdf', 'dcm'}


def allowed_file(filename):
    """Check if file extension is allowed."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    """Serve the main HTML page."""
    return send_from_directory('static', 'index.html')


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    Returns system status and configuration.
    """
    return jsonify({
        "status": "ok",
        "vision_mode": VISION_MODE,
        "gemini_model": "gemini-2.5-flash",
        "amd_endpoint": os.getenv("AMD_ENDPOINT"),
        "version": "1.0.0"
    })


@app.route('/triage', methods=['POST'])
def triage():
    """
    Multi-Modal Triage endpoint using Gemini 2.0 Flash.
    Analyzes symptoms and returns which inputs are needed for diagnosis.
    """
    try:
        data = request.get_json()
        if not data or 'symptoms' not in data:
            return jsonify({"success": False, "error": "No symptoms provided"}), 400
            
        symptoms = data['symptoms']
        
        prompt = f"""You are MediScan AI Multi-Modal Triage System powered by Gemini 2.0 Flash.

Analyze the patient's symptoms and determine:
1. The suspected medical category (Hematology, Oncology, Cardiology, Pulmonology, Dermatology, etc.)
2. Which file types are required for proper diagnosis
3. Any follow-up questions needed for better assessment
4. Suggested quick reply options for the follow-up question

Patient Symptoms: "{symptoms}"

Respond ONLY with valid JSON in this exact structure (no markdown formatting):
{{
  "suspected_category": "string (e.g., Hematology, Oncology, Cardiology)",
  "required_files": ["array of strings: blood_report_pdf, imaging_scan, physical_photo"],
  "follow_up_questions": ["array of strings with specific questions to ask the patient"],
  "suggested_answers": ["array of 3-4 short suggested answers for the follow-up question"],
  "reasoning": "Brief explanation of why these inputs are needed"
}}

Examples:
- Fatigue, bruising → {{"follow_up_questions": ["How long have you felt fatigued?"], "suggested_answers": ["Less than a week", "1-2 weeks", "2-4 weeks", "More than a month"]}}
- Joint pain → {{"follow_up_questions": ["Is the pain constant or does it come and go?"], "suggested_answers": ["Constant pain", "Comes and goes", "Only when moving", "Worse at night"]}}
- Persistent cough → {{"follow_up_questions": ["Do you smoke or have you smoked in the past?"], "suggested_answers": ["Yes, currently smoke", "Former smoker", "Never smoked", "Exposed to secondhand smoke"]}}
"""

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        result_text = response.text.strip()
        if result_text.startswith("```json"):
            result_text = result_text[7:]
        if result_text.endswith("```"):
            result_text = result_text[:-3]
            
        import json
        triage_data = json.loads(result_text.strip())
        
        return jsonify({
            "success": True,
            "suspected_category": triage_data.get("suspected_category", "General"),
            "required_files": triage_data.get("required_files", ["imaging_scan"]),
            "follow_up_questions": triage_data.get("follow_up_questions", []),
            "suggested_answers": triage_data.get("suggested_answers", []),
            "reasoning": triage_data.get("reasoning", "")
        })
    except Exception as e:
        print(f"[TRIAGE ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Main analysis endpoint with real-time streaming progress updates.
    Accepts medical scan images and patient data, processes through all three agents.
    """
    # Extract all request data BEFORE entering the generator
    # (request context is not available inside generator)
    try:
        # Check if at least one file is present
        if 'scan_image' not in request.files and 'scan_document' not in request.files:
            return jsonify({"success": False, "error": "No files provided. Please upload an image or document."}), 400
        
        # Collect patient data from form
        patient_data = {
            'patient_name': request.form.get('patient_name'),
            'age': request.form.get('age'),
            'gender': request.form.get('gender'),
            'blood_type': request.form.get('blood_type'),
            'scan_type': request.form.get('scan_type'),
            'body_region': request.form.get('body_region'),
            'known_conditions': request.form.get('known_conditions'),
            'symptoms': request.form.get('symptoms'),
            'smoking': request.form.get('smoking'),
            'alcohol': request.form.get('alcohol'),
            'family_history': request.form.get('family_history')
        }
        
        # Remove None values
        patient_data = {k: v for k, v in patient_data.items() if v is not None and v != ''}
        
        # Read files into memory
        main_image_bytes = None
        pdf_bytes = None
        
        if 'scan_image' in request.files:
            scan_file = request.files['scan_image']
            if scan_file.filename != '' and allowed_file(scan_file.filename):
                main_image_bytes = scan_file.read()
        
        if 'scan_document' in request.files:
            doc_file = request.files['scan_document']
            if doc_file.filename != '' and doc_file.filename.lower().endswith('.pdf'):
                pdf_bytes = doc_file.read()
                
    except Exception as e:
        return jsonify({"success": False, "error": f"Request processing error: {str(e)}"}), 400
    
    # Now define the generator with all data captured
    def generate():
        try:
            extracted_text_combined = ""
            
            # Notify extraction start
            yield json.dumps({"status": "extracting", "message": "Agent 1 Processing — Extracting visual features..."}) + "\n"
            
            if main_image_bytes:
                print(f"[EXTRACTOR] Processing image with {VISION_MODE} mode...")
                extractor_result = extract_from_image(main_image_bytes)
                if not extractor_result['success']:
                    yield json.dumps({"success": False, "error": f"Image Extractor failed: {extractor_result.get('error')}", "agent": "extractor"}) + "\n"
                    return
                extracted_text_combined += f"--- Imaging Scan Findings ---\n{extractor_result['extracted_text']}\n\n"
            
            if pdf_bytes:
                print(f"[EXTRACTOR] Processing PDF with Gemini...")
                extractor_result = extract_from_pdf(pdf_bytes)
                if not extractor_result['success']:
                    yield json.dumps({"success": False, "error": f"PDF Extractor failed: {extractor_result.get('error')}", "agent": "extractor"}) + "\n"
                    return
                extracted_text_combined += f"--- Medical Document / Blood Work Findings ---\n{extractor_result['extracted_text']}\n\n"
            
            if not extracted_text_combined:
                yield json.dumps({"success": False, "error": "Could not extract information from the uploaded files."}) + "\n"
                return
                
            print(f"[EXTRACTOR] Successfully extracted information")
            
            # Notify analysis start
            yield json.dumps({"status": "analyzing", "message": "Agent 2 Processing — Generating clinical report..."}) + "\n"
            
            # STEP 2: Analyze the extracted information (multimodal now)
            print("[ANALYST] Generating medical report...")
            analyst_result = analyze_scan(main_image_bytes if main_image_bytes else b'', extracted_text_combined, patient_data if patient_data else None)
            
            if not analyst_result['success']:
                yield json.dumps({"success": False, "error": f"Analyst failed: {analyst_result.get('error')}", "agent": "analyst"}) + "\n"
                return
            
            report = analyst_result['report']
            print("[ANALYST] Successfully generated report")
            
            # Notify validation start
            yield json.dumps({"status": "validating", "message": "Agent 3 Processing — Validating report..."}) + "\n"
            
            # STEP 3: Validate the report
            print("[VALIDATOR] Validating report...")
            validator_result = validate_report(report)
            
            if not validator_result['success']:
                # If AI validation fails, fall back to structural validation
                print(f"[VALIDATOR] AI Validation failed: {validator_result.get('error')}")
                print("[VALIDATOR] Falling back to structural validation...")
                fallback_result = quick_validate(report)
                validation = fallback_result['validation']
            else:
                validation = validator_result['validation']
                print(f"[VALIDATOR] Validation complete - Score: {validation['reliability_score']}/10")
            
            # Send final complete response
            response_data = {
                "success": True,
                "status": "complete",
                "extractor_output": extracted_text_combined,
                "extractor_model": "multimodal",
                "report": report,
                "analyst_model": analyst_result.get('model_used'),
                "validation": validation,
                "validator_model": validator_result.get('model_used'),
                "patient": patient_data if patient_data else None
            }
            
            yield json.dumps(response_data) + "\n"
        
        except Exception as e:
            print(f"[ERROR] {str(e)}")
            traceback.print_exc()
            yield json.dumps({
                "success": False,
                "error": f"Server error: {str(e)}",
                "agent": "server"
            }) + "\n"

    return Response(generate(), mimetype='application/x-ndjson')


@app.route('/chat', methods=['POST'])
def chat():
    """
    Chat endpoint for conversational interaction.
    """
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({
                "success": False,
                "error": "No message provided"
            }), 400
        
        user_message = data['message']
        report_context = data.get('report_context', '')
        
        # Build the chat prompt
        system_prompt = """You are MediScan AI, a compassionate and knowledgeable medical assistant. Your role is to help patients understand their medical reports in a clear, detailed, and empathetic way.

Guidelines:
1. BE DETAILED AND THOROUGH: Provide comprehensive explanations that help users truly understand their condition. Don't be overly brief - patients deserve complete information.

2. BE EMPATHETIC AND SUPPORTIVE: Use a warm, caring tone. Acknowledge that medical results can be concerning and provide reassurance where appropriate.

3. EXPLAIN MEDICAL TERMS: Break down complex medical terminology into simple language. Help users understand what findings mean in practical terms.

4. PROVIDE CONTEXT: When discussing findings, explain:
   - What the condition is
   - What it means for the patient
   - Common treatment approaches (general information)
   - What next steps typically involve
   - Prognosis factors (in general terms)

5. STRUCTURE YOUR RESPONSES: Organize information logically with clear sections (but NO MARKDOWN - use plain text with line breaks for readability).

6. BE HONEST: If something is serious, acknowledge it compassionately. If prognosis varies, explain the factors involved.

7. ENCOURAGE PROFESSIONAL CONSULTATION: Always remind users to discuss specifics with their healthcare team, but provide enough information to help them prepare for those conversations.

8. NO MARKDOWN: Use plain text only. No asterisks, bold, bullets, or special formatting. Use line breaks and clear language for structure.

Remember: Patients are often scared and confused. Your job is to educate, support, and empower them while being honest about the importance of professional medical care."""

        # Combine context and message
        if report_context:
            full_prompt = f"{system_prompt}\n\nCurrent Report Context:\n{report_context}\n\nUser Question: {user_message}\n\nProvide a helpful, clear response:"
        else:
            full_prompt = f"{system_prompt}\n\nUser Question: {user_message}\n\nProvide a helpful, clear response:"
        
        # Generate response using Gemini API
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=full_prompt
        )
        reply = response.text.strip()
        
        return jsonify({
            "success": True,
            "reply": reply,
            "model": "gemini-2.5-flash"
        })
    
    except Exception as e:
        print(f"[CHAT ERROR] {str(e)}")
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Chat error: {str(e)}"
        }), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify({"success": False, "error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({"success": False, "error": "Internal server error"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=FLASK_PORT, debug=FLASK_DEBUG)

# Made with Bob
