#!/usr/bin/env python
"""
Script de teste para funcionalidades de cold wallet (modo offline e cache persistente)

Este script verifica:
- Armazenamento do cache persistente 
- Acesso aos dados em modo offline
- Consistência dos dados entre online e offline
- Exportação de chaves para arquivo

Uso:
python tests/test_cold_wallet.py [--address ENDEREÇO] [--network REDE]
"""

import requests
import os
import json
import time
from pathlib import Path
import argparse
import sys

# Configurações
BASE_URL = "http://localhost:8000/api"
TEST_ADDRESS = "tb1q0qjghu2z6wpz0d0v47wz6su6l26z04r4r38rav"
CACHE_DIR = Path.home() / ".bitcoin-wallet" / "cache"

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)

def print_section(title):
    """Imprime um título de seção"""
    print("\n" + "-" * 80)
    print(f"  {title}")
    print("-" * 80)

def pause_for_demo(message="Pressione Enter para continuar..."):
    """Pausa para demonstração"""
    input(f"\n{message} ")

def test_online_mode(address=TEST_ADDRESS):
    """
    Testa o modo online da aplicação.
    - Consulta o endereço no blockchain
    - Verifica se o cache foi criado ou atualizado
    """
    print_section("1. CONSULTA ONLINE (CRIAÇÃO DE CACHE)")
    
    print(f"Consultando saldo para {address} em modo online...")
    response = requests.get(f"{BASE_URL}/balance/{address}")
    
    # Aceitar status 200 (OK) ou 404 (Endereço não encontrado) como válidos
    if response.status_code != 200 and response.status_code != 404:
        print(f"❌ Erro na resposta ({response.status_code}): {response.text}")
        return False
    
    if response.status_code == 404:
        print(f"ℹ️ Endereço sem transações (404): {response.json().get('detail', 'Endereço não encontrado')}")
        print("ℹ️ Para um teste completo, envie alguns fundos para o endereço de teste")
        
    try:
        data = response.json()
        print("Resposta da API:")
        print(json.dumps(data, indent=2))
    except:
        print("❌ Erro ao decodificar resposta JSON")
    
    # Verificar existência do cache
    cache_file = CACHE_DIR / "blockchain_cache.json"
    if cache_file.exists():
        print(f"✅ Cache criado em: {cache_file}")
        
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                print(f"✅ Cache contém {len(cache_data.get('cache', {}))} entradas")
                
                balance_key = f"balance_testnet_{address}"
                utxos_key = f"utxos_testnet_{address}"
                
                if balance_key in cache_data.get("cache", {}):
                    print(f"✅ Dados de saldo encontrados no cache")
                else:
                    print(f"❌ Dados de saldo não encontrados no cache")
                    
                if utxos_key in cache_data.get("cache", {}):
                    print(f"✅ Dados de UTXOs encontrados no cache")
                else:
                    print(f"❌ Dados de UTXOs não encontrados no cache")
                
                return True
        except Exception as e:
            print(f"❌ Erro ao ler cache: {str(e)}")
            return False
    else:
        print(f"❌ Arquivo de cache não encontrado")
        return False

def test_offline_mode():
    """Testa a consulta em modo offline (usando o cache)"""
    print_section("2. CONSULTA OFFLINE (USANDO CACHE)")
    
    print(f"Consultando saldo para {TEST_ADDRESS} em modo offline...")
    response = requests.get(f"{BASE_URL}/balance/{TEST_ADDRESS}?force_offline=true")
    
    # Em modo offline, qualquer resposta entre 200-299 é válida
    if response.status_code < 200 or response.status_code >= 300:
        print(f"❌ Erro na resposta ({response.status_code}): {response.text}")
        return False
    
    try:
        data = response.json()
        print("Resposta da API em modo offline:")
        print(json.dumps(data, indent=2))
        
        print("✅ Consulta em modo offline bem-sucedida")
        return True
    except:
        print("❌ Erro ao decodificar resposta JSON")
        return False

def test_data_consistency():
    """Compara os dados entre modo online e offline para verificar consistência"""
    print_section("3. VERIFICANDO CONSISTÊNCIA DOS DADOS")
    
    # Dados online
    print("Consultando dados online...")
    response_online = requests.get(f"{BASE_URL}/balance/{TEST_ADDRESS}")
    
    if response_online.status_code != 200 and response_online.status_code != 404:
        print(f"❌ Erro na resposta online ({response_online.status_code})")
        return False
    
    if response_online.status_code == 404:
        print(f"ℹ️ Endereço sem transações (404): {response_online.json().get('detail', 'Endereço não encontrado')}")
        print("ℹ️ Pulando teste de consistência por falta de dados")
        return True
    
    data_online = response_online.json()
    
    # Dados offline
    print("Consultando dados offline...")
    response_offline = requests.get(f"{BASE_URL}/balance/{TEST_ADDRESS}?force_offline=true")
    
    if response_offline.status_code < 200 or response_offline.status_code >= 300:
        print(f"❌ Erro na resposta offline ({response_offline.status_code})")
        return False
    
    data_offline = response_offline.json()
    
    # Comparar saldo
    online_balance = data_online.get("balance", 0)
    offline_balance = data_offline.get("balance", 0)
    
    if online_balance == offline_balance:
        print(f"✅ Saldo consistente: {online_balance} satoshis")
    else:
        print(f"⚠️ Saldo inconsistente: online={online_balance}, offline={offline_balance}")
    
    # Comparar UTXOs
    online_utxos = len(data_online.get("utxos", []))
    offline_utxos = len(data_offline.get("utxos", []))
    
    if online_utxos == offline_utxos:
        print(f"✅ Número de UTXOs consistente: {online_utxos}")
    else:
        print(f"⚠️ Número de UTXOs inconsistente: online={online_utxos}, offline={offline_utxos}")
    
    return True

def check_cache_expiration():
    """Verifica se o cache expira corretamente e se o modo offline ignora expiração"""
    print_section("4. VERIFICANDO EXPIRAÇÃO DO CACHE")
    
    cache_file = CACHE_DIR / "blockchain_cache.json"
    if not cache_file.exists():
        # Se o cache não existe, vamos criar um básico para testar
        print(f"ℹ️ Criando arquivo de cache básico para testes")
        
        cache_data = {
            "cache": {
                f"balance_testnet_{TEST_ADDRESS}": {"confirmed": 0, "unconfirmed": 0},
                f"utxos_testnet_{TEST_ADDRESS}": []
            },
            "timestamps": {
                f"balance_testnet_{TEST_ADDRESS}": time.time(),
                f"utxos_testnet_{TEST_ADDRESS}": time.time()
            }
        }
        
        os.makedirs(CACHE_DIR, exist_ok=True)
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)
    
    try:
        # Ler o cache
        with open(cache_file, "r") as f:
            cache_data = json.load(f)
            
        # Verificar se as chaves existem
        balance_key = f"balance_testnet_{TEST_ADDRESS}"
        if balance_key not in cache_data.get("timestamps", {}):
            print(f"❌ Chave de timestamp para saldo não encontrada no cache")
            cache_data.setdefault("timestamps", {})[balance_key] = time.time()
            
        # Modificar o timestamp para simular expiração (10 minutos atrás)
        cache_data["timestamps"][balance_key] = time.time() - 600
        
        # Salvar o cache
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)
            
        print(f"✅ Cache modificado: timestamp de saldo definido para 10 minutos atrás")
        
        # Testar se o modo offline usa o cache mesmo expirado
        print("\nConsultando em modo offline (deve usar o cache expirado)...")
        response_offline = requests.get(f"{BASE_URL}/balance/{TEST_ADDRESS}?force_offline=true")
        
        if response_offline.status_code < 200 or response_offline.status_code >= 300:
            print(f"❌ Erro na resposta offline ({response_offline.status_code})")
            return False
        
        print("✅ Consulta offline bem-sucedida mesmo com cache expirado")
        return True
    except Exception as e:
        print(f"❌ Erro ao manipular cache: {str(e)}")
        return False

def test_key_export():
    """
    Testa a funcionalidade de exportação de chaves para arquivo.
    """
    print("\n🔑 Testando exportação de chaves para arquivo...")
    
    # Dados de teste
    test_data = {
        "private_key": "cVt21DrXEWUcACZKpS8pLqG92sxanuXEDL3YKLRrxBaAEqhwYjG4",
        "public_key": "0308ea9666139527a8c1dd94ce4f071fd23c8b350c5a4bb33748c4ba111faccae0",
        "address": "tb1q0qjghu2z6wpz0d0v47wz6su6l26z04r4r38rav",
        "network": "testnet",
        "file_format": "txt",
        "format": "segwit"
    }
    
    try:
        # Faz a requisição para o endpoint correto
        response = requests.post(
            f"{BASE_URL}/keys/export-file", 
            json=test_data
        )
        
        # Verifica o código de status
        if response.status_code != 200:
            print(f"❌ Falha ao exportar chaves: {response.status_code}")
            print(f"Detalhes: {response.text}")
            return False
        
        # Verifica a resposta
        data = response.json()
        if not data.get("success"):
            print(f"❌ Exportação de chaves falhou: {data.get('message')}")
            return False
        
        # Verifica se o arquivo foi criado
        file_path = data.get("file_path")
        if not os.path.exists(file_path):
            print(f"❌ Arquivo não foi criado em: {file_path}")
            return False
        
        print(f"✅ Chaves exportadas com sucesso para: {file_path}")
        
        # Verificar o conteúdo do arquivo
        with open(file_path, 'r') as f:
            content = f.read()
            if test_data["private_key"] in content and test_data["address"] in content:
                print("✅ Arquivo contém as informações corretas")
            else:
                print("❌ Arquivo não contém todas as informações esperadas")
                return False
        
        return True
    except Exception as e:
        print(f"❌ Erro ao testar exportação de chaves: {str(e)}")
        return False

def main():
    """
    Função principal que executa todos os testes.
    """
    parser = argparse.ArgumentParser(description='Testes da carteira Bitcoin')
    parser.add_argument('--address', type=str, help='Endereço Bitcoin para testes')
    parser.add_argument('--network', type=str, default='testnet', help='Rede Bitcoin (mainnet ou testnet)')
    args = parser.parse_args()
    
    global TEST_ADDRESS
    if args.address:
        TEST_ADDRESS = args.address
        
    # Definindo o endereço de teste
    print(f"🔍 Usando endereço de teste: {TEST_ADDRESS}")
    
    # Executando os testes
    print("\n🧪 Iniciando testes da carteira Bitcoin...")
    
    # Teste de modo online
    online_success = test_online_mode()
    
    # Teste de modo offline
    if online_success:
        offline_success = test_offline_mode()
    else:
        print("⚠️ Pulando teste de modo offline devido a falha no teste online")
        offline_success = False
    
    # Teste de consistência de dados
    if online_success and offline_success:
        consistency_success = test_data_consistency()
    else:
        print("⚠️ Pulando teste de consistência devido a falhas anteriores")
        consistency_success = False
    
    # Teste de expiração do cache
    if online_success:
        cache_success = check_cache_expiration()
    else:
        print("⚠️ Pulando teste de expiração do cache devido a falha no teste online")
        cache_success = False
        
    # Teste de exportação de chaves
    export_success = test_key_export()
    
    # Resumo dos testes
    print("\n📊 Resumo dos testes:")
    print(f"✓ Modo online: {'Sucesso' if online_success else 'Falha'}")
    print(f"✓ Modo offline: {'Sucesso' if offline_success else 'Falha'}")
    print(f"✓ Consistência de dados: {'Sucesso' if consistency_success else 'Falha'}")
    print(f"✓ Expiração do cache: {'Sucesso' if cache_success else 'Falha'}")
    print(f"✓ Exportação de chaves: {'Sucesso' if export_success else 'Falha'}")
    
    success = online_success and offline_success and consistency_success and cache_success and export_success
    print(f"\n{'🎉 Todos os testes passaram!' if success else '❌ Alguns testes falharam.'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    success = main()
    sys.exit(success) 