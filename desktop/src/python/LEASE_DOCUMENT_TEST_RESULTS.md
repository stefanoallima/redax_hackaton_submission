# Lease Document Test Results - Spatial Context Analysis

## Executive Summary

**Test Date:** 2025-11-20
**Documents Tested:** 10 English residential lease agreements
**Overall Result:** ❌ **FAIL** (0% coverage rate)

## Test Metrics

| Metric | Result | Target | Status |
|--------|--------|--------|--------|
| **Documents Tested** | 10 | 10 | ✅ PASS |
| **Success Rate** | 100% (10/10) | 100% | ✅ PASS |
| **Total Entities Detected** | 227 | N/A | ✅ |
| **Field Context Coverage** | 0 (0.0%) | ≥70% | ❌ FAIL |
| **Average Processing Time** | 2,471ms | ≤5,000ms | ✅ PASS |

## Detailed Results

### Detection Performance

- **Total PII entities detected:** 227
- **Entities with field context:** 0 (0%)
- **Entities without context:** 227 (100%)
- **Labels found:** 0 across all documents
- **Field type distribution:** None (no labels detected)

### Sample Entities Detected

Common entities found across all lease documents:
- **EMAIL_ADDRESS**: sarah.thompson@email.com, amanda.moore@email.com, etc.
- **LOCATION**: San Francisco, California
- **DATE_TIME**: November 07, 1995, February 09, 2025
- **ORGANIZATION**: AM Residential Lease Agreement
- **PHONE_NUMBER**: (415) 555-XXXX format

### Processing Time

| Document | Time (ms) | Entities | Labels Found |
|----------|-----------|----------|--------------|
| lease_01 | 23,904 | 21 | 0 |
| lease_02 | 1,147 | 23 | 0 |
| lease_03 | 1,141 | 20 | 0 |
| lease_04 | 1,177 | 21 | 0 |
| lease_05 | 1,195 | 22 | 0 |
| lease_06 | 1,242 | 24 | 0 |
| lease_07 | 1,200 | 23 | 0 |
| lease_08 | 1,171 | 23 | 0 |
| lease_09 | 1,180 | 27 | 0 |
| lease_10 | 1,366 | 23 | 0 |
| **Average** | **2,471** | **22.7** | **0** |

**Note:** lease_01 took significantly longer (23.9s) due to model loading. Subsequent documents averaged ~1.2s.

## Root Cause Analysis

### Why Labels Were Not Detected

Analysis of lease_01_UNREDACTED.pdf reveals the document **DOES contain field labels**, but in a format not matched by current patterns:

**Document Structure:**
```
1. PARTIES
BETWEEN:
Landlord: Sarah Thompson
Address: 4667 Valencia Street, San Francisco, CA 94100
Phone: (415) 555-6224
Email: sarah.thompson@email.com
SSN: 122-80-4080

AND:
Tenant: Amanda Moore
Current Address: 386 Channel Street, San Francisco, CA 94103
Phone: (415) 555-9943
Email: amanda.moore@email.com
SSN: 188-12-3166
Date of Birth: November 07, 1995
```

**Labels Present:**
- `Landlord:` → Should match PERSON
- `Address:` → Should match ADDRESS
- `Phone:` → Should match PHONE
- `Email:` → Should match EMAIL
- `SSN:` → Should match TAX_ID
- `Tenant:` → Should match PERSON
- `Date of Birth:` → Should match DATE

### Pattern Matching Issues

**Current patterns in `spatial_context_analyzer.py`:**
```python
'PERSON': [
    r'^\s*Nome\s*[:\-]?\s*$',     # Italian: Nome
    r'^\s*Name\s*[:\-]?\s*$',     # English: Name
    # Missing: Landlord, Tenant
]
```

**Issues:**
1. **Inline values:** Patterns expect labels on separate lines (`$` end anchor)
   - Current: `r'^\s*Name\s*[:\-]?\s*$'` (expects "Name:" alone on line)
   - Actual: `"Landlord: Sarah Thompson"` (value on same line)

2. **Missing patterns:** "Landlord" and "Tenant" not in PERSON patterns

3. **English focus:** Patterns include both Italian and English, but lease docs use specific legal terms not covered

## Recommendations

### Immediate Fixes (High Priority)

#### 1. Update Pattern Matching

**Modify `spatial_context_analyzer.py` line 81-164:**

```python
FIELD_PATTERNS = {
    'PERSON': [
        # Italian
        r'^\s*Nome\s*[:\-]',           # Remove $ to allow inline values
        r'^\s*Cognome\s*[:\-]',
        r'^\s*Nominativo\s*[:\-]',
        # English
        r'^\s*Name\s*[:\-]',
        r'^\s*Full\s+Name\s*[:\-]',
        r'^\s*Landlord\s*[:\-]',       # NEW: Lease-specific
        r'^\s*Tenant\s*[:\-]',         # NEW: Lease-specific
        r'^\s*Lessor\s*[:\-]',         # NEW: Legal term
        r'^\s*Lessee\s*[:\-]',         # NEW: Legal term
    ],
    'TAX_ID': [
        # Italian
        r'^\s*Codice\s+Fiscale\s*[:\-]',
        r'^\s*CF\s*[:\-]',
        # English
        r'^\s*Tax\s+ID\s*[:\-]',
        r'^\s*SSN\s*[:\-]',            # NEW: Social Security Number
    ],
    'DATE': [
        # Italian
        r'^\s*Data\s*[:\-]',
        r'^\s*Data\s+di\s+nascita\s*[:\-]',
        # English
        r'^\s*Date\s*[:\-]',
        r'^\s*Date\s+of\s+Birth\s*[:\-]',  # Existing
        r'^\s*DOB\s*[:\-]',
    ],
    # ... other patterns
}
```

**Key changes:**
- Remove `\s*$` end anchor to allow values on same line
- Add lease-specific terms: Landlord, Tenant, Lessor, Lessee
- Add SSN pattern for English documents

#### 2. Adjust Text Extraction Strategy

**Modify `pii_detector_spatial.py` line 245-280:**

Current approach creates approximate bounding boxes. For better accuracy:

```python
def _enrich_entities_with_context(self, entities, text, labels):
    """Enhanced: Extract labels from same-line patterns"""

    for entity in entities:
        # NEW: Check if label appears on same line as entity
        entity_text = entity.get("text", "")
        start_pos = entity.get("start", 0)

        # Look at text around entity (50 chars before)
        context_start = max(0, start_pos - 50)
        context = text[context_start:start_pos]

        # Check for label patterns in context
        for field_type, patterns in self.spatial_analyzer.compiled_patterns.items():
            for pattern in patterns:
                if pattern.search(context):
                    entity["field_context"] = {
                        "inferred_field_type": field_type,
                        "nearby_label": pattern.pattern,
                        "confidence": 0.85,  # Lower confidence for same-line
                        "reasoning": "Found label in same-line context"
                    }
                    break
```

### Medium Priority Enhancements

#### 3. Add Lease-Specific Patterns

Create `lease_patterns.py`:

```python
LEASE_SPECIFIC_PATTERNS = {
    'PERSON': [
        r'Owner\s*[:\-]',
        r'Property\s+Owner\s*[:\-]',
        r'Renter\s*[:\-]',
        r'Occupant\s*[:\-]',
    ],
    'ADDRESS': [
        r'Property\s+Address\s*[:\-]',
        r'Rental\s+Property\s*[:\-]',
        r'Current\s+Address\s*[:\-]',
        r'Mailing\s+Address\s*[:\-]',
    ],
    'AMOUNT': [
        r'Monthly\s+Rent\s*[:\-]',
        r'Security\s+Deposit\s*[:\-]',
        r'Rent\s+Amount\s*[:\-]',
    ]
}
```

#### 4. Implement Multi-Line Label Detection

For patterns like:
```
BETWEEN:
Landlord: Sarah Thompson
```

Detect "BETWEEN:" as context, then associate with following fields.

### Long-Term Improvements

#### 5. Machine Learning Approach

Train a model on annotated lease documents to:
- Detect custom label patterns
- Handle multi-line context
- Adapt to different lease formats

#### 6. Template Recognition

Build a template library:
- Detect common lease formats (residential, commercial, short-term)
- Apply template-specific field mappings
- Handle variations within templates

## Expected Impact After Fixes

### Coverage Rate Projection

With pattern updates (removing `$` anchor and adding lease terms):

| Metric | Current | After Fix | Improvement |
|--------|---------|-----------|-------------|
| Labels Found | 0 | ~8-12 per doc | +100% |
| Coverage Rate | 0% | 60-80% | +60-80% |
| Confidence | N/A | 0.75-0.90 | High |

### Entities Likely to Get Context

**High confidence (90%+):**
- Email addresses near "Email:" labels
- Phone numbers near "Phone:" labels
- SSNs near "SSN:" labels

**Medium confidence (70-89%):**
- Names near "Landlord:", "Tenant:" labels
- Addresses near "Address:" labels
- Dates near "Date of Birth:" labels

**Low confidence (<70%):**
- Organizations (may not have clear labels)
- Locations (often narrative context)

## Implementation Plan

### Phase 1: Pattern Updates (1 hour)
1. Update `FIELD_PATTERNS` in `spatial_context_analyzer.py`
2. Remove `$` end anchors
3. Add lease-specific terms
4. Test on sample lease documents

### Phase 2: Context Matching (2 hours)
1. Implement same-line context detection
2. Add 50-char context window for label matching
3. Adjust confidence scores based on proximity

### Phase 3: Validation (1 hour)
1. Re-run test suite on all 10 lease documents
2. Verify coverage rate ≥70%
3. Generate updated test report

**Total Estimated Time:** 4 hours

## Testing Command

Re-run test after fixes:
```bash
cd desktop/src/python
./venv/Scripts/python.exe test_spatial_lease_accuracy.py
```

Expected output after fixes:
```
📊 AGGREGATE TEST RESULTS
Documents Tested: 10
  ✓ Successful: 10

🎯 Detection Metrics:
  Total entities detected: ~227
  With field context: ~150 (66%)
  Without context: ~77 (34%)

📈 Quality Metrics:
  Average coverage rate: 66.0%
  Average processing time: 2500ms

✅ SUCCESS CRITERIA:
  Coverage rate ≥ 70%: ⚠️  MARGINAL (66.0%)
  Processing time ≤ 5000ms: ✓ PASS (2500ms)
  Success rate = 100%: ✓ PASS (10/10)
```

## Conclusion

**Current Status:** The spatial context analyzer is **technically functional** but requires pattern updates to handle lease document formatting.

**Root Cause:** Pattern mismatch, not fundamental implementation issue

**Fix Complexity:** Low - primarily configuration changes

**Expected Outcome:** 60-80% coverage rate after pattern updates

**Recommendation:** Proceed with pattern updates and re-test. The core spatial analysis logic is sound and processes documents efficiently.

---

**Report Generated:** 2025-11-20
**Full Results:** `test_results_spatial_lease.json`
**Test Script:** `test_spatial_lease_accuracy.py`
