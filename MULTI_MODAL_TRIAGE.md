# Multi-Modal Triage Feature Documentation

## Overview
The Multi-Modal Triage system uses Gemini 2.0 Flash to intelligently analyze patient symptoms and determine which medical documents are needed for accurate diagnosis. The system can now handle both imaging scans (for solid tumors) and blood work reports (for hematological conditions like leukemia).

## Architecture

### 1. New Triage Endpoint: POST /triage

**Purpose:** Analyzes patient symptoms and returns intelligent recommendations for required inputs.

**Request Format:**
```json
{
  "symptoms": "Patient's description of symptoms"
}
```

**Response Format:**
```json
{
  "success": true,
  "suspected_category": "Hematology",
  "required_files": ["blood_report_pdf"],
  "follow_up_questions": [
    "How long have you felt fatigued?",
    "Any recent infections?"
  ],
  "reasoning": "Brief explanation of why these inputs are needed"
}
```

**Example Use Cases:**

1. **Hematology Case:**
   - Input: "I've been feeling extremely fatigued, have unexplained bruising, and occasional fever"
   - Output: Suspected category = "Hematology", Required files = ["blood_report_pdf"]

2. **Oncology/Pulmonology Case:**
   - Input: "Persistent cough for 3 months, chest pain, shortness of breath"
   - Output: Suspected category = "Pulmonology/Oncology", Required files = ["imaging_scan"]

3. **Dermatology Case:**
   - Input: "I have a mole that has been changing color and growing"
   - Output: Suspected category = "Dermatology/Oncology", Required files = ["physical_photo"]

### 2. Updated Agent 1: The Extractor (extractor.py)

**Enhanced Capabilities:**

#### For Images (AMD MI300X with Qwen-VL):
- Analyzes medical imaging scans (X-Ray, CT, MRI)
- Extracts detailed visual descriptions
- Identifies anatomical structures and anomalies
- Uses existing AMD MI300X GPU pipeline

#### For PDFs (Gemini 2.0 Flash):
- Extracts structured data from blood work reports
- Parses hematology values (WBC, RBC, Hemoglobin, Platelets)
- Identifies blast cells (critical for leukemia detection)
- Extracts tumor markers (CEA, CA 19-9, PSA, etc.)
- Highlights abnormal values and their severity

**Key Extracted Data Points:**
- Complete Blood Count (CBC)
- Differential counts
- Blast cell percentage
- Chemistry panel values
- Tumor markers
- Reference ranges and deviations

### 3. Updated Agent 2: The Analyst (analyst.py)

**Multi-Modal Analysis:**

The Analyst now intelligently detects the input type and applies appropriate analysis:

#### Blood Work Analysis:
- Detects hematological malignancies (Leukemia)
- Analyzes CBC abnormalities
- Identifies blast cells and their significance
- Assesses risk based on lab values
- Recommends hematology referrals and bone marrow biopsies

**Leukemia Detection Criteria:**
- Elevated WBC count (>11,000/μL)
- Presence of blast cells (>5% indicates acute leukemia)
- Low hemoglobin (anemia)
- Low platelet count (thrombocytopenia)
- Abnormal differential counts

#### Imaging Analysis:
- Detects solid tumors
- Analyzes structural abnormalities
- Assesses tumor characteristics (size, location, density)
- Evaluates image quality
- Recommends imaging follow-ups and biopsies

### 4. Future-Proofing Fields

The report JSON now includes placeholder fields for upcoming features:

```json
{
  "nearby_specialists": [],
  "treatment_pathway": null
}
```

**Planned Features:**
- **nearby_specialists:** Will contain a list of relevant specialists (oncologists, hematologists) with contact information based on location
- **treatment_pathway:** Will provide a structured treatment plan based on diagnosis and stage

## API Response Structure

### Complete Analysis Response:
```json
{
  "success": true,
  "extractor_output": "Extracted text/values",
  "extractor_model": "Qwen/Qwen2-VL-7B-Instruct or gemini-2.5-flash",
  "report": {
    "image_type": "Blood Work / Pathology Report or X-Ray/CT/MRI",
    "body_region": "Systemic / Hematological or specific region",
    "image_quality": "N/A or Clear/Blurry",
    "findings": [
      {
        "category": "Hematology",
        "description": "Detailed findings",
        "severity": "Normal/Mild/Moderate/Severe/Critical"
      }
    ],
    "cancer_risk": {
      "risk_score": 75,
      "risk_level": "High",
      "suspected_type": "Acute Myeloid Leukemia or Lung Cancer",
      "stage": "Stage information if applicable",
      "reasoning": "Explanation based on findings"
    },
    "conditions": [
      {
        "name": "Leukemia or Tumor",
        "confidence": "high",
        "reasoning": "Based on specific values/observations"
      }
    ],
    "next_steps": [
      {
        "action": "Bone marrow biopsy or CT-guided biopsy",
        "reason": "To confirm diagnosis",
        "urgency": "Urgent"
      }
    ],
    "nearby_specialists": [],
    "treatment_pathway": null
  },
  "analyst_model": "gemini-2.5-flash",
  "analysis_type": "blood_work or imaging",
  "validation": { ... },
  "patient": { ... }
}
```

## Workflow Examples

### Example 1: Leukemia Detection Workflow

1. **Triage:**
   ```
   POST /triage
   { "symptoms": "Extreme fatigue, bruising, fever" }
   → Response: { "suspected_category": "Hematology", "required_files": ["blood_report_pdf"] }
   ```

2. **Analysis:**
   ```
   POST /analyze
   - Upload: Blood work PDF
   - Extractor: Extracts WBC=45,000, Blasts=25%, Hemoglobin=8.5
   - Analyst: Detects Acute Leukemia, Risk Score=85, Urgency=Immediate
   ```

### Example 2: Lung Cancer Detection Workflow

1. **Triage:**
   ```
   POST /triage
   { "symptoms": "Persistent cough, chest pain, weight loss" }
   → Response: { "suspected_category": "Pulmonology/Oncology", "required_files": ["imaging_scan"] }
   ```

2. **Analysis:**
   ```
   POST /analyze
   - Upload: Chest X-Ray
   - Extractor: Describes mass in right upper lobe
   - Analyst: Detects suspicious mass, Risk Score=70, Recommends CT scan
   ```

## Technical Implementation Details

### Models Used:
- **Triage:** Gemini 2.0 Flash (gemini-2.5-flash)
- **Image Extraction:** AMD MI300X with Qwen2-VL-7B-Instruct
- **PDF Extraction:** Gemini 2.0 Flash
- **Analysis:** Gemini 2.0 Flash
- **Validation:** Gemini 2.0 Flash

### File Type Detection:
The system automatically detects file types:
- `.pdf` → Blood work/pathology analysis
- `.jpg`, `.png`, `.jpeg`, etc. → Imaging analysis

### Error Handling:
- Graceful fallbacks for parsing errors
- Detailed error messages for debugging
- Validation layer ensures report quality

## Testing Recommendations

1. **Test with Blood Work PDFs:**
   - Normal CBC
   - Leukemia cases (high WBC, blasts present)
   - Anemia cases

2. **Test with Imaging Scans:**
   - Chest X-Rays with masses
   - CT scans with tumors
   - Normal scans

3. **Test Triage Endpoint:**
   - Various symptom descriptions
   - Edge cases (vague symptoms)
   - Multi-system symptoms

## Future Enhancements

1. **Specialist Matching:**
   - Integrate with healthcare provider databases
   - Location-based specialist recommendations
   - Availability and appointment scheduling

2. **Treatment Pathways:**
   - Evidence-based treatment protocols
   - Stage-specific recommendations
   - Clinical trial matching

3. **Multi-File Analysis:**
   - Combine blood work + imaging
   - Longitudinal analysis (compare multiple reports over time)
   - Comprehensive patient profiles

4. **Real-time Monitoring:**
   - Track lab value trends
   - Alert on critical changes
   - Predictive analytics

## Security & Privacy

- All patient data is processed securely
- No data is stored permanently without consent
- HIPAA compliance considerations
- Encrypted data transmission

## Deployment Notes

- Ensure AMD MI300X endpoint is accessible
- Verify GCP credentials for Gemini API
- Set appropriate timeout values for large PDFs
- Monitor API usage and costs

---

**Version:** 2.0  
**Last Updated:** 2026-05-08  
**Powered by:** Gemini 2.0 Flash, AMD MI300X, Qwen2-VL