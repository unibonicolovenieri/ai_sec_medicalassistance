# 🧠 Integrazione Letta AI - Setup Guide

## Cos'è Letta?

**Letta** (ex MemGPT) è un sistema di memoria persistente per agenti AI che permette:

- 💾 **Memoria a lungo termine** - Gli agenti ricordano conversazioni e dati tra sessioni
- 🔍 **RAG automatico** - Retrieval-Augmented Generation integrato
- 🔒 **Isolamento dati** - Ogni paziente ha un agente dedicato
- 🏥 **Perfetto per dati medici** - Mantiene contesto e cronologia

## Installazione

### ⚡ Setup Veloce (Raccomandato)

**IMPORTANTE**: Per evitare conflitti di dipendenze, Letta viene eseguito come **servizio separato**.

#### Opzione A: Virtual Environment Separato (2 minuti)

```bash
# 1. Crea ambiente Letta separato
mkdir ~/letta-server && cd ~/letta-server
python3 -m venv venv-letta
source venv-letta/bin/activate
pip install letta

# 2. Avvia Letta server
letta server

# 3. In un altro terminale - Setup progetto
cd /Users/luca/Documents/cybersec
source venv/bin/activate
pip install -r requirements.txt  # Velocissimo ora!
```

#### Opzione B: Docker (1 minuto)

```bash
# Usa docker-compose.yml fornito
docker-compose up -d

# Verifica
curl http://localhost:8283/api/health
```

#### Opzione C: Letta Cloud (30 secondi)

```bash
# Registrati su https://cloud.letta.com
# Ottieni API key

# .env
LETTA_BASE_URL=https://api.letta.com
LETTA_API_KEY=your_key_here
```

📖 **Guida dettagliata**: [LETTA_SEPARATE_SETUP.md](./LETTA_SEPARATE_SETUP.md)

### 1. Installa dipendenze progetto

```bash
pip install -r requirements.txt
```

**Note**: `requirements.txt` contiene solo `requests` e `httpx` per comunicare con Letta via HTTP, non il pesante SDK completo.

### 3. Configura variabili ambiente

Crea/aggiorna il file `.env`:

```bash
# Letta Configuration
LETTA_BASE_URL=http://localhost:8283
LETTA_SERVER_URL=http://localhost:8283
LETTA_API_KEY=  # Opzionale per server locale
```

### 4. Verifica installazione

```bash
python -c "from database.letta_client import get_letta_db; db = get_letta_db(); print('✅ Letta disponibile!' if db.is_available() else '❌ Letta non disponibile')"
```

## Architettura

```
┌─────────────────────────────────────────────┐
│           CrewAI Agents                     │
│  (Privacy Guardian, Receptionist, Info)     │
└────────────────┬────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────┐
│         medical_tools.py                    │
│  (authenticate, book_appointment, etc)      │
└────────────────┬────────────────────────────┘
                 │
       ┌─────────┴─────────┐
       │                   │
       ▼                   ▼
┌─────────────┐    ┌──────────────┐
│  Letta AI   │    │  MemoryDB    │
│  (Primary)  │    │  (Fallback)  │
└─────────────┘    └──────────────┘
```

### Flusso dati:

1. **Autenticazione**: 
   - Tool `authenticate_patient` → Letta verifica PIN
   - Crea sessione per paziente

2. **Prenotazione**:
   - Tool `book_appointment` → Salva in Letta agent del paziente
   - Letta memorizza nel core memory + recall memory

3. **Recupero appuntamenti**:
   - Tool `get_my_appointments` → Query RAG su memoria Letta
   - Letta usa semantic search per trovare appuntamenti

## Vantaggi Letta vs Database Tradizionale

| Feature | Letta AI | SQL Database |
|---------|----------|--------------|
| **Memoria contestuale** | ✅ Si ricorda preferenze | ❌ Solo dati raw |
| **Query naturali** | ✅ "quando era ultima visita?" | ❌ Serve query SQL |
| **Apprendimento** | ✅ Impara da interazioni | ❌ Statico |
| **RAG integrato** | ✅ Built-in | ❌ Da implementare |
| **Privacy by design** | ✅ Agente per paziente | ⚠️  Serve gestione ACL |
| **Scalabilità** | ⚠️  Medium | ✅ High |
| **ACID compliance** | ⚠️  Limited | ✅ Full |

## Uso avanzato

### Interrogare memoria direttamente

```python
from database.letta_client import get_letta_db

letta = get_letta_db()

# Ricerca semantica
result = letta.search_in_memory(
    patient_id="PAZ001",
    query="Quando era la mia ultima visita cardiologica?"
)

print(result)
```

### Creare tool custom per agenti

```python
# In medical_tools.py

@tool
def search_patient_history(patient_id: str, query: str) -> str:
    """Cerca nello storico del paziente usando Letta RAG"""
    if not db.is_authenticated(patient_id):
        return "❌ Autenticazione richiesta"
    
    letta = get_letta_db()
    return letta.search_in_memory(patient_id, query)
```

## Monitoraggio

### Visualizza agenti attivi

```bash
letta list agents
```

### Ispeziona memoria di un agente

```bash
letta view agent patient_PAZ001
```

### Log e debug

I log Letta sono in:
```
~/.letta/logs/
```

Abilita verbose logging:
```python
# In letta_client.py
logging.basicConfig(level=logging.DEBUG)
```

## Fallback Strategy

Il sistema implementa **graceful degradation**:

1. ✅ **Letta disponibile** → Usa Letta come primary storage
2. ⚠️  **Letta down** → Fallback automatico a MemoryDB in-memory
3. 🔄 **Letta recovery** → Sync automatico da MemoryDB a Letta

## Best Practices

### 1. Un agente per paziente
```python
# ✅ CORRETTO - Isolamento dati
agent_paz001 = letta.create_agent(name="patient_PAZ001")
agent_paz002 = letta.create_agent(name="patient_PAZ002")

# ❌ SBAGLIATO - Mixing dati
shared_agent = letta.create_agent(name="all_patients")
```

### 2. Sanitizza input
```python
# Prima di salvare in Letta
def sanitize_medical_data(data: dict) -> dict:
    # Rimuovi PII non necessari
    # Hash sensitive fields
    return data
```

### 3. Audit logging
```python
# Logga sempre accessi a dati sensibili
logger.info(f"[AUDIT] {patient_id} accessed appointments at {datetime.now()}")
```

## Troubleshooting

### Problema: "Letta client connessione fallita"

**Soluzione**:
```bash
# Verifica server running
lsof -i :8283

# Riavvia server
letta server --clean
```

### Problema: "Agent not found"

**Soluzione**:
```python
# Resetta cache agenti
letta_db.agents_cache.clear()
```

### Problema: Performance lente

**Soluzione**:
```bash
# Usa PostgreSQL invece di SQLite
export LETTA_PG_URI=postgresql://user:pass@localhost/letta
letta server
```

## Migrazione da MemoryDB a Letta

Script di migrazione:

```python
# scripts/migrate_to_letta.py
from database.letta_client import get_letta_db
from tools.medical_tools import db as memory_db

letta = get_letta_db()

# Migra pazienti
for patient_id in memory_db.patients.keys():
    agent_id = letta._get_or_create_agent(patient_id)
    
    # Migra appuntamenti
    appointments = memory_db.get_appointments(patient_id)
    for apt in appointments:
        letta.store_appointment(patient_id, apt)

print("✅ Migrazione completata")
```

## Risorse

- 📚 [Letta Docs](https://docs.letta.com)
- 🐙 [GitHub](https://github.com/letta-ai/letta)
- 💬 [Discord Community](https://discord.gg/letta)

## Prossimi Step

1. ✅ Setup base completato
2. 🔄 Implementa sync bidirezionale
3. 🔐 Aggiungi encryption at rest
4. 📊 Dashboard monitoraggio
5. 🧪 Test carico con 1000+ pazienti
