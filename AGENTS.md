# AGENTS.md — Excel Timetable to ICS

## 0. MISSION

Tu es le développeur principal de ce projet.

Ta mission est de **concevoir et développer entièrement une application web personnelle permettant de transformer des emplois du temps Excel (.xlsx) en calendrier .ics importable dans Google Calendar, Apple Calendar, Outlook ou tout autre calendrier compatible ICS.**

Ce n'est PAS un simple script Excel → ICS.

Le cœur du produit est un moteur capable de comprendre un emploi du temps Excel dont la structure est visuelle et potentiellement complexe :

- cellules fusionnées ;
- grille horaire ;
- jours organisés en colonnes ou lignes ;
- événements occupant plusieurs créneaux ;
- couleurs ;
- bordures ;
- zones imbriquées ;
- plusieurs semaines ;
- semaines irrégulières ;
- exceptions ;
- informations partiellement explicites ;
- texte positionné de manière non triviale.

L'application doit reconstruire la structure logique de l'emploi du temps avant de produire les événements calendrier.

---

# 1. OBJECTIF PRODUIT

L'expérience utilisateur finale doit être :

Utilisateur
    ↓
Upload d'un fichier .xlsx
    ↓
Analyse automatique
    ↓
Reconstruction de l'emploi du temps
    ↓
Détection des événements
    ↓
Calcul de confiance
    ↓
Détection des ambiguïtés
    ↓
Prévisualisation sous forme de calendrier
    ↓
Correction éventuelle par l'utilisateur
    ↓
Validation
    ↓
Export .ics

Le produit doit privilégier :

    exactitude > automatisation > sophistication

Si le système n'est pas certain d'une information, il doit le signaler plutôt que l'inventer.
2. CONSIGNE DE DÉVELOPPEMENT

Tu dois réellement construire le produit dans le repository.

Ne te contente pas de :

    proposer une architecture ;

    expliquer ce qu'il faudrait faire ;

    écrire du pseudo-code ;

    produire une roadmap sans implémentation.

Tu dois :

    inspecter le repository ;

    inspecter les fichiers disponibles ;

    choisir une architecture cohérente ;

    créer les fichiers nécessaires ;

    implémenter le backend ;

    implémenter le frontend ;

    écrire les tests ;

    exécuter les tests ;

    corriger les erreurs ;

    lancer l'application ;

    vérifier le fonctionnement ;

    documenter le projet.

Si une décision technique raisonnable peut être prise sans demander confirmation, prends-la et avance.

Ne bloque pas le développement pour des détails secondaires.
3. STACK TECHNIQUE

Utilise cette stack sauf contrainte réelle découverte dans le repository.
Backend

    Python 3.12+

    FastAPI

    Pydantic

    openpyxl

    icalendar

    pytest

Frontend

    React

    TypeScript

    Vite

    CSS moderne ou Tailwind si déjà présent / pertinent

Architecture

frontend/
backend/
tests/
fixtures/
docs/

Le backend et le frontend doivent être séparés proprement.
4. PREMIÈRE ACTION OBLIGATOIRE

Avant d'écrire du code :
Inspecte le repository.

Tu dois déterminer :

    fichiers présents ;

    stack existante ;

    package managers ;

    configuration ;

    éventuelle application déjà commencée ;

    fichiers Excel disponibles ;

    README existant ;

    tests existants.

Ensuite, si un fichier .xlsx est disponible :
analyse-le réellement.

Ne suppose PAS sa structure.

Tu dois inspecter :

    feuilles ;

    dimensions ;

    cellules non vides ;

    cellules fusionnées ;

    coordonnées ;

    valeurs ;

    types ;

    formules ;

    couleurs ;

    styles ;

    bordures ;

    largeur des colonnes ;

    hauteur des lignes ;

    représentation des jours ;

    représentation des heures ;

    représentation des dates ;

    organisation des semaines.

Le parser initial doit être développé à partir de la structure réelle du fichier fourni, pas à partir d'un exemple imaginaire.
5. ARCHITECTURE DU PRODUIT

L'application doit être organisée en pipeline.

                    XLSX
                     │
                     ▼
              ┌───────────────┐
              │ Excel Reader  │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Workbook Model│
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Grid Analyzer │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Region Detector│
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Event Detector│
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Interpreter   │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ Validation    │
              └───────┬───────┘
                      │
                      ▼
              ┌───────────────┐
              │ ICS Generator │
              └───────────────┘

Chaque couche doit avoir une responsabilité claire.
6. NE PAS COUPLER LE DOMAINE À OPENPYXL

openpyxl ne doit être utilisé que dans la couche d'import Excel.

Ne fais PAS circuler des objets openpyxl.Cell dans toute l'application.

Construis tes propres modèles.

Par exemple :

WorkbookModel
SheetModel
CellModel
MergedRegion
GridModel
GridRegion
TimeSlot
DayColumn
EventCandidate
CalendarEvent

Ainsi :

Excel
 ↓
openpyxl
 ↓
Domain Model
 ↓
reste de l'application

et non :

Excel
 ↓
openpyxl
 ↓
toute l'application

7. MODÈLE DE DONNÉES

Créer des modèles Pydantic/dataclasses propres.

Exemple conceptuel :

class CellModel:
    coordinate: str
    row: int
    column: int
    value: str | None
    background_color: str | None
    font_color: str | None
    is_merged: bool
    merged_region_id: str | None

class GridRegion:
    id: str

    sheet_name: str

    min_row: int
    max_row: int
    min_column: int
    max_column: int

    text: str | None

    background_color: str | None

    parent_region_id: str | None
    child_region_ids: list[str]

    source_cells: list[str]

class EventCandidate:
    id: str

    title: str | None

    date: date | None

    start_time: time | None
    end_time: time | None

    location: str | None
    teacher: str | None
    group: str | None

    confidence: float

    warnings: list[str]

    source_region_ids: list[str]

    status: str

Adapter les modèles à la réalité du fichier.
8. ANALYSE DE LA GRILLE

Le parser doit comprendre la géométrie du fichier.

Il doit être capable de déterminer :

    quelle zone représente les jours ;

    quelle zone représente les horaires ;

    quelles lignes correspondent aux créneaux ;

    quelles colonnes correspondent aux jours ;

    quelles zones correspondent aux événements.

Exemple :

        L      M      M      J      V
07:00
08:00
09:00
10:00
11:00
12:00
13:00
14:00

doit devenir une structure logique exploitable.
9. HORAIRES

Supporter différents formats :

7
7h
07h
07:00
7:00
7h30
07h30
07:30

Créer une fonction de normalisation.

Exemple :

parse_time("7h30") == time(7, 30)
parse_time("07:30") == time(7, 30)

Ne pas disperser la logique de parsing des heures dans le code.
10. JOURS

Supporter le français.

Exemples :

Lundi
Mardi
Mercredi
Jeudi
Vendredi
Samedi
Dimanche

ainsi que les abréviations lorsqu'elles sont non ambiguës.

Attention aux structures comme :

L M M J V

où les deux M correspondent à des jours différents.

La position dans la grille doit être utilisée.
11. CELLULES FUSIONNÉES

Les cellules fusionnées sont un élément essentiel du parser.

Exemple :

B7:H20

doit être représenté comme une région unique.

Le système doit savoir :

région
├── coordonnées
├── texte
├── dimensions
├── cellules couvertes
├── parent éventuel
└── enfants éventuels

Ne jamais traiter les cellules fusionnées uniquement comme une collection de cellules indépendantes.
12. RÉGIONS IMBRIQUÉES

Le fichier peut contenir une structure de ce type :

┌─────────────────────────────────┐
│            Tout projet          │
│                                 │
│       ┌─────────────────┐       │
│       │ 13h             │       │
│       │ leçons du mardi │       │
│       └─────────────────┘       │
│                                 │
└─────────────────────────────────┘

Le système doit comprendre qu'il existe :

Region A
└── Region B

et non deux événements indépendants automatiquement.

La géométrie doit donc être conservée.
13. COULEURS ET STYLES

Les styles Excel peuvent contenir de l'information utile.

Extraire au minimum :

    background ;

    font ;

    bordures ;

    alignement.

Mais :

    une couleur seule ne doit jamais être considérée comme preuve qu'une zone est un événement.

La couleur est un signal.

Elle peut être utilisée conjointement avec :

    position ;

    texte ;

    fusion ;

    durée ;

    contexte ;

    voisinage.

14. DÉTECTION DES ÉVÉNEMENTS

Créer un véritable EventDetector.

Il reçoit :

GridModel

et produit :

list[EventCandidate]

Il doit rechercher les régions pouvant représenter des événements.

Un événement peut provenir :

    d'une cellule ;

    d'une plage ;

    d'une cellule fusionnée ;

    d'une région ;

    d'une structure composée de plusieurs régions.

15. NE PAS INVENTER LES DONNÉES

Règle critique :

Si le fichier ne permet pas de déterminer une information avec suffisamment de certitude :

date = null
start_time = null
end_time = null

et non une valeur arbitraire.

Le système doit alors créer :

warning

Exemple :

"Impossible de déterminer automatiquement l'heure de fin."

L'interface demandera ensuite confirmation.
16. SYSTÈME DE CONFIANCE

Chaque EventCandidate possède :

confidence ∈ [0,1]

Le score doit être calculé par des règles compréhensibles.

Par exemple :

date clairement détectée       +0.30
heure début clairement détectée +0.25
heure fin clairement détectée   +0.25
titre clairement détecté        +0.10
lieu clairement détecté         +0.05
structure cohérente             +0.05

Ces coefficients doivent être centralisés et facilement modifiables.

Ne pas faire :

confidence = random...

ou un score opaque.
17. STATUT DES ÉVÉNEMENTS

Utiliser des statuts explicites.

Par exemple :

DETECTED
NEEDS_REVIEW
VALIDATED
IGNORED
INVALID

Flux :

DETECTED
   │
   ├── confiance élevée ──→ VALIDATED
   │
   └── ambigu ──→ NEEDS_REVIEW
                       │
                 utilisateur
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
         VALIDATED            IGNORED

18. SEMAINES

Le produit doit gérer plusieurs semaines.

Il ne faut pas supposer :

même cours toutes les semaines

Exemple :

Semaine 1
Mardi 09:00 Mathématiques

Semaine 2
Mardi 10:00 Informatique

Semaine 3
Mardi 09:00 Mathématiques

Ces événements sont des occurrences différentes.

Ne pas générer automatiquement :

RRULE:FREQ=WEEKLY

simplement parce que le jour est identique.
19. RÉCURRENCES

Une récurrence ICS ne doit être générée que si le moteur a identifié un pattern réellement régulier.

Sinon :

VEVENT
VEVENT
VEVENT

est préférable.

La priorité est la fidélité au planning Excel.
20. EXPORT ICS

Créer une couche dédiée :

generate_ics(events, timezone)

Utiliser icalendar.

Chaque événement doit contenir autant que possible :

UID
DTSTAMP
DTSTART
DTEND
SUMMARY
LOCATION
DESCRIPTION

Gérer correctement :

    timezone ;

    accents ;

    caractères spéciaux ;

    échappement ;

    retours à la ligne ;

    dates ;

    heures.

Timezone par défaut :

Europe/Paris

mais configurable.
21. UID

Les UID doivent être stables.

Ne pas générer un nouvel UUID aléatoire à chaque export si cela empêche de comparer deux versions du planning.

Créer une stratégie déterministe basée sur les propriétés pertinentes de l'événement.

Cette stratégie doit être documentée.
22. BACKEND API

Créer une API propre.

Minimum :

POST /api/import

→ upload du .xlsx

Retour :

{
  "import_id": "...",
  "events": [...],
  "warnings": [...]
}

Puis :

GET /api/import/{id}

pour récupérer l'analyse.

Prévoir ensuite :

PUT /api/import/{id}/events/{event_id}

pour modifier un événement.

Et :

POST /api/import/{id}/export

pour générer le .ics.

Les endpoints peuvent être adaptés selon l'architecture finale.
23. FRONTEND

Créer une interface réellement utilisable.

L'utilisateur doit voir :
Écran 1

Importer mon emploi du temps

[ Déposer mon fichier Excel ]

ou

[ Choisir un fichier ]

Écran 2

Après analyse :

Analyse terminée

42 événements détectés

✓ 38 événements fiables
⚠ 4 événements à vérifier

[Voir mon emploi du temps]

Écran 3

Afficher une vraie vue calendrier.

Exemple :

         LUNDI       MARDI       MERCREDI

08:00    ███████
09:00    ███████    ███████
10:00               ███████
11:00
12:00
13:00               ███████
14:00               ███████

Les événements doivent être cliquables.
24. MODIFICATION D'UN ÉVÉNEMENT

Cliquer sur un événement doit ouvrir un formulaire.

Champs :

Titre
Date
Heure de début
Heure de fin
Salle
Enseignant
Groupe
Description

Afficher également :

Niveau de confiance
Warnings
Source Excel

Exemple :

Événement ambigu

"Leçons du mardi"

Date
[22/09/2026]

Début
[13:00]

Fin
[15:00]

⚠ L'heure de fin a été déduite

L'utilisateur peut alors :

[Valider]

25. SOURCE EXCEL

L'interface doit pouvoir indiquer pourquoi un événement a été créé.

Exemple :

Source :

Feuille : Planning
Zone : B12:D15
Cellule principale : B12

Texte détecté :
"Mathématiques"

Heure détectée :
09:00 → 11:00

C'est important pour la confiance dans le produit et le debugging.
26. VALIDATION AVANT EXPORT

L'utilisateur ne doit pas pouvoir exporter silencieusement des événements incomplets.

Avant export :

42 événements

✓ 39 validés
⚠ 3 nécessitent une vérification

Afficher :

[Corriger les 3 problèmes]

ou permettre explicitement de les ignorer.
27. COMPARAISON ENTRE IMPORTS

Préparer l'architecture pour permettre plus tard :

planning_ancien.xlsx
planning_nouveau.xlsx

et détecter :

+ nouveaux
  ~ modifiés

- supprimés
  = inchangés

Cette fonctionnalité peut être hors MVP, mais les modèles de données doivent permettre de l'ajouter sans réécrire tout le parser.
28. PROFILS DE FORMAT

Le parser doit être extensible.

Créer une abstraction de type :

TimetableFormatProfile

Un profil peut définir :

position des jours
position des heures
règles de détection
règles de couleurs
règles spécifiques

Le premier profil doit être celui correspondant au fichier Excel réel fourni avec le projet.

Ne pas construire immédiatement 15 profils hypothétiques.
29. GESTION DES ERREURS

L'utilisateur ne doit jamais voir :

Traceback...
KeyError...
AttributeError...

Afficher des erreurs compréhensibles.

Exemple :

Nous n'avons pas réussi à identifier la grille horaire
de cette feuille.

Vous pouvez sélectionner manuellement la feuille
à utiliser.

Les détails techniques doivent être disponibles dans les logs.
30. TESTS OBLIGATOIRES

Créer de vrais tests.

Minimum :

tests/
├── parser/
├── detection/
├── interpretation/
├── calendar/
└── integration/

Tester notamment :
Excel

    feuille simple ;

    cellules fusionnées ;

    plusieurs feuilles ;

    cellules vides ;

    couleurs ;

    horaires différents ;

    jours ambigus.

Détection

    événement simple ;

    événement de 2h ;

    événement de plusieurs créneaux ;

    régions imbriquées ;

    événements qui se chevauchent ;

    informations manquantes.

ICS

    événement simple ;

    timezone ;

    accents ;

    lieu ;

    description ;

    UID ;

    événements multiples ;

    récurrence lorsque pertinente.

31. GOLDEN FILES

Créer des fichiers de référence.

Exemple :

fixtures/
├── simple_week.xlsx
├── merged_event.xlsx
├── nested_regions.xlsx
├── irregular_weeks.xlsx
└── ambiguous.xlsx

Chaque fixture doit avoir un résultat attendu.

Par exemple :

fixtures/simple_week.expected.json

permettant de comparer :

Excel réel
      ↓
parser
      ↓
résultat
      ↓
expected.json

32. NON-RÉGRESSION

Chaque bug découvert pendant le développement doit devenir un test.

Exemple :

bug_001_duplicate_monday
bug_002_merged_cell
bug_003_nested_region
bug_004_missing_end_time

Ne pas corriger un bug avec un hack qui casse un autre format.
33. DEBUGGING DU PARSER

Créer un mode permettant d'inspecter la reconstruction.

Il doit être possible d'obtenir quelque chose comme :

SHEET: Planning

TIME AXIS
07:00 → row 8
08:00 → row 9
09:00 → row 10

DAY AXIS
Monday    → column C
Tuesday   → column D
Wednesday → column E

REGIONS

R001
range: C8:C10
text: "Mathématiques"
merged: true
confidence: 0.97

R002
range: D8:D15
text: "Tout projet"
merged: true
children:
  R003

R003
text: "Leçons du mardi"

C'est un outil de développement important.
34. INTERDICTIONS

Ne fais PAS les choses suivantes :
Pas de parser naïf

Ne fais pas :

for row in worksheet:
    for cell in row:
        if cell.value:
            create_event(cell.value)

Ce type d'approche ne suffit pas pour ce projet.
Pas d'OCR

Le fichier est un Excel.

Exploite sa structure native.
Pas de LLM au cœur du parsing

Le LLM peut éventuellement être ajouté plus tard pour interpréter du texte ambigu.

Il ne doit pas remplacer :

    la géométrie ;

    les cellules fusionnées ;

    les coordonnées ;

    les horaires ;

    les dates.

Pas de hardcoding du fichier

Éviter :

if cell.coordinate == "B17":

sauf dans des tests ou règles explicitement propres au profil.
Pas de valeurs inventées

Si l'information est inconnue :

unknown

et non une supposition silencieuse.
35. QUALITÉ DU CODE

Le code doit être :

    typé ;

    lisible ;

    modulaire ;

    testable ;

    documenté lorsque nécessaire.

Éviter les fonctions de plusieurs centaines de lignes.

Éviter les classes inutiles.

Éviter les abstractions prématurées.

Mais ne pas sacrifier l'architecture du domaine au profit d'un prototype jetable.
36. PRIORITÉ DE DÉVELOPPEMENT

Développer dans cet ordre précis :
PHASE 1 — Compréhension du fichier

Analyser réellement le .xlsx.

Livrable :

analyse structurelle

PHASE 2 — Domain model

Créer :

WorkbookModel
SheetModel
CellModel
MergedRegion
GridModel
GridRegion

PHASE 3 — Grid Analyzer

Créer :

Excel → GridModel

avec détection :

    jours ;

    heures ;

    dimensions ;

    régions ;

    fusions.

PHASE 4 — Event Detector

Créer :

GridModel → EventCandidate[]

avec :

    titre ;

    date ;

    début ;

    fin ;

    lieu ;

    source ;

    confiance ;

    warnings.

PHASE 5 — Validation

Créer les statuts :

DETECTED
NEEDS_REVIEW
VALIDATED
IGNORED
INVALID

PHASE 6 — ICS

Créer :

CalendarEvent[] → .ics

PHASE 7 — API

Connecter le pipeline à FastAPI.
PHASE 8 — Frontend

Construire :

upload
→ analysis
→ calendar
→ review
→ export

PHASE 9 — Tests de bout en bout

Tester :

.xlsx
 ↓
parser
 ↓
events
 ↓
validation
 ↓
.ics

37. CRITÈRES D'ACCEPTATION DU MVP

Le MVP est considéré comme terminé uniquement lorsque :

    l'application démarre localement ;

    l'utilisateur peut importer un .xlsx ;

    le backend analyse réellement le fichier ;

    les cellules fusionnées sont prises en compte ;

    les jours sont détectés ;

    les horaires sont détectés ;

    les régions sont reconstruites ;

    les événements sont détectés ;

    les événements ambigus sont signalés ;

    chaque événement possède une source ;

    chaque événement possède un niveau de confiance ;

    l'utilisateur peut modifier un événement ;

    l'utilisateur peut ignorer un événement ;

    l'utilisateur peut valider un événement ;

    un calendrier visuel est affiché ;

    le fichier ICS est généré ;

    les dates et heures sont correctes ;

    Europe/Paris est correctement géré ;

    les accents fonctionnent ;

    les tests passent ;

    le README explique comment lancer le projet.

38. CRITÈRES DE QUALITÉ

Le projet ne doit pas seulement "fonctionner".

Je veux pouvoir ouvrir le repository dans quelques mois et comprendre :

où le fichier Excel est lu
où la grille est reconstruite
où les événements sont détectés
où la confiance est calculée
où les événements sont validés
où le ICS est généré

L'architecture doit rendre ces responsabilités évidentes.
39. RÈGLE IMPORTANTE SUR LES DÉCISIONS

Lorsque tu rencontres un problème :
Si tu peux le résoudre proprement :

résous-le.
Si plusieurs solutions sont raisonnables :

choisis celle qui :

    est la plus simple ;

    est robuste ;

    est testable ;

    permet une extension future.

Si le fichier Excel est réellement ambigu :

ne devine pas.

Représente l'ambiguïté dans le modèle et expose-la à l'utilisateur.
40. MODE DE TRAVAIL

Travaille de manière incrémentale.

Après chaque étape importante :

    implémente ;

    lance les tests ;

    corrige les erreurs ;

    vérifie que le projet démarre ;

    seulement ensuite passe à l'étape suivante.

Ne fais pas un énorme changement non testé.
41. PREMIÈRE SESSION DE TRAVAIL

Commence immédiatement.
Étape 1

Inspecte le repository.
Étape 2

Trouve les fichiers .xlsx.
Étape 3

Analyse le fichier Excel réel.
Étape 4

Documente sa structure.
Étape 5

Crée le domain model.
Étape 6

Implémente le premier parser.
Étape 7

Ajoute les premiers tests basés sur le fichier réel.
Étape 8

Lance les tests.

Ne passe pas directement au frontend.

Le parser est la partie la plus importante du projet.
42. FORMAT DE TES COMPTES-RENDUS

À chaque étape importante, réponds brièvement avec :

## Fait

Ce qui a été implémenté.

## Fichiers modifiés

Liste des fichiers importants.

## Tests

Tests exécutés et résultat.

## Problèmes rencontrés

Uniquement les vrais problèmes.

## Prochaine étape

Ce que tu vas implémenter ensuite.

Ne transforme pas chaque réponse en long document théorique.

Le travail doit être effectué dans le repository.
43. DEFINITION OF DONE

Une fonctionnalité n'est pas considérée comme terminée simplement parce que le code a été écrit.

Elle est terminée lorsque :

code
+
tests
+
exécution réussie
+
gestion des erreurs
+
intégration au reste du système

sont réalisés.
44. OBJECTIF FINAL

Le résultat final doit donner à l'utilisateur l'impression suivante :

    "Je donne mon fichier Excel compliqué au logiciel, il comprend comment mon emploi du temps est construit, me montre ce qu'il a compris, me demande uniquement de vérifier les choses ambiguës, puis me donne un calendrier propre."

C'est cette expérience qui constitue le produit.

Construis donc le système autour de cette promesse.

Commence maintenant par inspecter le repository et le fichier Excel réel.
