from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Bitcoin Wallet API", version="1.0.0")

# Configuração CORS para permitir requisições do frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],  # URL do Angular
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclui rotas
from app.routers import keys, addresses, balance, tx, broadcast
app.include_router(keys.router, prefix="/api/keys")
app.include_router(addresses.router, prefix="/api/addresses")
app.include_router(balance.router, prefix="/api/balance")
app.include_router(tx.router, prefix="/api/tx")
app.include_router(broadcast.router, prefix="/api/broadcast")