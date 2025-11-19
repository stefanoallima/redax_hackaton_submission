"""
Minimal GLiNER test to isolate the issue
"""
import os
os.environ['HF_HUB_DISABLE_SYMLINKS_WARNING'] = '1'
os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'

print("Step 1: Import GLiNER...")
try:
    from gliner import GLiNER
    print("[OK] Import successful")
except Exception as e:
    print(f"[FAIL] Import failed: {e}")
    exit(1)

print("\nStep 2: Check ONNX Runtime...")
try:
    import onnxruntime as ort
    print(f"[OK] ONNX Runtime {ort.__version__}")
    print(f"  Providers: {ort.get_available_providers()}")
except Exception as e:
    print(f"[FAIL] ONNX Runtime error: {e}")
    exit(1)

print("\nStep 3: Load model (this is where it might fail)...")
try:
    import sys
    print(f"  Python: {sys.version}")
    print(f"  Loading from cache...")

    # Try with explicit local_files_only to avoid download issues
    model = GLiNER.from_pretrained(
        "urchade/gliner_multi_pii-v1",
        local_files_only=False
    )
    print("[OK] Model loaded successfully!")

    # Quick test
    text = "Mario Rossi, email: test@example.com"
    entities = model.predict_entities(text, ["person", "email"], threshold=0.5)
    print(f"[OK] Detected {len(entities)} entities: {[e['label'] for e in entities]}")

except Exception as e:
    print(f"[FAIL] Model loading failed: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

print("\n[SUCCESS] All tests passed!")
