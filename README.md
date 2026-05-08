# MediScan AI - Multi-Modal Medical Analysis Platform

## 🚀 Overview

MediScan AI is an advanced medical analysis platform that combines AMD MI300X GPU acceleration with Google's Gemini 2.0 Flash AI to provide intelligent triage and comprehensive analysis of medical scans and blood work reports.

### Key Features

- **🎯 Smart Multi-Modal Triage**: Analyzes symptoms and recommends required medical documents
- **🔬 Blood Work Analysis**: Detects hematological conditions including Leukemia
- **🏥 Medical Imaging Analysis**: Identifies solid tumors and structural abnormalities
- **⚡ AMD MI300X Acceleration**: High-performance image analysis with Qwen2-VL
- **🤖 Gemini 2.0 Flash Integration**: Advanced AI-powered medical insights
- **📊 Comprehensive Reporting**: Detailed clinical reports with risk assessment

## 🏗️ Architecture

### Three-Agent System

1. **Agent 1: The Extractor**
   - Processes medical images using AMD MI300X (Qwen2-VL)
   - Extracts clinical data from PDF blood reports using Gemini
   - Identifies key values, anomalies, and structures

2. **Agent 2: The Analyst**
   - Generates comprehensive clinical reports
   - Detects Leukemia from blood values
   - Identifies solid tumors from imaging scans
   - Provides risk assessment and staging

3. **Agent 3: The Validator**
   - Validates report accuracy and completeness
   - Ensures clinical reliability
   - Provides confidence scores

## 🆕 Multi-Modal Triage Feature

The new triage system intelligently determines which medical documents are needed based on patient symptoms.

### Supported Analysis Types

| Category | Input Type | Detects |
|----------|-----------|---------|
| **Hematology** | Blood Work PDF | Leukemia, Anemia, Blood disorders |
| **Oncology (Solid)** | Imaging Scans | Lung, Breast, Bone tumors |
| **Pulmonology** | Chest X-Ray/CT | Lung masses, Pneumonia |
| **Dermatology** | Physical Photos | Skin lesions, Melanoma |

### API Endpoints

#### 1. POST /triage
Analyzes symptoms and recommends required inputs.

**Request:**
```json
{
  "symptoms": "Extreme fatigue, unexplained bruising, fever"
}
```

**Response:**
```json
{
  "success": true,
  "suspected_category": "Hematology",
  "required_files": ["blood_report_pdf"],
  "follow_up_questions": [
    "How long have you felt fatigued?",
    "Any recent infections?"
  ],
  "reasoning": "Symptoms suggest hematological investigation needed"
}
```

#### 2. POST /analyze
Performs comprehensive medical analysis.

**Request:**
- `scan_image`: Medical image or PDF file
- `patient_name`: Patient name (optional)
- `age`: Patient age (optional)
- `symptoms`: Symptom description (optional)
- Additional patient metadata

**Response:**
```json
{
  "success": true,
  "extractor_output": "Extracted findings...",
  "report": {
    "image_type": "Blood Work / Pathology Report",
    "body_region": "Systemic / Hematological",
    "findings": [...],
    "cancer_risk": {
      "risk_score": 85,
      "risk_level": "High",
      "suspected_type": "Acute Myeloid Leukemia",
      "reasoning": "Elevated WBC with 25% blast cells"
    },
    "conditions": [...],
    "next_steps": [...],
    "nearby_specialists": [],
    "treatment_pathway": null
  },
  "validation": {...}
}
```

#### 3. POST /chat
Interactive chat for report clarification.

#### 4. GET /health
System health check.

## 🔧 Setup & Installation

### Prerequisites

- Python 3.8+
- AMD MI300X GPU access (for image analysis)
- Google Cloud Platform account with Vertex AI enabled
- GCP Service Account credentials

### Installation Steps

1. **Clone the repository:**
```bash
git clone <repository-url>
cd amd_hackaton
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Configure environment variables:**
Create a `.env` file:
```env
GOOGLE_APPLICATION_CREDENTIALS="credentials/gcp-key.json"
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1
VISION_MODE=amd
AMD_ENDPOINT=http://your-amd-endpoint:8000
FLASK_PORT=5000
```

4. **Add GCP credentials:**
Place your service account JSON key in `credentials/gcp-key.json`

5. **Run the application:**
```bash
python app.py
```

The server will start on `http://localhost:5000`

## 📖 Documentation

- **[Multi-Modal Triage Guide](MULTI_MODAL_TRIAGE.md)**: Comprehensive documentation of the triage system
- **[Setup Guide](SETUP_GUIDE.md)**: Detailed setup instructions
- **[Deployment Guide](DEPLOYMENT.md)**: Production deployment instructions

## 🧪 Testing

### Test Blood Work Analysis

```bash
curl -X POST http://localhost:5000/analyze \
  -F "scan_image=@blood_report.pdf" \
  -F "symptoms=Fatigue and bruising"
```

### Test Imaging Analysis

```bash
curl -X POST http://localhost:5000/analyze \
  -F "scan_image=@chest_xray.jpg" \
  -F "symptoms=Persistent cough"
```

### Test Triage

```bash
curl -X POST http://localhost:5000/triage \
  -H "Content-Type: application/json" \
  -d '{"symptoms": "Extreme fatigue, unexplained bruising, fever"}'
```

## 🎯 Use Cases

### 1. Leukemia Detection
- Upload blood work PDF
- System extracts WBC, blast cells, hemoglobin
- Detects acute/chronic leukemia
- Recommends bone marrow biopsy

### 2. Lung Cancer Screening
- Upload chest X-Ray or CT scan
- System identifies masses and nodules
- Assesses malignancy risk
- Recommends follow-up imaging

### 3. Comprehensive Health Assessment
- Start with symptom triage
- Upload recommended documents
- Receive detailed analysis
- Get specialist referrals

## 🔮 Future Enhancements

- **Specialist Matching**: Location-based specialist recommendations
- **Treatment Pathways**: Evidence-based treatment protocols
- **Longitudinal Analysis**: Track changes over time
- **Multi-File Analysis**: Combine blood work + imaging
- **Clinical Trial Matching**: Connect patients with relevant trials

## 🛡️ Security & Privacy

- All data processed securely
- No permanent storage without consent
- HIPAA compliance considerations
- Encrypted data transmission

## 🤝 Technology Stack

- **Backend**: Flask (Python)
- **AI Models**: 
  - Gemini 2.0 Flash (Google Vertex AI)
  - Qwen2-VL-7B-Instruct (AMD MI300X)
- **GPU**: AMD MI300X
- **Cloud**: Google Cloud Platform

## 📊 Performance

- **Image Analysis**: ~2-5 seconds
- **PDF Extraction**: ~3-7 seconds
- **Report Generation**: ~5-10 seconds
- **Total Pipeline**: ~10-20 seconds

## 🐛 Troubleshooting

### Common Issues

1. **AMD Endpoint Connection Failed**
   - Verify AMD_ENDPOINT in .env
   - Check network connectivity
   - Ensure endpoint is running

2. **GCP Authentication Error**
   - Verify credentials file path
   - Check service account permissions
   - Ensure Vertex AI API is enabled

3. **PDF Extraction Failed**
   - Ensure PDF is not password-protected
   - Check file size (<10MB recommended)
   - Verify PDF contains text/tables

## 📝 License

[Your License Here]

## 👥 Contributors

Built with ❤️ using AMD MI300X and Google Gemini 2.0 Flash

## 📧 Contact

For questions or support, please open an issue on GitHub.

---

**Version**: 2.0  
**Last Updated**: 2026-05-08  
**Status**: Production Ready ✅