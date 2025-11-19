"""
PII Detector Factory - Feature Flag Management

Provides a factory pattern for switching between old and new detector implementations.
Enables gradual rollout and A/B testing in production.

Usage:
    # Use feature flag
    detector = PIIDetectorFactory.create(use_new_architecture=True)

    # Auto-select based on environment variable
    detector = PIIDetectorFactory.create_from_env()

    # Get comparison
    comparison = PIIDetectorFactory.compare(text, depth="balanced")

Author: RedaxAI.app  Team
Date: 2025-11-14
"""

import os
import logging
from typing import Optional, Dict, Any

# Import both detector versions
try:
    from pii_detector_enhanced import EnhancedPIIDetector as OldDetector
    OLD_DETECTOR_AVAILABLE = True
except ImportError:
    print("Warning: Old detector (pii_detector_enhanced.py) not available")
    OLD_DETECTOR_AVAILABLE = False

from pii_detector_integrated import IntegratedPIIDetector as NewDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PIIDetectorFactory:
    """
    Factory for creating PII detectors with feature flag support.
    """

    # Environment variable for feature flag
    ENV_VAR_USE_NEW = "USE_NEW_PII_DETECTOR"

    # Default configuration
    DEFAULT_CONFIG = {
        "use_new_architecture": False,  # Conservative default - use old until validated
        "enable_gliner": True,
        "enable_prefilter": True,
        "enable_italian_context": True,
        "enable_entity_thresholds": True
    }

    @classmethod
    def create(
        cls,
        use_new_architecture: Optional[bool] = None,
        **kwargs
    ):
        """
        Create PII detector based on feature flag.

        Args:
            use_new_architecture: If True, use new integrated architecture.
                                 If False, use old detector.
                                 If None, check environment variable.
            **kwargs: Additional configuration for new detector

        Returns:
            PII detector instance (old or new)

        Example:
            # Explicit selection
            detector = PIIDetectorFactory.create(use_new_architecture=True)

            # Environment-based
            os.environ["USE_NEW_PII_DETECTOR"] = "true"
            detector = PIIDetectorFactory.create()  # Uses new architecture
        """
        # Determine which detector to use
        if use_new_architecture is None:
            use_new_architecture = cls._check_env_flag()

        logger.info(
            f"Creating PII detector: "
            f"{'NEW (integrated)' if use_new_architecture else 'OLD (enhanced)'}"
        )

        if use_new_architecture:
            # Create new integrated detector
            config = {
                "enable_gliner": kwargs.get("enable_gliner", cls.DEFAULT_CONFIG["enable_gliner"]),
                "enable_prefilter": kwargs.get("enable_prefilter", cls.DEFAULT_CONFIG["enable_prefilter"]),
                "enable_italian_context": kwargs.get("enable_italian_context", cls.DEFAULT_CONFIG["enable_italian_context"]),
                "enable_entity_thresholds": kwargs.get("enable_entity_thresholds", cls.DEFAULT_CONFIG["enable_entity_thresholds"])
            }

            detector = NewDetector(**config)
            detector._is_new_architecture = True  # Tag for identification
            return detector

        else:
            # Create old detector (if available)
            if not OLD_DETECTOR_AVAILABLE:
                logger.warning(
                    "Old detector not available - falling back to new architecture"
                )
                return cls.create(use_new_architecture=True, **kwargs)

            detector = OldDetector()
            detector._is_new_architecture = False  # Tag for identification
            return detector

    @classmethod
    def create_from_env(cls, **kwargs):
        """
        Create detector based on environment variable.

        Environment variable:
            USE_NEW_PII_DETECTOR=true/false/1/0

        Example:
            # In terminal or .env file:
            export USE_NEW_PII_DETECTOR=true

            # In Python:
            detector = PIIDetectorFactory.create_from_env()
        """
        return cls.create(use_new_architecture=None, **kwargs)

    @classmethod
    def compare(
        cls,
        text: str,
        depth: str = "balanced",
        **kwargs
    ) -> Dict:
        """
        Run both detectors and compare results.

        Args:
            text: Input text
            depth: Detection depth
            **kwargs: Additional detector configuration

        Returns:
            {
                "old": {...},
                "new": {...},
                "comparison": {...}
            }
        """
        import time

        results = {}

        # Run old detector
        if OLD_DETECTOR_AVAILABLE:
            try:
                old_detector = OldDetector()
                start = time.time()
                old_entities = old_detector.detect_pii(text, depth=depth)
                old_time = time.time() - start

                results["old"] = {
                    "entities": old_entities if isinstance(old_entities, list) else [],
                    "time_ms": round(old_time * 1000, 2),
                    "count": len(old_entities) if isinstance(old_entities, list) else 0
                }
            except Exception as e:
                results["old"] = {"error": str(e)}
        else:
            results["old"] = {"error": "Old detector not available"}

        # Run new detector
        try:
            new_detector = NewDetector(**kwargs)
            start = time.time()
            new_result = new_detector.detect_pii(text, depth=depth)
            new_time = time.time() - start

            results["new"] = {
                "entities": new_result["entities"],
                "time_ms": round(new_time * 1000, 2),
                "count": len(new_result["entities"]),
                "full_result": new_result
            }
        except Exception as e:
            results["new"] = {"error": str(e)}

        # Comparison
        if "error" not in results["old"] and "error" not in results["new"]:
            old_time = results["old"]["time_ms"]
            new_time = results["new"]["time_ms"]
            speedup = old_time / new_time if new_time > 0 else 0

            results["comparison"] = {
                "speedup": round(speedup, 2),
                "time_saved_ms": round(old_time - new_time, 2),
                "entity_diff": results["new"]["count"] - results["old"]["count"],
                "entity_diff_pct": round(
                    (results["new"]["count"] - results["old"]["count"]) / results["old"]["count"] * 100, 1
                ) if results["old"]["count"] > 0 else 0
            }

        return results

    @classmethod
    def _check_env_flag(cls) -> bool:
        """
        Check environment variable for feature flag.

        Returns:
            True if new architecture should be used, False otherwise
        """
        env_value = os.getenv(cls.ENV_VAR_USE_NEW, "false").lower()

        # Parse various boolean representations
        return env_value in ["true", "1", "yes", "on", "enabled"]

    @classmethod
    def get_current_architecture(cls) -> str:
        """
        Get currently active architecture based on environment.

        Returns:
            "new" or "old"
        """
        return "new" if cls._check_env_flag() else "old"


class PIIDetectorWrapper:
    """
    Unified wrapper for both old and new detectors.
    Provides consistent API regardless of underlying implementation.
    """

    def __init__(self, use_new_architecture: Optional[bool] = None, **kwargs):
        """
        Initialize wrapper.

        Args:
            use_new_architecture: Which detector to use (None = check env)
            **kwargs: Configuration for new detector
        """
        self.detector = PIIDetectorFactory.create(
            use_new_architecture=use_new_architecture,
            **kwargs
        )
        self.is_new_architecture = getattr(self.detector, "_is_new_architecture", False)

    def detect_pii(self, text: str, depth: str = "balanced", **kwargs):
        """
        Detect PII with unified API.

        Args:
            text: Input text
            depth: Detection depth
            **kwargs: Additional parameters

        Returns:
            Normalized result format
        """
        if self.is_new_architecture:
            # New detector returns structured dict
            result = self.detector.detect_pii(text, depth=depth, **kwargs)
            return result
        else:
            # Old detector returns list of entities
            entities = self.detector.detect_pii(text, depth=depth)

            # Wrap in new format for consistency
            return {
                "entities": entities if isinstance(entities, list) else [],
                "stats": {
                    "total_entities": len(entities) if isinstance(entities, list) else 0,
                    "by_type": {},
                    "by_source": {"old_detector": len(entities) if isinstance(entities, list) else 0},
                    "avg_confidence": 0.0
                },
                "performance": {
                    "total_time_ms": 0,
                    "entities_per_second": 0
                },
                "metadata": {
                    "architecture": "old",
                    "prefilter_applied": False,
                    "italian_context_filtered": 0
                }
            }

    def get_architecture_info(self) -> Dict:
        """Get information about current detector architecture."""
        return {
            "architecture": "new" if self.is_new_architecture else "old",
            "detector_class": self.detector.__class__.__name__,
            "features": {
                "gliner": getattr(self.detector, "enable_gliner", False) if self.is_new_architecture else False,
                "prefilter": getattr(self.detector, "enable_prefilter", False) if self.is_new_architecture else False,
                "italian_context": getattr(self.detector, "enable_italian_context", False) if self.is_new_architecture else False,
                "entity_thresholds": getattr(self.detector, "enable_entity_thresholds", False) if self.is_new_architecture else False
            }
        }


# Testing/example usage
if __name__ == "__main__":
    print("PII Detector Factory - Test")
    print("=" * 70)

    # Test 1: Explicit selection
    print("\n1. Explicit Selection:")
    detector_old = PIIDetectorFactory.create(use_new_architecture=False)
    print(f"  Old detector: {detector_old.__class__.__name__}")

    detector_new = PIIDetectorFactory.create(use_new_architecture=True)
    print(f"  New detector: {detector_new.__class__.__name__}")

    # Test 2: Environment-based
    print("\n2. Environment-Based Selection:")
    os.environ["USE_NEW_PII_DETECTOR"] = "true"
    detector_env = PIIDetectorFactory.create_from_env()
    print(f"  ENV=true: {detector_env.__class__.__name__}")

    os.environ["USE_NEW_PII_DETECTOR"] = "false"
    detector_env2 = PIIDetectorFactory.create_from_env()
    print(f"  ENV=false: {detector_env2.__class__.__name__}")

    # Test 3: Wrapper
    print("\n3. Unified Wrapper:")
    wrapper = PIIDetectorWrapper(use_new_architecture=True)
    print(f"  Architecture: {wrapper.get_architecture_info()}")

    # Test 4: Comparison (if old detector available)
    if OLD_DETECTOR_AVAILABLE:
        print("\n4. Comparison Test:")
        test_text = "Mario Rossi, CF: RSSMRA85C15H501X"
        comparison = PIIDetectorFactory.compare(test_text)

        print(f"  Old detector: {comparison['old'].get('count', 'N/A')} entities, "
              f"{comparison['old'].get('time_ms', 'N/A')}ms")
        print(f"  New detector: {comparison['new'].get('count', 'N/A')} entities, "
              f"{comparison['new'].get('time_ms', 'N/A')}ms")

        if "comparison" in comparison:
            print(f"  Speedup: {comparison['comparison']['speedup']}x")

    print("\n" + "=" * 70)
    print("Factory test complete")
