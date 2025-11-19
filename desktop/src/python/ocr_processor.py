"""
OCR Processing for Scanned Documents
Uses Tesseract OCR with Italian language support
"""
import pytesseract
from PIL import Image
import fitz  # PyMuPDF
from pathlib import Path
import logging
from typing import Dict, List
import io

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Process scanned documents with OCR"""
    
    def __init__(self, lang='ita'):
        """
        Initialize OCR processor
        
        Args:
            lang: Tesseract language code (default: 'ita' for Italian)
        """
        self.lang = lang
        
        # Configure Tesseract (adjust path for your system)
        # Windows: pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    
    @staticmethod
    def is_scanned_page(page, text_threshold=100):
        """
        Detect if a PDF page is scanned (low text content)
        
        Args:
            page: PyMuPDF page object
            text_threshold: Minimum characters to consider digital
            
        Returns:
            bool: True if page appears to be scanned
        """
        text = page.get_text()
        char_count = len(text.strip())
        has_images = len(page.get_images()) > 0
        
        # Scanned if very little text but has images
        return char_count < text_threshold and has_images
    
    def ocr_page(self, page) -> Dict:
        """
        Run OCR on a single PDF page
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            dict with OCR text and confidence
        """
        try:
            # Render page to image
            pix = page.get_pixmap(dpi=300)  # High DPI for better OCR
            
            # Convert to PIL Image
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            
            # Run Tesseract OCR
            ocr_result = pytesseract.image_to_data(
                img,
                lang=self.lang,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text and confidence
            text_parts = []
            confidences = []
            
            for i, text in enumerate(ocr_result['text']):
                if text.strip():
                    text_parts.append(text)
                    conf = int(ocr_result['conf'][i])
                    if conf > 0:
                        confidences.append(conf)
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "status": "success",
                "text": full_text,
                "confidence": avg_confidence,
                "word_count": len(text_parts)
            }
            
        except Exception as e:
            logger.error(f"OCR error on page: {e}")
            return {
                "status": "error",
                "error": str(e),
                "text": "",
                "confidence": 0
            }
    
    def process_scanned_pdf(self, file_path: str, progress_callback=None) -> Dict:
        """
        Process entire scanned PDF with OCR
        
        Args:
            file_path: Path to PDF file
            progress_callback: Optional callback(current, total) for progress
            
        Returns:
            dict with OCR results for all pages
        """
        try:
            doc = fitz.open(file_path)
            pages = []
            total_pages = len(doc)
            scanned_pages = 0
            
            for page_num in range(total_pages):
                page = doc[page_num]
                
                # Check if page needs OCR
                if self.is_scanned_page(page):
                    scanned_pages += 1
                    logger.info(f"Running OCR on page {page_num + 1}/{total_pages}")
                    
                    # Run OCR
                    ocr_result = self.ocr_page(page)
                    
                    page_info = {
                        "page_number": page_num + 1,
                        "is_scanned": True,
                        "text": ocr_result["text"],
                        "ocr_confidence": ocr_result["confidence"],
                        "word_count": ocr_result.get("word_count", 0)
                    }
                else:
                    # Use existing text
                    page_info = {
                        "page_number": page_num + 1,
                        "is_scanned": False,
                        "text": page.get_text(),
                        "ocr_confidence": 100.0,
                        "word_count": len(page.get_text().split())
                    }
                
                pages.append(page_info)
                
                # Progress callback
                if progress_callback:
                    progress_callback(page_num + 1, total_pages)
            
            doc.close()
            
            # Combine all text
            full_text = "\n\n".join([p["text"] for p in pages])
            
            # Calculate average OCR confidence
            ocr_pages = [p for p in pages if p["is_scanned"]]
            avg_ocr_confidence = (
                sum(p["ocr_confidence"] for p in ocr_pages) / len(ocr_pages)
                if ocr_pages else 100.0
            )
            
            return {
                "status": "success",
                "file_type": "pdf",
                "pages": pages,
                "full_text": full_text,
                "metadata": {
                    "page_count": total_pages,
                    "scanned_pages": scanned_pages,
                    "digital_pages": total_pages - scanned_pages,
                    "avg_ocr_confidence": avg_ocr_confidence,
                    "total_chars": len(full_text)
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing scanned PDF: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def ocr_image_file(self, file_path: str) -> Dict:
        """
        Run OCR on standalone image file
        
        Args:
            file_path: Path to image file
            
        Returns:
            dict with OCR results
        """
        try:
            img = Image.open(file_path)
            
            # Run OCR
            text = pytesseract.image_to_string(img, lang=self.lang)
            
            # Get confidence data
            ocr_data = pytesseract.image_to_data(
                img,
                lang=self.lang,
                output_type=pytesseract.Output.DICT
            )
            
            confidences = [int(c) for c in ocr_data['conf'] if int(c) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            return {
                "status": "success",
                "text": text,
                "confidence": avg_confidence,
                "word_count": len(text.split())
            }
            
        except Exception as e:
            logger.error(f"Error processing image: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    processor = OCRProcessor(lang='ita')
    
    # Test with a scanned PDF
    result = processor.process_scanned_pdf("sample_scanned.pdf")
    print(f"OCR complete: {result['metadata']['scanned_pages']} pages processed")
    print(f"Average confidence: {result['metadata']['avg_ocr_confidence']:.1f}%")
