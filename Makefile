.PHONY: run
run:
	docker-compose -f docker-compose.yml up -d

.PHONY: build
build:
	test -f .env || cp .env.example .env ; docker-compose -f docker-compose.yml up -d --build


.PHONY: down
down:
	docker-compose down --remove-orphans


.PHONY: build-migrate
build-migrate:
	docker-compose -f docker-compose.yml up -d --build;
	cd app && dbmate -u "postgres://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable" up


.PHONY: create-empty-migration
create-empty-migration:
ifndef name
	$(error name is undefined. Usage: make create-migration name=<name_of_migration>)
endif
	cd app && dbmate new '$(name)'


.PHONY: run-pending-migrations
run-pending-migrations:
	cd app && dbmate -u "postgres://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable" migrate


.PHONY: run-downgrade
run-downgrade:
	cd app && dbmate -u "postgres://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable" rollback


.PHONY: status
status:
	cd app && dbmate -u "postgres://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable" status
