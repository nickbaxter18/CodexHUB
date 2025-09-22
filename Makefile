install:
    npm install

dev:
    npm run dev

lint:
    npm run lint

test:
    npm test

docker-build:
    docker build -t codexbuilder .

docker-run:
    docker run -p 3000:3000 codexbuilder
