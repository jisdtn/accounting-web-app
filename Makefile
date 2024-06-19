.PHONY: run
run:
	docker-compose -f docker-compose.yml up -d

.PHONY: build
build:
	test -f .env || cp .env.example .env ; docker-compose -f docker-compose.yml up -d --build


.PHONY: down
down:
	docker-compose down --remove-orphans
