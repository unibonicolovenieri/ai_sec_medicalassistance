# ❓ FAQ - Letta AI Integration

## Generale

### Q: Cos'è Letta AI?
**A:** Letta (ex MemGPT) è un framework che aggiunge **memoria persistente** agli agenti AI. Invece di perdere il contesto tra sessioni, gli agenti Letta "ricordano" tutto permanentemente e possono fare ricerche semantiche nella loro memoria.

### Q: Perché usare Letta invece di un database SQL tradizionale?
**A:** 
| Feature | Letta AI | SQL Database |
|---------|----------|--------------|
| Query naturali | ✅ "quando era l'ultima visita?" | ❌ Serve query SQL esplicita |
| Contesto conversazionale | ✅ Mantiene stato | ❌ Stateless |
| Apprendimento | ✅ Impara da interazioni | ❌ Dati statici |
| RAG integrato | ✅ Built-in | ❌ Da implementare |
| Scalabilità | ⚠️ Buona | ✅ Eccellente |

**Ideale per**: Assistenti conversazionali, chatbot medici, customer support
**Meno ideale per**: Analytics complessi, transazioni ACID critiche

### Q: Letta è obbligatorio?
**A:** No! Il sistema ha **graceful degradation**:
- ✅ **Con Letta**: Funzionalità complete + memoria persistente
- ⚠️ **Senza Letta**: Fallback a MemoryDB in-memory (funziona comunque)

### Q: Quanto costa Letta?
**A:** 
- **Self-hosted** (localhost): Gratis ✅
- **Letta Cloud**: Pay-as-you-go (circa $0.001/query)
- **Hardware needs**: ~2GB RAM, qualsiasi CPU moderna

---

## Setup & Installazione

### Q: Come installo Letta?
**A:**
```bash
# Via pip
pip install letta

# Verifica installazione
letta --version

# Avvia server locale
letta server
```

### Q: Quali porte usa Letta?
**A:** 
- Default: **8283** (HTTP API)
- Configurabile: `letta server --port 9000`

### Q: Come configuro Letta per produzione?
**A:**
```bash
# 1. Usa PostgreSQL invece SQLite
export LETTA_PG_URI="postgresql://user:pass@host/dbname"

# 2. Abilita autenticazione
export LETTA_SERVER_PASS="secure_password"

# 3. Avvia con persistenza
letta server --postgres
```

### Q: Posso usare Letta Cloud invece di self-host?
**A:** Sì! Cambia configurazione:
```python
# .env
LETTA_BASE_URL=https://api.letta.com
LETTA_API_KEY=your_api_key_here
```

Pro: Zero manutenzione, alta disponibilità
Contro: Costi variabili, dati su cloud esterno

---

## Architettura

### Q: Dove vengono salvati i dati in Letta?
**A:** Letta usa tre livelli di memoria:

1. **Core Memory** (sempre caricata): 
   - Info paziente base
   - Preferenze
   - ~2KB max

2. **Recall Memory** (RAG automatico):
   - Appuntamenti
   - Conversazioni recenti
   - Ricerca semantica

3. **Archival Memory** (long-term):
   - Storico completo
   - Archiviato ma recuperabile

```
┌─────────────────────────────┐
│ Core Memory (Hot)           │ ← Sempre in RAM
│  • Patient ID: PAZ001       │
│  • Name: Mario Rossi        │
│  • Preferences: {...}       │
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ Recall Memory (Warm)        │ ← RAG search
│  • Last 100 interactions    │
│  • Recent appointments      │
│  • Conversation state       │
└─────────────────────────────┘
          │
          ▼
┌─────────────────────────────┐
│ Archival Memory (Cold)      │ ← Long-term
│  • Full history             │
│  • Old appointments         │
│  • Archived conversations   │
└─────────────────────────────┘
```

### Q: Un agente per paziente o uno condiviso?
**A:** **SEMPRE un agente per paziente** per:
- 🔒 Isolamento dati (privacy)
- 🎯 Contesto specifico
- ⚡ Performance migliori

```python
# ✅ CORRETTO
agent_paz001 = letta.create_agent(name="patient_PAZ001")
agent_paz002 = letta.create_agent(name="patient_PAZ002")

# ❌ SBAGLIATO
shared_agent = letta.create_agent(name="all_patients")  # Privacy risk!
```

### Q: Cosa succede se Letta va down?
**A:** **Automatic fallback**:
1. Tool rileva errore Letta
2. Switch automatico a MemoryDB
3. Sistema continua a funzionare
4. Al recovery: sync dati

```python
# In medical_tools.py
if letta_db.is_available():
    # Usa Letta
    result = letta_db.store_appointment(...)
else:
    # Fallback
    result = memory_db.add_appointment(...)
```

---

## Privacy & Security

### Q: I dati su Letta sono criptati?
**A:** 
- **At rest**: Dipende da storage backend (PostgreSQL supporta encryption)
- **In transit**: HTTPS se usi Letta Cloud
- **In memory**: No (RAM)

**Best practice**: Cripta PHI sensibili prima di salvare in Letta:
```python
from cryptography.fernet import Fernet

key = Fernet.generate_key()
cipher = Fernet(key)

# Cripta prima di salvare
encrypted_data = cipher.encrypt(patient_data.encode())
letta.store(encrypted_data)
```

### Q: Letta è GDPR compliant?
**A:** Letta è uno strumento, la compliance dipende da come lo usi:

✅ **DO**:
- Anonimizza dati dove possibile
- Implementa right-to-erasure (GDPR Art. 17)
- Log accessi per audit trail
- Data minimization

❌ **DON'T**:
- Salvare PII non necessari
- Condividere agenti tra pazienti
- Ignorare data retention policies

### Q: Come implemento "Right to be Forgotten" (GDPR)?
**A:**
```python
def delete_patient_data(patient_id: str):
    """GDPR Art. 17 - Right to erasure"""
    
    letta = get_letta_db()
    
    # 1. Trova agente paziente
    agent_id = letta._get_or_create_agent(patient_id)
    
    # 2. Elimina agente (e tutta la memoria)
    letta.client.delete_agent(agent_id)
    
    # 3. Rimuovi da cache
    if patient_id in letta.agents_cache:
        del letta.agents_cache[patient_id]
    
    # 4. Log per audit
    logger.info(f"[GDPR] Deleted all data for {patient_id}")
    
    return "✅ Tutti i dati eliminati"
```

### Q: Come faccio audit logging con Letta?
**A:**
```python
# Wrapper con logging
def audit_log_access(func):
    def wrapper(patient_id: str, *args, **kwargs):
        logger.info(f"[AUDIT] {func.__name__} accessed by {patient_id}")
        result = func(patient_id, *args, **kwargs)
        logger.info(f"[AUDIT] {func.__name__} completed for {patient_id}")
        return result
    return wrapper

@audit_log_access
def get_appointments(patient_id: str):
    # ... implementazione
```

---

## Performance

### Q: Letta è veloce abbastanza per produzione?
**A:** Dipende da scale:
- **< 1000 pazienti**: Ottimo ✅ (< 200ms per query)
- **1000-10k pazienti**: Buono ⚠️ (usa PostgreSQL)
- **> 10k pazienti**: Considera sharding o hybrid approach

**Benchmark** (hardware medio):
```
Query singola:        ~150ms
Creazione agente:     ~300ms
RAG search:           ~400ms
Update memoria:       ~100ms
```

### Q: Come ottimizzo performance Letta?
**A:**
1. **Usa PostgreSQL** invece SQLite
2. **Cache agent IDs** (già implementato)
3. **Limita recall memory size** (max 100 items)
4. **Archivia vecchi dati** periodicamente
5. **Connection pooling** per produzione

```python
# Ottimizzazione: Cache warming
class LettaMedicalDB:
    def warmup_cache(self, patient_ids: List[str]):
        """Pre-carica agenti in cache"""
        for pid in patient_ids:
            self._get_or_create_agent(pid)
```

### Q: Quanta RAM serve per Letta?
**A:**
- **Server Letta**: ~500MB base + 50KB per agente
- **1000 agenti**: ~500MB + 50MB = 550MB
- **10000 agenti**: ~500MB + 500MB = 1GB

Raccomandato: **2GB RAM** minimum per produzione

---

## Troubleshooting

### Q: "Connection refused" quando avvio app
**A:** Letta server non in esecuzione:
```bash
# Verifica
lsof -i :8283

# Se vuoto, avvia server
letta server

# Oppure usa fallback
# Sistema funziona comunque senza Letta
```

### Q: "Agent not found" error
**A:**
```python
# Reset cache
letta_db.agents_cache.clear()

# Ricrea agente
agent_id = letta._get_or_create_agent(patient_id)
```

### Q: Query RAG tornano risultati vuoti
**A:** Memoria non popolata:
```python
# Debug: Ispeziona memoria
letta = get_letta_db()
agent_id = letta._get_or_create_agent("PAZ001")
memory = letta.client.get_agent_memory(agent_id)

print(f"Recall items: {len(memory.recall_memory)}")

# Se vuota, popola manualmente
letta.store_appointment("PAZ001", test_appointment)
```

### Q: Performance degradate nel tempo
**A:** Archiva vecchi dati:
```python
def cleanup_old_memories(days=180):
    """Archivia conversazioni > 6 mesi"""
    
    cutoff = datetime.now() - timedelta(days=days)
    
    for agent in letta.client.list_agents():
        # Sposta recall → archival
        letta.client.archive_old_memory(
            agent_id=agent.id,
            before=cutoff
        )
```

### Q: Come faccio debug Letta?
**A:**
```python
# Enable verbose logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("letta")
logger.setLevel(logging.DEBUG)

# Oppure usa Letta CLI
letta view agent patient_PAZ001
letta logs --tail 100
```

---

## Migration & Backup

### Q: Come migro da database esistente a Letta?
**A:** Vedi `EXAMPLES.md` sezione "Migrazione Dati", oppure:
```bash
python scripts/migrate_to_letta.py
```

### Q: Come faccio backup Letta?
**A:**
```bash
# Export completo
python scripts/backup_letta.py

# Output: backup_letta_20251121_103045.json
```

### Q: Posso esportare dati Letta in formato standard?
**A:** Sì:
```python
def export_to_json(patient_id: str):
    """Export paziente in JSON portable"""
    
    letta = get_letta_db()
    agent_id = letta._get_or_create_agent(patient_id)
    memory = letta.client.get_agent_memory(agent_id)
    
    export_data = {
        "patient_id": patient_id,
        "core_memory": memory.core_memory,
        "appointments": [],  # Parse da recall memory
        "exported_at": datetime.now().isoformat()
    }
    
    with open(f"{patient_id}_export.json", "w") as f:
        json.dump(export_data, f, indent=2)
```

---

## Integrazione

### Q: Posso usare Letta con altri LLM (non Gemini)?
**A:** Sì! Letta supporta:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Local LLMs (Ollama, LMStudio)

```python
# In letta_client.py
agent = self.client.create_agent(
    name=f"patient_{patient_id}",
    llm_config={
        "model": "gpt-4",  # o "claude-3", "llama2"
        "context_window": 8000
    }
)
```

### Q: Posso usare Letta con frontend React/Next.js?
**A:** Assolutamente:
```javascript
// frontend/api/letta.js
const queryPatient = async (patientId, query) => {
  const response = await fetch('/api/letta/query', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({patient_id: patientId, query})
  });
  
  return await response.json();
};
```

### Q: Letta funziona con Docker?
**A:** Sì:
```dockerfile
# Dockerfile
FROM python:3.11-slim

# Install Letta
RUN pip install letta

# App code
COPY . /app
WORKDIR /app

# Start both
CMD letta server & python main.py
```

---

## Best Practices

### Q: Quanti dati devo salvare in Letta?
**A:** **Data minimization**:
- ✅ Salva: Appuntamenti, preferenze, note conversazione
- ❌ Non salvare: PII non necessari, dati ridondanti, file pesanti

**Regola**: Se non serve per conversazione futura, non salvare.

### Q: Quando devo usare Letta vs database tradizionale?
**A:**

**Usa Letta per**:
- Assistenti conversazionali
- Contesto multi-turno
- Query in linguaggio naturale
- Personalizzazione dinamica

**Usa SQL per**:
- Transazioni finanziarie
- Analytics complessi
- Reporting strutturato
- Compliance strict (ACID)

**Hybrid approach** (raccomandato):
```
┌─────────────────┐
│   Letta AI      │ ← Conversazioni, contesto
│  (Hot layer)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  PostgreSQL     │ ← Dati strutturati, backup
│  (Cold layer)   │
└─────────────────┘
```

### Q: Come testo integrazione Letta?
**A:**
```bash
# Test suite inclusa
python test_letta_integration.py

# Test manuale
python -c "
from database.letta_client import get_letta_db
letta = get_letta_db()
print('✅ OK' if letta.is_available() else '❌ KO')
"
```

---

## Costi & Licensing

### Q: Quanto costa far girare Letta?
**A:**

**Self-hosted** (raccomandato per inizio):
- Server: $5-10/mese (VPS 2GB RAM)
- Storage: ~100MB per 1000 pazienti
- LLM API: Gemini ~$0.0001/query

**Letta Cloud**:
- ~$0.001 per query
- Storage incluso
- No infrastructure management

### Q: Letta è open source?
**A:** Sì! Licenza Apache 2.0
- ✅ Uso commerciale OK
- ✅ Modifiche OK
- ✅ Distribuzione OK

---

## Support

### Q: Dove trovo più documentazione?
**A:**
- 📚 [Letta Docs ufficiali](https://docs.letta.com)
- 📖 [LETTA_SETUP.md](./LETTA_SETUP.md) (questo repo)
- 💡 [EXAMPLES.md](./EXAMPLES.md) (esempi pratici)
- 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md) (architettura)

### Q: Dove posso chiedere aiuto?
**A:**
- 💬 [Letta Discord](https://discord.gg/letta)
- 🐛 [GitHub Issues](https://github.com/unibonicolovenieri/MedicAI-Assistant/issues)
- 📧 Email: [support@yourproject.com]

### Q: Come contribuisco al progetto?
**A:**
1. Fork repository
2. Crea branch feature
3. Commit modifiche
4. Apri Pull Request

Grazie! 🙏
