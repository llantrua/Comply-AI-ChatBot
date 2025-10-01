import json
import os
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import anthropic
from tqdm import tqdm
import re
from config import *


class AdvancedKiwiRAG:
    def __init__(self):
        self.claude_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

        # Système vectoriel avancé
        self.vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 3),  # Uni, bi et trigrammes
            stop_words=None,
            min_df=2,
            max_df=0.8,
            analyzer='word',
            lowercase=True
        )

        # Réduction dimensionnelle pour de meilleures performances
        self.svd = TruncatedSVD(n_components=300, random_state=42)

        # Stockage
        self.documents = []
        self.doc_vectors = None
        self.reduced_vectors = None

        # Métadonnées pour améliorer la recherche
        self.document_metadata = {}

    def load_and_process_all_kiwi_data(self) -> List[Dict]:
        """Charge et traite intelligemment tous les fichiers Kiwi"""
        all_documents = []
        data_path = Path(DATA_DIR)

        print("🔍 Analyse intelligente des fichiers Kiwi...")

        json_files = list(data_path.glob("*.json"))
        print(f"📁 Fichiers détectés: {[f.name for f in json_files]}")

        for json_file in json_files:
            print(f"\n📄 Traitement avancé: {json_file.name}")

            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Détection intelligente du type
                file_type = self._detect_kiwi_file_type(json_file.name, data)
                print(f"   🎯 Type détecté: {file_type}")

                # Traitement spécialisé
                documents = self._process_by_type(
                    data, json_file.name, file_type)
                all_documents.extend(documents)

                print(
                    f"   ✅ {len(documents)} sections extraites et optimisées")

            except Exception as e:
                print(f"   ❌ Erreur: {e}")

        print(f"\n🎯 Total optimisé: {len(all_documents)} documents")
        return all_documents

    def _detect_kiwi_file_type(self, filename: str, data: Any) -> str:
        """Détection intelligente du type de fichier Kiwi"""
        filename_lower = filename.lower()

        # Détection par nom de fichier
        for pattern, file_type in KIWI_FILE_TYPES.items():
            if pattern in filename_lower:
                return file_type

        # Détection par contenu si nom ambigu
        data_str = str(data)[:1000].lower()

        if any(word in data_str for word in [
               'question', 'answer', 'faq', 'reponse']):
            return 'faq'
        elif any(word in data_str for word in ['junior', 'entreprise', 'ecole', 'ville']):
            return 'junior_entreprises'
        elif any(word in data_str for word in ['rse', 'durable', 'environnement', 'formation']):
            return 'rse_formation'
        elif any(word in data_str for word in ['legal', 'juridique', 'contrat', 'droit']):
            return 'legal_site'

        return 'unknown'

    def _process_by_type(self, data: Any, filename: str,
                         file_type: str) -> List[Dict]:
        """Traitement spécialisé selon le type détecté"""
        processors = {
            'faq': self._process_faq_advanced,
            'junior_entreprises': self._process_junior_entreprises_advanced,
            'legal_site': self._process_legal_site_advanced,
            'rse_formation': self._process_rse_formation_advanced
        }

        processor = processors.get(file_type, self._process_generic_advanced)
        return processor(data, filename, file_type)

    def _process_faq_advanced(
            self, data: Any, filename: str, file_type: str) -> List[Dict]:
        """Traitement avancé des FAQ Kiwi Legal"""
        documents = []

        def extract_qa_recursive(obj, category_path="", depth=0):
            if depth > 5:  # Éviter récursion infinie
                return

            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        qa_doc = self._extract_single_qa(
                            item, category_path, i)
                        if qa_doc:
                            documents.append({
                                **qa_doc,
                                "source": filename,
                                "type": file_type,
                                "category_path": category_path,
                                "priority": self._calculate_faq_priority(qa_doc)
                            })

            elif isinstance(obj, dict):
                # Vérifier si c'est une Q&A directe
                if self._is_qa_object(obj):
                    qa_doc = self._extract_single_qa(obj, category_path, 0)
                    if qa_doc:
                        documents.append({
                            **qa_doc,
                            "source": filename,
                            "type": file_type,
                            "category_path": category_path
                        })
                else:
                    # Explorer récursivement
                    for key, value in obj.items():
                        new_path = f"{category_path}/{key}" if category_path else key
                        extract_qa_recursive(value, new_path, depth + 1)

        extract_qa_recursive(data)
        return documents

    def _extract_single_qa(self, obj: dict, category: str, index: int) -> Dict:
        """Extrait une paire question-réponse avec enrichissement"""
        # Variations possibles des clés
        question_keys = [
            'question',
            'q',
            'titre',
            'title',
            'demande',
            'probleme']
        answer_keys = [
            'answer',
            'a',
            'reponse',
            'response',
            'solution',
            'explication']

        question = ""
        answer = ""

        # Extraction flexible de la question
        for key in question_keys:
            if key in obj:
                question = str(obj[key]).strip()
                break

        # Extraction flexible de la réponse
        for key in answer_keys:
            if key in obj:
                answer = str(obj[key]).strip()
                break

        if not question or not answer:
            return None

        # Enrichissement du contenu
        content_parts = [
            f"=== FAQ KIWI LEGAL ===",
            f"Catégorie: {category}" if category else "",
            f"❓ QUESTION: {question}",
            f"✅ RÉPONSE: {answer}"
        ]

        # Ajout d'informations contextuelles
        if 'tags' in obj:
            content_parts.append(f"🏷️ Tags: {', '.join(obj['tags'])}")

        if 'niveau' in obj or 'difficulty' in obj:
            niveau = obj.get('niveau', obj.get('difficulty', ''))
            content_parts.append(f"📊 Niveau: {niveau}")

        return {
            "content": "\n".join(
                filter(
                    None,
                    content_parts)),
            "question": question,
            "answer": answer,
            "category": category,
            "enriched_content": self._create_searchable_content(
                question,
                answer,
                category)}

    def _process_junior_entreprises_advanced(
            self, data: Any, filename: str, file_type: str) -> List[Dict]:
        """Traitement avancé des Junior Entreprises"""
        documents = []

        def extract_je_recursive(obj, region_context=""):
            if isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, dict):
                        je_doc = self._extract_single_je(
                            item, region_context, i)
                        if je_doc:
                            documents.append({
                                **je_doc,
                                "source": filename,
                                "type": file_type,
                                "region_context": region_context
                            })

            elif isinstance(obj, dict):
                # Vérifier si c'est une JE directe
                if self._is_je_object(obj):
                    je_doc = self._extract_single_je(obj, region_context, 0)
                    if je_doc:
                        documents.append({
                            **je_doc,
                            "source": filename,
                            "type": file_type,
                            "region_context": region_context
                        })
                else:
                    # Explorer par régions/catégories
                    for key, value in obj.items():
                        new_context = f"{region_context}/{key}" if region_context else key
                        extract_je_recursive(value, new_context)

        extract_je_recursive(data)
        return documents

    def _extract_single_je(self, obj: dict, region: str, index: int) -> Dict:
        """Extrait et enrichit les infos d'une Junior Entreprise"""
        # Mapping flexible des champs
        name = self._get_flexible_field(obj, ['nom', 'name', 'denomination'])
        city = self._get_flexible_field(obj, ['ville', 'city', 'localisation'])
        school = self._get_flexible_field(
            obj, ['ecole', 'school', 'etablissement', 'universite'])
        domain = self._get_flexible_field(
            obj, ['domaine', 'domain', 'secteur', 'specialite'])
        website = self._get_flexible_field(
            obj, ['site_web', 'website', 'url', 'site'])
        email = self._get_flexible_field(
            obj, ['email', 'mail', 'contact_email'])
        phone = self._get_flexible_field(obj, ['telephone', 'phone', 'tel'])

        if not name:
            return None

        # Construction du contenu enrichi
        content_parts = [
            f"=== JUNIOR ENTREPRISE: {name.upper()} ===",
            f"Région/Contexte: {region}" if region else "",
            f"🎓 École: {school}" if school else "",
            f"🏙️ Ville: {city}" if city else "",
            f"💼 Domaine: {domain}" if domain else "",
            f"🌐 Site web: {website}" if website else "",
            f"📧 Email: {email}" if email else "",
            f"📞 Téléphone: {phone}" if phone else ""
        ]

        # Ajout d'informations supplémentaires
        for key, value in obj.items():
            if key not in ['nom', 'name', 'ville', 'city',
                           'ecole', 'school', 'domaine', 'domain'] and value:
                if isinstance(value, list):
                    content_parts.append(
                        f"{key.title()}: {' | '.join(map(str, value))}")
                elif isinstance(value, str) and len(value) > 0:
                    content_parts.append(f"{key.title()}: {value}")

        return {
            "content": "\n".join(
                filter(
                    None,
                    content_parts)),
            "name": name,
            "city": city,
            "school": school,
            "domain": domain,
            "website": website,
            "email": email,
            "enriched_content": self._create_je_searchable_content(
                name,
                city,
                school,
                domain)}

    def _process_legal_site_advanced(self, data: Any, filename: str, file_type: str) -> List[Dict]:
        """Traitement avancé du site Kiwi Legal scrapé"""
        documents = []

        def extract_legal_content(obj, url_path="", section_type=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{url_path}/{key}" if url_path else key
                    # Détecter les pages/sections importantes
                    if self._is_legal_page(key, value):
                        legal_doc = self._extract_legal_page(
                            key, value, current_path, section_type)
                        if legal_doc:
                            documents.append({
                                **legal_doc,
                                "source": filename,
                                "type": file_type,
                                "url_path": current_path,
                                "legal_category": self._categorize_legal_content(key, value)
                            })
                    elif isinstance(value, dict):
                        extract_legal_content(value, current_path, key)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, dict):
                                extract_legal_content(
                                    item, f"{current_path}[{i}]", key)

        extract_legal_content(data)
        return documents

    def _extract_legal_page(self, key: str, value: Any, path: str, section_type: str) -> Dict:
        """Extrait une page légale"""
        if isinstance(value, dict):
            content = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            content = str(value)
        return {
            "content": f"=== PAGE KIWI LEGAL: {key} ===\n{content}",
            "title": key,
            "path": path,
            "section_type": section_type
        }
        
    def _process_rse_formation_advanced(
            self, data: Any, filename: str, file_type: str) -> List[Dict]:
        """Traitement avancé des formations RSE"""
        documents = []

        def extract_rse_content(obj, module_path="", formation_type=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{module_path}/{key}" if module_path else key
                    if self._is_rse_module(key, value):
                        rse_doc = self._extract_rse_module(
                            key, value, current_path, formation_type)
                        if rse_doc:
                            documents.append({
                                **rse_doc,
                                "source": filename,
                                "type": file_type,
                                "module_path": current_path,
                                "rse_category": self._categorize_rse_content(key, value)
                            })
                    elif isinstance(value, dict):
                        extract_rse_content(value, current_path, key)

        extract_rse_content(data)
        return documents

    def _extract_rse_module(self, key: str, value: Any, path: str, formation_type: str) -> Dict:
        """Extrait un module RSE"""
        if isinstance(value, dict):
            content = json.dumps(value, ensure_ascii=False, indent=2)
        else:
            content = str(value)
        return {
            "content": f"=== MODULE RSE: {key} ===\n{content}",
            "title": key,
            "path": path,
            "formation_type": formation_type
        }

    def _process_generic_advanced(
            self, data: Any, filename: str, file_type: str) -> List[Dict]:
        """Traitement générique avancé pour contenus non reconnus"""
        content = json.dumps(data, ensure_ascii=False, indent=2)

        # Découpage intelligent du contenu générique
        chunks = self._smart_chunk_content(content, filename)

        documents = []
        for i, chunk in enumerate(chunks):
            documents.append({
                "content": chunk,
                "source": filename,
                "type": file_type,
                "chunk_index": i,
                # Résumé pour recherche
                "enriched_content": chunk[:200] + "..."
            })

        return documents

    # =============== HELPERS AVANCÉS ===============

    def _get_flexible_field(self, obj: dict, possible_keys: List[str]) -> str:
        """Récupère une valeur avec clés flexibles"""
        for key in possible_keys:
            if key in obj and obj[key]:
                return str(obj[key]).strip()
        return ""

    def _is_qa_object(self, obj: dict) -> bool:
        """Vérifie si un objet est une Q&A"""
        qa_indicators = ['question', 'q', 'answer', 'a', 'reponse', 'response']
        return any(key in obj for key in qa_indicators)

    def _is_je_object(self, obj: dict) -> bool:
        """Vérifie si un objet est une Junior Entreprise"""
        je_indicators = [
            'nom',
            'name',
            'ecole',
            'school',
            'ville',
            'city',
            'domaine']
        return any(key in obj for key in je_indicators)

    def _is_legal_page(self, key: str, value: Any) -> bool:
        """Vérifie si c'est une page légale importante"""
        legal_indicators = [
            'titre',
            'title',
            'content',
            'contenu',
            'article',
            'section']
        return any(
            indicator in str(key).lower() for indicator in legal_indicators) and isinstance(
            value, (dict, str)) and len(
            str(value)) > 100

    def _is_rse_module(self, key: str, value: Any) -> bool:
        """Vérifie si c'est un module RSE"""
        rse_indicators = [
            'module',
            'formation',
            'cours',
            'objectif',
            'competence']
        return any(
            indicator in str(key).lower() for indicator in rse_indicators) and isinstance(
            value, (dict, str)) and len(
            str(value)) > 50

    def _create_searchable_content(
            self, question: str, answer: str, category: str) -> str:
        """Crée un contenu optimisé pour la recherche"""
        keywords = self._extract_keywords(question + " " + answer)
        return f"{category} {question} {answer} {' '.join(keywords)}"

    def _create_je_searchable_content(
            self, name: str, city: str, school: str, domain: str) -> str:
        """Crée un contenu JE optimisé pour la recherche"""
        elements = [name, city, school, domain]
        return " ".join([elem for elem in elements if elem])

    def _extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés importants d'un texte"""
        # Nettoyage et extraction basique
        words = re.findall(r'\b[a-zA-Zàâäéèêëïîôöùûüÿç]{3,}\b', text.lower())
        # Filtrages des mots vides basiques
        stop_words = {
            'les',
            'des',
            'une',
            'est',
            'sont',
            'avec',
            'pour',
            'dans',
            'sur'}
        return [word for word in words if word not in stop_words][:10]

    def _calculate_faq_priority(self, qa_doc: dict) -> int:
        """Calcule la priorité d'une FAQ"""
        priority = 1
        question = qa_doc.get('question', '').lower()

        # Priorité selon les mots-clés critiques
        high_priority_words = [
            'urgent',
            'important',
            'obligatoire',
            'legal',
            'contrat']
        if any(word in question for word in high_priority_words):
            priority += 2

        return priority

    def _categorize_legal_content(self, key: str, value: Any) -> str:
        """Catégorise le contenu légal"""
        content_str = f"{key} {str(value)}".lower()

        categories = {
            'contrats': ['contrat', 'contract', 'accord', 'convention'],
            'statuts': ['statut', 'constitution', 'creation'],
            'comptabilite': ['comptable', 'fiscal', 'tva', 'urssaf'],
            'assurances': ['assurance', 'responsabilite', 'couverture'],
            'social': ['social', 'salarie', 'cotisation'],
            'procedure': ['procedure', 'demarche', 'etape']
        }

        for category, keywords in categories.items():
            if any(keyword in content_str for keyword in keywords):
                return category

        return 'general'

    def _categorize_rse_content(self, key: str, value: Any) -> str:
        """Catégorise le contenu RSE"""
        content_str = f"{key} {str(value)}".lower()

        categories = {
            'environnement': [
                'environnement', 'carbone', 'ecologie', 'durable'], 'social': [
                'social', 'inclusivite', 'diversite', 'equite'], 'gouvernance': [
                'gouvernance', 'ethique', 'transparence'], 'formation': [
                    'formation', 'sensibilisation', 'competence']}

        for category, keywords in categories.items():
            if any(keyword in content_str for keyword in keywords):
                return category

        return 'general'

    def _smart_chunk_content(self, content: str, source: str) -> List[str]:
        """Découpage intelligent du contenu"""
        if len(content) <= CHUNK_SIZE:
            return [content]

        chunks = []
        # Découpage par sections JSON d'abord
        json_sections = content.split('\n  "')
        current_chunk = ""

        for section in json_sections:
            if len(current_chunk + section) > CHUNK_SIZE:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = section
            else:
                current_chunk += '\n  "' + section if current_chunk else section

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    # =============== SYSTÈME VECTORIEL AVANCÉ ===============

    def create_advanced_chunks(self, documents: List[Dict]) -> List[Dict]:
        """Création de chunks avec préprocessing avancé"""
        chunks = []

        print("✂️ Création de chunks intelligents...")

        for doc in tqdm(documents):
            content = doc["content"]
            doc_type = doc.get("type", "unknown")

            # Taille adaptée selon le type
            if doc_type == "legal_site":
                target_size = CHUNK_SIZE + 200
            elif doc_type == "faq":
                target_size = CHUNK_SIZE
            elif doc_type == "junior_entreprises":
                target_size = CHUNK_SIZE - 100
            else:
                target_size = CHUNK_SIZE

            if len(content) <= target_size:
                # Enrichissement du contenu court
                enriched_doc = doc.copy()
                enriched_doc["search_content"] = self._create_search_optimized_content(
                    doc)
                chunks.append(enriched_doc)
            else:
                # Découpage intelligent préservant le contexte
                chunk_parts = self._intelligent_split(
                    content, target_size, doc_type)
                for i, part in enumerate(chunk_parts):
                    chunk_doc = doc.copy()
                    chunk_doc["content"] = part
                    chunk_doc["chunk_id"] = f"{doc.get('source', 'doc')}_{doc_type}_{i}"
                    chunk_doc["search_content"] = self._create_search_optimized_content(
                        chunk_doc)
                    chunks.append(chunk_doc)

        return chunks

    def _create_search_optimized_content(self, doc: Dict) -> str:
        """Crée un contenu optimisé pour la recherche vectorielle"""
        content = doc.get("content", "")
        doc_type = doc.get("type", "")

        # Extraction d'éléments importants selon le type
        if doc_type == "faq":
            question = doc.get("question", "")
            answer = doc.get("answer", "")
            category = doc.get("category", "")
            return f"{category} {question} {answer} FAQ junior entreprise"

        elif doc_type == "junior_entreprises":
            name = doc.get("name", "")
            city = doc.get("city", "")
            domain = doc.get("domain", "")
            school = doc.get("school", "")
            return f"{name} {city} {domain} {school} junior entreprise"

        elif doc_type == "legal_site":
            category = doc.get("legal_category", "")
            return f"{content} {category} juridique legal"

        elif doc_type == "rse_formation":
            category = doc.get("rse_category", "")
            return f"{content} {category} RSE formation durable"

        return content

    def _intelligent_split(self, content: str, max_size: int,
                           doc_type: str) -> List[str]:
        """Découpage intelligent préservant le contexte"""
        if doc_type == "faq":
            # Pour FAQ, ne pas découper les Q&A
            return [content[:max_size]]

        # Découpage par sections importantes
        sections = content.split('\n===')
        chunks = []
        current_chunk = ""

        for section in sections:
            if len(current_chunk + section) > max_size:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = "===" + \
                    section if not section.startswith('===') else section
            else:
                current_chunk += "\n===" + section if current_chunk else section

        if current_chunk:
            chunks.append(current_chunk.strip())

        return chunks

    def index_documents_advanced(self):
        """Indexation avancée avec système vectoriel optimisé"""
        print("🚀 Indexation avancée Kiwi...")

        # 1. Chargement et traitement intelligent
        documents = self.load_and_process_all_kiwi_data()
        if not documents:
            print("❌ Aucun document trouvé")
            return

        # 2. Création de chunks optimisés
        chunks = self.create_advanced_chunks(documents)

        # 3. Préparation des textes pour vectorisation
        print(f"🧠 Vectorisation avancée de {len(chunks)} chunks...")

        # Contenu principal pour recherche
        search_texts = [
            chunk.get(
                "search_content",
                chunk["content"]) for chunk in chunks]

        # Création des vecteurs TF-IDF
        self.doc_vectors = self.vectorizer.fit_transform(search_texts)

        # Réduction dimensionnelle pour performances
        print("📊 Optimisation dimensionnelle...")

       # Vérification des dimensions avant SVD
        n_features = self.doc_vectors.shape[1]
        n_samples = self.doc_vectors.shape[0]
        max_components = min(n_features, n_samples) - 1

        if max_components > 1:
            # Ajuster le nombre de composantes SVD
            target_components = getattr(self.svd, 'n_components', 300)
            actual_components = min(target_components, max_components)

            # Recréer SVD avec les bonnes dimensions si nécessaire
            if actual_components != target_components:
                from sklearn.decomposition import TruncatedSVD
                self.svd = TruncatedSVD(
                    n_components=actual_components, random_state=42)
                print(
                    f"🔧 SVD ajustée: {actual_components} composantes (max: {max_components})")

            self.reduced_vectors = self.svd.fit_transform(
                self.doc_vectors.toarray())
        else:
            print(
                f"⚠️ Pas assez de données pour SVD ({n_features} features, {n_samples} samples)")
            self.reduced_vectors = self.doc_vectors.toarray()

        # Stockage
        self.documents = chunks

        # Création de métadonnées pour améliorer la recherche
        self._build_metadata_index()

        # Sauvegarde
        self._save_advanced_index()

        print(
            f"✅ Indexation avancée terminée: {len(chunks)} chunks optimisés!")
        self._print_advanced_stats()

    def _build_metadata_index(self):
        """Construit un index de métadonnées pour recherche rapide"""
        self.document_metadata = {
            'by_type': {},
            'by_category': {},
            'by_source': {},
            'keywords': {}
        }

        for i, doc in enumerate(self.documents):
            doc_type = doc.get('type', 'unknown')
            category = doc.get(
                'category', doc.get(
                    'legal_category', doc.get(
                        'rse_category', 'unknown')))
            source = doc.get('source', 'unknown')

            # Index par type
            if doc_type not in self.document_metadata['by_type']:
                self.document_metadata['by_type'][doc_type] = []
            self.document_metadata['by_type'][doc_type].append(i)

            # Index par catégorie
            if category not in self.document_metadata['by_category']:
                self.document_metadata['by_category'][category] = []
            self.document_metadata['by_category'][category].append(i)

            # Index par source
            if source not in self.document_metadata['by_source']:
                self.document_metadata['by_source'][source] = []
            self.document_metadata['by_source'][source].append(i)

    def search_advanced(self,
                        query: str,
                        preferred_types: List[str] = None,
                        boost_categories: List[str] = None) -> List[Tuple[Dict,
                                                                          float]]:
        """Recherche avancée avec boost et filtrage"""
        if self.reduced_vectors is None:
            if not self._load_advanced_index():
                return []

        # Vectorisation de la requête
        query_vector = self.vectorizer.transform([query])
        query_reduced = self.svd.transform(query_vector.toarray())

        # Calcul de similarité sur vecteurs réduits (plus rapide)
        similarities = cosine_similarity(
            query_reduced, self.reduced_vectors)[0]

        # Application des boosts
        if preferred_types or boost_categories:
            similarities = self._apply_search_boosts(
                similarities, preferred_types, boost_categories)

        # Récupération des meilleurs résultats
        top_indices = np.argsort(similarities)[::-1][:MAX_CONTEXT_DOCS * 2]

        results = []
        for idx in top_indices:
            if similarities[idx] > 0.1:  # Seuil de pertinence
                results.append((self.documents[idx], similarities[idx]))

        return results[:MAX_CONTEXT_DOCS]

    def _apply_search_boosts(
            self,
            similarities: np.ndarray,
            preferred_types: List[str] = None,
            boost_categories: List[str] = None) -> np.ndarray:
        """Applique des boosts selon les préférences"""
        boosted_similarities = similarities.copy()

        for i, doc in enumerate(self.documents):
            # Boost par type
            if preferred_types and doc.get('type') in preferred_types:
                boosted_similarities[i] *= 1.3

            # Boost par catégorie
            doc_category = doc.get(
                'category',
                doc.get(
                    'legal_category',
                    doc.get('rse_category')))
            if boost_categories and doc_category in boost_categories:
                boosted_similarities[i] *= 1.2

            # Boost par priorité (pour FAQ)
            if doc.get('priority', 0) > 1:
                boosted_similarities[i] *= 1.1

        return boosted_similarities

    def get_smart_context(self, query: str, context_type: str = "auto") -> str:
        """Récupère un contexte intelligent selon le type de requête"""
        # Détection automatique du type de requête
        if context_type == "auto":
            context_type = self._detect_query_type(query)

        # Définition des préférences selon le type
        type_preferences = {
            "legal": (
                ["legal_site"], [
                    "contrats", "statuts", "comptabilite"]), "faq": (
                ["faq"], ["general"]), "junior": (
                    ["junior_entreprises"], ["general"]), "rse": (
                        ["rse_formation"], [
                            "environnement", "social", "gouvernance"])}

        preferred_types, boost_categories = type_preferences.get(
            context_type, (None, None))

        # Recherche avec préférences
        results = self.search_advanced(
            query, preferred_types, boost_categories)

        if not results:
            return "Aucune information pertinente trouvée dans la base Kiwi."

        # Construction du contexte enrichi
        context_parts = []
        for doc, score in results:
            kiwi_info = f"Source: {doc['source']} | Type: {doc.get('type', 'N/A')} | Score: {score:.3f}"

            # Ajout d'infos contextuelles
            if doc.get('category'):
                kiwi_info += f" | Catégorie: {doc['category']}"
            if doc.get('legal_category'):
                kiwi_info += f" | Domaine juridique: {doc['legal_category']}"
            if doc.get('rse_category'):
                kiwi_info += f" | Domaine RSE: {doc['rse_category']}"

            context_parts.append(kiwi_info)
            context_parts.append(f"Contenu: {doc['content']}")
            context_parts.append("---")

        return "\n".join(context_parts)

    def _detect_query_type(self, query: str) -> str:
        """Détecte intelligemment le type de requête"""
        query_lower = query.lower()

        # Patterns pour chaque type
        patterns = {
            "legal": [
                "juridique",
                "legal",
                "contrat",
                "droit",
                "statut",
                "assurance",
                "comptable",
                "fiscal"],
            "faq": [
                "comment",
                "pourquoi",
                "que faire",
                "question",
                "aide",
                "probleme"],
            "junior": [
                "junior",
                "je ",
                "entreprise",
                "ecole",
                "ville",
                "contact",
                "trouve",
                "cherche"],
            "rse": [
                "rse",
                "durable",
                "environnement",
                "social",
                "formation",
                "responsabilite",
                "carbone"]}

        scores = {}
        for query_type, keywords in patterns.items():
            scores[query_type] = sum(
                1 for keyword in keywords if keyword in query_lower)

        # Retourne le type avec le plus de matches
        return max(scores, key=scores.get) if max(
            scores.values()) > 0 else "general"

    def ask_kiwi_advanced(self, question: str,
                          debug: bool = False) -> Dict[str, Any]:
        """Système de question-réponse avancé pour Kiwi"""
        # Détection du type et récupération du contexte
        query_type = self._detect_query_type(question)
        context = self.get_smart_context(question, query_type)

        if debug:
            print(f"🎯 Type de requête détecté: {query_type}")
            print(f"📊 Contexte trouvé: {len(context.split('---'))} documents")

        # Sélection du prompt spécialisé
        specialized_prompts = {
            "legal": """Tu es un expert juridique spécialisé en droit des junior entreprises avec accès à la base complète Kiwi Legal.
Tu maitrises parfaitement tous les aspects juridiques, contractuels et réglementaires.""",
            "faq": """Tu réponds aux questions fréquentes en utilisant la FAQ officielle de Kiwi Legal.
Sois direct, pratique et base-toi sur les réponses validées.""",
            "junior": """Tu es un expert des junior entreprises françaises avec accès à la base complète des JE.
Tu connais leurs spécialités, localisations et contacts.""",
            "rse": """Tu es un formateur RSE expert utilisant les contenus pédagogiques de Kiwi RSE.
Tu maitrises le développement durable appliqué aux junior entreprises."""}

        context_prompt = specialized_prompts.get(
            query_type,
            "Tu es l'assistant IA officiel de l'écosystème Kiwi pour les junior entrepreneurs français.")

        # Construction du prompt optimisé
        prompt = f"""{context_prompt}

CONTEXTE KIWI SPÉCIALISÉ:
{context}

QUESTION: {question}

INSTRUCTIONS EXPERTES:
- Base-toi PRIORITAIREMENT sur les données officielles Kiwi (Legal, RSE, FAQ, Base JE)
- Cite précisément tes sources Kiwi quand tu les utilises
- Pour les questions juridiques: utilise Kiwi Legal et mentionne les références précises
- Pour les questions sur les JE: fournis des informations concrètes (contacts, spécialités)
- Pour les questions RSE: utilise les modules de formation Kiwi RSE
- Donne des conseils actionnables et spécifiques aux junior entrepreneurs
- Indique clairement quand tu utilises les données Kiwi vs tes connaissances générales
- Sois précis, expert et fiable dans tes réponses

RÉPONSE EXPERTE:"""

        try:
            print(f"Model {CLAUDE_MODEL} - Max tokens: {MAX_TOKENS} - Temp: {TEMPERATURE}")
            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "question": question,
                "answer": response.content[0].text,
                "context_found": context != "Aucune information pertinente trouvée dans la base Kiwi.",
                "query_type": query_type,
                "sources_count": len(
                    context.split('---')) if context else 0,
                "kiwi_specialized": True,
                "status": "success"}

        except Exception as e:
            return {
                "question": question,
                "answer": f"Erreur système Kiwi: {e}",
                "context_found": False,
                "status": "error"
            }

    def _print_advanced_stats(self):
        """Affiche des statistiques détaillées du système"""
        if not self.documents:
            return

        print("\n📊 STATISTIQUES SYSTÈME KIWI AVANCÉ:")

        # Stats par source et type
        by_source = {}
        by_type = {}
        by_category = {}

        for doc in self.documents:
            source = doc.get('source', 'unknown')
            doc_type = doc.get('type', 'unknown')
            category = doc.get(
                'category', doc.get(
                    'legal_category', doc.get(
                        'rse_category', 'unknown')))

            by_source[source] = by_source.get(source, 0) + 1
            by_type[doc_type] = by_type.get(doc_type, 0) + 1
            by_category[category] = by_category.get(category, 0) + 1

        print("   📁 Répartition par fichier Kiwi:")
        for source, count in sorted(by_source.items()):
            print(f"     - {source}: {count} chunks")

        print("   🏷️ Répartition par type:")
        for doc_type, count in sorted(by_type.items()):
            print(f"     - {doc_type}: {count} chunks")

        print("   📂 Répartition par catégorie:")
        for category, count in sorted(by_category.items()):
            if category != 'unknown':
                print(f"     - {category}: {count} chunks")

        # Stats techniques
        if self.doc_vectors is not None:
            print(f"\n   🔬 Statistiques techniques:")
            print(f"     - Dimensions TF-IDF: {self.doc_vectors.shape}")
            print(f"     - Dimensions réduites: {self.reduced_vectors.shape}")
            print(
                f"     - Vocabulaire: {len(self.vectorizer.vocabulary_)} termes")

        # Résumé Kiwi
        faq_count = by_type.get('faq', 0)
        je_count = by_type.get('junior_entreprises', 0)
        legal_count = by_type.get('legal_site', 0)
        rse_count = by_type.get('rse_formation', 0)

        print(f"\n   🎯 RÉSUMÉ ÉCOSYSTÈME KIWI:")
        print(f"     - 💬 FAQ Kiwi Legal: {faq_count} Q&A")
        print(f"     - 🏢 Junior Entreprises: {je_count} fiches")
        print(f"     - ⚖️ Pages Kiwi Legal: {legal_count} pages")
        print(f"     - 🌱 Modules RSE: {rse_count} formations")
        print(f"     - 📈 Performance système: OPTIMISÉE")

    def _save_advanced_index(self):
        """Sauvegarde avancée de l'index"""
        try:
            with open("kiwi_advanced_index.pkl", 'wb') as f:
                pickle.dump({
                    "documents": self.documents,
                    "vectorizer": self.vectorizer,
                    "svd": self.svd,
                    "doc_vectors": self.doc_vectors,
                    "reduced_vectors": self.reduced_vectors,
                    "metadata": self.document_metadata
                }, f)
            print("💾 Index avancé Kiwi sauvegardé")
        except Exception as e:
            print(f"❌ Erreur sauvegarde: {e}")

    def _load_advanced_index(self):
        """Chargement avancé de l'index"""
        try:
            with open("kiwi_advanced_index.pkl", 'rb') as f:
                data = pickle.load(f)
                self.documents = data["documents"]
                self.vectorizer = data["vectorizer"]
                self.svd = data["svd"]
                self.doc_vectors = data["doc_vectors"]
                self.reduced_vectors = data["reduced_vectors"]
                self.document_metadata = data["metadata"]
            print("📂 Index avancé Kiwi chargé depuis le cache")
            return True
        except Exception as e:
            print(f"❌ Erreur chargement: {e}")
            return False

    # =============== FONCTIONNALITÉS EXPERTES ===============

    def search_junior_entreprises(
            self,
            city: str = None,
            domain: str = None,
            school: str = None,
            region: str = None) -> List[Dict]:
        """Recherche experte de Junior Entreprises"""
        query_parts = []
        if city:
            query_parts.append(f"ville {city}")
        if domain:
            query_parts.append(f"domaine {domain}")
        if school:
            query_parts.append(f"école {school}")
        if region:
            query_parts.append(f"région {region}")

        query = " ".join(query_parts) if query_parts else "junior entreprise"

        results = self.search_advanced(query, ["junior_entreprises"])

        je_list = []
        for doc, score in results:
            if doc.get('type') == 'junior_entreprises':
                je_info = {
                    "name": doc.get('name', 'N/A'),
                    "city": doc.get('city', 'N/A'),
                    "school": doc.get('school', 'N/A'),
                    "domain": doc.get('domain', 'N/A'),
                    "email": doc.get('email', 'N/A'),
                    "website": doc.get('website', 'N/A'),
                    "score": score,
                    "content": doc.get('content', '')
                }
                je_list.append(je_info)

        return je_list

    def search_faq_kiwi(self, query: str, category: str = None) -> List[Dict]:
        """Recherche experte dans la FAQ Kiwi Legal"""
        search_query = f"{query} {category}" if category else query
        results = self.search_advanced(search_query, ["faq"])

        faq_list = []
        for doc, score in results:
            if doc.get('type') == 'faq':
                faq_info = {
                    "question": doc.get('question', 'N/A'),
                    "answer": doc.get('answer', 'N/A'),
                    "category": doc.get('category', 'N/A'),
                    "score": score,
                    "priority": doc.get('priority', 1)
                }
                faq_list.append(faq_info)

        return faq_list

    def get_legal_guidance(
            self, topic: str, category: str = None) -> Dict[str, Any]:
        """Guidance juridique experte via Kiwi Legal"""
        search_query = f"{topic} {category}" if category else topic
        results = self.search_advanced(search_query, ["legal_site"], [
                                       category] if category else None)

        if not results:
            return {
                "guidance": "Aucune guidance juridique trouvée",
                "sources": []}

        # Compilation de la guidance
        legal_content = []
        sources = []

        for doc, score in results:
            legal_content.append(doc.get('content', ''))
            sources.append({
                "source": doc.get('source', ''),
                "category": doc.get('legal_category', ''),
                "url_path": doc.get('url_path', ''),
                "score": score
            })

        # Génération de guidance via Claude
        context = "\n---\n".join(legal_content)
        prompt = f"""En tant qu'expert juridique Kiwi Legal, fournis une guidance précise sur: {topic}

SOURCES KIWI LEGAL:
{context}

Fournis une guidance structurée, précise et actionnable."""

        try:
            response = self.claude_client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=MAX_TOKENS,
                temperature=0.1,
                messages=[{"role": "user", "content": prompt}]
            )

            return {
                "topic": topic,
                "guidance": response.content[0].text,
                "sources": sources,
                "kiwi_legal_verified": True
            }
        except Exception as e:
            return {"guidance": f"Erreur génération guidance: {e}",
                    "sources": sources}
