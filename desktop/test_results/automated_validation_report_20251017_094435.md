# Automated Validation Report

**Date:** 2025-11-14 09:44:35
**Detector:** pii_detector_presidio_v2.py
**Test Cases:** 27

---

## Summary

**Overall Status:** [PASS]

| Metric | Value |
|--------|-------|
| **Accuracy** | 100.00% |
| **Precision** | 100.00% |
| **Recall** | 100.00% |
| **F1 Score** | 100.00% |
| Tests Passed | 27 / 27 |
| Tests Failed | 0 / 27 |
| Critical Passed | 7 / 7 |
| **Critical Failed** | 0 / 7 |

---

## Detailed Results

### [PASS] Passed Tests

- A1-1 - Simple Names
- A1-2 - Simple Names
- A2-1 - ALL CAPS Names
- A2-2 - ALL CAPS Names
- A3-1-REGRESSION - Apostrophe Names (Title Case)
- A3-2 - Apostrophe Names (Title Case)
- A3-3 - Apostrophe Names (Title Case)
- A4-1 - Apostrophe Names (ALL CAPS)
- A4-2 - Apostrophe Names (ALL CAPS)
- A5-1 - Names in Strong Context
- A6-1 - Italian Document IDs
- A6-2 - Italian Document IDs
- A7-1 - Contact Information
- A7-2 - Contact Information
- A8-1 - ALL CAPS Emails
- A11-1-USER-REPORTED - Emails with Prefixes
- B1-1-FIXED - Job Titles (False Positive Fix)
- B1-2-FIXED - Job Titles (False Positive Fix)
- B2-1-FIXED - Organizational Terms (False Positive Fix)
- B3-1-FIXED - Document Labels (False Positive Fix)
- B3-2-FIXED - Document Labels (False Positive Fix)
- B4-1 - Legal Institutions
- B4-2 - Legal Institutions
- B5-1 - Government Agencies
- B5-2 - Government Agencies
- B7-1 - Legal References
- C1-1 - Invalid Document IDs

---

## Recommendations

[PASS] **Validation PASSED** - Ready to proceed

- Architecture improvements confirmed
- False positive fixes working
- Consider implementing Phase 2 enhancements
