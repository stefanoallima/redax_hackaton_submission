"""
Document Structure Analyzer
Identifies document sections and prioritizes PII detection
Based on auditing best practices: PII is concentrated at beginning and end
"""
import logging
from typing import Dict, List, Tuple
import re

logger = logging.getLogger(__name__)


class DocumentAnalyzer:
    """
    Analyze document structure to optimize PII detection
    Based on auditing knowledge: most PII is in first/last pages
    """
    
    def __init__(self):
        """Initialize document analyzer"""
        self.section_keywords = {
            'signature': ['firma', 'firmato', 'sottoscritto', 'signature', 'signed'],
            'parties': ['tra', 'contraente', 'parte', 'cliente', 'fornitore'],
            'appendix': ['allegato', 'appendice', 'annesso', 'attachment'],
            'header': ['contratto', 'accordo', 'convenzione', 'agreement'],
            'footer': ['pagina', 'page', 'documento'],
            'contact': ['telefono', 'email', 'indirizzo', 'tel', 'fax'],
            'financial': ['iban', 'conto', 'pagamento', 'bonifico', 'payment']
        }
    
    def analyze_structure(self, doc) -> Dict:
        """
        Analyze document structure and identify key sections
        
        Args:
            doc: PyMuPDF document object
            
        Returns:
            dict with document structure analysis
        """
        total_pages = len(doc)
        
        analysis = {
            'total_pages': total_pages,
            'high_priority_pages': [],
            'medium_priority_pages': [],
            'low_priority_pages': [],
            'appendix_start': None,
            'main_content_end': None,
            'sections': {}
        }
        
        # Identify appendix start (if any)
        appendix_start = self._find_appendix_start(doc)
        analysis['appendix_start'] = appendix_start
        
        # Determine main content end
        if appendix_start:
            analysis['main_content_end'] = appendix_start - 1
        else:
            analysis['main_content_end'] = total_pages
        
        # Prioritize pages based on auditing knowledge
        analysis = self._prioritize_pages(doc, analysis)
        
        return analysis
    
    def _find_appendix_start(self, doc) -> int:
        """
        Find where appendices start
        
        Returns:
            Page number where appendix starts, or None
        """
        appendix_keywords = ['allegato', 'appendice', 'annesso', 'attachment', 'annex']
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text().lower()
            
            # Check if page starts with appendix keyword
            first_100_chars = text[:100]
            
            for keyword in appendix_keywords:
                if keyword in first_100_chars:
                    logger.info(f"Appendix detected starting at page {page_num + 1}")
                    return page_num
        
        return None
    
    def _prioritize_pages(self, doc, analysis: Dict) -> Dict:
        """
        Prioritize pages for PII detection based on content likelihood
        
        Priority levels:
        - HIGH: First 3 pages, last 3 pages (before appendix)
        - MEDIUM: Pages with contact/financial keywords
        - LOW: Middle pages, appendices
        """
        total_pages = analysis['total_pages']
        main_end = analysis['main_content_end']
        
        # HIGH PRIORITY: Beginning pages (parties, signatures, contact info)
        beginning_pages = min(3, total_pages)
        for i in range(beginning_pages):
            analysis['high_priority_pages'].append(i)
        
        # HIGH PRIORITY: End pages (signatures, final terms)
        # But only before appendix starts
        end_start = max(beginning_pages, main_end - 3)
        for i in range(end_start, main_end):
            if i not in analysis['high_priority_pages']:
                analysis['high_priority_pages'].append(i)
        
        # MEDIUM PRIORITY: Pages with PII-related keywords
        for page_num in range(beginning_pages, end_start):
            page = doc[page_num]
            text = page.get_text().lower()
            
            # Check for PII-related keywords
            has_pii_keywords = any(
                keyword in text 
                for keywords in self.section_keywords.values() 
                for keyword in keywords
            )
            
            if has_pii_keywords:
                analysis['medium_priority_pages'].append(page_num)
            else:
                analysis['low_priority_pages'].append(page_num)
        
        # LOW PRIORITY: Appendices (usually contain technical data, not PII)
        if analysis['appendix_start']:
            for i in range(analysis['appendix_start'], total_pages):
                analysis['low_priority_pages'].append(i)
        
        logger.info(f"Page prioritization: HIGH={len(analysis['high_priority_pages'])}, "
                   f"MEDIUM={len(analysis['medium_priority_pages'])}, "
                   f"LOW={len(analysis['low_priority_pages'])}")
        
        return analysis
    
    def get_detection_strategy(self, doc) -> Dict:
        """
        Get recommended detection strategy based on document analysis
        
        IMPORTANT: Regex detection ALWAYS runs on ALL pages
        LLM and Visual are applied selectively based on page priority
        
        Returns:
            dict with detection recommendations
        """
        analysis = self.analyze_structure(doc)
        
        strategy = {
            'analysis': analysis,
            'recommendations': {
                'all_pages': {
                    'pages': list(range(len(doc))),
                    'use_regex': True,
                    'description': 'Regex detection on ALL pages (never skip)'
                },
                'high_priority': {
                    'pages': analysis['high_priority_pages'],
                    'use_regex': True,  # Always
                    'use_llm': True,    # Enhanced detection
                    'use_visual': True,  # Enhanced detection
                    'description': 'First/last pages - apply all detection methods'
                },
                'medium_priority': {
                    'pages': analysis['medium_priority_pages'],
                    'use_regex': True,  # Always
                    'use_llm': True,    # Enhanced detection (has PII keywords)
                    'use_visual': False,
                    'description': 'Pages with PII keywords - apply regex + LLM'
                },
                'low_priority': {
                    'pages': analysis['low_priority_pages'],
                    'use_regex': True,  # Always
                    'use_llm': False,   # Skip (no keywords, unlikely PII)
                    'use_visual': False,
                    'description': 'Other pages - regex only (but still checked!)'
                }
            }
        }
        
        return strategy
    
    def estimate_processing_time(self, doc) -> Dict:
        """
        Estimate processing time based on document structure
        
        IMPORTANT: All pages get regex detection
        LLM/Visual are applied selectively
        
        Returns:
            dict with time estimates
        """
        strategy = self.get_detection_strategy(doc)
        
        # Time estimates (in seconds)
        TIME_PER_PAGE = {
            'regex': 0.1,
            'llm': 0.5,
            'visual': 2.0
        }
        
        total_pages = len(doc)
        high_pages = len(strategy['recommendations']['high_priority']['pages'])
        medium_pages = len(strategy['recommendations']['medium_priority']['pages'])
        low_pages = len(strategy['recommendations']['low_priority']['pages'])
        
        # Calculate time
        time_estimate = {
            'regex_all_pages': total_pages * TIME_PER_PAGE['regex'],  # ALL pages
            'llm_enhancement': (high_pages + medium_pages) * TIME_PER_PAGE['llm'],
            'visual_enhancement': high_pages * TIME_PER_PAGE['visual'],
            'total': 0
        }
        
        time_estimate['total'] = (
            time_estimate['regex_all_pages'] +
            time_estimate['llm_enhancement'] +
            time_estimate['visual_enhancement']
        )
        
        # Breakdown by priority
        time_estimate['breakdown'] = {
            'high_priority': high_pages * (TIME_PER_PAGE['regex'] + TIME_PER_PAGE['llm'] + TIME_PER_PAGE['visual']),
            'medium_priority': medium_pages * (TIME_PER_PAGE['regex'] + TIME_PER_PAGE['llm']),
            'low_priority': low_pages * TIME_PER_PAGE['regex']
        }
        
        return time_estimate


# Example usage
if __name__ == "__main__":
    import fitz
    
    # Test with sample document
    doc = fitz.open("sample_contract.pdf")
    
    analyzer = DocumentAnalyzer()
    
    # Analyze structure
    print("=" * 80)
    print("DOCUMENT STRUCTURE ANALYSIS")
    print("=" * 80)
    
    strategy = analyzer.get_detection_strategy(doc)
    
    print(f"\nTotal pages: {strategy['analysis']['total_pages']}")
    print(f"Main content ends at: page {strategy['analysis']['main_content_end']}")
    
    if strategy['analysis']['appendix_start']:
        print(f"Appendix starts at: page {strategy['analysis']['appendix_start'] + 1}")
    
    print("\n" + "=" * 80)
    print("DETECTION STRATEGY")
    print("=" * 80)
    
    for priority, config in strategy['recommendations'].items():
        print(f"\n{priority.upper().replace('_', ' ')}:")
        print(f"  Pages: {len(config['pages'])} pages")
        print(f"  Pages: {[p+1 for p in config['pages'][:10]]}{'...' if len(config['pages']) > 10 else ''}")
        print(f"  Detection: {config['detection_level']}")
        print(f"  LLM: {'Yes' if config['use_llm'] else 'No'}")
        print(f"  Visual: {'Yes' if config['use_visual'] else 'No'}")
        print(f"  Reason: {config['description']}")
    
    # Time estimate
    print("\n" + "=" * 80)
    print("TIME ESTIMATE")
    print("=" * 80)
    
    time_est = analyzer.estimate_processing_time(doc)
    
    print(f"\nHigh priority pages: {time_est['high_priority']:.1f}s")
    print(f"Medium priority pages: {time_est['medium_priority']:.1f}s")
    print(f"Low priority pages: {time_est['low_priority']:.1f}s")
    print(f"\nTotal estimated time: {time_est['total']:.1f}s")
    
    print("\n" + "=" * 80)
    print("OPTIMIZATION BENEFIT")
    print("=" * 80)
    
    # Compare with naive approach
    naive_time = len(doc) * (0.1 + 0.5 + 2.0)  # All pages with all methods
    optimized_time = time_est['total']
    
    print(f"\nNaive approach (all pages, all methods): {naive_time:.1f}s")
    print(f"Optimized approach (smart prioritization): {optimized_time:.1f}s")
    print(f"Time saved: {naive_time - optimized_time:.1f}s ({((naive_time - optimized_time) / naive_time * 100):.0f}%)")
    
    doc.close()
