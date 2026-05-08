import os
import json
from extractor import extract_from_image
from analyst import analyze_scan
from validator import validate_report

def main():
    print("Testing Pipeline...")
    
    # 1. Load test image
    image_path = "original.jpg"
    if not os.path.exists(image_path):
        print("Test image original.jpg not found!")
        return
        
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    # 2. Test Extractor (AMD GPU)
    print("\n--- Testing Extractor (Qwen2-VL on AMD MI300X) ---")
    extract_result = extract_from_image(image_bytes)
    if extract_result["success"]:
        print("Success! Extracted text length:", len(extract_result["extracted_text"]))
        print("Preview:", extract_result["extracted_text"][:200], "...")
    else:
        print("Extractor Failed:", extract_result.get("error"))
        return
        
    # 3. Test Analyst (Gemini)
    print("\n--- Testing Analyst (Gemini-2.5-flash) ---")
    patient_data = {"patient_name": "Test User", "age": 45, "gender": "Male"}
    analyze_result = analyze_scan(image_bytes, extract_result["extracted_text"], patient_data)
    
    if analyze_result["success"]:
        print("Success! Report keys:", analyze_result["report"].keys())
        report = analyze_result["report"]
    else:
        print("Analyst Failed:", analyze_result.get("error"))
        return
        
    # 4. Test Validator (Gemini)
    print("\n--- Testing Validator (Gemini-2.5-flash) ---")
    validate_result = validate_report(report)
    
    if validate_result["success"]:
        print("Success! Validation score:", validate_result["validation"].get("reliability_score"))
        print("Verdict:", validate_result["validation"].get("verdict"))
    else:
        print("Validator Failed:", validate_result.get("error"))

if __name__ == "__main__":
    main()
