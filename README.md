# OFE Filter – QGIS Plugin für On-Farm-Experimente

Das OFE Filter Plugin ist das zweite Plugin im OFE-Werkzeugkasten der OG SNaPwürZ. Es unterstützt dich in QGIS beim Bereinigen und Filtern von Punktdatensätzen, wie sie in On-Farm-Experimenten anfallen (z. B. Ertragsdaten). Dazu gehören räumliche Zuschnitte über Polygonflächen (z.B. Feldgrenze oder Parzellen), Ausreißerfilter (Unter-/Obergrenze, Standardabweichung), das manuelle Entfernen von Punkten sowie die Übertragung von Parzellenattributen (z.B. Versuchsvariante, Block).

> Hinweis: Das Plugin arbeitet projektbasiert. Das QGIS-Projekt muss gespeichert sein, damit Output-Ordner und Logs angelegt werden können.

---

## 📋 Inhaltsverzeichnis

- [Überblick](#überblick)
- [Features](#features)
- [Filtermethoden](#filtermethoden)
- [Installation](#installation)
- [Schnellstart](#schnellstart)
- [Voraussetzungen](#voraussetzungen)
- [Verzeichnisstruktur](#verzeichnisstruktur)
- [Output-Struktur](#output-struktur)
- [Logging](#logging)
- [Support & Kontakt](#support--kontakt)
- [Lizenz](#lizenz)

---

## 🎯 Überblick

Mit dem OFE Filter erstellst du aus einem bestehenden Punkt-Layer eine Kopie (Shapefile) und kannst diese anschließend:

- räumlich zuschneiden (Feldgrenze / Innenfläche / Parzellen),
- Ausreißer anhand von Attributwerten selektieren,
- Punkte manuell selektieren und löschen,
- Parzellenattribute in den Punktdatensatz übernehmen,
- und bei Bedarf Attribute/Spalten manuell anlegen und Werte für ausgewählte Punkte setzen.

Die Ergebnisse werden im Projekt abgelegt und in QGIS in einer eigenen Layergruppe organisiert.

---

## ✨ Features

### Daten & Ausgabe
- ✅ Erstellt automatisch einen neuen Layer **`Filter_<Originalname>`**
- ✅ Speichert Ausgabe im Projektordner (Ordner **`OFE_Filter/`**)
- ✅ Fügt den neuen Layer in die Gruppe **„Gefilterte Daten“** ein
- ✅ Graduierte Symbolisierung für numerische Attribute (8 Klassen)

### Datenzuschnitt (räumlich)
- **Auf Feldgrenze zuschneiden**: entfernt Punkte außerhalb der Feldgrenze
- **Vorgewende abschneiden**: behält nur Punkte innerhalb einer „Innenfläche“
- **Auf Parzellen zuschneiden**: entfernt Punkte außerhalb der Parzellenflächen
- **Ausschlussfläche**: entfernt Punkte innerhalb einer Ausschlussfläche (z. B. Fahrspuren, Störungen)
- **Punkte manuell löschen**: interaktive Auswahl im Kartenfenster

### Attributfilter (numerisch)
- Untergrenze (mit Vergleich „<“ oder „≤“)
- Obergrenze (mit Vergleich „>“ oder „≥“)
- Standardabweichung: Mittelwert ± (Multiplikator × SD), wahlweise nur Unter- oder Obergrenze  
  Optional kann die SD auf Basis bereits gefilterter Daten berechnet werden.

### Attribute anfügen & manuell setzen
- **Parzellenattribute anfügen**: räumlicher Join (Polygon → Punkt) für ausgewählte Felder
- **Attribute manuell einfügen**: neue Spalten anlegen (String/Ganzzahl/Dezimalzahl)
- **Werte manuell setzen**: Punkte auswählen und Wert für ein Attribut überschreiben

### Visualisierung
- Histogramm-/Verteilungsplot (inkl. gefilterter Werte und Grenzlinien)
- Histogramm-Export als PNG/JPG/PDF

---

## 🧪 Filtermethoden

| Filter | Beschreibung | Typ |
|-------|--------------|-----|
| **Untergrenze** | Selektiert Werte unterhalb einer Schwelle (`<` oder `≤`) | numerisch |
| **Obergrenze** | Selektiert Werte oberhalb einer Schwelle (`>` oder `≥`) | numerisch |
| **Standardabweichung** | Selektiert Ausreißer über Mittelwert ± (Multiplikator × SD); Methode: beidseitig / nur unten / nur oben | numerisch |


---

## 🧩 Installation

### Option A (empfohlen): Installation über QGIS-Plugin-Repository (Auto-Updates)
> Hier gehts zum ausführlichen Tutorial: [Installation der SNaPWürZ Plugins für QGIS](https://farmwiki.de/de/Tutorials/GIS/QGIS/installation_snapwuerz_plugin)

1. QGIS öffnen
2. **Erweiterungen → Erweiterungen verwalten und installieren…**
3. Reiter **Einstellungen**
4. Sicherstellen, dass **Auch experimentelle Erweiterungen anzeigen** aktiviert ist
5. Unter **Erweiterungsrepositorien** auf **Hinzufügen…** klicken
5. Name vergeben (z. B. `SNaPwürZ OFE-Filter`) und folgende URL eintragen:

   `https://github.com/FARMWISSEN/OFE-Filter/releases/latest/download/plugins.xml`

6. Mit **OK** bestätigen und **Repos aktualisieren** / **Neu laden**
7. Reiter **Alle** (oder Suche) → **OFE-Filter** auswählen → **Installieren**


### Option B: Manuelle Installation aus dem Quellcode (für Entwicklung)
Diese Variante ist für Entwickler gedacht.

1. Repository klonen oder herunterladen
2. Sicherstellen, dass der Plugin-Ordner **`ofe_filter/`** direkt im QGIS-Plugin-Verzeichnis liegt:

   Windows (Standardprofil):
   `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\ofe_filter`

3. QGIS neu starten und Plugin im Plugin-Manager aktivieren

### Python-Abhängigkeiten
Das Plugin benötigt zusätzliche Python-Module: pandas und matplotlib (siehe `metadata.txt`).
> Hier gehts zum ausführlichen Tutorial: [Installation von Python-Paketen in der Python-Umgebung von QGIS](https://farmwiki.de/de/Tutorials/GIS/QGIS/installation_python_pakete_qgis)

**Windows (OSGeo4W Shell):**
```bash
python -m pip install pandas matplotlib
```

**Mac (QGIS App Bundle):**
```bash
/Applications/QGIS-LTR.app/Contents/MacOS/bin/pip3 install pandas matplotlib
```

> In vielen QGIS-Installationen sind `numpy`/`matplotlib` bereits vorhanden – `pandas` ist jedoch nicht immer vorinstalliert.

---

## 🚀 Schnellstart

1. **Projekt speichern** (wichtig, sonst kann kein Output erzeugt werden).
2. Plugin öffnen: **Praxisversuche → OFE-Filter**
3. Unter **Daten**:
   - Punktdaten-Layer auswählen
   - optional: Parzellen, Feldgrenze, Innenfläche, Ausschlussfläche auswählen
   - **Hinzufügen** klicken → es wird `Filter_<Layer>` erstellt
4. Unter **Datenzuschnitt**:
   - gewünschte Zuschnitte ausführen (Feldgrenze / Innenfläche / Parzellen / Ausschlussfläche)
5. Unter **Filter**:
   - Attribut auswählen
   - Unter-/Obergrenze und/oder SD-Filter anwenden
   - Histogramm prüfen und bei Bedarf speichern
6. Optional:
   - Punkte manuell löschen
   - Parzellenattribute anfügen
   - Attribute manuell anlegen und Werte für ausgewählte Punkte setzen

---

## 🧰 Voraussetzungen

- QGIS >= 3.x
- Python-Module: pandas, matplotlib (zusätzlich zu QGIS-Standardbibliotheken)

---

## 🗂️ Verzeichnisstruktur

```text
OFE-Filter/
├── metadata.txt                 # Plugin-Metadaten (Name, Version, Abhängigkeiten)
├── ofe_filter.py                # Hauptlogik (Layerkopie, Zuschnitt, Filter, Selektion)
├── ofe_filter_dialog.py         # UI-Controller (Workflow, Plot, Button-Logik)
├── ofe_filter_dialog_base.ui    # Qt Designer UI
├── ofe_LogManager.py            # Logging (JSON + CSV)
├── resources.qrc / resources.py # Icons/Resources
├── i18n/                        # Übersetzungen
└── help/                        # Sphinx-Doku (Template)
```

---

## 📦 Output-Struktur

Im (Projekt-)Ordner werden u. a. folgende Verzeichnisse verwendet:

```text
<Projektordner>/
├── OFE_Filter/                  # erzeugte Filter-Shapefiles (Filter_<Layer>.shp + Nebenfiles)
├── Logs/                        # Filter-Logs (JSON + CSV)
└── Histogramme/                 # gespeicherte Histogramme (PNG/JPG/PDF)
```

---

## 🧾 Logging

Alle wichtigen Aktionen (Zuschnitt, Filterparameter, Attributübernahmen etc.) werden in **`Logs/`** protokolliert:

- **JSON**: strukturierter Log (für Auswertung/Archivierung)
- **CSV**: einfache, tabellarische Nachvollziehbarkeit

Die Logdateien enthalten einen Zeitstempel im Dateinamen.

---

## 🆘 Support & Kontakt

- Fehler bitte als Issue melden: https://github.com/FARMWISSEN/OFE-Filter/issues 
- Repository: https://github.com/FARMWISSEN/OFE-Filter
- Projekthomepage: https://snapwürz.de/
![](https://xn--snapwrz-r2a.de/wp-content/uploads/2024/06/Logo_Transparent-1-1024x635.png)

---

## :dollar: Förderung
### Europäische Innovationspartnerschaft (EIP Agri)
Das Projekt **Chancen durch digitale Innovation in On Farm Research und Exaktversuchen** (SNaPwürZ) wird durch die EU im Rahmen der Europäischen Innovationspartnerschaft (EIP Agri) und das Landesprogramm Ländlicher Raum des Landes Schleswig-Holstein (LPLR) gefördert. Ziel ist es, neue Problemlösungen anzuregen, die die Nachhaltigkeit und Effizienz in der Landwirtschaft steigern. Jedes Projekt wird durch eine Operationelle Gruppe (OG) gesteuert. Darin arbeiten Landwirte, Wissenschaftler, Berater, NGOs und Wirtschaftspartner gemeinsam.

www.eip-agrar-sh.de 

---

## 📄 Lizenz

Dieses Projekt ist freie Software: Du kannst es unter den Bedingungen der **GNU General Public License** weiterverbreiten und/oder modifizieren, wie von der Free Software Foundation veröffentlicht; entweder **Version 2 der Lizenz** oder (nach deiner Wahl) **jeder späteren Version**.

Der vollständige Lizenztext liegt in der Datei **LICENSE.txt**.

**SPDX-License-Identifier:** `GPL-2.0-or-later`
