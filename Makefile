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
	@echo "  make docker-build-chat  # Build NiceGUI-Image inkl. Chat"
	@echo "  make docker-up-chat     # Startet gesamten Stack (inkl. Ollama)"
	@echo "  make docker-down        # Stoppt und entfernt Container"
	@echo "  make docker-ps          # Zeigt Status der Container"
	@echo "  make docker-logs S=svc  # Logs eines Service (z.B. S=nicegui)"
	@echo "  make ollama-pull        # Pullt Modell im Ollama-Container"

.PHONY: docker-build-chat docker-up-chat docker-down docker-ps docker-logs ollama-pull

COMPOSE:=docker compose -f docker-compose.yml -f docker-compose.chat.override.yml

docker-build-chat:
	$(COMPOSE) build nicegui

docker-up-chat:
	$(COMPOSE) up -d --build
	$(COMPOSE) ps

docker-down:
	$(COMPOSE) down -v

docker-ps:
	$(COMPOSE) ps

docker-logs:
	@if [ -z "$(S)" ]; then echo "Bitte Service angeben, z.B. make docker-logs S=nicegui"; exit 1; fi
	$(COMPOSE) logs -f $(S)

ollama-pull:
	$(COMPOSE) exec ollama ollama pull $${LLM_MODEL:-llama3:8b}
