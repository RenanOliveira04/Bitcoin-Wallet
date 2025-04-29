FROM python:3.13-slim as builder

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pyinstaller

COPY . .

RUN pyinstaller --onefile \
    --add-data "app:app" \
    --hidden-import=uvicorn.logging \
    --hidden-import=uvicorn.loops \
    --hidden-import=uvicorn.loops.auto \
    --hidden-import=uvicorn.protocols \
    --hidden-import=uvicorn.protocols.http \
    --hidden-import=uvicorn.protocols.http.auto \
    --hidden-import=uvicorn.protocols.websockets \
    --hidden-import=uvicorn.protocols.websockets.auto \
    --hidden-import=uvicorn.lifespan \
    --hidden-import=uvicorn.lifespan.on \
    app/main.py

FROM debian:buster-slim

WORKDIR /app

COPY --from=builder /app/dist/main .

ENV NETWORK=testnet
ENV BLOCKCHAIN_API_URL=https://blockstream.info/testnet/api
ENV MAINNET_API_URL=https://blockstream.info/api
ENV PORT=8000

EXPOSE 8000

CMD ["./main"] 