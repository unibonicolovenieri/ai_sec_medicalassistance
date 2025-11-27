#!/usr/bin/env python3
"""
Quick setup script per Medical AI Assistant
"""

import os
import sys
import subprocess
from pathlib import Path

BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
RESET = '\033[0m'

def print_header(text):
    print(f"\n{BLUE}{'='*70}{RESET}")
    print(f"{BLUE}{text.center(70)}{RESET}")
    print(f"{BLUE}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_warning(text):
    print(f"{YELLOW}⚠️  {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def run_command(cmd, check=True):
    """Esegui comando shell"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=check,
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError:
        return False

def check_python_version():
    """Verifica versione Python"""
    print_header("1. Verifica Python")
    
    version = sys.version_info
    if version.major >= 3 and version.minor >= 8:
        print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print_error(f"Python {version.major}.{version.minor} non supportato")
        print_warning("Richiesto: Python 3.8+")
        return False

def check_venv():
    """Verifica virtual environment"""
    print_header("2. Virtual Environment")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Virtual environment attivo")
        return True
    else:
        print_warning("Virtual environment non attivo")
        print("\n💡 Attiva con:")
        print("   python3 -m venv venv")
        print("   source venv/bin/activate")
        return False

def check_dependencies():
    """Verifica dipendenze installate"""
    print_header("3. Dipendenze")
    
    required = {
        'crewai': 'CrewAI',
        'letta': 'Letta AI',
        'openai': 'OpenAI SDK',
        'pydantic': 'Pydantic'
    }
    
    all_ok = True
    for package, name in required.items():
        try:
            __import__(package)
            print_success(f"{name} installato")
        except ImportError:
            print_error(f"{name} mancante")
            all_ok = False
    
    if not all_ok:
        print("\n💡 Installa con:")
        print("   pip install -r requirements.txt")
    
    return all_ok

def check_env_file():
    """Verifica file .env"""
    print_header("4. Configurazione")
    
    env_file = Path(".env")
    
    if not env_file.exists():
        print_warning(".env non trovato")
        print("\n💡 Crea da template:")
        print("   cp .env.example .env")
        print("   # Poi edita .env e inserisci GEMINI_API_KEY")
        return False
    
    # Verifica GEMINI_API_KEY
    with open(env_file) as f:
        content = f.read()
        if 'GEMINI_API_KEY=' in content and 'your_gemini' not in content:
            print_success(".env configurato")
            return True
        else:
            print_warning(".env presente ma GEMINI_API_KEY non configurata")
            print("\n💡 Edita .env e inserisci la tua API key")
            return False

def check_letta_server():
    """Verifica Letta server"""
    print_header("5. Letta Server (Opzionale)")
    
    # Check se letta è installato
    if not run_command("which letta", check=False):
        print_warning("Letta CLI non installato")
        print("\n💡 Installa con:")
        print("   pip install letta")
        return False
    
    # Check se server è in running
    if run_command("curl -s http://localhost:8283/health > /dev/null 2>&1", check=False):
        print_success("Letta server in esecuzione")
        return True
    else:
        print_warning("Letta server non in esecuzione")
        print("\n💡 Avvia con:")
        print("   letta server")
        print("\nNOTA: Sistema funziona anche senza Letta (usa fallback in-memory)")
        return False

def run_tests():
    """Esegui test integrazione"""
    print_header("6. Test Sistema")
    
    print("Eseguo test integrazione...\n")
    
    if run_command("python test_letta_integration.py"):
        print_success("Test passati!")
        return True
    else:
        print_error("Alcuni test falliti")
        return False

def main():
    """Main setup flow"""
    os.chdir(Path(__file__).parent)
    
    print(f"\n{BLUE}{'🏥'*35}{RESET}")
    print(f"{BLUE}MEDICAL AI ASSISTANT - SETUP{RESET}".center(80))
    print(f"{BLUE}{'🏥'*35}{RESET}")
    
    results = {
        'Python': check_python_version(),
        'VirtualEnv': check_venv(),
        'Dependencies': check_dependencies(),
        'Configuration': check_env_file(),
        'Letta': check_letta_server()
    }
    
    # Summary
    print_header("SUMMARY")
    
    critical_ok = results['Python'] and results['Configuration']
    all_ok = all(results.values())
    
    for check, status in results.items():
        if status:
            print_success(f"{check}")
        else:
            symbol = "⚠️ " if check == "Letta" else "❌"
            print(f"{symbol} {check}")
    
    print()
    
    if critical_ok:
        print_success("Setup base completato! Sistema pronto.")
        print("\n🚀 Avvia con:")
        print("   python main.py")
        
        if not results['Letta']:
            print("\n💡 Per funzionalità complete:")
            print("   1. pip install letta")
            print("   2. letta server")
            print("   3. python main.py")
        
        # Opzionale: run tests
        print("\n🧪 Vuoi eseguire i test? (y/n): ", end='')
        if input().lower() == 'y':
            run_tests()
        
    else:
        print_error("Setup incompleto. Segui le istruzioni sopra.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Setup interrotto{RESET}")
        sys.exit(1)
