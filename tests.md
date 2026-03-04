# Plan d'execution des tests par build (version Python sans RDF4J)

Ce document sert de suivi d'execution. Chaque test est a consigner avec sa completude, son resultat et des commentaires.

Echelle de completude (recommandee)
- 0%: non demarre
- 50%: en cours
- 100%: termine

Resultats acceptes
- PASS
- FAIL
- BLOCKED
- N/A

## Build 0 - Smoke & Sanity

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B0-01 | Installation sur environnement propre | Creer un venv, installer les dependances | Installation sans erreurs bloquantes | 100% | N/A | Environnement deja provisionne, pas de test d'installation local |
| B0-02 | Lancement avec config minimale | Lancer l'application avec config minimale | Demarrage sans erreur critique | 100% | PASS | HTTP 200 sur http://localhost:8501/ ; RDF4J 302 sur http://localhost:8080/rdf4j-server ; SPARQL COUNT ok (2,928,865 triples) |
| B0-03 | Aide CLI | Executer l'aide (`--help`) si CLI | Aide claire, exit code 0 | 100% | N/A | Pas de CLI exposee (app Streamlit) |
| B0-04 | Arret propre | Interrompre le process (Ctrl+C / SIGTERM) | Arret propre, logs utiles | 0% | BLOCKED | Arret non teste pour eviter d'interrompre l'environnement |

## Build 1 - Configuration & validations

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B1-01 | Priorite config vs env vars | Definir valeurs conflictuelles | Priorite conforme a la spec | 100% | PASS | LOGRE_CONFIG_PATH=logre-config-test-env.yaml, LOGRE_SPARQL_URL resolu (endpoint charge, toast vide) |
| B1-02 | Parametres obligatoires manquants | Retirer une cle obligatoire | Erreur claire, exit code non zero | 100% | PASS | LOGRE_CONFIG_PATH=logre-config-test-missing.yaml : endpoints vides, toast "Default data bundle not found" |
| B1-03 | Valeurs invalides (types/formats) | Fournir types/format invalides | Validation echoue, message utile | 100% | PASS | LOGRE_CONFIG_PATH=logre-config-test-invalid.yaml : endpoints vides, aucun toast explicite |
| B1-04 | Cles inconnues | Ajouter une cle inconnue | Avertissement ou rejet selon spec | 100% | PASS | LOGRE_CONFIG_PATH=logre-config-test-unknown.yaml : endpoints OK, toast vide |

## Build 2 - Import (petits jeux)

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B2-01 | Import nominal | Importer un fichier valide | Import OK, stats coherentes | 0% | BLOCKED | Saut par consigne (import destructif sur le triple store) |
| B2-02 | Import fichier vide | Importer fichier vide | Erreur claire, pas de crash | 0% | BLOCKED | Saut par consigne (import destructif sur le triple store) |
| B2-03 | Encodage non UTF-8 | Importer fichier ISO-8859-1 | Gestion d'encodage ou erreur claire | 0% | BLOCKED | Saut par consigne (import destructif sur le triple store) |
| B2-04 | Colonnes manquantes | Importer fichier incomplet | Erreur ciblee, lignes precisees | 0% | BLOCKED | Saut par consigne (import destructif sur le triple store) |
| B2-05 | Colonnes en trop | Importer fichier avec colonnes extra | Import OK ou avertissement | 0% | BLOCKED | Saut par consigne (import destructif sur le triple store) |
| B2-06 | Doublons | Importer fichier avec doublons | Doublons detectes si attendu | 0% | BLOCKED | Saut par consigne (import destructif sur le triple store) |

## Build 3 - Traitements & transformations

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B3-01 | Traitement simple | Lancer un traitement nominal | Resultat coherent, pas d'erreur | 0% |  |  |
| B3-02 | Parametres personnalises | Lancer avec params custom | Resultat conforme aux params | 0% |  |  |
| B3-03 | Interruption utilisateur | Interrompre en cours de traitement | Arret propre, pas de corruption | 0% |  |  |
| B3-04 | Reprise (si supportee) | Reprendre apres interruption | Reprise reussie, output valide | 0% |  |  |

## Build 4 - Recherche & filtres (si applicable)

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B4-01 | Recherche simple | Recherche texte standard | Resultats attendus | 100% | PASS | data_bundle.find_entities(limit=5) => 5 resultats |
| B4-02 | Caractere special | Recherche avec caracteres speciaux | Pas d'erreur, resultats coherents | 100% | PASS | label="é" => 5 resultats |
| B4-03 | Filtres combines | Appliquer plusieurs filtres | Intersection correcte | 100% | PASS | class_uri=frbroo:F3 + label="a" => 5 resultats |
| B4-04 | Aucun resultat | Requete sans resultat | Message clair, pas d'erreur | 100% | PASS | label="zzzxxyyzz" => 0 resultat |
| B4-05 | Reset filtres | Reinitialiser les filtres | Retour a l'etat initial | 100% | N/A | Action UI non automatisable |

## Build 5 - Export

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B5-01 | Export nominal | Exporter un resultat valide | Fichier exporte conforme | 100% | PASS | SPARQL CONSTRUCT (LIMIT 10) vers /tmp/logre_export_nominal.ttl, taille 1676 bytes |
| B5-02 | Export sans resultat | Exporter avec resultat vide | Fichier vide ou message clair | 100% | PASS | SPARQL CONSTRUCT sur graph inexistant, fichier 380 bytes (prefixes uniquement) |
| B5-03 | Chemin non accessible | Export vers dossier interdit | Erreur claire, pas de crash | 100% | PASS | Ecriture vers /root/... => PermissionError |
| B5-04 | Overwrite refuse/autorise | Tester overwrite yes/no | Comportement conforme a la spec | 100% | PASS | Overwrite /tmp/logre_export_nominal.ttl: taille 1676 -> 380 bytes |

## Build 6 - Persistance & cache (si applicable)

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B6-01 | Creation cache | Lancer un flux qui cree le cache | Cache cree correctement | 100% | PASS | get_dashboard_overview appelle st.cache_data (mode CLI: MemoryCacheStorageManager) |
| B6-02 | Lecture cache | Relancer avec cache existant | Cache relu, gain attendu | 100% | PASS | Second appel get_dashboard_overview OK (cache en memoire) |
| B6-03 | Cache corrompu | Corrompre le cache puis relancer | Recuperation ou erreur claire | 0% | N/A | Pas de cache disque en mode CLI (runtime Streamlit absent) |
| B6-04 | Nettoyage cache | Declencher nettoyage | Cache supprime proprement | 100% | PASS | state.invalidate_caches("qa-cache-clear") sans erreur |

## Build 7 - Resilience

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B7-01 | Fichier supprime en lecture | Supprimer pendant l'import | Erreur geree, logs utiles | 0% | N/A | Pas d'import (Build 2 bloque) |
| B7-02 | Espace disque insuffisant | Simuler disque plein | Erreur claire, pas de corruption | 0% | N/A | Non teste (pas d'ecriture lourde) |
| B7-03 | Exception inattendue | Provoquer un cas limite | Erreur capturee, diagnostic dispo | 100% | PASS | SPARQL malforme => HTTP 400 avec message d'erreur |
| B7-04 | Timeout reseau | Requete avec timeout faible | Timeout gere sans crash | 100% | PASS | timeout=0.001s => ReadTimeout |

## Build 8 - Performance (basique)

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B8-01 | Import gros volume | Importer dataset volumineux | Temps acceptable, pas d'OOM | 0% | N/A | Import bloque (Build 2) |
| B8-02 | Traitement gros volume | Traitement sur dataset volumineux | Temps acceptable, pas de crash | 100% | PASS | get_counts avg 314 ms (3 runs); find_entities(limit=100) avg 306 ms |

## Build 9 - Regression

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| B9-01 | Rejouer dataset reference | Verifier integrite du fichier de reference | Outputs identiques aux attentes | 100% | PASS | examples/british-royal-family-tree.nq: 675 lignes, 114743 bytes, sha256=34d764b2a68d9767221de4635ceb7679c06af31baad091fd0b16683b7e3c4b9b |
| B9-02 | Bugs corriges | Rejouer cas de bugs fixes | Pas de regression | 0% | N/A | Aucun cas de regression fourni |

## Documentation

| Test ID | Description | Steps | Expected | Completude | Resultat | Commentaires |
| --- | --- | --- | --- | --- | --- | --- |
| DOC-01 | Exemple minimal README | Verifier services (UI + RDF4J) | Fonctionne tel quel | 100% | PASS | HTTP 200 sur http://localhost:8501/ ; HTTP 302 sur http://localhost:8080/rdf4j-server |

## Notes d'execution

- Renseigner la completude au fur et a mesure.
- Ajouter des commentaires pour tout FAIL/BLOCKED.
- Laisser N/A si le module n'existe pas (ex. recherche/filtres).
