import asyncio
import json
from fastapi import FastAPI, HTTPException, Query, Request
# BaseModel ne sera plus nécessaire si SearchQuery est supprimé
import uvicorn
import sys
import os

# Add worker directory to sys.path to allow direct import
# This assumes api_server.py is in the root, and worker is a subdirectory
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

# Imports for the new search logic
from orchestrator.orchestrator import create_orchestrator
from agents import Runner

try:
    # Attempt to import the refactored functions from worker.main_agent
    # IMPORTANT: This import will succeed ONLY if worker/main_agent.py has been
    # refactored to include `get_configured_agent` function.
    from main_agent import get_configured_agent
except ImportError as e:
    print(f"ATTENTION: Erreur lors de l'importation depuis worker.main_agent: {e}")
    print("Cela signifie probablement que worker/main_agent.py n'a pas encore été adapté.")
    print("L'API utilisera des fonctions de remplacement qui retourneront des erreurs.")
    
    # Placeholder function if the real one isn't available from worker.main_agent
    async def get_configured_agent(): # type: ignore
        print("LOGIQUE DE L'AGENT NON DISPONIBLE: Appel de get_configured_agent avec la version placeholder.")
        print("Assurez-vous que worker/main_agent.py expose 'get_configured_agent'.")
        return None

app = FastAPI(
    title="Deep Search Agent API",
    description="API pour déclencher un agent de recherche approfondie pour un sujet donné.",
    version="1.0.0"
)
# Initialize app.state for storing shared objects
app.state.orchestrator = None
app.state.agent = None


@app.on_event("startup")
async def startup_event():
    """
    Au démarrage, essaie de pré-configurer l'agent et l'orchestrateur.
    """
    print("Démarrage du serveur API...")
    print("Tentative de pré-configuration de l'agent...")
    try:
        agent = await get_configured_agent()
        if agent:
            app.state.agent = agent
            print("Agent pré-configuré avec succès (si la vraie fonction a été importée).")
        else:
            print("La pré-configuration de l'agent a échoué ou a utilisé une version placeholder.")
            print("Vérifiez la configuration LLM, les clés API et l'état de worker/main_agent.py.")
    except Exception as e:
        print(f"Erreur lors de la pré-configuration de l'agent: {e}")
        app.state.agent = None # Assurer un état cohérent

    print("Tentative de création de l'orchestrateur...")
    try:
        orchestrator = await create_orchestrator()
        app.state.orchestrator = orchestrator
        if orchestrator:
            print("Orchestrateur créé avec succès.")
        else:
            # create_orchestrator pourrait retourner None ou lever une exception en cas d'échec
            print("La création de l'orchestrateur a échoué (retourné None).")
    except Exception as e:
        print(f"Erreur lors de la création de l'orchestrateur au démarrage: {e}")
        app.state.orchestrator = None # Assurer un état cohérent
        # Optionnel: lever une exception ici si l'orchestrateur est critique pour démarrer
        # raise RuntimeError(f"Impossible de créer l'orchestrateur au démarrage: {e}")


@app.post("/search/", response_model=None) # Exemple d'appel: POST /search/?question=Quelle+est+la+capitale+de+la+France
async def run_search_agent(request: Request, question: str = Query(..., description="Le sujet ou la question pour l'agent de recherche approfondie.")):
    """
    Point de terminaison pour exécuter l'agent de recherche approfondie.
    Prend une 'question' comme paramètre d'URL et retourne la sortie JSON de l'agent.
    Utilise l'orchestrateur pré-initialisé.
    """
    print(f"Requête de recherche reçue pour: {question}")
    if not question or not question.strip():
        raise HTTPException(status_code=400, detail="La question ne peut pas être vide.")
    
    orchestrator = request.app.state.orchestrator
    if orchestrator is None:
        print("ERREUR: L'orchestrateur n'est pas initialisé. Vérifiez les logs de démarrage.")
        raise HTTPException(status_code=503, detail={"error": "Service non disponible", "message": "L'orchestrateur n'a pas pu être initialisé."})

    try:
        user_request = question
        print(f"INFO: Utilisation de l'orchestrateur pré-initialisé pour la requête: '{user_request}'")
        
        print(f"INFO: Démarrage de l'orchestration de l'agent REAL avec l'Orchestrateur pour: '{user_request}'")
        # Using max_turns=25 as in run_demo.py
        result = await Runner.run(orchestrator, user_request, max_turns=25) 
        
        print("INFO: Orchestration de l'agent REAL terminée avec succès")
        print(f"INFO: Résultat final (pour les logs serveur): {result.final_output}") 
        
        return result.final_output

    except Exception as e:
        print(f"ERREUR: Une erreur inattendue est survenue dans le point de terminaison /search: {e}")
        import traceback
        traceback.print_exc() 
        raise HTTPException(
            status_code=500, 
            detail={"error": "Une erreur inattendue est survenue lors du traitement de votre requête.", "details": str(e)}
        )

@app.get("/")
async def read_root():
    return {"message": "Bienvenue sur l'API Deep Search Agent. Utilisez le point de terminaison /search/ pour faire des requêtes."}




if __name__ == "__main__":
    print("Démarrage du serveur Uvicorn pour l'API Deep Search Agent...")
    # Assurez-vous que LINKUP_API_KEY et les autres variables d'environnement nécessaires sont définies.
    uvicorn.run(app, host="0.0.0.0", port=8034) 