"""
Detection Configuration Handler
Manages user-configurable detection settings
"""
import logging
from typing import Dict, List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DetectionConfig:
    """User-configurable detection settings"""
    
    # Detection depth level
    depth: str = 'balanced'  # fast, balanced, thorough, maximum
    
    # Focus areas (triggers enhanced detection)
    focus_areas: List[str] = None
    
    # Custom keywords for enhanced detection
    custom_keywords: List[str] = None
    
    # Method toggles
    enable_llm: bool = True
    enable_visual: bool = False
    
    def __post_init__(self):
        if self.focus_areas is None:
            self.focus_areas = []
        if self.custom_keywords is None:
            self.custom_keywords = []
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DetectionConfig':
        """Create config from dictionary"""
        return cls(
            depth=data.get('depth', 'balanced'),
            focus_areas=data.get('focusAreas', []),
            custom_keywords=data.get('customKeywords', []),
            enable_llm=data.get('enableLLM', True),
            enable_visual=data.get('enableVisual', False)
        )
    
    def get_keywords(self) -> List[str]:
        """Get all keywords (focus areas + custom)"""
        # Predefined keywords for focus areas
        FOCUS_AREA_KEYWORDS = {
            'iban': ['iban', 'conto', 'bancario', 'bonifico'],
            'cf': ['codice fiscale', 'cf', 'c.f.', 'codice', 'fiscale'],
            'contact': ['telefono', 'email', 'tel', 'fax', 'cellulare', 'cell'],
            'address': ['indirizzo', 'residente', 'domicilio', 'via', 'piazza', 'corso'],
            'personal': ['nato', 'nascita', 'età', 'sesso', 'data di nascita'],
            'financial': ['stipendio', 'pagamento', 'importo', 'euro', 'retribuzione'],
            'medical': ['diagnosi', 'terapia', 'medico', 'paziente', 'malattia'],
            'legal': ['sentenza', 'tribunale', 'giudice', 'avvocato', 'causa']
        }
        
        keywords = []
        
        # Add keywords from selected focus areas
        for area in self.focus_areas:
            if area in FOCUS_AREA_KEYWORDS:
                keywords.extend(FOCUS_AREA_KEYWORDS[area])
        
        # Add custom keywords
        keywords.extend(self.custom_keywords)
        
        # Remove duplicates and return
        return list(set(keywords))
    
    def should_use_llm(self, page_text: str = None, is_priority_page: bool = False) -> bool:
        """
        Determine if LLM should be used for this page
        
        Args:
            page_text: Text content of the page
            is_priority_page: Whether page is high priority (first/last 3)
            
        Returns:
            bool: True if LLM should be used
        """
        # Check if LLM is enabled
        if not self.enable_llm:
            return False
        
        # Depth-based logic
        if self.depth == 'fast':
            return False  # No LLM in fast mode
        
        if self.depth == 'maximum':
            return True  # LLM on all pages in maximum mode
        
        # For balanced/thorough: use LLM on priority pages or keyword pages
        if is_priority_page:
            return True
        
        # Check for keywords in page text
        if page_text:
            keywords = self.get_keywords()
            page_lower = page_text.lower()
            
            for keyword in keywords:
                if keyword.lower() in page_lower:
                    logger.info(f"Keyword '{keyword}' found - triggering LLM")
                    return True
        
        return False
    
    def should_use_visual(self, has_images: bool = False, is_priority_page: bool = False) -> bool:
        """
        Determine if visual detection should be used for this page
        
        Args:
            has_images: Whether page has embedded images
            is_priority_page: Whether page is high priority
            
        Returns:
            bool: True if visual detection should be used
        """
        # Check if visual is enabled
        if not self.enable_visual:
            return False
        
        # Depth-based logic
        if self.depth in ['fast', 'balanced']:
            return False  # No visual in fast/balanced mode
        
        if self.depth == 'maximum':
            return True  # Visual on all pages in maximum mode
        
        # For thorough: use visual on priority pages or pages with images
        if is_priority_page or has_images:
            return True
        
        return False
    
    def get_time_estimate(self, total_pages: int, priority_pages: int, keyword_pages: int, image_pages: int) -> Dict:
        """
        Estimate processing time based on configuration
        
        Args:
            total_pages: Total number of pages
            priority_pages: Number of high-priority pages
            keyword_pages: Number of pages with keywords
            image_pages: Number of pages with images
            
        Returns:
            dict with time estimates
        """
        TIME_PER_PAGE = {
            'regex': 0.1,
            'llm': 0.5,
            'visual': 2.0
        }
        
        # Regex always runs on all pages
        regex_time = total_pages * TIME_PER_PAGE['regex']
        
        # LLM time depends on depth
        if self.depth == 'fast':
            llm_time = 0
        elif self.depth == 'maximum':
            llm_time = total_pages * TIME_PER_PAGE['llm']
        else:  # balanced or thorough
            llm_pages = priority_pages + keyword_pages
            llm_time = llm_pages * TIME_PER_PAGE['llm']
        
        # Visual time depends on depth
        if self.depth in ['fast', 'balanced']:
            visual_time = 0
        elif self.depth == 'maximum':
            visual_time = total_pages * TIME_PER_PAGE['visual']
        else:  # thorough
            visual_pages = min(priority_pages + image_pages, total_pages)
            visual_time = visual_pages * TIME_PER_PAGE['visual']
        
        total_time = regex_time + llm_time + visual_time
        
        return {
            'regex': regex_time,
            'llm': llm_time,
            'visual': visual_time,
            'total': total_time,
            'breakdown': {
                'fast': f"{regex_time:.1f}s",
                'enhanced': f"{llm_time + visual_time:.1f}s",
                'total': f"{total_time:.1f}s"
            }
        }


# Example usage
if __name__ == "__main__":
    # Test different configurations
    
    print("=" * 80)
    print("DETECTION CONFIGURATION EXAMPLES")
    print("=" * 80)
    
    # Example 1: Fast mode
    print("\n1. FAST MODE")
    print("-" * 80)
    config_fast = DetectionConfig(depth='fast', enable_llm=False, enable_visual=False)
    print(f"Depth: {config_fast.depth}")
    print(f"LLM enabled: {config_fast.enable_llm}")
    print(f"Visual enabled: {config_fast.enable_visual}")
    
    time_est = config_fast.get_time_estimate(
        total_pages=50,
        priority_pages=6,
        keyword_pages=8,
        image_pages=3
    )
    print(f"Estimated time: {time_est['total']:.1f}s")
    print(f"  - Regex: {time_est['regex']:.1f}s")
    print(f"  - LLM: {time_est['llm']:.1f}s")
    print(f"  - Visual: {time_est['visual']:.1f}s")
    
    # Example 2: Balanced with focus areas
    print("\n2. BALANCED MODE with IBAN focus")
    print("-" * 80)
    config_balanced = DetectionConfig(
        depth='balanced',
        focus_areas=['iban', 'cf'],
        custom_keywords=['società', 'contratto'],
        enable_llm=True,
        enable_visual=False
    )
    print(f"Depth: {config_balanced.depth}")
    print(f"Focus areas: {config_balanced.focus_areas}")
    print(f"Keywords: {config_balanced.get_keywords()[:5]}...")
    
    time_est = config_balanced.get_time_estimate(
        total_pages=50,
        priority_pages=6,
        keyword_pages=12,  # More pages have IBAN/CF keywords
        image_pages=3
    )
    print(f"Estimated time: {time_est['total']:.1f}s")
    
    # Test keyword detection
    test_text = "Il pagamento sarà effettuato tramite IBAN IT60..."
    should_llm = config_balanced.should_use_llm(test_text, is_priority_page=False)
    print(f"Should use LLM on page with IBAN keyword: {should_llm}")
    
    # Example 3: Thorough mode
    print("\n3. THOROUGH MODE")
    print("-" * 80)
    config_thorough = DetectionConfig(
        depth='thorough',
        enable_llm=True,
        enable_visual=True
    )
    print(f"Depth: {config_thorough.depth}")
    
    time_est = config_thorough.get_time_estimate(
        total_pages=50,
        priority_pages=6,
        keyword_pages=8,
        image_pages=3
    )
    print(f"Estimated time: {time_est['total']:.1f}s")
    print(f"  - Regex: {time_est['regex']:.1f}s")
    print(f"  - LLM: {time_est['llm']:.1f}s")
    print(f"  - Visual: {time_est['visual']:.1f}s")
    
    # Example 4: Maximum mode
    print("\n4. MAXIMUM MODE")
    print("-" * 80)
    config_max = DetectionConfig(
        depth='maximum',
        enable_llm=True,
        enable_visual=True
    )
    print(f"Depth: {config_max.depth}")
    
    time_est = config_max.get_time_estimate(
        total_pages=50,
        priority_pages=6,
        keyword_pages=8,
        image_pages=3
    )
    print(f"Estimated time: {time_est['total']:.1f}s (⚠️ Slow but thorough)")
    print(f"  - Regex: {time_est['regex']:.1f}s")
    print(f"  - LLM: {time_est['llm']:.1f}s (all pages)")
    print(f"  - Visual: {time_est['visual']:.1f}s (all pages)")
    
    print("\n" + "=" * 80)
    print("COMPARISON")
    print("=" * 80)
    
    configs = [
        ('Fast', config_fast),
        ('Balanced', config_balanced),
        ('Thorough', config_thorough),
        ('Maximum', config_max)
    ]
    
    for name, cfg in configs:
        time_est = cfg.get_time_estimate(50, 6, 8, 3)
        print(f"{name:12} {time_est['total']:6.1f}s  (LLM: {cfg.enable_llm}, Visual: {cfg.enable_visual})")
