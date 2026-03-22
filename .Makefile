BACKEND_DIR		:= backend
FRONTEND_DIR	:= frontend


run: backend frontend
dev: backend frontend

backend:
	$(MAKE) -C $(BACKEND_DIR) $(MAKECMDGOALS)

frontend:
	$(MAKE) -C $(FRONTEND_DIR) $(MAKECMDGOALS)


.PHONY: all backend frontend