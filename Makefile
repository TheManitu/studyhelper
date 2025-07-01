.PHONY: install install-dev run test help

# Installiert alle Python-Abhängigkeiten aus requirements.txt
install:
	pip install --upgrade pip
	pip install -r requirements.txt

# Installiert zusätzliche Dev-Tools (z.B. pytest)
install-dev:
	pip install pytest

# Startet die Streamlit-App (Streamlit.py im Projektverzeichnis)
run:
	python -m streamlit run app.py

# Führt alle Tests aus (z.B. test_*.py)
test:
	python -m pytest --maxfail=1 --disable-warnings

# Übersicht der verfügbaren Befehle
help:
	@echo "Verfügbare Targets:"
	@echo "  make install      # Installiert Projekt-Abhängigkeiten"
	@echo "  make install-dev  # Installiert Dev-Tools (z.B. pytest)"
	@echo "  make run          # Startet die Streamlit-App"
	@echo "  make test         # Führt Tests aus"
