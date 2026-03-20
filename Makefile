up:
	docker compose up -d

up-build:
	docker compose up -d --build

down:
	docker compose down

pull:
	docker compose pull

build-base:
	docker build -t ghcr.io/fukumen/rep2-base:latest -f docker/Dockerfile.base .
	docker image prune -f

build-base-extra:
	docker build -t ghcr.io/fukumen/rep2-base-extra:latest --build-arg FLAG_EXTRA=true -f docker/Dockerfile.base .
	docker image prune -f

build:
	docker build -t ghcr.io/fukumen/rep2:latest -f docker/Dockerfile .
	docker image prune -f

build-extra:
	docker build -t ghcr.io/fukumen/rep2-extra:latest --build-arg FLAG_EXTRA=true -f docker/Dockerfile .
	docker image prune -f

config:
	docker compose config

logs:
	docker compose logs -f

exec:
	docker compose exec rep2php8 /bin/sh

confdiff:
	docker compose exec rep2php8 diff /var/www/conf.orig /ext/conf | iconv -f SHIFT_JIS -t UTF-8

clean:
	docker image prune -f
	docker builder prune -a

-include local.mk
