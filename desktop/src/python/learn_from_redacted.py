"""
Learn from Redacted Documents using Gemini Vision
Detects black boxes and infers entity types from context
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
import base64
import google.generativeai as genai
from pdf2image import convert_from_path
import io

class RedactedDocumentLearner:
    """
    Analyzes already-redacted documents to learn redaction patterns.
    Uses Gemini Vision to detect black boxes and classify field types.
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize with Gemini API key"""
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')

    def pdf_to_image_base64(self, pdf_path: str, page_num: int = 0) -> str:
        """Convert PDF page to base64 image"""
        images = convert_from_path(pdf_path, first_page=page_num+1, last_page=page_num+1, dpi=200)

        if not images:
            raise ValueError(f"Could not convert PDF page {page_num}")

        # Convert to PNG bytes
        img_buffer = io.BytesIO()
        images[0].save(img_buffer, format='PNG')
        img_bytes = img_buffer.getvalue()

        # Encode to base64
        return base64.b64encode(img_bytes).decode('utf-8')

    def analyze_redacted_document(self, pdf_path: str, page_num: int = 0) -> Dict[str, Any]:
        """
        Analyze a redacted document to find redacted regions.

        Args:
            pdf_path: Path to redacted PDF
            page_num: Page number to analyze (0-indexed)

        Returns:
            {
                "status": "success",
                "regions": [
                    {
                        "bbox": [x, y, width, height],  # Normalized 0-1
                        "inferred_type": "PERSON",
                        "context": "appears after 'Tenant:' label",
                        "confidence": 0.95
                    }
                ]
            }
        """
        print(f"[RedactedLearner] Analyzing: {pdf_path}")

        try:
            # Convert PDF to image
            image_base64 = self.pdf_to_image_base64(pdf_path, page_num)

            # Create prompt for Gemini Vision
            prompt = """You are a privacy expert analyzing a REDACTED document.

Your task: Find ALL redacted regions (areas where sensitive information has been hidden).

Look for:
1. **Black rectangles** covering text
2. **White boxes** covering text
3. **Blurred areas**
4. **[REDACTED]** or similar placeholder text
5. **Solid colored boxes** over text

For EACH redacted region you find:
1. Measure its position and size (as percentage of page: 0.0 to 1.0)
2. Read the surrounding text to understand WHAT was redacted
3. Classify the entity type based on context

**Entity Types:**
- PERSON: Names of people
- SSN: Social Security Numbers (format: XXX-XX-XXXX)
- PHONE: Phone numbers
- EMAIL: Email addresses
- ADDRESS: Street addresses, cities
- DATE: Dates (birth dates, agreement dates)
- FINANCIAL: Bank accounts, amounts, income
- ORGANIZATION: Company names
- LICENSE: License numbers, IDs

**Output Format** (JSON only, no explanation):
{
  "regions": [
    {
      "bbox": [x, y, width, height],
      "inferred_type": "PERSON",
      "context": "appears after 'Landlord:' label on line 5",
      "confidence": 0.95,
      "surrounding_text": "Landlord: [REDACTED]"
    }
  ]
}

**Important:**
- bbox values are 0.0 to 1.0 (percentage of page dimensions)
- x, y = top-left corner
- Be thorough - find EVERY redacted area
- If multiple fields are close together, separate them
- Higher confidence for clear context (e.g., "SSN:" label)

Analyze this redacted document:"""

            # Upload image and analyze
            image_part = {
                'mime_type': 'image/png',
                'data': image_base64
            }

            response = self.model.generate_content(
                [prompt, image_part],
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            # Parse response
            result = json.loads(response.text)

            print(f"[RedactedLearner] Found {len(result.get('regions', []))} redacted regions")

            return {
                "status": "success",
                "regions": result.get("regions", []),
                "page": page_num,
                "source_file": pdf_path
            }

        except Exception as e:
            print(f"[RedactedLearner] Error: {e}")
            return {
                "status": "error",
                "error": str(e),
                "regions": []
            }

    def save_template(self, regions: List[Dict], template_name: str, output_dir: str = "templates") -> Dict[str, Any]:
        """
        Save learned template for future use.

        Args:
            regions: List of region dicts from analyze_redacted_document
            template_name: Name for this template
            output_dir: Directory to save template

        Returns:
            {"status": "success", "template_path": "..."}
        """
        try:
            # Create output directory
            Path(output_dir).mkdir(exist_ok=True)

            template = {
                "template_id": f"template_{template_name}",
                "name": template_name,
                "regions": regions,
                "created_at": str(Path(__file__).stat().st_mtime)
            }

            output_path = Path(output_dir) / f"{template_name}.json"

            with open(output_path, 'w') as f:
                json.dump(template, f, indent=2)

            print(f"[RedactedLearner] Template saved: {output_path}")

            return {
                "status": "success",
                "template_path": str(output_path),
                "template_id": template["template_id"]
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python learn_from_redacted.py <redacted_pdf_path>")
        sys.exit(1)

    pdf_path = sys.argv[1]

    if not os.path.exists(pdf_path):
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)

    # Initialize learner
    learner = RedactedDocumentLearner()

    # Analyze document
    print(f"\nAnalyzing redacted document: {pdf_path}\n")
    result = learner.analyze_redacted_document(pdf_path)

    if result["status"] == "success":
        print(f"\nFound {len(result['regions'])} redacted regions:\n")

        for i, region in enumerate(result['regions'], 1):
            print(f"{i}. Type: {region['inferred_type']}")
            print(f"   Context: {region['context']}")
            print(f"   Confidence: {region['confidence']}")
            print(f"   BBox: {region['bbox']}")
            print()

        # Save template
        template_name = Path(pdf_path).stem
        save_result = learner.save_template(result['regions'], template_name)

        if save_result["status"] == "success":
            print(f"Template saved: {save_result['template_path']}")
        else:
            print(f"Error saving template: {save_result['error']}")
    else:
        print(f"Error: {result['error']}")
