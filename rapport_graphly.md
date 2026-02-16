# Rapport Graphly (Logre)

## 1. Contexte et objectif
Ce rapport clarifie comment Graphly est intégré dans Logre, pourquoi plusieurs logiques se superposent, et quelles options sont possibles pour stabiliser la dépendance. L’objectif est d’aider l’équipe à comprendre l’état actuel, les contraintes (notamment Docker), et les conséquences des choix “vendorisé” vs “forké”.

## 2. Inventaire des sources Graphly dans le repo
Graphly apparaît sous plusieurs formes dans ce dépôt :

- `graphly/` : copie complète du code Graphly utilisée en local et en Docker.
- `graphly_backup/` : seconde copie quasiment identique, avec quelques différences fonctionnelles.
- `requirements.txt` : installe Graphly depuis GitHub (`git+https://github.com/lod4hss-apps/graphly.git`).
- Scripts d’installation : `makefile` et `logre.bat` clonent Graphly puis font `pip install .`.
- `Dockerfile` : installe les requirements puis force `pip install ./graphly`.
- `KB.md` : décrit `graphly/` comme “vendored dependency”.

## 3. Logique d’installation actuelle (et ordre réel de priorité)
Les différents chemins d’installation se superposent :

### 3.1. Dans Docker
- `requirements.txt` installe Graphly depuis GitHub.
- Ensuite, `pip install ./graphly` force la version locale à écraser la version installée.

Conséquence : en Docker, **la version réellement utilisée est `graphly/`** (vendorisée dans le dépôt), même si `requirements.txt` installe autre chose auparavant.

### 3.2. En local (Makefile)
- `make install` installe d’abord les requirements (GitHub Graphly).
- Puis clone/maj Graphly dans `graphly/` et `pip install .`.

Conséquence : en local, **la version réellement utilisée est aussi `graphly/`**, qui écrase la version GitHub.

### 3.3. En local (Windows / `logre.bat`)
- Même logique : clone Graphly et `pip install .` après `requirements.txt`.

## 4. Observations sur l’état actuel
### 4.1. Graphly est bien “vendored” et versionné
Même si `.gitignore` contient `graphly`, le dossier est déjà suivi par Git (donc bien distribué dans le repo). Cela explique pourquoi Docker peut installer `./graphly` sans cloner.

### 4.2. Le packaging Graphly est atypique
`graphly/pyproject.toml` déclare `name = "myproject"` (et non “graphly”). Ce n’est pas standard et peut expliquer des divergences d’installation/metadata. C’est un indicateur fort de “clone rapide + packaging minimal”.

### 4.3. Duplication réelle : `graphly/` vs `graphly_backup/`
Les deux copies sont quasi identiques, avec 3 fichiers divergents :

- `graphly/graphly/models/shacl.py`
  - Version “graphly” gère un `range_datatype` distinct et le mappe sur `range_target`.
  - Version “backup” fusionne `datatype` directement dans `range_class_uri`.
- `graphly/graphly/schema/graph.py`
  - Version “graphly” traite explicitement `str()` pour sujet/objet avant `prepare`.
  - Version “backup” utilise les valeurs sans conversion explicite.
- `graphly/graphly/sparql/allegrograph.py`
  - Version “graphly” ajoute le préfixe `franz` et évite de muter les Prefixes partagés.
  - Version “backup” modifie l’objet Prefixes passé en paramètre.

Ces écarts suggèrent des **patches ciblés pour Logre**, notamment :
- robustesse de l’export Turtle,
- meilleure gestion des datatypes SHACL,
- compat AllegroGraph sans effets de bord.

## 5. Hypothèses plausibles sur “pourquoi c’est comme ça”
1. **Besoin de modifications rapides non upstreamées** : Logre a exigé des ajustements qui n’étaient pas (ou pas encore) dans le Graphly original.
2. **Contraintes Docker** : le build doit être reproductible sans dépendre d’un repo externe non figé. `pip install ./graphly` garantit une version locale stable.
3. **Historique de migration** : `graphly_backup/` ressemble à un snapshot “avant patch”, conservé comme référence ou sécurité.
4. **Risque d’instabilité upstream** : Graphly n’est pas sur PyPI, packaging minimal → le vendor rend l’intégration plus sûre.

## 6. Options pour stabiliser l’intégration

### Option A — Vendorisé (Graphly dans Logre)
**Principe** : garder Graphly dans ce repo, le versionner ici, et supprimer la dépendance GitHub.

Avantages :
- Reproductibilité maximale (Docker, CI, offline).
- Modifications locales immédiates.
- Moins de dépendances externes.

Inconvénients :
- Duplication d’un projet entier dans Logre.
- Maintenance plus lourde (merges manuels si Graphly évolue en amont).
- Risque d’accumuler du “fork implicite” sans gouvernance claire.

Conditions de réussite :
- Nettoyer `requirements.txt` (retirer `git+...graphly`).
- Supprimer la logique de clone dans `makefile`/`logre.bat`.
- Conserver uniquement `pip install ./graphly` (Docker et local).

### Option B — Fork officiel de Graphly
**Principe** : créer un fork Graphly (ex: `lod4hss-apps/graphly-logre`) et pinner un commit dans `requirements.txt`.

Avantages :
- Source de vérité claire et versionnée.
- Patches partagés et historisés proprement.
- Réduction de la duplication dans Logre.

Inconvénients :
- Besoin d’un repo séparé + gouvernance.
- Dépendance externe au build (GitHub disponible, réseau nécessaire).
- Moins “offline-ready” qu’un vendor pur.

Conditions de réussite :
- `requirements.txt` pointe vers le fork (commit/tag figé).
- Supprimer `graphly/` du repo Logre.
- Retirer le `pip install ./graphly` dans Dockerfile et scripts.

### Option C — Hybride (actuel)
**Principe** : garder `graphly/` dans Logre tout en installant aussi Graphly GitHub.

Conséquence :
- Cela fonctionne mais **crée de l’ambiguïté** (deux sources de vérité).
- La version réellement utilisée est locale, mais la présence du GitHub crée une confusion fonctionnelle et un risque de divergence silencieuse.

## 7. Contraintes spécifiques Docker
- Dockerfile installe `requirements.txt` puis force `pip install ./graphly`.
- Ce choix indique clairement une volonté de **prioriser une version locale “bundled”** pour éviter les surprises.
- Si l’équipe bascule vers un fork, il faudra **retirer cette étape** ou elle écrasera systématiquement la version forkée.

## 8. Risques actuels identifiés
- Ambiguïté de source de vérité (GitHub vs local).
- Possibles divergences invisibles si quelqu’un modifie `graphly/` sans le refléter ailleurs.
- `graphly_backup/` entretient la confusion (on ne sait pas laquelle est “bonne”).
- Packaging Graphly (pyproject “myproject”) rend la traçabilité pip fragile.

## 9. Pistes de clarification immédiate
Sans modifier le choix stratégique, voici des actions “low risk” :

- Documenter explicitement la source de vérité dans `README.md` ou `KB.md`.
- Supprimer ou archiver `graphly_backup/` après validation de son utilité.
- Ajouter un check simple “quelle version est utilisée” dans la doc dev.

## 10. Conclusion
L’intégration actuelle fonctionne car **la version locale `graphly/` écrase la version GitHub**. Cela donne un comportement de type “vendor”, mais sans l’assumer explicitement dans la documentation et les dépendances. Deux chemins clairs existent :

- **Assumer le vendor** (supprimer l’install GitHub + scripts de clone).
- **Assumer le fork** (retirer `graphly/` du repo Logre et pinner un fork).

Dans les deux cas, l’objectif est de supprimer la logique hybride qui brouille la compréhension et augmente le risque de divergence.

---

## Ticket GitHub propose

**Titre**: Assumer Graphly vendorise et supprimer la logique hybride

**Contexte**
Graphly est installe via deux voies concurrentes (GitHub + copie locale) mais la version locale ecrase toujours la version distante (Docker et scripts locaux). Cela cree une ambiguite de source de verite, un risque de divergence silencieuse et complique la maintenance. La decision d equipe est de ne pas developper Graphly en dehors de Logre.

**Decision**
Assumer officiellement l integration vendorisee de Graphly dans Logre et supprimer toute logique qui installe Graphly depuis un repo externe.

**Justification**
- Aligne l architecture avec l intention: toutes les modifications Graphly restent dans Logre.
- Stabilite et reproductibilite (Docker et local) sans dependance externe.
- Reduction du risque de divergence et de confusion pour les nouveaux contributeurs.

**Plan d actions**
1) Supprimer la dependance Graphly GitHub de `requirements.txt`.
2) Simplifier l installation locale:
   - `makefile`: retirer le clone/pull Graphly et conserver uniquement `pip install ./graphly`.
   - `logre.bat`: idem.
3) Docker:
   - Conserver l installation locale `pip install ./graphly`.
   - S assurer qu aucune autre etape n ecrase cette version.
4) Nettoyage:
   - Archiver ou supprimer `graphly_backup/` apres validation.
5) Documentation:
   - Mettre a jour `README.md` et/ou `KB.md` pour declarer Graphly comme dependency vendorisee.

**Criteres d acceptation**
- Logre demarre et fonctionne en local et en Docker sans installer Graphly depuis GitHub.
- La source de verite Graphly est unique: `graphly/`.
- Documentation explicite de cette decision.
