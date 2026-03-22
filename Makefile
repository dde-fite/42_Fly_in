BACKEND_DIR		:= backend
FRONTEND_DIR	:= frontend


run:
	@$(MAKE) -j2 -f .Makefile run

dev:
	@$(MAKE) -j2 -f .Makefile dev

.PHONY: all