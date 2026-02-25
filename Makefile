FRONTEND_DIR := frontend
BACKEND_DIR := backend
BACKEND_VENV := $(BACKEND_DIR)/venv
PYTHON := python3

.PHONY: backend-venv
backend-venv:
	@if [ ! -d "$(BACKEND_VENV)" ]; then \
	  echo "Creating backend virtualenv and installing requirements..."; \
	  cd $(BACKEND_DIR) && $(PYTHON) -m venv venv && . venv/bin/activate && pip install -r requirements.txt; \
	fi

.PHONY: local-deploy
local-deploy: backend-venv
	npm --prefix $(FRONTEND_DIR) ci
	npm --prefix $(FRONTEND_DIR) run build
	cd $(BACKEND_DIR) && . venv/bin/activate && FLASK_APP=app:create_app flask run --port 5000


