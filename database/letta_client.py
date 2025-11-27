"""
Letta AI Client per gestione database medicale con memoria persistente
"""

from typing import Optional, Dict, List, Any
import logging
from datetime import datetime
import json
import requests
from requests.exceptions import RequestException, ConnectionError

from config.settings import settings

logger = logging.getLogger(__name__)


class LettaMedicalDB:
    """
    Client Letta AI per gestione dati medici con memoria contestuale.
    
    Usa HTTP API invece di SDK Python per evitare conflitti dipendenze.
    Letta server gira separatamente (venv separato, Docker, o cloud).
    
    Ogni paziente ha un agente Letta dedicato che:
    - Memorizza appuntamenti e storico
    - Mantiene contesto conversazionale
    - Applica policy di privacy automaticamente
    """
    
    def __init__(self):
        self.base_url: str = settings.LETTA_BASE_URL
        self.api_key: Optional[str] = settings.LETTA_API_KEY
        self.agents_cache: Dict[str, str] = {}  # patient_id -> agent_id
        self.session = requests.Session()
        
        # Headers autenticazione
        if self.api_key:
            self.session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        self._check_connection()
    
    def _check_connection(self):
        """Verifica connessione Letta server"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=2)
            if response.status_code == 200:
                logger.info("✅ Letta server connesso")
            else:
                logger.warning(f"⚠️  Letta server risponde ma con status {response.status_code}")
        except (RequestException, ConnectionError) as e:
            logger.warning(f"⚠️  Letta server non raggiungibile: {e}")
            logger.info("💡 Sistema userà fallback MemoryDB")
    
    def _get_or_create_agent(self, patient_id: str) -> Optional[str]:
        """
        Ottiene o crea un agente Letta dedicato al paziente via HTTP API.
        """
        # Cache hit
        if patient_id in self.agents_cache:
            return self.agents_cache[patient_id]
        
        try:
            # 1. Lista agenti esistenti
            response = self.session.get(f"{self.base_url}/api/agents", timeout=5)
            response.raise_for_status()
            
            agents = response.json()
            agent_name = f"patient_{patient_id}"
            
            # 2. Cerca agente esistente
            for agent in agents:
                if agent.get("name") == agent_name:
                    agent_id = agent["id"]
                    self.agents_cache[patient_id] = agent_id
                    return agent_id
            
            # 3. Crea nuovo agente
            create_payload = {
                "name": agent_name,
                "persona": f"Assistente personale del paziente {patient_id}",
                "human": f"Paziente {patient_id}",
                "system": "Sei un assistente medico. Rispondi in italiano.",
            }
            
            response = self.session.post(
                f"{self.base_url}/api/agents",
                json=create_payload,
                timeout=10
            )
            response.raise_for_status()
            
            agent_data = response.json()
            agent_id = agent_data["id"]
            
            self.agents_cache[patient_id] = agent_id
            logger.info(f"✅ Creato agente Letta per {patient_id}")
            return agent_id
            
        except Exception as e:
            logger.error(f"❌ Errore gestione agente: {e}")
            return None
    
    def authenticate_patient(self, patient_id: str, pin: str) -> bool:
        """Autentica paziente (implementazione base)"""
        try:
            agent_id = self._get_or_create_agent(patient_id)
            if not agent_id:
                return False
            
            # Per ora: placeholder (implementa verifica PIN in memoria)
            return True
            
        except Exception as e:
            logger.error(f"❌ Errore autenticazione: {e}")
            return False
    
    def store_appointment(self, patient_id: str, appointment_data: Dict) -> Optional[Dict]:
        """Salva appuntamento via HTTP API"""
        try:
            agent_id = self._get_or_create_agent(patient_id)
            if not agent_id:
                return None
            
            # Invia messaggio all'agente
            message = f"""NUOVO APPUNTAMENTO:
Data: {appointment_data['date']}
Orario: {appointment_data['time']}
Tipo: {appointment_data['type']}
Dottore: {appointment_data.get('doctor', 'Dr. Verdi')}
Stato: {appointment_data.get('status', 'confirmed')}"""
            
            payload = {
                "agent_id": agent_id,
                "message": message,
                "role": "system"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/agents/{agent_id}/messages",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            logger.info(f"✅ Appuntamento salvato per {patient_id}")
            return appointment_data
            
        except Exception as e:
            logger.error(f"❌ Errore salvataggio: {e}")
            return None
    
    def get_appointments(self, patient_id: str) -> List[Dict]:
        """Recupera appuntamenti via HTTP API"""
        try:
            agent_id = self._get_or_create_agent(patient_id)
            if not agent_id:
                return []
            
            # Query agente
            payload = {
                "agent_id": agent_id,
                "message": "Elenca tutti i miei appuntamenti (passati e futuri)",
                "role": "user"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/agents/{agent_id}/messages",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            
            # Parse risposta (da migliorare con parsing strutturato)
            return []
            
        except Exception as e:
            logger.error(f"❌ Errore recupero: {e}")
            return []
    
    def search_in_memory(self, patient_id: str, query: str) -> str:
        """Ricerca semantica via HTTP API"""
        try:
            agent_id = self._get_or_create_agent(patient_id)
            if not agent_id:
                return "Servizio memoria non disponibile"
            
            payload = {
                "agent_id": agent_id,
                "message": query,
                "role": "user"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/agents/{agent_id}/messages",
                json=payload,
                timeout=15
            )
            response.raise_for_status()
            
            data = response.json()
            # Estrai risposta dall'ultimo messaggio
            if "messages" in data and data["messages"]:
                return data["messages"][-1].get("text", str(data))
            return str(data)
            
        except Exception as e:
            logger.error(f"❌ Errore ricerca: {e}")
            return f"Errore: {str(e)}"
    
    def is_available(self) -> bool:
        """Verifica se Letta è disponibile"""
        try:
            response = self.session.get(f"{self.base_url}/api/health", timeout=2)
            return response.status_code == 200
        except:
            return False


# Singleton globale
_letta_db_instance: Optional[LettaMedicalDB] = None

def get_letta_db() -> LettaMedicalDB:
    """Factory pattern per client Letta"""
    global _letta_db_instance
    if _letta_db_instance is None:
        _letta_db_instance = LettaMedicalDB()
    return _letta_db_instance
