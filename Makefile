.PHONY: build dev clean docker

build:
	npm install
	npm run build
	composer install --no-dev

dev:
	npm run dev

clean:
	rm -rf node_modules vendor js css

docker:
	cd docker && docker-compose up --build -d

docker-stop:
	cd docker && docker-compose down
