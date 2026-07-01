NPM=npm
PYTHON=python3
SRC=src
DIST=dist
DIST_FILES=$(DIST)/index.html $(DIST)/assets $(DIST)/icons.svg

# COLORS
GREEN		:= \033[1;32m
BLUE		:= \033[1;34m
YELLOW		:= \033[1;33m
PURPLE		:= \033[1;35m
CYAN		:= \033[1;36m
RED			:= \033[1;31m
RESET		:= \033[0m


run: $(DIST_FILES)
	@$(PYTHON) -m granian --port 3000 --interface asgi main:app

dev:
	@npm run dev

check-venv:
ifdef VIRTUAL_ENV
	@echo -e "$(GREEN)Virtual environment found$(RESET)"
else
	@echo -e "$(RED)WARNING: Not in a virtual environment. Risk of dependency conflicts.$(RESET)"
	@read -p "Continue anyway? [y/N] " ans && { [ "$$ans" = "y" ] || [ "$$ans" = "Y" ]; } || \
		{ echo -e "$(RED)Aborted.$(RESET)"; exit 1; }
endif

install: check-venv
	@$(PYTHON) -m pip install -r requirements.txt
	@npm install

build: install-dev
	@npm run build

$(DIST_FILES):
	@make build

preview:
	@npm run preview

lint:
	@npm run lint
	@flake8 .
	@mypy . --warn-return-any \
		--warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

format:
	@npm run format

clean:
	@echo -e "\n$(RED)Deleting Python temporary files... $(RESET)"
	@rm -rf $(GARBAGE)
	@npm run clean
	@echo -e "\n$(GREEN)Deleted Python and JS temporary files successfully!$(RESET)"

fclean: clean
	@echo -e "\n$(RED)Deleting build and dependencies files... $(RESET)"
	@npm run fclean
	@echo -e "\n$(GREEN)Deleted build and dependencies successfully!$(RESET)"

.PHONY: install install-dev build run dev preview lint format clean fclean