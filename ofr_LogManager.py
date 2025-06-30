import os
import json
import csv
from datetime import datetime
from qgis.core import QgsProject

class LogManager:
    def __init__(self, layer_source: str, project_path: str):
        # Zeitstempel für die Log-Datei
        timestamp = datetime.now().strftime("%d.%m.%Y_%H-%M-%S")
        self.base_name = f"Filter_log_{layer_source}_{timestamp}"

        # Verzeichnis für Logs im Projektverzeichnis anlegen
        self.log_dir = os.path.join(project_path, "Logs")
        os.makedirs(self.log_dir, exist_ok=True)

        # Pfade für JSON- und CSV-Logdateien
        self.json_path = os.path.join(self.log_dir, self.base_name + ".json")
        self.csv_path = os.path.join(self.log_dir, self.base_name + ".csv")

        # Initiale Logdatenstruktur
        self.data = {
            "plugin": {
                "name": "",
                # Gibt es schon eine Version?
                "version": "",
                "timestamp": timestamp
            },
            "project": {
                "name": QgsProject.instance().fileName().rsplit('/', 1)[1]
            },
            "layers": {},
            "actions": [],
            "statistics": []
        }

    def set_plugin_info(self, name, version):
        self.data["plugin"]["name"] = name
        self.data["plugin"]["version"] = version

    # Speichert Layerinformationen (z.B. Feldgrenze)
    def set_layer_info(self, **kwargs):
        self.data["layers"].update(kwargs)

    # Protokolliert eine Aktion (z. B. "Filter: Standardabweichung")
    def log_event(self, action_type: str, details: dict):
        entry = {
            "timestamp": datetime.now().strftime("%d.%m.%Y_%H-%M-%S"),
            "type": action_type,
            "details": details # Dictionary mit statistischen Kennwerten
        }
        self.data["actions"].append(entry)

    # Fügt statistische Informationen zu einem Attribut hinzu (z. B. Mittelwert)
    def log_statistic(self, attribute_r: str, stats_r: dict, attribute_f:str, stats_f: dict):
        self.data["statistics"].append({
            "timestamp": datetime.now().strftime("%d.%m.%Y_%H-%M-%S"),
            "Daten gesamt:": attribute_r,
            "Werte gesamt": stats_r,
            "Daten gefiltert:": attribute_f,
            "Werte gefilter": stats_f
        })

    def write_logs(self):
        # Schreibt die gesamte Logstruktur in eine JSON-Datei
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

        # Schreibt alle Aktionen in eine CSV-Datei (einfache Nachvollziehbarkeit)
        with open(self.csv_path, "w", newline='', encoding="utf-8") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(["Zeit", "Typ", "Details"])
            for entry in self.data["actions"]:
                writer.writerow([
                    entry["timestamp"],
                    entry["type"],
                    json.dumps(entry["details"], ensure_ascii=False)
                ])