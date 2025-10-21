SHELL := /bin/zsh

.PHONY: start-dev
start-dev:
	@./scripts/start-dev.sh

.PHONY: bundle-frontend
bundle-frontend:
	@./scripts/bundle-frontend.sh

