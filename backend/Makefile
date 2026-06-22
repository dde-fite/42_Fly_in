PYTHON=python3
SRC=src

CACHE_FOLDERS = __pycache__ .pytest_cache .mypy_cache
GARBAGE := $(foreach d,$(CACHE_FOLDERS),$(shell find . -type d -name "$(d)"))

# COLORS
GREEN		:= \033[1;32m
BLUE		:= \033[1;34m
YELLOW		:= \033[1;33m
PURPLE		:= \033[1;35m
CYAN		:= \033[1;36m
RED			:= \033[1;31m
RESET		:= \033[0m

run:
	@$(PYTHON) -m fastapi run $(SRC)

dev:
	@$(PYTHON) -m fastapi dev $(SRC)

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

install-dev: install
	@$(PYTHON) -m pip install -r requirements_dev.txt

test:
	@$(PYTHON) -m pytest

debug:
	@$(PYTHON) -m pdb $(SRC)/main.py

lint:
	@flake8 src/ tests/
	@mypy src/ tests/ --warn-return-any \
		--warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

clean:
	@echo -e "\n$(RED)Deleting temporary files... $(RESET)"
	@rm -rf $(GARBAGE)
	@echo -e "\n$(GREEN)Deleted $(CACHE_FOLDERS) folders successfully!$(RESET)"

fclean: clean

.PHONY: install install-dev run dev test debug lint clean fclean