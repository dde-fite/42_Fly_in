BACKEND_DIR		:= backend
FRONTEND_DIR	:= frontend

run:
	@$(MAKE) -j2 -f .Makefile run

dev:
	@$(MAKE) -j2 -f .Makefile dev

build:
	@$(MAKE) -C $(FRONTEND_DIR) build

install:
	@$(MAKE) -C $(BACKEND_DIR) install
	@$(MAKE) -C $(FRONTEND_DIR) install

install-dev:
	@$(MAKE) -C $(BACKEND_DIR) install-dev
	@$(MAKE) -C $(FRONTEND_DIR) install-dev

debug:
	@$(MAKE) -C $(BACKEND_DIR) debug

lint:
	@$(MAKE) -C $(BACKEND_DIR) lint
	@$(MAKE) -C $(FRONTEND_DIR) lint

clean:
	@$(MAKE) -C $(BACKEND_DIR) clean
	@$(MAKE) -C $(FRONTEND_DIR) clean

fclean:
	@$(MAKE) -C $(BACKEND_DIR) fclean
	@$(MAKE) -C $(FRONTEND_DIR) fclean

.PHONY: run dev install install-dev debug lint clean fclean