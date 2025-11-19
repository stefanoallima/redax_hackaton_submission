"""
Redaction Export Module
Generates redacted PDFs with placeholder strategy

WHY CUSTOM IMPLEMENTATION vs Presidio Anonymizer?
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Presidio Anonymizer is designed for TEXT, not PDFs.

PDF Requirements Our Approach Meets:
✅ Layout preservation (same-length placeholders)
✅ Visual redaction (black boxes via PyMuPDF)
✅ Coordinate-based positioning (precise targeting)
✅ Safety checks (invisible text, double-redaction prevention)
✅ Audit trail (mapping table CSV)

Example:
  "Mario Rossi" (11 chars) → "[PER1-----]" (11 chars) ✅ Layout preserved

See: PRESIDIO_ANONYMIZATION_ANALYSIS.md for comparison
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
import fitz  # PyMuPDF
from pathlib import Path
import logging
from typing import Dict, List
from datetime import datetime
import re
from redaction_safety import RedactionSafetyChecker

logger = logging.getLogger(__name__)


class RedactionExporter:
    """
    Export redacted documents with consistent placeholder strategy
    Same entity → same placeholder ([PERSONA_A], [INDIRIZZO_1], etc.)
    """
    
    def __init__(self):
        """Initialize exporter with placeholder counters"""
        self.entity_mappings = {}
        self.counters = {}
    
    def _get_placeholder(self, entity_type: str, original_text: str) -> str:
        """
        Get consistent placeholder for entity - SAME LENGTH as original

        Args:
            entity_type: Type of PII entity
            original_text: Original text to redact

        Returns:
            Placeholder string with EXACT same length as original_text
        """
        # Check if we've seen this exact text before
        key = f"{entity_type}:{original_text}"

        if key in self.entity_mappings:
            return self.entity_mappings[key]

        # Create new placeholder
        if entity_type not in self.counters:
            self.counters[entity_type] = 0

        self.counters[entity_type] += 1
        count = self.counters[entity_type]

        # Generate base placeholder based on entity type
        placeholder_prefixes = {
            "PERSON": "PER",
            "CODICE_FISCALE": "CF",
            "PHONE_NUMBER": "TEL",
            "EMAIL_ADDRESS": "EML",
            "IBAN": "IBN",
            "IT_ADDRESS": "ADR",
            "LOCATION": "LOC",
            "DATE_TIME": "DAT"
        }

        prefix = placeholder_prefixes.get(entity_type, "PII")
        base_placeholder = f"[{prefix}{count}]"

        # Get target length (same as original text)
        target_length = len(original_text)

        # Adjust placeholder to match exact length
        if len(base_placeholder) == target_length:
            # Perfect match
            placeholder = base_placeholder
        elif len(base_placeholder) < target_length:
            # Pad with dashes to reach target length
            padding_needed = target_length - len(base_placeholder)
            # Insert padding before closing bracket
            placeholder = base_placeholder[:-1] + ('-' * padding_needed) + ']'
        else:
            # Truncate or use alternative short form
            if target_length >= 5:
                # Use [P1], [P2], etc. format
                short_form = f"[{prefix[0]}{count}]"
                if len(short_form) <= target_length:
                    # Pad if needed
                    padding = target_length - len(short_form)
                    placeholder = short_form[:-1] + ('-' * padding) + ']'
                else:
                    # Use asterisks as last resort
                    placeholder = '*' * target_length
            else:
                # Very short text - use block characters
                placeholder = '█' * target_length

        self.entity_mappings[key] = placeholder

        return placeholder
    
    def export_redacted_pdf(
        self,
        input_path: str,
        output_path: str,
        entities: List[Dict],
        add_watermark: bool = False,
        clean_metadata: bool = True,
        enable_safety_checks: bool = True
    ) -> Dict:
        """
        Export PDF with redacted PII entities with comprehensive safety checks

        Args:
            input_path: Original PDF path
            output_path: Output PDF path
            entities: List of PII entities to redact
            add_watermark: Add "REDACTED" watermark
            clean_metadata: Remove metadata from PDF
            enable_safety_checks: Enable visibility and text matching safety checks

        Returns:
            dict with export status, mapping table, and safety check statistics
        """
        try:
            doc = fitz.open(input_path)

            # Initialize safety checker
            safety_checker = RedactionSafetyChecker()

            # Reset mappings for new document
            self.entity_mappings = {}
            self.counters = {}

            # Track blocked redactions for reporting
            blocked_redactions = {
                'already_redacted': [],
                'invisible_text': [],
                'text_mismatch': []
            }

            # DEBUG: Log all entities being redacted
            logger.info(f"Starting redaction export with {len(entities)} entities")
            for i, entity in enumerate(entities, 1):
                has_locations = 'locations' in entity and entity['locations']
                loc_count = len(entity['locations']) if has_locations else 0
                logger.debug(f"  Entity {i}: '{entity['text'][:40]}' ({entity['entity_type']}) - {loc_count} pre-computed locations")

            # Sort entities by position (reverse to process from end to start)
            sorted_entities = sorted(entities, key=lambda e: e['start'], reverse=True)
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_text = page.get_text()

                # Detect existing redactions on this page (safety check)
                existing_redactions = safety_checker.detect_existing_redactions(page) if enable_safety_checks else []

                # Track text replacements for this page
                replacements = []

                # Find entities on this page and apply redactions
                for entity in sorted_entities:
                    # Get placeholder (same length as original)
                    placeholder = self._get_placeholder(
                        entity['entity_type'],
                        entity['text']
                    )

                    text_instances = []

                    # Priority 1: Use pre-computed locations if available (more accurate for emails, etc.)
                    if 'locations' in entity and entity['locations']:
                        for loc in entity['locations']:
                            if loc['page'] == page_num + 1:  # locations are 1-indexed
                                rect_data = loc['rect']
                                rect = fitz.Rect(
                                    rect_data['x0'],
                                    rect_data['y0'],
                                    rect_data['x1'],
                                    rect_data['y1']
                                )
                                text_instances.append(rect)

                                # DEBUG: Log entity location details
                                logger.debug(f"[Page {page_num + 1}] Entity '{entity['text'][:30]}' ({entity['entity_type']}) -> Pre-computed location: x={rect.x0:.1f}-{rect.x1:.1f}, y={rect.y0:.1f}-{rect.y1:.1f}")

                    # Fallback: Search for entity text on page if no locations provided
                    if not text_instances:
                        text_instances = page.search_for(entity['text'])
                        if text_instances:
                            logger.debug(f"[Page {page_num + 1}] Entity '{entity['text'][:30]}' ({entity['entity_type']}) -> Fallback search found {len(text_instances)} location(s)")

                    if text_instances:
                        # Apply safety checks before redacting each instance
                        for inst in text_instances:
                            # COMPREHENSIVE SAFETY CHECKS
                            if enable_safety_checks:
                                is_safe, reason = safety_checker.is_safe_to_redact(
                                    page=page,
                                    rect=inst,
                                    expected_text=entity['text'],
                                    existing_redactions=existing_redactions,
                                    check_visibility=True,
                                    check_text_match=True
                                )

                                if not is_safe:
                                    # Log and skip this redaction
                                    logger.info(f"[Page {page_num + 1}] Skipped: {entity['text'][:30]}... - Reason: {reason}")

                                    # Track blocked redaction
                                    if "Already redacted" in reason:
                                        blocked_redactions['already_redacted'].append({
                                            'text': entity['text'],
                                            'page': page_num + 1,
                                            'reason': reason
                                        })
                                    elif "Invisible" in reason:
                                        blocked_redactions['invisible_text'].append({
                                            'text': entity['text'],
                                            'page': page_num + 1,
                                            'reason': reason
                                        })
                                    elif "mismatch" in reason:
                                        blocked_redactions['text_mismatch'].append({
                                            'text': entity['text'],
                                            'page': page_num + 1,
                                            'reason': reason
                                        })

                                    continue  # Skip this redaction

                                # Safety checks passed
                                logger.debug(f"[Page {page_num + 1}] Safe to redact: {entity['text'][:30]}...")

                            # All checks passed - safe to redact
                            replacements.append({
                                'rect': inst,
                                'original': entity['text'],
                                'placeholder': placeholder
                            })

                            # Add redaction annotation to remove original text
                            page.add_redact_annot(inst, fill=(1, 1, 1))  # White fill

                # Apply all redactions at once (removes original text)
                page.apply_redactions()

                # Now draw solid black rectangles over redacted areas
                for replacement in replacements:
                    rect = replacement['rect']

                    # Expand rectangle slightly to ensure complete coverage
                    display_rect = fitz.Rect(
                        rect.x0 - 1,
                        rect.y0 - 1,
                        rect.x1 + 1,
                        rect.y1 + 1
                    )

                    # Draw solid black rectangle (traditional censorship style)
                    page.draw_rect(display_rect, color=(0, 0, 0), fill=(0, 0, 0))

                # Add watermark if requested
                if add_watermark:
                    self._add_watermark(page)
            
            # Clean metadata if requested
            if clean_metadata:
                doc.set_metadata({
                    'title': 'Redacted Document',
                    'author': '',
                    'subject': '',
                    'keywords': '',
                    'creator': 'CodiceCivile Redact',
                    'producer': 'CodiceCivile Redact',
                    'creationDate': datetime.now().strftime("D:%Y%m%d%H%M%S"),
                    'modDate': datetime.now().strftime("D:%Y%m%d%H%M%S")
                })
            
            # Save redacted PDF
            doc.save(output_path, garbage=4, deflate=True, clean=True)
            doc.close()
            
            logger.info(f"Redacted PDF saved to: {output_path}")

            # Get safety check statistics
            safety_stats = safety_checker.get_stats()

            # Generate mapping table
            mapping_table = [
                {
                    "original": key.split(':', 1)[1],
                    "placeholder": placeholder,
                    "type": key.split(':', 1)[0]
                }
                for key, placeholder in self.entity_mappings.items()
            ]

            # Count total blocked redactions
            total_blocked = sum(len(v) for v in blocked_redactions.values())

            # Log summary
            logger.info(f"Redaction Summary:")
            logger.info(f"  - Safe redactions: {safety_stats['safe_redactions']}")
            logger.info(f"  - Blocked (already redacted): {len(blocked_redactions['already_redacted'])}")
            logger.info(f"  - Blocked (invisible text): {len(blocked_redactions['invisible_text'])}")
            logger.info(f"  - Blocked (text mismatch): {len(blocked_redactions['text_mismatch'])}")
            logger.info(f"  - Total blocked: {total_blocked}")

            return {
                "status": "success",
                "output_path": output_path,
                "entities_redacted": len(entities),
                "unique_entities": len(self.entity_mappings),
                "mapping_table": mapping_table,
                "safety_checks": {
                    "enabled": enable_safety_checks,
                    "statistics": safety_stats,
                    "blocked_redactions": blocked_redactions,
                    "total_blocked": total_blocked
                }
            }
            
        except Exception as e:
            logger.error(f"Error exporting redacted PDF: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _add_watermark(self, page):
        """
        Add "REDACTED" watermark to page

        Args:
            page: PyMuPDF page object
        """
        try:
            rect = page.rect
            text = "REDACTED"

            # Add watermark in center with proper rotation
            # Use insert_textbox instead of insert_text for rotation support
            watermark_rect = fitz.Rect(
                rect.width / 4,
                rect.height / 2 - 50,
                rect.width * 3 / 4,
                rect.height / 2 + 50
            )

            page.insert_textbox(
                watermark_rect,
                text,
                fontsize=48,
                color=(0.9, 0.9, 0.9),  # Light gray
                align=fitz.TEXT_ALIGN_CENTER,
                rotate=0  # No rotation to avoid compatibility issues
            )
        except Exception as e:
            logger.error(f"Error adding watermark: {e}")
    
    def export_mapping_table(self, output_path: str) -> Dict:
        """
        Export entity mapping table to CSV

        Args:
            output_path: CSV file path

        Returns:
            dict with export status
        """
        try:
            import csv

            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Original Text', 'Placeholder', 'Entity Type'])

                for key, placeholder in self.entity_mappings.items():
                    entity_type, original = key.split(':', 1)
                    writer.writerow([original, placeholder, entity_type])

            return {
                "status": "success",
                "output_path": output_path,
                "rows": len(self.entity_mappings)
            }

        except Exception as e:
            logger.error(f"Error exporting mapping table: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def export_redacted_text(
        self,
        input_path: str,
        output_path: str,
        entities: List[Dict],
        reuse_mappings: bool = True
    ) -> Dict:
        """
        Export redacted document as plain text (for LLM use)

        Args:
            input_path: Original document path (PDF, DOCX, TXT)
            output_path: Output TXT file path
            entities: List of PII entities to redact
            reuse_mappings: If True, keep existing entity mappings for consistency

        Returns:
            dict with export status
        """
        try:
            logger.info(f"Exporting redacted text: {input_path}")

            # Reset mappings only if not reusing
            if not reuse_mappings:
                self.entity_mappings = {}
                self.counters = {}

            # Extract text from document
            input_file = Path(input_path)
            if input_file.suffix.lower() == '.pdf':
                # Extract from PDF
                doc = fitz.open(input_path)
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
            elif input_file.suffix.lower() in ['.docx', '.doc']:
                # Extract from DOCX (requires python-docx)
                try:
                    import docx
                    doc = docx.Document(input_path)
                    full_text = "\n".join([para.text for para in doc.paragraphs])
                except ImportError:
                    return {
                        "status": "error",
                        "error": "python-docx not installed for DOCX support"
                    }
            else:
                # Plain text file
                with open(input_path, 'r', encoding='utf-8') as f:
                    full_text = f.read()

            # Use text-based replacement instead of character offsets
            # This is more robust when text formatting differs between extraction methods

            # Build entity -> placeholder mapping
            entity_replacements = {}
            for entity in entities:
                placeholder = self._get_placeholder(
                    entity['entity_type'],
                    entity['text']
                )
                entity_replacements[entity['text']] = placeholder

            # Sort by length (longest first) to avoid partial replacements
            # Example: replace "Mario Rossi Company" before "Mario Rossi"
            sorted_texts = sorted(entity_replacements.keys(), key=len, reverse=True)

            # Replace all occurrences of each entity text
            for entity_text in sorted_texts:
                placeholder = entity_replacements[entity_text]
                full_text = full_text.replace(entity_text, placeholder)

            # Save redacted text
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)

            logger.info(f"Redacted text saved to: {output_path}")

            return {
                "status": "success",
                "output_path": output_path,
                "entities_redacted": len(entities),
                "unique_entities": len(self.entity_mappings)
            }

        except Exception as e:
            logger.error(f"Error exporting redacted text: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# Example usage
if __name__ == "__main__":
    exporter = RedactionExporter()
    
    # Sample entities
    entities = [
        {"entity_type": "PERSON", "text": "Mario Rossi", "start": 10, "end": 21},
        {"entity_type": "CODICE_FISCALE", "text": "RSSMRA85C15H501X", "start": 50, "end": 66},
        {"entity_type": "PHONE_NUMBER", "text": "+39 333 1234567", "start": 100, "end": 115}
    ]
    
    result = exporter.export_redacted_pdf(
        input_path="original.pdf",
        output_path="redacted.pdf",
        entities=entities,
        add_watermark=True
    )
    
    print(f"Redaction complete: {result['entities_redacted']} entities redacted")
    print(f"Mapping table entries: {result['unique_entities']}")
