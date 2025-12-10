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

## 🚀 Hauptfunktionen (Update v2.0)

### ⚡ Schnelleingabe & Workflow

  * **📝 Schnelleingabe:** Eine Matrix-Ansicht (Grid), um Noten für mehrere Fächer und Prüfungen gleichzeitig einzutragen – ideal für schnelle Korrekturen.
  * **📋 Smart Templates:** Erstellen Sie neue Prüfungen mit einem Klick basierend auf Vorlagen ("Wochentest", "Vortrag") oder kopieren Sie die letzte Prüfung.
  * **📊 Live-Kontext:** Sehen Sie während der Noteneingabe sofort den Klassenschnitt und visuelle Warnungen bei ungenügenden Noten (< 4.0).
  * **🔗 LMS-Integration:** Verlinken Sie Moodle/LMS-Kurse direkt in der Prüfungsübersicht.

### 🏫 Klassen- & Schülerverwaltung

  * **Multi-Klassen-Support:** Verwalten Sie mehrere Klassen in einer Instanz.
  * **Dashboard Schnellzugriff:** Springen Sie vom Hauptmenü direkt in die Fächer (GESELLSCHAFT / SPRACHE).
  * **Einfacher Import:** Importieren Sie Schülerlisten und Noten via Excel direkt in den Fächern oder im zentralen Daten-Tab.

### ✉️ Smart Email Center

  * **🤖 Smart Batch Report:** Das System erkennt automatisch Schüler/innen mit neuen Noten und schlägt einen personalisierten Wochenbericht vor.
  * **Vorlagen-Engine:** Nutzen Sie Platzhalter wie `{firstname}`, `{average}` oder `{grades_list}` (formatiert als HTML-Tabelle).
  * **Massenversand:** Senden Sie personalisierte Berichte via SMTP (BBW Mail Server).

### 📊 Analyse & Monitoring

  * **Wochen-Summary:** Ein Dashboard zeigt auf einen Blick erledigte Prüfungen, offene E-Mails und Handlungsbedarf (Risikoschüler).
  * **Trend-Erkennung:** Visuelle Indikatoren (📈📉) zeigen, ob sich ein/e Schüler/in verbessert oder verschlechtert hat.

### 🛡️ Datensicherheit

  * **Backup-System:** Erstellen Sie manuelle Snapshots oder laden Sie das gesamte System als ZIP herunter.
  * **Audit-Log:** Lückenlose Nachvollziehbarkeit aller Änderungen (z. B. "Note geändert von 4.5 auf 5.0").

-----

## 🛠️ Installation & Start

Voraussetzung: Python 3.8 oder höher. Empfohlen Python 3.12. [Installationsanleitung](https://github.com/aburossi/noten-verwaltung/blob/main/python_installation.md)

1.  **Repository klonen oder herunterladen:**

    ```bash
    git clone [https://github.com/aburossi/noten-verwaltung](https://github.com/aburossi/noten-verwaltung)
    cd aburossi-noten-verwaltung
    ```

2.  **Abhängigkeiten installieren:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Anwendung starten:**

    ```bash
    streamlit run app.py
    ```

-----

## 📖 Bedienungsanleitung

### 1. Dashboard (Startseite)
Hier sehen Sie alle Klassen. Nutzen Sie die **Schnellzugriff-Buttons** ("GESELLSCHAFT", "SPRACHE"), um direkt in das jeweilige Fach zu springen.

### 2. Navigation & Module

  * **📝 Schnelleingabe:** Die effizienteste Methode für die Noteneingabe. Bearbeiten Sie alle Fächer in einer Tabelle.
  * **📊 Übersicht:** Zeigt den aktuellen Wochenstatus, KPIs und Klassenschnitte.
  * **📝 Fächer (z. B. GESELLSCHAFT):**
      * Nutzen Sie "Kopiere letzte Prüfung" für wiederkehrende Tests.
      * Importieren Sie Notenlisten direkt via Excel.
      * Geben Sie Noten ein (0.0 zum Löschen).
  * **✉️ Smart Emails:** Klicken Sie auf "✨ Wochenbericht senden", um automatisch alle Schüler/innen mit neuen Noten auszuwählen.
  * **📁 Import/Export/Backup:** Zentraler Ort für Datenmanagement, Backups und Wiederherstellung.

-----

## ⚙️ Konfiguration (SMTP)

Um E-Mails zu versenden, müssen Sie im Reiter "Smart Emails" Ihr Absender-Passwort eingeben.
**Standard-Server:** `mail.bbw.ch` (Port 465).
Das Passwort wird **nicht** gespeichert, sondern nur für die Laufzeit der Sitzung im RAM gehalten.

-----

## 📂 Projektstruktur

```text
aburossi-noten-verwaltung/
├── app.py                  # Hauptanwendung (Streamlit Entry Point)
├── generate_demo_data.py   # Skript zur Erzeugung von Testdaten
├── run_app.py              # Wrapper-Skript (für Deployment/Exe)
├── requirements.txt        # Python Abhängigkeiten
├── data/                   # Lokaler Datenspeicher (JSON)
│   ├── classes.json        # Klassen-Registry
│   └── classes/            # Datenordner pro Klasse
├── pages_ui/               # UI-Module (Frontend)
│   ├── analytics.py        # Charts & Reports
│   ├── backups.py          # (Legacy) Backup Logik
│   ├── data_io.py          # Import, Export & Backup UI (Zentral)
│   ├── emails.py           # Smart Email Center
│   ├── overview.py         # Dashboard & Wochen-Summary
│   ├── quick_entry.py      # NEU: Matrix-Eingabe
│   └── subjects.py         # Noteneingabe & Prüfungsverwaltung
└── utils/                  # Hilfsfunktionen (Backend Logic)
    ├── constants.py        # Konfiguration & Konstanten
    ├── data_manager.py     # JSON IO, File-Handling & Backups
    ├── email_manager.py    # SMTP Versand & Change Detection
    ├── grading.py          # Notenberechnung & Trend-Logik
    └── template_manager.py # Verwaltung der E-Mail Vorlagen