
help: ## 💬 this help message
	@egrep -h '\s##\s' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m  %-30s\033[0m %s\n", $$1, $$2}'

requirements: ## 📝 export poetry.lock to requirements.txt
	poetry export --without-hashes --format=requirements.txt > requirements.txt