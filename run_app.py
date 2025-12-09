import streamlit.web.cli as stcli
import os, sys

def resolve_path(path):
    """Findet den Pfad, egal ob als Skript oder als Exe"""
    if getattr(sys, '_MEIPASS', False):
        # Wenn als Exe ausgeführt
        return os.path.join(sys._MEIPASS, path)
    return os.path.join(os.path.abspath("."), path)

if __name__ == "__main__":
    # Wir simulieren den Befehl "streamlit run app.py"
    sys.argv = [
        "streamlit",
        "run",
        resolve_path("app.py"),
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())