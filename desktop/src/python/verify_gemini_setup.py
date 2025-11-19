"""
Gemini Integration Setup Verification Script
Checks that all dependencies, API keys, and code are properly configured

Run with: python verify_gemini_setup.py

This script performs 6 critical checks:
1. google-generativeai package installed
2. GEMINI_API_KEY environment variable configured
3. Learned entities database accessible
4. Gemini client module importable
5. Main IPC handlers present
6. Test Gemini API connection (if key is valid)
"""

import sys
import os
from pathlib import Path

# ANSI colors for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'


def check_google_generativeai():
    """Check if google-generativeai package is installed"""
    try:
        import google.generativeai as genai
        version = genai.__version__
        print(f"{GREEN}[OK] google-generativeai installed (version {version}){RESET}")
        return True, genai
    except ImportError:
        print(f"{RED}[FAIL] google-generativeai not installed{RESET}")
        print(f"{YELLOW}   Fix: cd desktop/src/python && pip install google-generativeai==0.8.3{RESET}")
        return False, None


def check_env_file():
    """Check if .env file exists and has GEMINI_API_KEY"""
    env_path = Path(__file__).parent.parent.parent / '.env'

    if not env_path.exists():
        print(f"{RED}[FAIL] .env file not found at {env_path}{RESET}")
        print(f"{YELLOW}   Fix: cp desktop/.env.example desktop/.env{RESET}")
        return False, None

    # Read .env file
    api_key = None
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip().startswith('GEMINI_API_KEY='):
                api_key = line.strip().split('=', 1)[1]
                break

    if not api_key or api_key == 'your_gemini_api_key_here':
        print(f"{RED}[FAIL] GEMINI_API_KEY not configured in .env{RESET}")
        print(f"{YELLOW}   Fix: Edit desktop/.env and add your API key from https://aistudio.google.com/app/apikey{RESET}")
        return False, None

    # Also set as environment variable for this script
    os.environ['GEMINI_API_KEY'] = api_key

    print(f"{GREEN}[OK] .env file exists with GEMINI_API_KEY configured{RESET}")
    print(f"{BLUE}   Key: {api_key[:10]}...{api_key[-4:]}{RESET}")
    return True, api_key


def check_learned_db():
    """Check if learned_entities_db.py is accessible"""
    try:
        from learned_entities_db import get_learned_db
        db = get_learned_db()
        stats = db.get_stats()

        print(f"{GREEN}[OK] Learned entities database accessible{RESET}")
        print(f"{BLUE}   Total learned: {stats.get('total_learned', 0)} entities{RESET}")
        print(f"{BLUE}   DB path: {db.db_path}{RESET}")
        return True
    except Exception as e:
        print(f"{RED}[FAIL] Learned DB error: {e}{RESET}")
        print(f"{YELLOW}   Check: desktop/src/python/learned_entities_db.py exists{RESET}")
        return False


def check_gemini_client():
    """Check if gemini_client.py is importable"""
    try:
        from gemini_client import get_gemini_detector
        print(f"{GREEN}[OK] Gemini client module importable{RESET}")
        print(f"{BLUE}   Module: desktop/src/python/gemini_client.py{RESET}")
        return True
    except Exception as e:
        print(f"{RED}[FAIL] Gemini client error: {e}{RESET}")
        print(f"{YELLOW}   Check: desktop/src/python/gemini_client.py exists{RESET}")
        return False


def check_main_handlers():
    """Check if main.py has the required IPC handlers"""
    try:
        main_path = Path(__file__).parent / 'main.py'
        with open(main_path, 'r', encoding='utf-8') as f:
            main_content = f.read()

        required_handlers = [
            'gemini_scan',
            'learn_from_gemini',
            'get_learned_stats'
        ]

        missing = []
        for handler in required_handlers:
            if f"'{handler}'" not in main_content and f'"{handler}"' not in main_content:
                missing.append(handler)

        if missing:
            print(f"{RED}[FAIL] Missing IPC handlers in main.py: {', '.join(missing)}{RESET}")
            return False

        print(f"{GREEN}[OK] All required IPC handlers present in main.py{RESET}")
        print(f"{BLUE}   Handlers: {', '.join(required_handlers)}{RESET}")
        return True

    except Exception as e:
        print(f"{RED}[FAIL] Error checking main.py: {e}{RESET}")
        return False


def check_gemini_connection(genai_module, api_key):
    """Test actual connection to Gemini API"""
    if not genai_module or not api_key:
        print(f"{YELLOW}[SKIP] Skipping Gemini API connection test (dependencies not met){RESET}")
        return False

    try:
        print(f"{BLUE}[TESTING] Testing Gemini API connection...{RESET}")
        genai_module.configure(api_key=api_key)

        # Try to list models (lightweight operation)
        models = list(genai_module.list_models())

        # Find gemini-2.5-pro model
        pro_models = [m for m in models if 'gemini-2.5-pro' in m.name.lower()]

        if pro_models:
            print(f"{GREEN}[OK] Gemini API connection successful{RESET}")
            print(f"{BLUE}   Available model: {pro_models[0].name}{RESET}")
            return True
        else:
            print(f"{YELLOW}[WARN] Connected but gemini-2.5-pro not found{RESET}")
            print(f"{BLUE}   Available models: {len(models)}{RESET}")
            return False

    except Exception as e:
        print(f"{RED}[FAIL] Gemini API connection failed: {e}{RESET}")
        print(f"{YELLOW}   Check: API key is valid and has not exceeded quota{RESET}")
        return False


def main():
    """Run all verification checks"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BLUE}Gemini Integration Setup Verification{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")

    checks = {}

    # Check 1: google-generativeai installed
    print(f"{BLUE}[1/6]{RESET} Checking google-generativeai package...")
    checks['genai_installed'], genai_module = check_google_generativeai()
    print()

    # Check 2: .env file and API key
    print(f"{BLUE}[2/6]{RESET} Checking .env configuration...")
    checks['env_configured'], api_key = check_env_file()
    print()

    # Check 3: Learned DB
    print(f"{BLUE}[3/6]{RESET} Checking learned entities database...")
    checks['learned_db'] = check_learned_db()
    print()

    # Check 4: Gemini client
    print(f"{BLUE}[4/6]{RESET} Checking gemini_client.py...")
    checks['gemini_client'] = check_gemini_client()
    print()

    # Check 5: Main IPC handlers
    print(f"{BLUE}[5/6]{RESET} Checking main.py IPC handlers...")
    checks['main_handlers'] = check_main_handlers()
    print()

    # Check 6: Gemini API connection
    print(f"{BLUE}[6/6]{RESET} Testing Gemini API connection...")
    checks['api_connection'] = check_gemini_connection(genai_module, api_key)
    print()

    # Summary
    print(f"{BLUE}{'='*60}{RESET}")
    passed = sum(checks.values())
    total = len(checks)

    if passed == total:
        print(f"{GREEN}[SUCCESS] ALL CHECKS PASSED ({passed}/{total}){RESET}")
        print(f"{GREEN}   Ready for Gemini integration testing!{RESET}")
        print(f"\n{BLUE}Next steps:{RESET}")
        print(f"  1. Run: npm run electron:dev")
        print(f"  2. Upload a PDF")
        print(f"  3. Click 'Analizza con Gemini AI'")
        print(f"  4. Confirm entities in modal")
        print(f"  5. Re-scan same PDF with Standard mode")
        print(f"  6. Verify learned entities appear automatically\n")
        return 0
    else:
        print(f"{YELLOW}[WARNING] SOME CHECKS FAILED ({passed}/{total} passed){RESET}")
        print(f"{YELLOW}   See above for fix instructions{RESET}\n")

        # List failed checks
        failed = [name for name, status in checks.items() if not status]
        print(f"{RED}Failed checks:{RESET}")
        for check_name in failed:
            print(f"  - {check_name}")
        print()
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
