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

install:
	@pip install -r requirements.txt

run:
	@fastapi run $(SRC)

dev:
	@fastapi dev $(SRC)

test:
	@pytest

debug:
	$(PYTHON) -m pdb $(SRC)/main.py

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
