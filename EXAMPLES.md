# 💡 Esempi Pratici - Letta AI Integration

## Scenario 1: Primo Utilizzo Paziente

### Step 1: Creazione Agente Letta

Quando un nuovo paziente si registra, viene creato automaticamente un agente Letta dedicato:

```python
from database.letta_client import get_letta_db

letta = get_letta_db()

# Automatico alla prima autenticazione
agent_id = letta._get_or_create_agent("PAZ003")

# Letta crea:
# - Core memory con info paziente
# - Recall memory (vuota inizialmente)
# - Archival memory per storico
```

**Output Letta:**
```
✅ Creato agente Letta per PAZ003
Agent ID: agt_abc123xyz
```

### Step 2: Prima Prenotazione

```python
# User interagisce
result = crew.process_query(
    "Vorrei prenotare una visita generale per lunedì prossimo alle 10",
    patient_id="PAZ003",
    pin="789012"
)
```

**Cosa succede in Letta:**

1. **Autenticazione**: Verifica PIN nell'agente PAZ003
2. **Salvataggio**: Memorizza appuntamento nella recall memory
3. **Contesto**: Aggiorna preferenze (orario mattina)

```json
// Letta Memory Update
{
  "type": "appointment_created",
  "timestamp": "2025-11-21T10:30:00Z",
  "data": {
    "date": "2025-11-25",
    "time": "10:00",
    "type": "Visita generale",
    "doctor": "Dr. Verdi"
  },
  "context": {
    "user_preference": "morning_slots",
    "recurring": false
  }
}
```

## Scenario 2: Query Semantica

Il potere di Letta è nella **ricerca semantica**. L'utente può chiedere in linguaggio naturale:

### Esempio A: Storico Visite

```python
# User
"Quando era la mia ultima visita dal cardiologo?"

# Letta processa
┌─────────────────────────────────────┐
│ 1. Embedding query                  │
│    keywords: [ultima, visita,       │
│               cardiologo]            │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│ 2. Search in PAZ003 recall memory   │
│    Matches:                         │
│    - [2025-09-10] Visita cardio ✅  │
│    - [2025-03-15] ECG              │
│    - [2024-12-20] Visita cardio     │
└─────────────────────────────────────┘
          ↓
┌─────────────────────────────────────┐
│ 3. Generate response                │
│    "La tua ultima visita            │
│     cardiologica era il             │
│     10 settembre 2025 con           │
│     Dr. Verdi."                     │
└─────────────────────────────────────┘
```

**Codice:**

```python
from database.letta_client import get_letta_db

letta = get_letta_db()

response = letta.search_in_memory(
    patient_id="PAZ003",
    query="Quando era la mia ultima visita dal cardiologo?"
)

print(response)
# Output: "La tua ultima visita cardiologica era il 10 settembre 2025..."
```

### Esempio B: Preferenze Implicite

```python
# User (seconda prenotazione)
"Vorrei prenotare come l'altra volta"

# Letta ricorda
┌─────────────────────────────────────┐
│ Recall Memory Search:               │
│ - Ultima prenotazione: 10:00        │
│ - Tipo: Visita generale             │
│ - Dottore: Dr. Verdi                │
│ - Preferenza: mattina               │
└─────────────────────────────────────┘

# Response
"Perfetto! Vuoi prenotare una visita generale 
alle 10:00 con Dr. Verdi? Che giorno preferisci?"
```

## Scenario 3: Multi-Turn Conversation

Letta mantiene il **contesto conversazionale** tra turni:

```python
# Turn 1
User: "Ho bisogno di una visita"
Agent: "Certo! Che tipo di visita? Generale o specialistica?"

# Turn 2
User: "Generale, possibilmente mattina"
Agent: "Ho disponibilità lunedì 25/11 alle 09:00 o 10:30. Quale preferisci?"

# Turn 3
User: "La prima"
Agent: "Confermo visita generale lunedì 25/11 alle 09:00 con Dr. Verdi?"

# Turn 4
User: "Sì grazie"
Agent: "✅ Prenotato! Ti invio conferma via SMS."
```

**Letta Memory durante conversazione:**

```json
{
  "conversation_state": {
    "intent": "book_appointment",
    "appointment_type": "generale",
    "time_preference": "mattina",
    "proposed_slots": ["2025-11-25T09:00", "2025-11-25T10:30"],
    "selected_slot": "2025-11-25T09:00",
    "confirmed": true
  }
}
```

## Scenario 4: Integrazione con Tool Custom

### Tool: Ricorda Preferenze

```python
# In medical_tools.py

@tool
def remember_patient_preference(patient_id: str, preference_type: str, value: str) -> str:
    """
    Salva preferenza paziente in Letta per ricordi futuri.
    
    Args:
        patient_id: ID paziente
        preference_type: Tipo (doctor, time_slot, visit_type)
        value: Valore preferenza
    """
    if not db.is_authenticated(patient_id):
        return "❌ Autenticazione richiesta"
    
    letta = get_letta_db()
    
    # Salva in core memory Letta
    message = f"PREFERENCE UPDATE: {preference_type} = {value}"
    
    response = letta.client.send_message(
        agent_id=letta._get_or_create_agent(patient_id),
        message=message,
        role="system"
    )
    
    return f"✅ Preferenza '{preference_type}' salvata: {value}"


# Uso
result = remember_patient_preference(
    patient_id="PAZ003",
    preference_type="preferred_doctor",
    value="Dr. Verdi"
)
```

### Tool: Analizza Pattern Visite

```python
@tool
def analyze_visit_patterns(patient_id: str) -> str:
    """
    Analizza pattern visite usando Letta per insights.
    """
    if not db.is_authenticated(patient_id):
        return "❌ Autenticazione richiesta"
    
    letta = get_letta_db()
    
    query = """
    Analizza le mie visite passate e dimmi:
    1. Frequenza visite (ogni quanto vengo?)
    2. Tipo visite più comuni
    3. Orari preferiti
    4. Suggerimenti per prossimo check-up
    """
    
    response = letta.search_in_memory(patient_id, query)
    return response


# Uso
insights = analyze_visit_patterns("PAZ003")
print(insights)

# Output da Letta:
"""
📊 Analisi tue visite:

1. Frequenza: Ogni 3-4 mesi
2. Tipo comune: Controllo generale (60%)
3. Orari preferiti: 09:00-11:00 (mattina)
4. Prossimo check-up suggerito: Febbraio 2026

💡 Consiglio: Prenota già ora per slot mattutino!
"""
```

## Scenario 5: Migrazione Dati Esistenti

Se hai già dati in DB tradizionale, puoi migrarli in Letta:

```python
# scripts/migrate_to_letta.py

from database.letta_client import get_letta_db
from tools.medical_tools import db as memory_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def migrate_patient_data():
    """Migra dati da MemoryDB a Letta"""
    
    letta = get_letta_db()
    
    if not letta.is_available():
        logger.error("Letta non disponibile")
        return
    
    # Itera pazienti
    for patient_id, patient_data in memory_db.patients.items():
        logger.info(f"Migrating {patient_id}...")
        
        # 1. Crea agente
        agent_id = letta._get_or_create_agent(patient_id)
        
        # 2. Popola core memory
        letta.client.send_message(
            agent_id=agent_id,
            message=f"""PATIENT DATA IMPORT:
            Name: {patient_data['name']}
            DOB: {patient_data['dob']}
            Phone: {patient_data['phone']}
            """,
            role="system"
        )
        
        # 3. Migra appuntamenti
        appointments = [
            apt for apt in memory_db.appointments 
            if apt['patient_id'] == patient_id
        ]
        
        for apt in appointments:
            letta.store_appointment(patient_id, apt)
            logger.info(f"  ✅ Migrated appointment {apt['id']}")
        
        logger.info(f"✅ {patient_id} migrated ({len(appointments)} appointments)")
    
    logger.info("🎉 Migration completed!")


if __name__ == "__main__":
    migrate_patient_data()
```

**Esegui migrazione:**

```bash
python scripts/migrate_to_letta.py
```

## Scenario 6: Backup e Restore

### Backup Memory Letta

```python
# scripts/backup_letta.py

from database.letta_client import get_letta_db
import json
from datetime import datetime

def backup_all_patients():
    """Backup completo memoria Letta"""
    
    letta = get_letta_db()
    
    backup_data = {
        "timestamp": datetime.now().isoformat(),
        "patients": []
    }
    
    # Per ogni agente
    agents = letta.client.list_agents()
    
    for agent in agents:
        if agent.name.startswith("patient_"):
            patient_id = agent.name.replace("patient_", "")
            
            # Estrai memoria
            memory = letta.client.get_agent_memory(agent.id)
            
            backup_data["patients"].append({
                "patient_id": patient_id,
                "agent_id": agent.id,
                "core_memory": memory.core_memory,
                "recall_memory": memory.recall_memory
            })
    
    # Salva
    filename = f"backup_letta_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, 'w') as f:
        json.dump(backup_data, f, indent=2)
    
    print(f"✅ Backup salvato: {filename}")


if __name__ == "__main__":
    backup_all_patients()
```

### Restore da Backup

```python
# scripts/restore_letta.py

def restore_from_backup(backup_file: str):
    """Restore memoria da backup"""
    
    letta = get_letta_db()
    
    with open(backup_file) as f:
        backup_data = json.load(f)
    
    for patient in backup_data["patients"]:
        patient_id = patient["patient_id"]
        
        # Ricrea agente
        agent_id = letta._get_or_create_agent(patient_id)
        
        # Restore core memory
        letta.client.update_agent_memory(
            agent_id=agent_id,
            core_memory=patient["core_memory"]
        )
        
        print(f"✅ Restored {patient_id}")
    
    print("🎉 Restore completato!")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python restore_letta.py <backup_file>")
        sys.exit(1)
    
    restore_from_backup(sys.argv[1])
```

## Scenario 7: Monitoring e Analytics

### Dashboard Utilizzo Letta

```python
# scripts/letta_stats.py

from database.letta_client import get_letta_db
from collections import Counter

def get_letta_stats():
    """Statistiche utilizzo Letta"""
    
    letta = get_letta_db()
    
    agents = letta.client.list_agents()
    patient_agents = [a for a in agents if a.name.startswith("patient_")]
    
    stats = {
        "total_patients": len(patient_agents),
        "total_appointments": 0,
        "memory_usage": {},
        "most_active": []
    }
    
    for agent in patient_agents:
        # Conta appuntamenti
        memory = letta.client.get_agent_memory(agent.id)
        appointments = len([
            m for m in memory.recall_memory 
            if "appointment" in m.lower()
        ])
        
        stats["total_appointments"] += appointments
        stats["most_active"].append({
            "patient": agent.name,
            "appointments": appointments
        })
    
    # Sort più attivi
    stats["most_active"].sort(key=lambda x: x["appointments"], reverse=True)
    
    return stats


def print_stats():
    stats = get_letta_stats()
    
    print("📊 LETTA STATISTICS")
    print("=" * 50)
    print(f"Total Patients: {stats['total_patients']}")
    print(f"Total Appointments: {stats['total_appointments']}")
    print(f"\nTop 5 Most Active Patients:")
    
    for patient in stats["most_active"][:5]:
        print(f"  • {patient['patient']}: {patient['appointments']} appointments")


if __name__ == "__main__":
    print_stats()
```

## Best Practices

### ✅ DO

1. **Un agente per paziente** - Mai mischiare dati
2. **Salva sempre contesto** - Preferenze, storia, feedback
3. **Query semantiche** - Sfrutta il RAG di Letta
4. **Backup regolare** - Export memoria periodicamente
5. **Log appropriati** - Traccia accessi per GDPR

### ❌ DON'T

1. **Non condividere agenti** - Privacy violation
2. **Non salvare PIN in chiaro** - Sempre hash (bcrypt)
3. **Non ignorare fallback** - Sistema deve funzionare anche senza Letta
4. **Non sovra-popolare memoria** - Pulisci dati vecchi
5. **Non esporre agent_id** - Informazione interna

## Troubleshooting

### Problema: "Agent creation failed"

```python
# Debug
letta = get_letta_db()
print(f"Letta available: {letta.is_available()}")

# Check logs
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Problema: "Memory search returns empty"

```python
# Verifica popolazione memoria
agent_id = letta._get_or_create_agent("PAZ001")
memory = letta.client.get_agent_memory(agent_id)

print(f"Core: {memory.core_memory}")
print(f"Recall: {len(memory.recall_memory)} items")
```

### Problema: Performance lente

```python
# Usa PostgreSQL invece SQLite
# .env
LETTA_PG_URI=postgresql://user:pass@localhost/letta

# Rebuild con Postgres backend
letta server --postgres
```

## Risorse Extra

- 📚 [Letta Documentation](https://docs.letta.com)
- 💬 [Discord Community](https://discord.gg/letta)
- 🐙 [GitHub Examples](https://github.com/letta-ai/letta/tree/main/examples)
- 📺 [Video Tutorials](https://www.youtube.com/@letta-ai)
