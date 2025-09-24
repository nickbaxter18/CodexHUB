install:
	pnpm install

dev:
	pnpm run dev

lint:
	pnpm run lint

test:
	pnpm test

docker-build:
	docker build -t codexhub .

docker-run:
	docker run -p 3000:3000 codexhub
