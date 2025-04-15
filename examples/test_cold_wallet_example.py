#!/usr/bin/env python
"""
Exemplo de uso dos testes da cold wallet do Bitcoin Wallet

Este script demonstra como executar os testes da cold wallet
para verificar a funcionalidade da carteira offline.

Uso:
  python examples/test_cold_wallet_example.py
"""

import sys
import os
import subprocess
import time

# Verificar se o diretório principal está no path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

def print_header(title):
    """Imprime um cabeçalho formatado"""
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80 + "\n")

def check_server_running():
    """Verifica se o servidor API está rodando"""
    import requests
    try:
        response = requests.get("http://localhost:8000/", timeout=2)
        if response.status_code == 200:
            print("✅ Servidor da API está funcionando")
            return True
    except:
        pass
    
    print("❌ Servidor da API não está rodando")
    print("   Inicie o servidor em outro terminal com: uvicorn app.main:app --reload")
    return False

def run_example():
    """Executa os testes da cold wallet como exemplo"""
    print_header("EXEMPLO DE TESTE DA COLD WALLET")
    
    print("📝 Este exemplo demonstra como executar os testes da carteira offline (cold wallet).")
    print("   Serão testadas as seguintes funcionalidades:")
    print("   1. Modo online: consulta e criação de cache")
    print("   2. Modo offline: acesso a dados sem conexão")
    print("   3. Consistência: verificação da consistência dos dados")
    print("   4. Expiração: ignore expiração do cache em modo offline")
    print("   5. Exportação: salvar chaves em arquivo\n")
    
    if not check_server_running():
        print("\n⚠️ Execute o servidor em outro terminal e tente novamente.")
        return
    
    # Endereço de teste (opcional)
    test_address = "tb1q0qjghu2z6wpz0d0v47wz6su6l26z04r4r38rav"  # Endereço de exemplo para testnet
    
    print(f"\n🧪 Executando teste com endereço: {test_address}\n")
    
    try:
        # Executa o teste
        subprocess.run([
            sys.executable, 
            os.path.join(root_dir, "tests", "test_cold_wallet.py"),
            "--address", test_address
        ])
        
        print("\n✅ Exemplo concluído!")
        print("   Se todos os testes passaram, sua implementação de cold wallet está funcionando corretamente.")
        print("   Isso significa que você pode usar o Bitcoin Wallet mesmo sem conexão com a internet.")
        print("   Os dados necessários serão armazenados em cache e acessíveis offline.")
        
    except Exception as e:
        print(f"\n❌ Erro ao executar o teste: {str(e)}")
        
if __name__ == "__main__":
    run_example() 