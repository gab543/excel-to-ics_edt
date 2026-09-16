# EDT to ICS

Application en construction pour analyser le classeur Excel fourni et produire un calendrier ICS fidèle à sa géométrie.

## Démarrage

```powershell
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --reload
```

L'API est disponible sur `http://127.0.0.1:8000`; la documentation interactive est sur `/docs`.

Le parseur conserve les plages fusionnées et les sources Excel. Les informations absentes restent inconnues et sont exposées dans `warnings`; l'export est refusé tant qu'un événement est incomplet.

## Tests

```powershell
python -m pytest -q
```
