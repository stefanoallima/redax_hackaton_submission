"""
Test GLiNER for PII Detection
Compare with Presidio results
"""
import time
import psutil
import os
from typing import Dict, List

# Italian legal text samples for testing
TEST_SAMPLES = {
    "employment_contract": """
    CONTRATTO DI LAVORO SUBORDINATO

    Il presente contratto è stipulato tra:

    DATORE DI LAVORO:
    Società: TechItalia S.p.A.
    Sede Legale: Via Milano 45, 20100 Milano (MI)
    Partita IVA: 12345678901
    Rappresentata da: Dott. Giovanni Bianchi
    Codice Fiscale: BNCGNN75H15F205Z

    LAVORATORE:
    Nome: Maria Rossi
    Data di nascita: 15/08/1990
    Luogo di nascita: Roma (RM)
    Residenza: Via Roma 123, 00100 Roma (RM)
    Codice Fiscale: RSSMRA90M55H501A
    Telefono: +39 333 1234567
    Email: maria.rossi@email.com
    IBAN: IT60 X054 2811 1010 0000 0123 456

    INFORMAZIONI BANCARIE:
    Conto corrente: IBAN IT75 K030 6909 6061 0000 0012 345
    Intestato a: Maria Rossi
    Banca: UniCredit S.p.A.
    """,

    "court_filing": """
    TRIBUNALE DI ROMA
    Sezione Civile

    Il sottoscritto Avv. Paolo Verdi (CF: VRDPLA80A01H501B),
    con studio in Piazza Venezia 10, 00186 Roma,
    telefono 06 12345678, email: p.verdi@studiolegale.it

    in nome e per conto di:
    Sig. Luca Neri, nato a Napoli il 20/03/1985,
    residente in Via Napoli 78, 80100 Napoli (NA),
    CF: NRELCU85C20F839D, tel: 081 9876543

    DEPOSITA
    il seguente atto...
    """,

    "privacy_doc": """
    INFORMATIVA PRIVACY

    Il Titolare del trattamento è:
    Studio Legale Associato Rossi & Partners
    Via Dante 56, 50100 Firenze (FI)
    P.IVA: 98765432109
    Email: privacy@studiorossi.it
    PEC: studiorossi@pec.it
    Tel: +39 055 1234567

    Il Responsabile della Protezione dei Dati è:
    Dott.ssa Elena Gialli
    CF: GLLLNE88D50D612C
    Email: dpo@studiorossi.it
    """
}


def test_gliner_installation():
    """Test if GLiNER is installed and working"""
    print("=" * 80)
    print("TEST 1: GLiNER Installation")
    print("=" * 80)

    try:
        from gliner import GLiNER
        print("[OK] GLiNER module imported successfully")
        return True
    except ImportError as e:
        print(f"[ERROR] GLiNER not installed: {e}")
        print("\nInstall with: pip install gliner")
        return False


def test_gliner_model_download():
    """Test downloading the gliner_multi_pii-v1 model"""
    print("\n" + "=" * 80)
    print("TEST 2: GLiNER Model Download")
    print("=" * 80)

    try:
        from gliner import GLiNER

        print("Downloading gliner_multi_pii-v1 model...")
        print("(This may take a few minutes on first run)")

        start_time = time.time()
        model = GLiNER.from_pretrained("urchade/gliner_multi_pii-v1")
        download_time = time.time() - start_time

        print(f"[OK] Model downloaded successfully in {download_time:.2f}s")
        return model
    except Exception as e:
        print(f"[ERROR] Error downloading model: {e}")
        return None


def test_gliner_detection(model, text: str, labels: List[str]) -> Dict:
    """Test GLiNER PII detection on text"""

    try:
        start_time = time.time()

        # Get memory before
        process = psutil.Process(os.getpid())
        mem_before = process.memory_info().rss / 1024 / 1024  # MB

        # Run detection
        entities = model.predict_entities(text, labels, threshold=0.5)

        # Get memory after
        mem_after = process.memory_info().rss / 1024 / 1024  # MB
        detection_time = time.time() - start_time

        return {
            "status": "success",
            "entities": entities,
            "count": len(entities),
            "time": detection_time,
            "memory_used": mem_after - mem_before
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def test_presidio_detection(text: str) -> Dict:
    """Test Presidio detection for comparison"""

    try:
        from pii_detector import PIIDetector

        detector = PIIDetector()
        start_time = time.time()

        entities = detector.detect_pii(text, language="it")
        detection_time = time.time() - start_time

        return {
            "status": "success",
            "entities": entities,
            "count": len(entities),
            "time": detection_time
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }


def compare_results(gliner_result: Dict, presidio_result: Dict, sample_name: str):
    """Compare GLiNER and Presidio results"""

    print(f"\n{'=' * 80}")
    print(f"COMPARISON: {sample_name}")
    print("=" * 80)

    # GLiNER results
    print(f"\n>> GLiNER Results:")
    print(f"   Entities found: {gliner_result['count']}")
    print(f"   Detection time: {gliner_result['time']:.3f}s")
    print(f"   Memory used: {gliner_result.get('memory_used', 0):.2f} MB")

    if gliner_result['count'] > 0:
        print(f"\n   Detected entities:")
        for i, entity in enumerate(gliner_result['entities'][:10], 1):  # Show first 10
            print(f"   {i}. {entity['label']}: '{entity['text']}' (score: {entity['score']:.2f})")
        if gliner_result['count'] > 10:
            print(f"   ... and {gliner_result['count'] - 10} more")

    # Presidio results
    print(f"\n>> Presidio Results:")
    print(f"   Entities found: {presidio_result['count']}")
    print(f"   Detection time: {presidio_result['time']:.3f}s")

    if presidio_result['count'] > 0:
        print(f"\n   Detected entities:")
        for i, entity in enumerate(presidio_result['entities'][:10], 1):
            print(f"   {i}. {entity['entity_type']}: '{entity['text']}' (score: {entity['score']:.2f})")
        if presidio_result['count'] > 10:
            print(f"   ... and {presidio_result['count'] - 10} more")

    # Comparison
    print(f"\n>> Comparison:")
    print(f"   Coverage: GLiNER found {gliner_result['count'] - presidio_result['count']:+d} entities")
    print(f"   Speed: {'GLiNER' if gliner_result['time'] < presidio_result['time'] else 'Presidio'} was faster")
    print(f"   Time difference: {abs(gliner_result['time'] - presidio_result['time']):.3f}s")


def main():
    """Run all tests"""

    print("\n" + "=" * 80)
    print("GLiNER PII Detection Test Suite")
    print("=" * 80 + "\n")

    # Test 1: Installation
    if not test_gliner_installation():
        return

    # Test 2: Model download
    model = test_gliner_model_download()
    if model is None:
        return

    # Define PII labels for GLiNER
    pii_labels = [
        "person",
        "email",
        "phone number",
        "address",
        "date",
        "fiscal code",
        "codice fiscale",
        "iban",
        "bank account",
        "passport number",
        "vat number",
        "partita iva",
        "tax id",
        "organization",
        "location",
        "pec"
    ]

    print("\n" + "=" * 80)
    print("TEST 3: Detection on Italian Legal Text")
    print("=" * 80)
    print(f"\nPII Labels: {', '.join(pii_labels)}")

    # Test on each sample
    for sample_name, text in TEST_SAMPLES.items():
        print(f"\n\n{'-' * 80}")
        print(f"Testing: {sample_name.replace('_', ' ').title()}")
        print('-' * 80)

        # Test GLiNER
        print("\nRunning GLiNER detection...")
        gliner_result = test_gliner_detection(model, text, pii_labels)

        # Test Presidio
        print("Running Presidio detection...")
        presidio_result = test_presidio_detection(text)

        # Compare
        if gliner_result['status'] == 'success' and presidio_result['status'] == 'success':
            compare_results(gliner_result, presidio_result, sample_name)
        else:
            print(f"\n❌ Error in detection:")
            if gliner_result['status'] == 'error':
                print(f"   GLiNER: {gliner_result['error']}")
            if presidio_result['status'] == 'error':
                print(f"   Presidio: {presidio_result['error']}")

    # Final summary
    print("\n\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print("\nAll tests completed!")
    print("\nNext steps:")
    print("1. Review detection results above")
    print("2. Compare accuracy and speed")
    print("3. Decide on integration strategy")
    print("4. Consider GLiNER as Layer 2 in pipeline")
    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    main()
