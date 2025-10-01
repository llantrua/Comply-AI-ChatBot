from fastapi import FastAPI, HTTPException, Query, Path
from pydantic import BaseModel, Field
from kiwi_rag_advanced import AdvancedKiwiRAG
import uvicorn
from typing import Optional, List

app = FastAPI(
    title="🥝 Kiwi AI Advanced - Expert Junior Entrepreneurs",
    version="3.0.0",
    description="Système IA avancé pour l'écosystème Kiwi avec recherche vectorielle optimisée"
)

# Initialisation du système avancé
kiwi_ai = AdvancedKiwiRAG()

# =============== MODÈLES PYDANTIC ===============

class AdvancedQuestion(BaseModel):
    question: str = Field(..., description="Question à poser au système Kiwi")
    debug: bool = Field(False, description="Mode debug pour voir les détails")
    context_type: str = Field("auto", description="Type de contexte: auto, legal, faq, junior, rse")

class AdvancedAnswer(BaseModel):
    question: str
    answer: str
    context_found: bool
    query_type: str = Field(..., description="Type de requête, obligatoire")
    sources_count: int = Field(0, description="Nombre de sources, par défaut 0")
    kiwi_specialized: bool = Field(False, description="Indique si Kiwi est spécialisé, par défaut False")
    status: str

class JESearchParams(BaseModel):
    city: Optional[str] = Field(None, description="Ville de la JE")
    domain: Optional[str] = Field(None, description="Domaine d'activité")
    school: Optional[str] = Field(None, description="École")
    region: Optional[str] = Field(None, description="Région")

class LegalGuidanceRequest(BaseModel):
    topic: str = Field(..., description="Sujet juridique")
    category: Optional[str] = Field(None, description="Catégorie légale spécifique")

# =============== ÉVÉNEMENTS ===============

@app.on_event("startup")
async def startup_advanced():
    """Démarrage du système avancé Kiwi"""
    print("🚀 KIWI AI ADVANCED - Système expert en démarrage...")
    print("📊 Fonctionnalités avancées:")
    print("   🧠 Recherche vectorielle TF-IDF + SVD")
    print("   🎯 Détection automatique du type de requête")
    print("   ⚡ Système de boost et filtrage intelligent")
    print("   🔍 Recherche spécialisée par domaine")
    
    if not kiwi_ai._load_advanced_index():
        print("\n🔧 Index avancé non trouvé, création complète...")
        kiwi_ai.index_documents_advanced()
    else:
        print("\n📂 Index avancé chargé depuis le cache")
        kiwi_ai._print_advanced_stats()
    
    print("✅ Kiwi AI Advanced prêt! Système expert opérationnel.")

# =============== ENDPOINTS AVANCÉS ===============

@app.post("/ask", response_model=AdvancedAnswer, 
          summary="Question avancée au système Kiwi",
          description="Pose une question avec détection automatique du type et recherche optimisée")
async def ask_advanced_question(question: AdvancedQuestion):
    """Endpoint principal pour questions avancées"""
    try:
        result = kiwi_ai.ask_kiwi_advanced(question.question, question.debug)
        # Ensure all required fields are present in the result
        result.setdefault("query_type", "unknown")
        result.setdefault("sources_count", 0)
        result.setdefault("kiwi_specialized", False)
        return AdvancedAnswer(**result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur système avancé: {e}")

@app.get("/search/je", 
         summary="Recherche experte de Junior Entreprises",
         description="Recherche avancée dans la base des JE françaises avec critères multiples")
async def search_je_advanced(
    city: Optional[str] = Query(None, description="Ville"),
    domain: Optional[str] = Query(None, description="Domaine d'activité"),
    school: Optional[str] = Query(None, description="École"),
    region: Optional[str] = Query(None, description="Région"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de résultats")
):
    """Recherche experte de Junior Entreprises"""
    try:
        results = kiwi_ai.search_junior_entreprises(city, domain, school, region)
        return {
            "query": {
                "city": city,
                "domain": domain,
                "school": school,
                "region": region
            },
            "results": results[:limit],
            "total_found": len(results),
            "search_type": "expert_je_search"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/faq",
         summary="Recherche experte dans la FAQ Kiwi Legal",
         description="Recherche optimisée dans la FAQ officielle avec scoring")
async def search_faq_advanced(
    query: str = Query(..., description="Question à rechercher"),
    category: Optional[str] = Query(None, description="Catégorie FAQ"),
    limit: int = Query(5, ge=1, le=20, description="Nombre de résultats")
):
    """Recherche experte dans la FAQ"""
    try:
        results = kiwi_ai.search_faq_kiwi(query, category)
        return {
            "query": query,
            "category": category,
            "faq_results": results[:limit],
            "total_found": len(results),
            "search_type": "expert_faq_search"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/legal/guidance",
          summary="Guidance juridique experte",
          description="Obtient une guidance juridique experte basée sur Kiwi Legal")
async def get_legal_guidance(request: LegalGuidanceRequest):
    """Guidance juridique experte"""
    try:
        guidance = kiwi_ai.get_legal_guidance(request.topic, request.category)
        return guidance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/advanced",
         summary="Recherche vectorielle avancée",
         description="Recherche avec contrôle total des paramètres avancés")
async def advanced_search(
    query: str = Query(..., description="Requête de recherche"),
    types: Optional[List[str]] = Query(None, description="Types préférés"),
    categories: Optional[List[str]] = Query(None, description="Catégories à booster"),
    limit: int = Query(5, ge=1, le=20, description="Nombre de résultats")
):
    """Recherche vectorielle avec contrôle avancé"""
    try:
        results = kiwi_ai.search_advanced(query, types, categories)
        
        formatted_results = []
        for doc, score in results[:limit]:
            formatted_results.append({
                "content": doc.get('content', ''),
                "source": doc.get('source', ''),
                "type": doc.get('type', ''),
                "category": doc.get('category', ''),
                "score": float(score),
                "metadata": {k: v for k, v in doc.items() if k not in ['content']}
            })
        
        return {
            "query": query,
            "parameters": {
                "preferred_types": types,
                "boost_categories": categories
            },
            "results": formatted_results,
            "total_found": len(results),
            "search_type": "advanced_vectorial"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reindex",
          summary="Réindexation complète",
          description="Lance une réindexation complète du système avancé")
async def reindex_advanced():
    """Réindexation complète du système"""
    try:
        kiwi_ai.index_documents_advanced()
        return {
            "message": "✅ Réindexation avancée terminée",
            "system": "Kiwi AI Advanced",
            "features": ["TF-IDF", "SVD", "Boost", "Metadata"],
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stats/advanced",
         summary="Statistiques système avancées",
         description="Statistiques détaillées du système vectoriel")
async def get_advanced_stats():
    """Statistiques avancées du système"""
    if not kiwi_ai.documents:
        return {"error": "Système non indexé"}
    
    # Calculs statistiques avancés
    by_source = {}
    by_type = {}
    by_category = {}
    
    for doc in kiwi_ai.documents:
        source = doc.get('source', 'unknown')
        doc_type = doc.get('type', 'unknown')
        category = doc.get('category', doc.get('legal_category', doc.get('rse_category', 'unknown')))
        
        by_source[source] = by_source.get(source, 0) + 1
        by_type[doc_type] = by_type.get(doc_type, 0) + 1
        by_category[category] = by_category.get(category, 0) + 1
    
    return {
        "system_info": {
            "name": "Kiwi AI Advanced",
            "version": "3.0.0",
            "features": ["TF-IDF Vectorization", "SVD Reduction", "Smart Boosting", "Metadata Indexing"]
        },
        "documents": {
            "total_chunks": len(kiwi_ai.documents),
            "by_source": by_source,
            "by_type": by_type,
            "by_category": {k: v for k, v in by_category.items() if k != 'unknown'}
        },
        "vectorial_system": {
            "tfidf_dimensions": kiwi_ai.doc_vectors.shape if kiwi_ai.doc_vectors is not None else None,
            "reduced_dimensions": kiwi_ai.reduced_vectors.shape if kiwi_ai.reduced_vectors is not None else None,
            "vocabulary_size": len(kiwi_ai.vectorizer.vocabulary_) if hasattr(kiwi_ai.vectorizer, 'vocabulary_') else 0
        },
        "kiwi_ecosystem": {
            "faq_count": by_type.get('faq', 0),
            "junior_entreprises": by_type.get('junior_entreprises', 0),
            "legal_pages": by_type.get('legal_site', 0),
            "rse_modules": by_type.get('rse_formation', 0)
        }
    }

@app.get("/health/advanced",
         summary="État système avancé",
         description="Vérification complète de l'état du système")
async def advanced_health_check():
    """Vérification avancée de l'état du système"""
    system_status = {
        "status": "healthy",
        "system": "Kiwi AI Advanced v3.0.0",
        "components": {
            "vectorizer": kiwi_ai.vectorizer is not None,
            "svd": kiwi_ai.svd is not None,
            "documents": len(kiwi_ai.documents) > 0,
            "vectors": kiwi_ai.doc_vectors is not None,
            "reduced_vectors": kiwi_ai.reduced_vectors is not None,
            "metadata": bool(kiwi_ai.document_metadata)
        },
        "capabilities": {
            "smart_search": True,
            "type_detection": True,
            "boost_system": True,
            "expert_guidance": True,
            "je_search": True,
            "faq_search": True,
            "legal_guidance": True
        },
        "performance": {
            "documents_indexed": len(kiwi_ai.documents),
            "ready_for_queries": all([
                kiwi_ai.vectorizer is not None,
                kiwi_ai.reduced_vectors is not None,
                len(kiwi_ai.documents) > 0
            ])
        }
    }
    
    # Déterminer le statut global
    if not system_status["performance"]["ready_for_queries"]:
        system_status["status"] = "degraded"
    
    return system_status

@app.get("/",
         summary="Page d'accueil système avancé",
         description="Informations complètes sur le système Kiwi AI Advanced")
async def advanced_root():
    """Page d'accueil du système avancé"""
    return {
        "system": "🥝 Kiwi AI Advanced - Expert Junior Entrepreneurs",
        "version": "3.0.0",
        "description": "Système IA avancé avec recherche vectorielle optimisée pour l'écosystème Kiwi",
        "advanced_features": {
            "vectorial_search": "TF-IDF + SVD pour recherche optimisée",
            "smart_detection": "Détection automatique du type de requête",
            "boost_system": "Système de boost intelligent par type/catégorie",
            "expert_guidance": "Guidance juridique et RSE experte",
            "specialized_search": "Recherche spécialisée JE, FAQ, Legal, RSE"
        },
        "kiwi_ecosystem": {
            "kiwi_legal": "Base juridique complète + FAQ officielle",
            "kiwi_rse": "Formations RSE et développement durable",
            "junior_entreprises": "Base exhaustive des JE françaises",
            "expert_system": "IA spécialisée avec contexte métier"
        },
        "api_endpoints": {
            "ask": "POST /ask - Question experte avec IA avancée",
            "search_je": "GET /search/je - Recherche JE multi-critères",
            "search_faq": "GET /search/faq - Recherche FAQ optimisée",
            "legal_guidance": "POST /legal/guidance - Guidance juridique experte",
            "advanced_search": "GET /search/advanced - Recherche vectorielle",
            "stats": "GET /stats/advanced - Statistiques système",
            "health": "GET /health/advanced - État système complet"
        }
}
if __name__ == "__main__":
    print("Démarrage du serveur...")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        print(f"Erreur: {e}")
