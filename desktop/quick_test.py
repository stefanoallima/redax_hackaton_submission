"""
Quick CLI test - Send commands to backend via stdin/stdout
Simulates what the Electron app does
"""
import sys
import json
import subprocess
from pathlib import Path

def send_command(command):
    """Send command to backend and get response"""
    print(f"\n>>> Sending: {command['action']}")
    print(f"    File: {Path(command.get('file_path', '')).name}")

    # Start Python backend
    python_exe = Path("src/python/venv/Scripts/python.exe")
    main_py = Path("src/python/main.py")

    proc = subprocess.Popen(
        [str(python_exe), str(main_py)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=Path(__file__).parent
    )

    # Send command
    proc.stdin.write(json.dumps(command) + "\n")
    proc.stdin.flush()

    # Read response
    response_line = proc.stdout.readline()

    # Wait for process to complete
    proc.terminate()

    try:
        response = json.loads(response_line)
        return response
    except json.JSONDecodeError:
        print(f"[ERROR] Invalid JSON response: {response_line}")
        return None

def main():
    print("="*70)
    print("QUICK BACKEND TEST")
    print("="*70)

    test_file = Path("test_documents/sentenza con oscuramento 4892_02_2025_civ_oscuramento_noindex Edited Copyiban.pdf")

    if not test_file.exists():
        print(f"\n[ERROR] Test file not found: {test_file}")
        return

    print(f"\nTest file: {test_file.name}")

    # Step 1: Process document
    print("\n" + "-"*70)
    print("Step 1: Processing document...")
    print("-"*70)

    response = send_command({
        "action": "process_document",
        "file_path": str(test_file.absolute())
    })

    if response and response.get("status") == "success":
        print(f"[OK] Document processed")
        print(f"     Pages: {response['metadata']['page_count']}")
        print(f"     Characters: {response['metadata']['total_chars']}")

        entities = response.get("entities", [])
        print(f"     Entities detected: {len(entities)}")

        # Show entity types
        entity_types = {}
        for e in entities:
            entity_types[e['entity_type']] = entity_types.get(e['entity_type'], 0) + 1

        print("\n     Entity types:")
        for etype, count in sorted(entity_types.items()):
            print(f"       - {etype}: {count}")
    else:
        print(f"[ERROR] Failed: {response.get('error') if response else 'No response'}")
        return

    # Step 2: Export redacted PDF
    print("\n" + "-"*70)
    print("Step 2: Exporting redacted PDF...")
    print("-"*70)

    output_file = test_file.parent / f"{test_file.stem}_CLI_TEST_REDACTED.pdf"

    # Select all entities
    for entity in entities:
        entity['accepted'] = True

    response = send_command({
        "action": "export_redacted_pdf",
        "file_path": str(test_file.absolute()),
        "entities": entities,
        "export_txt": False
    })

    if response and response.get("status") == "success":
        print(f"[OK] Redacted PDF created")
        print(f"     Output: {Path(response['output_path']).name}")
        print(f"     Entities redacted: {response['entities_redacted']}")
        print(f"     Mapping table: {Path(response['mapping_table_path']).name}")
    else:
        print(f"[ERROR] Failed: {response.get('error') if response else 'No response'}")
        return

    # Step 3: Verify the output
    print("\n" + "-"*70)
    print("Step 3: Verifying redacted PDF...")
    print("-"*70)

    import fitz

    redacted_pdf = Path(response['output_path'])
    doc = fitz.open(str(redacted_pdf))

    # Check REPUBBLICA ITALIANA on page 1
    page1 = doc[0]
    repubblica = page1.search_for('REPUBBLICA ITALIANA')

    if repubblica:
        print("[OK] REPUBBLICA ITALIANA is VISIBLE (not redacted)")
        print(f"     Position: x={repubblica[0].x0:.1f}-{repubblica[0].x1:.1f}")
    else:
        partial = page1.search_for('ANA')
        if partial:
            print("[FAIL] REPUBBLICA ITALIANA is PARTIALLY REDACTED")
            print("       This means the bug still exists!")
        else:
            print("[FAIL] REPUBBLICA ITALIANA is COMPLETELY REDACTED")

    doc.close()

    print("\n" + "="*70)
    print("TEST COMPLETE")
    print("="*70)

    if repubblica:
        print("\n[SUCCESS] The page numbering fix is working!")
        print("\nYou can now test in the desktop app:")
        print("  1. cd desktop")
        print("  2. npm run electron:dev")
        print("  3. Load the same PDF and verify results")
    else:
        print("\n[FAILURE] Issue still exists")
        print("Please check the logs in src/python/redact.log")

if __name__ == "__main__":
    main()
