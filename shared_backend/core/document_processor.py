"""
Document processing module for PDF and DOCX files
"""
import pdfplumber  # Better email/structured data extraction than PyMuPDF
from docx import Document
from pathlib import Path
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """Process PDF, DOCX, and TXT files for text extraction"""

    SUPPORTED_FORMATS = ['.pdf', '.docx', '.doc', '.txt']
    MAX_FILE_SIZE = 100 * 1024 * 1024  # 100 MB
    
    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """Check if file format is supported"""
        return Path(file_path).suffix.lower() in DocumentProcessor.SUPPORTED_FORMATS
    
    @staticmethod
    def validate_file(file_path: str) -> tuple[bool, Optional[str]]:
        """
        Validate file before processing
        
        Returns:
            (is_valid, error_message)
        """
        path = Path(file_path)
        
        if not path.exists():
            return False, "File not found"
        
        if not path.is_file():
            return False, "Not a file"
        
        if path.stat().st_size > DocumentProcessor.MAX_FILE_SIZE:
            return False, f"File too large (max {DocumentProcessor.MAX_FILE_SIZE // (1024*1024)}MB)"
        
        if not DocumentProcessor.is_supported_format(file_path):
            return False, f"Unsupported format. Supported: {', '.join(DocumentProcessor.SUPPORTED_FORMATS)}"
        
        return True, None
    
    @staticmethod
    def process_pdf(file_path: str) -> Dict:
        """
        Extract text from PDF file using pdfplumber.

        Advantages over PyMuPDF:
        - Better email address extraction (preserves @ symbols and structure)
        - Preserves structured data (tables, forms)
        - Better handling of Italian legal document formatting
        - More accurate for documents with embedded objects

        Returns:
            dict with pages, text, metadata, is_scanned flag
        """
        try:
            pages = []
            total_text = ""
            total_chars = 0

            with pdfplumber.open(file_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()

                    # Handle None return (empty pages)
                    if text is None:
                        text = ""

                    # Get page info
                    page_info = {
                        "page_number": page_num + 1,
                        "text": text,
                        "char_count": len(text),
                        "has_images": len(page.images) > 0 if page.images else False,
                        "width": page.width,
                        "height": page.height
                    }

                    pages.append(page_info)
                    total_text += text + "\n\n"
                    total_chars += len(text)

            # Detect if scanned (low text density)
            avg_chars_per_page = total_chars / len(pages) if pages else 0
            is_scanned = avg_chars_per_page < 100  # Threshold for scanned docs

            logger.info(f"PDF processed: {len(pages)} pages, {total_chars} chars, scanned: {is_scanned}")

            return {
                "status": "success",
                "file_type": "pdf",
                "pages": pages,
                "full_text": total_text,
                "metadata": {
                    "page_count": len(pages),
                    "total_chars": total_chars,
                    "is_scanned": is_scanned,
                    "avg_chars_per_page": avg_chars_per_page
                }
            }

        except Exception as e:
            logger.error(f"Error processing PDF: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    @staticmethod
    def process_docx(file_path: str) -> Dict:
        """
        Extract text from DOCX file
        
        Returns:
            dict with paragraphs, text, metadata
        """
        try:
            doc = Document(file_path)
            paragraphs = []
            full_text = ""
            
            for para in doc.paragraphs:
                if para.text.strip():
                    paragraphs.append({
                        "text": para.text,
                        "style": para.style.name if para.style else "Normal"
                    })
                    full_text += para.text + "\n\n"
            
            return {
                "status": "success",
                "file_type": "docx",
                "paragraphs": paragraphs,
                "full_text": full_text,
                "metadata": {
                    "paragraph_count": len(paragraphs),
                    "total_chars": len(full_text),
                    "is_scanned": False
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing DOCX: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    def process_txt(file_path: str) -> Dict:
        """
        Extract text from plain text file

        Args:
            file_path: Path to TXT file

        Returns:
            dict with text and metadata
        """
        try:
            # Read text file with encoding detection
            with open(file_path, 'r', encoding='utf-8') as f:
                full_text = f.read()

            # Try alternative encodings if UTF-8 fails
            if not full_text:
                for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            full_text = f.read()
                        if full_text:
                            logger.info(f"Successfully read TXT file with {encoding} encoding")
                            break
                    except:
                        continue

            if not full_text:
                return {
                    "status": "error",
                    "error": "Unable to read file content with supported encodings"
                }

            # Split into lines for metadata
            lines = full_text.split('\n')

            logger.info(f"TXT processed: {len(lines)} lines, {len(full_text)} chars")

            return {
                "status": "success",
                "file_type": "txt",
                "full_text": full_text,
                "metadata": {
                    "line_count": len(lines),
                    "total_chars": len(full_text),
                    "is_scanned": False
                }
            }

        except Exception as e:
            logger.error(f"Error processing TXT: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    @staticmethod
    def process_document(file_path: str) -> Dict:
        """
        Main entry point for document processing
        
        Args:
            file_path: Path to document file
            
        Returns:
            Processing result with extracted text and metadata
        """
        # Validate file
        is_valid, error = DocumentProcessor.validate_file(file_path)
        if not is_valid:
            return {
                "status": "error",
                "error": error
            }
        
        # Process based on file type
        suffix = Path(file_path).suffix.lower()

        if suffix == '.pdf':
            return DocumentProcessor.process_pdf(file_path)
        elif suffix in ['.docx', '.doc']:
            return DocumentProcessor.process_docx(file_path)
        elif suffix == '.txt':
            return DocumentProcessor.process_txt(file_path)
        else:
            return {
                "status": "error",
                "error": f"Unsupported format: {suffix}"
            }

    @staticmethod
    def process_file(file_path: str) -> Dict:
        """
        Alias for process_document() for API consistency

        This method exists for backwards compatibility and consistency
        with the Gradio frontend which calls process_file().

        Args:
            file_path: Path to document file

        Returns:
            Processing result (same as process_document())
        """
        return DocumentProcessor.process_document(file_path)
