"""
End-to-End Test: Spatial Context Accuracy on Lease Documents
Tests the spatial context analyzer on real Italian lease agreements
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from spatial_integration import detect_pii_with_spatial_support, create_detector
from pii_detector_spatial import SpatialPIIDetector

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeaseDocumentAccuracyTest:
    """
    Test spatial context analyzer on lease documents
    Measures accuracy of field type detection
    """

    def __init__(self, demo_data_dir: str):
        """
        Initialize test

        Args:
            demo_data_dir: Path to directory with lease PDFs
        """
        self.demo_data_dir = Path(demo_data_dir)
        self.results = []

    def get_lease_documents(self) -> List[Path]:
        """Get all unredacted lease documents"""
        lease_files = list(self.demo_data_dir.glob("lease_*_UNREDACTED.pdf"))

        # Filter out already redacted versions
        lease_files = [
            f for f in lease_files
            if "_REDACTED" not in f.stem or f.stem.endswith("_UNREDACTED")
        ]

        return sorted(lease_files)

    def test_single_document(
        self,
        pdf_path: Path,
        detector: SpatialPIIDetector
    ) -> Dict[str, Any]:
        """
        Test spatial context on a single document

        Args:
            pdf_path: Path to PDF file
            detector: Spatial PII detector

        Returns:
            Test result dictionary
        """
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing: {pdf_path.name}")
        logger.info('='*80)

        start_time = time.time()

        try:
            # Detect PII with spatial context
            result = detector.detect_pii_from_pdf(
                pdf_path=str(pdf_path),
                depth="balanced",
                language="it"
            )

            processing_time = time.time() - start_time

            # Extract results
            entities = result.get("entities", [])
            metadata = result.get("metadata", {})
            spatial_context = metadata.get("spatial_context", {})

            # Count field context coverage
            entities_with_context = 0
            entities_without_context = 0
            field_type_counts = {}

            for entity in entities:
                if entity.get("field_context"):
                    entities_with_context += 1

                    field_type = entity["field_context"]["inferred_field_type"]
                    field_type_counts[field_type] = field_type_counts.get(field_type, 0) + 1
                else:
                    entities_without_context += 1

            # Calculate metrics
            total_entities = len(entities)
            coverage_rate = (entities_with_context / total_entities * 100) if total_entities > 0 else 0

            test_result = {
                "file": pdf_path.name,
                "status": "success",
                "processing_time_ms": round(processing_time * 1000, 2),
                "total_entities": total_entities,
                "entities_with_context": entities_with_context,
                "entities_without_context": entities_without_context,
                "coverage_rate": round(coverage_rate, 2),
                "labels_found": spatial_context.get("labels_found", 0),
                "field_types": field_type_counts,
                "spatial_analysis_time_ms": spatial_context.get("spatial_analysis_time_ms", 0)
            }

            # Print summary
            logger.info(f"\n📊 RESULTS for {pdf_path.name}:")
            logger.info(f"  Total entities detected: {total_entities}")
            logger.info(f"  With field context: {entities_with_context}")
            logger.info(f"  Without context: {entities_without_context}")
            logger.info(f"  Coverage rate: {coverage_rate:.1f}%")
            logger.info(f"  Labels found: {spatial_context.get('labels_found', 0)}")
            logger.info(f"  Processing time: {processing_time*1000:.0f}ms")

            if field_type_counts:
                logger.info(f"\n  Field Types Detected:")
                for field_type, count in sorted(field_type_counts.items()):
                    logger.info(f"    - {field_type}: {count}")

            # Show sample entities
            logger.info(f"\n  Sample Entities (first 5):")
            for i, entity in enumerate(entities[:5], 1):
                entity_text = entity.get("text", "N/A")[:30]
                entity_type = entity.get("entity_type", "N/A")
                score = entity.get("score", 0)

                fc = entity.get("field_context")
                if fc:
                    field_type = fc.get("inferred_field_type", "N/A")
                    label = fc.get("nearby_label", "N/A")
                    logger.info(
                        f"    {i}. \"{entity_text}\" - {entity_type} "
                        f"(score: {score:.2f}, field: {field_type}, label: \"{label}\")"
                    )
                else:
                    logger.info(
                        f"    {i}. \"{entity_text}\" - {entity_type} "
                        f"(score: {score:.2f}, field: NO CONTEXT)"
                    )

            return test_result

        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {e}", exc_info=True)

            return {
                "file": pdf_path.name,
                "status": "error",
                "error": str(e),
                "processing_time_ms": round((time.time() - start_time) * 1000, 2)
            }

    def run_full_test_suite(self) -> Dict[str, Any]:
        """
        Run accuracy test on all lease documents

        Returns:
            Comprehensive test results
        """
        logger.info("\n" + "="*80)
        logger.info("SPATIAL CONTEXT ACCURACY TEST - LEASE DOCUMENTS")
        logger.info("="*80)

        # Get lease documents
        lease_docs = self.get_lease_documents()

        logger.info(f"\nFound {len(lease_docs)} lease documents to test")

        if not lease_docs:
            logger.error("No lease documents found!")
            return {"status": "error", "error": "No lease documents found"}

        # Create detector
        logger.info("\nInitializing Spatial PII Detector...")

        detector = create_detector(
            enable_spatial=True,
            enable_gliner=True,
            enable_italian_context=True,
            enable_entity_thresholds=True
        )

        if not isinstance(detector, SpatialPIIDetector):
            logger.error("Failed to create spatial detector!")
            return {"status": "error", "error": "Spatial detector not available"}

        logger.info("✓ Spatial detector initialized")

        # Test each document
        self.results = []

        for pdf_path in lease_docs:
            result = self.test_single_document(pdf_path, detector)
            self.results.append(result)

        # Calculate aggregate metrics
        summary = self._calculate_summary()

        return summary

    def _calculate_summary(self) -> Dict[str, Any]:
        """Calculate aggregate test metrics"""

        successful_tests = [r for r in self.results if r["status"] == "success"]
        failed_tests = [r for r in self.results if r["status"] == "error"]

        if not successful_tests:
            return {
                "status": "error",
                "error": "No successful tests",
                "failed_count": len(failed_tests)
            }

        # Aggregate metrics
        total_entities = sum(r["total_entities"] for r in successful_tests)
        total_with_context = sum(r["entities_with_context"] for r in successful_tests)
        total_without_context = sum(r["entities_without_context"] for r in successful_tests)

        avg_coverage = sum(r["coverage_rate"] for r in successful_tests) / len(successful_tests)
        avg_processing_time = sum(r["processing_time_ms"] for r in successful_tests) / len(successful_tests)

        # Field type distribution
        all_field_types = {}
        for r in successful_tests:
            for field_type, count in r.get("field_types", {}).items():
                all_field_types[field_type] = all_field_types.get(field_type, 0) + count

        summary = {
            "status": "success",
            "documents_tested": len(self.results),
            "successful": len(successful_tests),
            "failed": len(failed_tests),
            "total_entities_detected": total_entities,
            "entities_with_field_context": total_with_context,
            "entities_without_context": total_without_context,
            "average_coverage_rate": round(avg_coverage, 2),
            "average_processing_time_ms": round(avg_processing_time, 2),
            "field_type_distribution": all_field_types,
            "individual_results": self.results
        }

        # Print summary
        logger.info("\n\n" + "="*80)
        logger.info("📊 AGGREGATE TEST RESULTS")
        logger.info("="*80)

        logger.info(f"\nDocuments Tested: {len(self.results)}")
        logger.info(f"  ✓ Successful: {len(successful_tests)}")
        logger.info(f"  ✗ Failed: {len(failed_tests)}")

        logger.info(f"\n🎯 Detection Metrics:")
        logger.info(f"  Total entities detected: {total_entities}")
        logger.info(f"  With field context: {total_with_context} ({total_with_context/total_entities*100:.1f}%)")
        logger.info(f"  Without context: {total_without_context} ({total_without_context/total_entities*100:.1f}%)")

        logger.info(f"\n📈 Quality Metrics:")
        logger.info(f"  Average coverage rate: {avg_coverage:.1f}%")
        logger.info(f"  Average processing time: {avg_processing_time:.0f}ms")

        if all_field_types:
            logger.info(f"\n🏷️  Field Types Across All Documents:")
            for field_type, count in sorted(all_field_types.items(), key=lambda x: x[1], reverse=True):
                percentage = count / total_with_context * 100
                logger.info(f"  {field_type}: {count} ({percentage:.1f}%)")

        # Success criteria
        logger.info(f"\n✅ SUCCESS CRITERIA:")
        logger.info(f"  Coverage rate ≥ 70%: {'✓ PASS' if avg_coverage >= 70 else '✗ FAIL'} ({avg_coverage:.1f}%)")
        logger.info(f"  Processing time ≤ 5000ms: {'✓ PASS' if avg_processing_time <= 5000 else '✗ FAIL'} ({avg_processing_time:.0f}ms)")
        logger.info(f"  Success rate = 100%: {'✓ PASS' if len(failed_tests) == 0 else '✗ FAIL'} ({len(successful_tests)}/{len(self.results)})")

        overall_pass = (
            avg_coverage >= 70 and
            avg_processing_time <= 5000 and
            len(failed_tests) == 0
        )

        logger.info(f"\n{'✅ OVERALL: PASS' if overall_pass else '❌ OVERALL: FAIL'}")

        return summary

    def save_results(self, output_path: str):
        """Save test results to JSON file"""
        summary = self._calculate_summary()

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)

        logger.info(f"\n💾 Results saved to: {output_path}")


def main():
    """Main test runner"""

    # Get demo data directory
    script_dir = Path(__file__).parent
    demo_data_dir = script_dir.parent.parent / "demo_data"

    if not demo_data_dir.exists():
        print(f"❌ Demo data directory not found: {demo_data_dir}")
        sys.exit(1)

    # Create test instance
    test = LeaseDocumentAccuracyTest(str(demo_data_dir))

    # Run tests
    summary = test.run_full_test_suite()

    # Save results
    results_path = script_dir / "test_results_spatial_lease.json"
    test.save_results(str(results_path))

    # Exit with appropriate code
    if summary.get("status") == "success":
        # Check if overall pass
        avg_coverage = summary.get("average_coverage_rate", 0)
        avg_time = summary.get("average_processing_time_ms", 0)
        failed_count = summary.get("failed", 0)

        if avg_coverage >= 70 and avg_time <= 5000 and failed_count == 0:
            logger.info("\n✅ All tests passed!")
            sys.exit(0)
        else:
            logger.warning("\n⚠️  Some success criteria not met")
            sys.exit(1)
    else:
        logger.error("\n❌ Test suite failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
