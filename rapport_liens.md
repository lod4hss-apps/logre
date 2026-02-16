# Rapport Liens (Logre)

## 1. Objectif
Clarifier pourquoi certains liens sortent de Logre (URI externes) et proposer une standardisation: tous les liens doivent rester internes a Logre, avec l URI reelle accessible uniquement depuis la carte d entite dans un endroit dedie.

## 2. Constat general
- Plusieurs vues rendent des URIs comme liens externes (Wikidata, etc.).
- D autres vues utilisent deja des liens internes ou des actions internes.
- Il existe une incoherence d URL interne entre pages (ex: /entity vs /entity-card).

## 3. Emplacements qui sortent de Logre

### 3.1. Raw Triples
- `src/pages/entity-triples.py` (fonction `render_resource`)
- Lien externe: `prefixes.lengthen(uri)`
- Effet: navigation hors Logre si l URI est resolvable.

### 3.2. Dialog Triple Info
- `src/dialogs/triple_info.py`
- Tous les champs URI sont rendus comme liens externes via `prefixes.lengthen(...)`.

## 4. Emplacements deja internes

### 4.1. Entity Card
- `src/pages/entity-card.py`
- Navigation interne via `state.set_entity_uri` + `st.switch_page`.
- Affichage de l URI actuelle via `st.code(entity.uri)` (sans lien externe).

### 4.2. Visualization
- `src/pages/entity-chart.py`
- Liens internes sous forme `/entity?db=...&uri=...`.
- Incoherence: cible differente de la data table.

### 4.3. Data Table
- `src/pages/data-table.py`
- Colonne Open vers `/entity-card?endpoint=...&db=...&uri=...` (interne).

## 5. Incoherence identifiee
- `entity-chart.py` utilise `/entity?...` alors que `data-table.py` utilise `/entity-card?...`.
- Risque: page inexistante ou comportement ambigu selon Streamlit.

## 6. Comportement cible
- Tous les liens doivent rester internes a Logre.
- Les URIs reelles ne doivent etre visibles et ouvrables que depuis la carte d entite, dans un bloc dedie.
- Les URIs doivent etre encodees en URL pour eviter les erreurs de navigation.

## 7. Proposition de normalisation
- Remplacer les liens externes par des liens internes dans:
  - `src/pages/entity-triples.py`
  - `src/dialogs/triple_info.py`
- Uniformiser la cible interne sur `/entity-card?endpoint=...&db=...&uri=...`.
- Ajouter un bloc explicite “External URI” sur `src/pages/entity-card.py` (avec bouton qui ouvre l URI reelle).
- Conserver l URI brute en code (lisible, copiable).

---

## Ticket GitHub propose

**Titre**: Standardiser la navigation interne et isoler les URIs externes

**Contexte**
Plusieurs ecrans rendent les URIs RDF comme liens externes, ce qui envoie l utilisateur hors Logre (Wikidata ou URL non resolvable). L objectif est que toute navigation reste interne, et que l URI reelle ne soit accessible que depuis la carte d entite.

**Decision**
Standardiser tous les liens entite vers des URLs internes Logre et limiter les liens externes a un bloc dedie dans la carte d entite.

**Plan d actions**
1) Remplacer les liens externes par des liens internes dans:
   - `src/pages/entity-triples.py`
   - `src/dialogs/triple_info.py`
2) Uniformiser la route interne vers `/entity-card` et encoder l URI.
3) Ajouter un bloc “External URI” sur `src/pages/entity-card.py` avec un lien explicite pour ouvrir l URI reelle.
4) Verifier la coherence avec la data table et la visualization.

**Criteres d acceptation**
- Aucune page ne genere de lien externe vers une URI RDF (hors bloc dedie de l entity card).
- Navigation interne fonctionne depuis Raw Triples, Triple Info, Visualization, Data Table.
- Toutes les URIs sont encodees dans les URLs internes.
