# Frontend Makefile for ADIF Drone Traffic Control System

# COLORS
GREEN		:= \033[1;32m
BLUE		:= \033[1;34m
YELLOW		:= \033[1;33m
PURPLE		:= \033[1;35m
CYAN		:= \033[1;36m
RED			:= \033[1;31m
RESET		:= \033[0m

.PHONY: help install build dev run lint clean fclean

help:
	@echo "$(CYAN)=== ADIF Drone Traffic Control Frontend ===$(RESET)"
	@echo ""
	@echo "$(GREEN)Available targets:$(RESET)"
	@echo "  $(BLUE)install$(RESET)      - Install npm dependencies"
	@echo "  $(BLUE)build$(RESET)        - Build production bundle"
	@echo "  $(BLUE)dev$(RESET)          - Start development server"
	@echo "  $(BLUE)preview$(RESET)      - Preview production build"
	@echo "  $(BLUE)run$(RESET)          - Alias for 'dev'"
	@echo "  $(BLUE)clean$(RESET)        - Remove build artifacts"
	@echo "  $(BLUE)fclean$(RESET)       - Full clean (includes node_modules)"
	@echo "  $(BLUE)lint$(RESET)         - Run TypeScript compiler"

install:
	@echo "$(CYAN)Installing dependencies...$(RESET)"
	@npm install

build:
	@echo "$(CYAN)Building production bundle...$(RESET)"
	@npm run build

dev:
	@echo "$(CYAN)Starting development server...$(RESET)"
	@echo "$(YELLOW)Frontend will be available at http://localhost:5173$(RESET)"
	@npm run dev

preview:
	@echo "$(CYAN)Previewing production build...$(RESET)"
	@npm run preview

run: dev

lint:
	@echo "$(CYAN)Running TypeScript compiler...$(RESET)"
	@npm run build -- --mode analyze

clean:
	@echo "$(CYAN)Cleaning build artifacts...$(RESET)"
	@npm run clean

fclean: clean
	@echo "$(CYAN)Full clean (removing node_modules)...$(RESET)"
	@npm run fclean

clean:
	@echo -e "\n$(RED)Deleting Python temporary files... $(RESET)"
	@rm -rf $(GARBAGE)
	@npm run clean
	@echo -e "\n$(GREEN)Deleted Python and JS temporary files successfully!$(RESET)"

fclean: clean
	@echo -e "\n$(RED)Deleting build and dependencies files... $(RESET)"
	@npm run fclean
	@echo -e "\n$(GREEN)Deleted build and dependencies successfully!$(RESET)"
