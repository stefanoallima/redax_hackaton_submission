# Automated Validation Report

**Date:** 2025-11-14 21:47:00
**Detector:** pii_detector_presidio_v2.py
**Test Cases:** 27

---

## Summary

**Overall Status:** [FAIL]

| Metric | Value |
|--------|-------|
| **Accuracy** | 81.48% |
| **Precision** | 76.19% |
| **Recall** | 100.00% |
| **F1 Score** | 86.49% |
| Tests Passed | 22 / 27 |
| Tests Failed | 5 / 27 |
| Critical Passed | 4 / 7 |
| **Critical Failed** | 3 / 7 |

---

## Detailed Results

### [FAIL] Failed Tests

#### B1-1-FIXED - Job Titles (False Positive Fix) **[CRITICAL]**

- **Status:** FAILED
- **Details:** Expected: NO DETECTION, Detected: ['Chief Technology Officer']
- **Note:** Previously FALSE POSITIVE - Should be fixed by deny list

#### B2-1-FIXED - Organizational Terms (False Positive Fix) **[CRITICAL]**

- **Status:** FAILED
- **Details:** Expected: NO DETECTION, Detected: ['Intergovernativi']
- **Note:** Previously FALSE POSITIVE - Should be fixed by deny list

#### B3-1-FIXED - Document Labels (False Positive Fix) **[CRITICAL]**

- **Status:** FAILED
- **Details:** Expected: NO DETECTION, Detected: ['Firmato Da']
- **Note:** Previously FALSE POSITIVE - Should be fixed by deny list

#### B4-2 - Legal Institutions

- **Status:** FAILED
- **Details:** Expected: NO DETECTION, Detected: ['Corte di Cassazione']

#### B5-1 - Government Agencies

- **Status:** FAILED
- **Details:** Expected: NO DETECTION, Detected: ['INPS']

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
- B1-2-FIXED - Job Titles (False Positive Fix)
- B3-2-FIXED - Document Labels (False Positive Fix)
- B4-1 - Legal Institutions
- B5-2 - Government Agencies
- B7-1 - Legal References
- C1-1 - Invalid Document IDs

---

## Recommendations

[FAIL] **Validation FAILED** - Do NOT proceed

- Fix failed tests before continuing
- Focus on critical failures first
- Re-run validation after fixes

[WARNING] **3 CRITICAL TEST(S) FAILED** - IMMEDIATE ACTION REQUIRED
