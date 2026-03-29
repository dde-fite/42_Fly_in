# PYTHON GARBAGE
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

install-dev: install
	@npm install

run:
	@fastapi run

dev:
	@npm run dev

lint:
	@flake8 .
	@mypy . --warn-return-any \
		--warn-unused-ignores --ignore-missing-imports \
		--disallow-untyped-defs --check-untyped-defs

clean:
	@echo -e "\n$(RED)Deleting Python temporary files... $(RESET)"
	@rm -rf $(GARBAGE)
	@npm run clean
	@echo -e "\n$(GREEN)Deleted Python and JS temporary files successfully!$(RESET)"

fclean: clean
	@echo -e "\n$(RED)Deleting build and dependencies files... $(RESET)"
	@npm run fclean
	@echo -e "\n$(GREEN)Deleted build and dependencies successfully!$(RESET)"
