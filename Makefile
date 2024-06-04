.PHONY: run
run:
	docker-compose -f docker-compose.yml up -d

.PHONY: build
build:
	docker-compose -f docker-compose.yml up -d --build