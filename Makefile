.PHONY: up down build logs test demo-dos demo-injection clean

up:          ## Démarrer la plateforme
	docker compose up -d --build

ia:          ## Démarrer Ollama (RAG) + tirer le modèle
	docker compose --profile ia up -d ollama
	docker exec -it resilience-alpha-ollama-1 ollama pull llama3.2:3b

down:        ## Arrêter
	docker compose down

logs:        ## Suivre les journaux
	docker compose logs -f

test:        ## Tests automatisés
	pip install -r tests/requirements.txt && pytest tests/ -v

demo-dos:    ## Déclencher l'incident DoS contrôlé (labo)
	python redteam/dos_controlled.py --duree 20 --rps 80 --jaccepte-labo

demo-injection: ## Sonde d'injection bénigne (labo)
	python redteam/injection_probe.py --jaccepte-labo

clean:       ## Tout supprimer (volumes inclus)
	docker compose down -v
