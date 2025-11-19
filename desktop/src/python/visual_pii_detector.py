"""
Visual PII Detection Module (Optional Enhancement - Task 1.12)
Detects PII in images, tables, headers/footers using Qwen-VL vision model
"""
import logging
from typing import List, Dict, Tuple
import fitz  # PyMuPDF
from PIL import Image
import io
import numpy as np

logger = logging.getLogger(__name__)


class VisualPIIDetector:
    """
    Detect PII in visual elements using Qwen-VL vision model
    Handles: images, tables as images, headers/footers, scanned forms
    """
    
    def __init__(self, model_path: str = None):
        """
        Initialize visual PII detector
        
        Args:
            model_path: Path to ONNX model (default: models/qwen-vl-chat.onnx)
        """
        self.model_path = model_path or "models/qwen-vl-chat.onnx"
        self.model = None
        
        try:
            # Import ONNX Runtime (lighter than full transformers)
            import onnxruntime as ort
            self.model = ort.InferenceSession(self.model_path)
            logger.info(f"Visual PII Detector initialized with model: {self.model_path}")
        except Exception as e:
            logger.warning(f"Could not load visual model: {e}")
            logger.warning("Visual PII detection will be disabled")
    
    def should_scan_page(self, page) -> bool:
        """
        Determine if a page needs visual PII scanning
        Only scan pages with images, headers, or complex layouts
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            bool: True if page should be scanned
        """
        try:
            # Check for embedded images
            image_list = page.get_images()
            if len(image_list) > 0:
                logger.info(f"Page has {len(image_list)} embedded images - scan recommended")
                return True
            
            # Check for drawings (might be tables/forms)
            drawings = page.get_drawings()
            if len(drawings) > 10:  # Threshold for complex layouts
                logger.info(f"Page has {len(drawings)} drawings - scan recommended")
                return True
            
            # Check text density (low density = might be scanned/image-based)
            text = page.get_text()
            text_density = len(text) / (page.rect.width * page.rect.height)
            if text_density < 0.01:  # Very low text density
                logger.info(f"Low text density ({text_density:.4f}) - scan recommended")
                return True
            
            logger.info("Page is text-only - visual scan not needed")
            return False
            
        except Exception as e:
            logger.error(f"Error checking page: {e}")
            return False  # Skip on error
    
    def detect_in_page(self, page, force: bool = False) -> List[Dict]:
        """
        Detect PII in visual elements of a PDF page
        Only scans if page has images/complex layout (unless forced)
        
        Args:
            page: PyMuPDF page object
            force: Force scan even if page appears text-only
            
        Returns:
            List of detected PII entities with bounding boxes
        """
        if self.model is None:
            return []
        
        # Skip visual scan for text-only pages (unless forced)
        if not force and not self.should_scan_page(page):
            return []
        
        try:
            # Get page images
            images = self._extract_page_images(page)
            
            # Detect PII in each image
            all_detections = []
            for img_info in images:
                detections = self._detect_in_image(
                    img_info['image'],
                    img_info['bbox']
                )
                all_detections.extend(detections)
            
            # Detect PII in page header/footer
            header_footer = self._detect_header_footer(page)
            all_detections.extend(header_footer)
            
            return all_detections
            
        except Exception as e:
            logger.error(f"Visual detection error: {e}")
            return []
    
    def _extract_page_images(self, page) -> List[Dict]:
        """Extract all images from a PDF page"""
        images = []
        
        try:
            # Get all images on page
            image_list = page.get_images()
            
            for img_index, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = page.parent.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Convert to PIL Image
                    pil_image = Image.open(io.BytesIO(image_bytes))
                    
                    # Get image position on page
                    image_rects = page.get_image_rects(xref)
                    bbox = image_rects[0] if image_rects else page.rect
                    
                    images.append({
                        'image': pil_image,
                        'bbox': bbox,
                        'index': img_index
                    })
                    
                except Exception as e:
                    logger.warning(f"Could not extract image {img_index}: {e}")
            
        except Exception as e:
            logger.error(f"Error extracting images: {e}")
        
        return images
    
    def _detect_in_image(self, image: Image.Image, bbox: fitz.Rect) -> List[Dict]:
        """
        Run visual PII detection on a single image
        
        Args:
            image: PIL Image
            bbox: Bounding box on page
            
        Returns:
            List of detected entities with coordinates
        """
        try:
            # Prepare image for model
            image_array = self._preprocess_image(image)
            
            # Run inference
            prompt = "Detect and extract any personal information (names, addresses, phone numbers, IDs) in this image. Format: [TYPE]: text"
            detections = self._run_vision_model(image_array, prompt)
            
            # Parse detections and add bounding box
            entities = []
            for detection in detections:
                entity = {
                    "entity_type": detection['type'],
                    "text": detection['text'],
                    "confidence": detection['score'],
                    "bbox": bbox,  # Image bounding box on page
                    "visual": True,  # Mark as visual detection
                    "source": "image"
                }
                entities.append(entity)
            
            return entities
            
        except Exception as e:
            logger.error(f"Image detection error: {e}")
            return []
    
    def _detect_header_footer(self, page) -> List[Dict]:
        """
        Detect PII in page headers and footers (often as images)
        
        Args:
            page: PyMuPDF page object
            
        Returns:
            List of detected entities in header/footer
        """
        try:
            rect = page.rect
            header_height = 100  # Top 100 points
            footer_height = 100  # Bottom 100 points
            
            # Render header and footer as images
            header_rect = fitz.Rect(0, 0, rect.width, header_height)
            footer_rect = fitz.Rect(0, rect.height - footer_height, rect.width, rect.height)
            
            header_pix = page.get_pixmap(clip=header_rect)
            footer_pix = page.get_pixmap(clip=footer_rect)
            
            # Convert to PIL Images
            header_img = Image.frombytes("RGB", [header_pix.width, header_pix.height], header_pix.samples)
            footer_img = Image.frombytes("RGB", [footer_pix.width, footer_pix.height], footer_pix.samples)
            
            # Detect PII
            header_entities = self._detect_in_image(header_img, header_rect)
            footer_entities = self._detect_in_image(footer_img, footer_rect)
            
            # Mark source
            for e in header_entities:
                e['source'] = 'header'
            for e in footer_entities:
                e['source'] = 'footer'
            
            return header_entities + footer_entities
            
        except Exception as e:
            logger.error(f"Header/footer detection error: {e}")
            return []
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for model input"""
        # Resize to model input size (e.g., 448x448 for Qwen-VL)
        image = image.resize((448, 448))
        
        # Convert to numpy array and normalize
        image_array = np.array(image).astype(np.float32) / 255.0
        
        # Add batch dimension
        image_array = np.expand_dims(image_array, axis=0)
        
        return image_array
    
    def _run_vision_model(self, image_array: np.ndarray, prompt: str) -> List[Dict]:
        """
        Run Qwen-VL inference
        
        Args:
            image_array: Preprocessed image array
            prompt: Detection prompt
            
        Returns:
            List of detected entities
        """
        try:
            # Run ONNX inference
            # Note: This is a simplified version - actual implementation depends on model format
            inputs = {
                self.model.get_inputs()[0].name: image_array
            }
            outputs = self.model.run(None, inputs)
            
            # Parse outputs (model-specific)
            detections = self._parse_vision_output(outputs)
            
            return detections
            
        except Exception as e:
            logger.error(f"Vision model inference error: {e}")
            return []
    
    def _parse_vision_output(self, outputs) -> List[Dict]:
        """
        Parse vision model outputs
        
        Returns:
            List of detected entities
        """
        # Placeholder - actual parsing depends on model output format
        # Qwen-VL typically returns text with entity markers
        
        detections = []
        
        # Example parsing (adjust based on actual model output)
        # Output format: "[PERSON]: John Doe [PHONE]: +39 333 1234567"
        
        try:
            text_output = str(outputs[0])
            
            # Simple regex parsing (improve based on model)
            import re
            pattern = r'\[([A-Z_]+)\]:\s*([^[\]]+)'
            matches = re.findall(pattern, text_output)
            
            for entity_type, text in matches:
                detections.append({
                    'type': entity_type,
                    'text': text.strip(),
                    'score': 0.85  # Default confidence for vision detections
                })
        
        except Exception as e:
            logger.error(f"Output parsing error: {e}")
        
        return detections
    
    def redact_visual_entities(self, page, entities: List[Dict]) -> None:
        """
        Add visual redaction boxes to page
        
        Args:
            page: PyMuPDF page object
            entities: List of visual entities with bboxes
        """
        try:
            for entity in entities:
                if not entity.get('visual'):
                    continue
                
                bbox = entity['bbox']
                
                # Draw black rectangle over entity
                page.draw_rect(
                    bbox,
                    color=(0, 0, 0),  # Black
                    fill=(0, 0, 0),
                    overlay=True
                )
                
                # Add placeholder text
                placeholder = f"[{entity['entity_type']}]"
                page.insert_text(
                    (bbox.x0 + 5, bbox.y0 + 15),
                    placeholder,
                    fontsize=10,
                    color=(1, 1, 1)  # White
                )
        
        except Exception as e:
            logger.error(f"Visual redaction error: {e}")


# Example usage
if __name__ == "__main__":
    detector = VisualPIIDetector()
    
    # Test with PDF
    doc = fitz.open("test.pdf")
    page = doc[0]
    
    # Detect PII in visual elements
    visual_entities = detector.detect_in_page(page)
    
    print(f"Detected {len(visual_entities)} visual PII entities")
    for entity in visual_entities:
        print(f"- {entity['entity_type']}: {entity['text']} (from {entity['source']})")
    
    # Apply visual redactions
    detector.redact_visual_entities(page, visual_entities)
    
    doc.save("test_redacted.pdf")
    doc.close()
