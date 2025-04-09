Structure de l'application :

archiviste-compteurs/
├── archiviste-compteurs.py  # Lanceur principal avec onglets
├── scripts/
│   ├── db_designer.py      # Adaptation de 00-DB_designer.py
│   ├── meter_readings.py   # Adaptation de 01-Releves_compteurs.py
│   ├── meter_reports.py    # Adaptation de 02-Rapports_compteurs.py
├── db/
│   └── meters.db           # Base de données SQLite