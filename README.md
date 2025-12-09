# 📚 BBW Notenverwaltung

**Ein modernes, lokales Dashboard zur Verwaltung von Schulnoten, Klassenanalysen und Kommunikation.**

Dieses Projekt ist eine Streamlit-basierte Webanwendung, die für Lehrpersonen entwickelt wurde, um den administrativen Aufwand im Schulalltag zu minimieren.

-----

### 🔒 WICHTIGER HINWEIS: Local-First Design

**Datenschutz hat bei diesem Projekt höchste Priorität.**
Diese Anwendung wurde bewusst mit einer **"Local-First"-Architektur** entwickelt. Das bedeutet:

1.  **Keine Cloud:** Es gibt keine zentrale Datenbank und keinen Cloud-Server, auf dem Schülerdaten gespeichert werden.
2.  **Lokale Speicherung:** Alle sensiblen Daten (Namen, Noten, E-Mail-Adressen) verbleiben ausschliesslich auf Ihrem lokalen Gerät (im Ordner `data/`).
3.  **Kontrolle:** Sie behalten die volle Kontrolle über Ihre Daten. Sie verlassen Ihren Rechner nur dann, wenn Sie explizit die E-Mail-Funktion nutzen.

-----

## 🚀 Hauptfunktionen

### 🏫 Klassen- & Schülerverwaltung

  * **Multi-Klassen-Support:** Verwalten Sie mehrere Klassen (z. B. "4PK26a") in einer einzigen Instanz.
  * **Einfacher Import:** Importieren Sie Schülerlisten und bestehende Noten bequem via Excel oder CSV.
  * **Schüler/innen-Management:** Einfaches Hinzufügen und Entfernen von Lernenden.

### 📝 Intelligentes Notenbuch

  * **Flexible Gewichtung:** Unterstützt verschiedene Gewichtungen (z. B. Tests 2.0, Lernpfade 1.0) und berechnet automatisch Schnitte.
  * **Bewertungsskalen:** Integrierte Skalen (z. B. 60%-Skala, 50%-Skala) zur automatischen Umrechnung von Punkten in Noten.
  * **Smart Tools:**
      * ⚡ **Curve:** Heben Sie Noten einer ganzen Prüfung pauschal an.
      * ⚡ **Auffüllen:** Füllen Sie fehlende Noten automatisch mit einem Standardwert (z. B. 1.0) auf.

### 📊 Analyse & Monitoring

  * **Echtzeit-Dashboards:** Visualisierung von Klassenschnitten und Notenverteilungen mittels interaktiver Charts (Plotly).
  * **Frühwarnsystem:** Automatische Erkennung von "Risikoschülern/innen" (Schnitt unter 4.0).
  * **Schülerdetails:** Detaillierte Ansicht pro Schüler/in mit Vergleich zum Klassendurchschnitt.

### ✉️ Smart Email Center

  * **Vorlagen-Engine:** Erstellen Sie wiederverwendbare E-Mail-Vorlagen (z. B. "Lob", "Warnung", "Notenbericht").
  * **Platzhalter:** Nutzen Sie Variablen wie `{firstname}`, `{average}` oder `{grades_list}` für personalisierte Nachrichten.
  * **Massenversand:** Senden Sie personalisierte Berichte an ausgewählte Schüler/innen oder die ganze Klasse via SMTP.

### 🛡️ Datensicherheit & Audit

  * **Backup-System:** Erstellen Sie manuelle oder automatische Snapshots des gesamten Systems.
  * **Audit-Log:** Lückenlose Nachvollziehbarkeit aller Änderungen (z. B. "Note geändert von 4.5 auf 5.0").

-----

## 🛠️ Installation & Start

Voraussetzung: Python 3.8 oder höher.

1.  **Repository klonen oder herunterladen:**

    ```bash
    git clone https://github.com/aburossi/noten-verwaltung
    cd aburossi-noten-verwaltung
    ```

2.  **Abhängigkeiten installieren:**
    Es wird empfohlen, eine virtuelle Umgebung (venv) zu nutzen.

    ```bash
    pip install -r requirements.txt
    ```

3.  **Demo-Daten generieren (Optional):**
    Um das Tool direkt mit einer gefüllten Testklasse auszuprobieren, führen Sie dieses Skript aus:

    ```bash
    python generate_demo_data.py
    ```

4.  **Anwendung starten:**

    ```bash
    streamlit run app.py
    ```

-----

## 📖 Bedienungsanleitung

### 1\. Dashboard (Startseite)

Hier sehen Sie alle angelegten Klassen. Wählen Sie eine Klasse aus ("Öffnen") oder erstellen Sie über das Panel rechts eine neue Klasse.

### 2\. Navigation

Nach dem Öffnen einer Klasse erscheint in der Sidebar das Menü:

  * **📊 Übersicht:** Schneller Blick auf Klassenschnitte in den Fächern (z. B. GESELLSCHAFT, SPRACHE).
  * **📈 Analyse:** Tiefere Einblicke. Identifizieren Sie schwierige Prüfungen oder Schüler/innen mit Handlungsbedarf.
  * **📝 Fächer (z. B. GESELLSCHAFT):** Das Herzstück der Verwaltung.
      * Erstellen Sie hier neue Prüfungen.
      * Tragen Sie Punkte ein (Note wird automatisch berechnet).
      * Nutzen Sie die "Smart Tools" (im Dropdown-Menü jeder Prüfung), um Noten anzupassen.
  * **✉️ Smart Emails:** Wählen Sie eine Vorlage und filtern Sie Empfänger (z. B. "Nur Ungenügende").
  * **💾 Backup & Log:** Erstellen Sie Backups vor grossen Änderungen oder stellen Sie alte Stände wieder her.

### 3\. Daten Import/Export

Unter dem Menüpunkt **📁 Import/Export** können Sie Schülerlisten via Excel importieren.

  * Format Excel/CSV: Spalten `Anmeldename`, `Vorname`, `Nachname`.

-----

## 📂 Projektstruktur

```text
aburossi-noten-verwaltung/
├── app.py                  # Hauptanwendung (Entry Point)
├── generate_demo_data.py   # Skript zum Erzeugen von Testdaten
├── requirements.txt        # Python Abhängigkeiten
├── data/                   # Datenspeicher (JSON Files, wird autom. erstellt)
│   ├── classes.json        # Register aller Klassen
│   └── classes/            # Ordner für jede einzelne Klasse
├── pages_ui/               # UI-Module für die verschiedenen Seiten
│   ├── analytics.py        # Analyse & Charts
│   ├── backups.py          # Backup Logik
│   ├── data_io.py          # Import/Export UI
│   ├── emails.py           # E-Mail Center
│   ├── overview.py         # Start-Übersicht der Klasse
│   └── subjects.py         # Noteneingabe & Prüfungsverwaltung
└── utils/                  # Hilfsfunktionen & Logik
    ├── data_manager.py     # Laden/Speichern von JSON, Backups
    ├── email_manager.py    # SMTP Versandlogik
    ├── grading.py          # Notenberechnung & Gewichtung
    └── template_manager.py # Verwaltung der E-Mail Vorlagen
```

-----

## ⚙️ Konfiguration

Die globalen Einstellungen (z. B. Bewertungsskalen, Fächerliste) befinden sich in `utils/constants.py` oder werden nach dem ersten Start in `data/global_config.json` gespeichert.

**E-Mail Konfiguration:**
Standardmässig ist der SMTP-Server auf `mail.bbw.ch` konfiguriert. Um E-Mails zu versenden, müssen Sie im Reiter "Smart Emails" Ihr Absender-Passwort eingeben. Dieses wird **nicht** gespeichert, sondern nur für die Laufzeit der aktuellen Sitzung im Arbeitsspeicher gehalten.

-----

## 🔐 Datenschutz & Git-Konfiguration (WICHTIG)

Wenn Sie den Programmcode mit Git verwalten (z. B. auf GitHub speichern), müssen Sie zwingend verhindern, dass echte Schülerdaten hochgeladen werden. Da der Code und die Daten strikt getrennt sind, lässt sich dies einfach über `.gitignore` lösen.

### .gitignore Einrichtung

Erstellen Sie im Hauptverzeichnis eine Datei namens `.gitignore` mit folgendem Inhalt:

```text
# --- BBW Notenverwaltung Gitignore ---

# 1. Ignoriere alle sensiblen Daten im Data-Ordner
data/

# 2. Ignoriere Python Systemdateien & Umgebung
__pycache__/
*.pyc
venv/
.env
.DS_Store
```

**Was bewirkt das?**
Durch den Eintrag `data/` ignoriert Git alle Dateien in diesem Ordner.

  * **Vorteil:** Sie können Updates am Programmcode (`app.py`, `utils/`) herunterladen (`git pull`), ohne dass Ihre lokalen Noten überschrieben werden.
  * **Sicherheit:** Es landen versehentlich keine Personendaten in öffentlichen Repositories.

-----

## 📄 Lizenz

Dieses Projekt ist für interne Bildungszwecke konzipiert.
**Author:** Pietro Rossi
