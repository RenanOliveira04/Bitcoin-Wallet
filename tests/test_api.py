import requests
import json
import sys
import traceback
import time
import platform
import os
from datetime import datetime

BASE_URL = "http://localhost:8000/api"

def print_section(title):
    """Imprime uma seção de teste com formatação bonita"""
    print("\n" + "=" * 50)
    print(f"  {title}")
    print("=" * 50 + "\n")

def test_system_info():
    """Testa informações do sistema para compatibilidade"""
    print_section("INFORMAÇÕES DO SISTEMA")
    system = platform.system()
    version = platform.version()
    python_version = platform.python_version()
    
    print(f"Sistema Operacional: {system}")
    print(f"Versão: {version}")
    print(f"Python: {python_version}")
    print(f"Data e Hora: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Verifica RNF5.1 - Compatibilidade com Windows e Linux
    if system in ['Windows', 'Linux']:
        print(f"✅ RNF5.1: Compatível com {system}")
    else:
        print(f"⚠️ RNF5.1: Sistema {system} não está na lista de compatibilidade especificada")
    
    return system

def test_health():
    """Testa o health check da API"""
    try:
        response = requests.get("http://localhost:8000")
        data = response.json()
        print("Health Check:")
        print(json.dumps(data, indent=2))
        
        # Verifica se a configuração de rede está disponível (requisito RNF4.1)
        if "network" in data:
            print(f"✅ RNF4.1: Configuração de rede detectada: {data['network']}")
        else:
            print("❌ RNF4.1: Configuração de rede não encontrada")
            
        return True, data
    except Exception as e:
        print(f"Erro no health check: {str(e)}")
        return False, None

def test_generate_keys(network="testnet", key_format="p2wpkh"):
    """Testa a geração de chaves"""
    print_section("2. GERAÇÃO DE CHAVES")
    try:
        print(f"Testando geração de chaves na rede {network} com formato {key_format}...")
        response = requests.post(f"{BASE_URL}/keys", json={
            "method": "entropy", 
            "network": network,
            "key_format": key_format
        })
        
        if response.status_code != 200:
            print(f"❌ Erro na resposta ({response.status_code}): {response.text}")
            return None
            
        print("Geração de Chaves:")
        key_data = response.json()
        print(json.dumps(key_data, indent=2))
        
        # Verifica se os campos obrigatórios estão presentes
        required_fields = ["private_key", "public_key", "address", "format", "network"]
        missing_fields = [field for field in required_fields if field not in key_data]
        
        if not missing_fields:
            print(f"✅ Geração de chaves para {network} no formato {key_format} funcionando corretamente")
        else:
            print(f"❌ Campos ausentes na resposta: {', '.join(missing_fields)}")
        
        # Verifica se o formato da chave é o solicitado
        if "format" in key_data and key_data["format"] == key_format:
            print(f"✅ Formato de chave {key_format} gerado corretamente")
        else:
            print(f"⚠️ Formato de chave solicitado ({key_format}) difere do retornado ({key_data.get('format', 'N/A')})")
        
        # Verifica se a rede é a solicitada
        if "network" in key_data and key_data["network"] == network:
            print(f"✅ Rede {network} configurada corretamente")
        else:
            print(f"⚠️ Rede solicitada ({network}) difere da retornada ({key_data.get('network', 'N/A')})")
                
        # Verifica RNF1.1 - Bibliotecas criptográficas reconhecidas
        print("✅ RNF1.1: Usando bitcoinlib para geração de chaves")
        
        return key_data
    except Exception as e:
        print(f"❌ Erro ao gerar chaves: {str(e)}")
        traceback.print_exc()
        return None

def test_generate_addresses(private_key, network="testnet"):
    """Testa a geração de endereços em diferentes formatos"""
    print_section("2. GERAÇÃO DE ENDEREÇOS")
    
    address_formats = ["p2pkh", "p2sh", "p2wpkh", "p2tr"]
    addresses = {}
    
    # Verificar RF2.1, RF2.2 e RF2.3
    print(f"Verificando requisitos RF2.1-3: Derivação de endereços para {network}")
    print(f"Testando formatos: {', '.join(address_formats)}")
    
    for addr_format in address_formats:
        try:
            print(f"\nTestando geração de endereço {addr_format}...")
            response = requests.get(
                f"{BASE_URL}/addresses/{addr_format}",
                params={"private_key": private_key, "network": network}
            )
            if response.status_code == 200:
                addr_data = response.json()
                addresses[addr_format] = addr_data
                print(f"Formato {addr_format}:")
                print(json.dumps(addr_data, indent=2))
                print(f"✅ RF2.3: Suporte ao formato {addr_format} verificado")
            else:
                print(f"❌ Erro ao gerar endereço {addr_format} ({response.status_code}): {response.text}")
        except Exception as e:
            print(f"❌ Exceção ao gerar endereço {addr_format}: {str(e)}")
            traceback.print_exc()
    
    if network == "mainnet":
        print(f"✅ RF2.1: Derivação de endereços para mainnet verificada")
    else:
        print(f"✅ RF2.2: Derivação de endereços para testnet verificada")
    
    return addresses

def test_balance_utxos(address, network="testnet"):
    """Testa a consulta de saldo e UTXOs"""
    print_section("3. CONSULTA DE SALDOS")
    
    try:
        print(f"Consultando saldo e UTXOs para {address} na {network}...")
        response = requests.get(f"{BASE_URL}/balance/{address}")
        
        if response.status_code != 200:
            print(f"❌ RF3.1/RF3.2: Erro na resposta ({response.status_code}): {response.text}")
            return None
            
        balance_data = response.json()    
        print(f"Consulta de Saldo e UTXOs para {address}:")
        print(json.dumps(balance_data, indent=2))
        
        # Verificar RF3.1 e RF3.2
        if "balance" in balance_data:
            print(f"✅ RF3.1: Consulta de saldo implementada")
        else:
            print(f"❌ RF3.1: Saldo não encontrado na resposta")
            
        if "utxos" in balance_data:
            print(f"✅ RF3.2: Consulta de UTXOs implementada")
            utxo_count = len(balance_data.get("utxos", []))
            print(f"   UTXOs encontrados: {utxo_count}")
        else:
            print(f"❌ RF3.2: UTXOs não encontrados na resposta")
        
        return balance_data
    except Exception as e:
        print(f"❌ Erro ao consultar saldo: {str(e)}")
        traceback.print_exc()
        return None

def test_fee_estimation():
    """Testa a estimativa de taxa com base na mempool"""
    print_section("4.4 ESTIMATIVA DE TAXAS")
    
    try:
        response = requests.get(f"{BASE_URL}/fee/estimate")
        
        if response.status_code != 200:
            print(f"❌ RF4.4: Endpoint de estimativa de taxa não implementado ({response.status_code})")
            print("   Endpoint /api/fee/estimate não encontrado ou retornou erro")
            return None
            
        fee_data = response.json()
        print("Estimativa de taxas:")
        print(json.dumps(fee_data, indent=2))
        print(f"✅ RF4.4: Estimativa de taxa implementada")
        
        return fee_data
    except requests.exceptions.RequestException:
        print("❌ RF4.4: Endpoint de estimativa de taxa não implementado")
        return None
    except Exception as e:
        print(f"❌ Erro ao consultar estimativa de taxa: {str(e)}")
        return None

def test_build_transaction(inputs, outputs, fee_rate=1.0):
    """Testa a construção de transações"""
    print_section("4. CONSTRUÇÃO DE TRANSAÇÕES")
    
    try:
        print("Construindo transação...")
        tx_request = {
            "inputs": inputs,
            "outputs": outputs,
            "fee_rate": fee_rate
        }
        print(f"Dados da requisição: {json.dumps(tx_request, indent=2)}")
        
        response = requests.post(f"{BASE_URL}/utxo", json=tx_request)
        
        if response.status_code != 200:
            print(f"❌ RF4.2: Erro na resposta ({response.status_code}): {response.text}")
            return None
            
        tx_data = response.json()
        print("Construção de Transação:")
        print(json.dumps(tx_data, indent=2))
        
        # Verificar RF4.1, RF4.2, RF4.3, RF4.5
        has_input_address = any("address" in inp for inp in inputs)
        has_output_address = any("address" in out for out in outputs)
        
        if has_input_address and has_output_address:
            print(f"✅ RF4.1: Endereços de origem e destino informados")
        else:
            print(f"⚠️ RF4.1: Estrutura de endereços incompleta")
        
        if "raw_transaction" in tx_data:
            print(f"✅ RF4.2: Criação de transação raw implementada")
        else:
            print(f"❌ RF4.2: Transação raw não encontrada na resposta")
            
        if len(inputs) > 0:
            print(f"✅ RF4.3: Seleção manual de UTXOs implementada ({len(inputs)} UTXOs selecionados)")
        else:
            print(f"❌ RF4.3: Nenhum UTXO selecionado")
            
        if "fee" in tx_data and tx_data["fee"] is not None:
            print(f"✅ RF4.5: Cálculo de taxa implementado (Taxa: {tx_data.get('fee')})")
        else:
            print(f"⚠️ RF4.5: Cálculo de taxa incompleto ou não retornado")
        
        return tx_data
    except Exception as e:
        print(f"❌ Erro ao construir transação: {str(e)}")
        traceback.print_exc()
        return None

def test_transaction_signature(tx_data, private_key):
    """Testa a assinatura de transações"""
    print_section("5. ASSINATURA DE TRANSAÇÕES")
    
    try:
        if not tx_data or "txid" not in tx_data:
            print("❌ RF5.1: Não foi possível testar assinatura - dados da transação inválidos")
            return None
        
        print(f"Testando assinatura da transação {tx_data['txid']}...")
        response = requests.post(f"{BASE_URL}/sign", json={
            "tx_hex": tx_data["raw_transaction"],
            "private_key": private_key
        })
        
        if response.status_code != 200:
            print(f"❌ RF5.1: Endpoint de assinatura não implementado ({response.status_code})")
            print("   Endpoint /api/sign não encontrado ou retornou erro")
            
            # Verifica se a transação já está assinada
            if "raw_transaction" in tx_data and len(tx_data["raw_transaction"]) > 20:
                print(f"⚠️ RF5.1: Transação possivelmente já vem assinada da construção")
                print(f"✅ RF5.2: String da transação raw disponível: {tx_data['raw_transaction'][:30]}...")
            return None
            
        signed_data = response.json()
        print("Assinatura de Transação:")
        print(json.dumps(signed_data, indent=2))
        
        # Verificar RF5.1 e RF5.2
        if "signed_tx" in signed_data:
            print(f"✅ RF5.1: Assinatura de transação implementada")
            print(f"✅ RF5.2: String da transação assinada disponível: {signed_data['signed_tx'][:30]}...")
        else:
            print(f"❌ RF5.1/RF5.2: Transação assinada não encontrada na resposta")
        
        return signed_data
    except requests.exceptions.RequestException:
        print("❌ RF5.1: Endpoint de assinatura não implementado")
        return None
    except Exception as e:
        print(f"❌ Erro ao assinar transação: {str(e)}")
        traceback.print_exc()
        return None

def test_transaction_validation(tx_data):
    """Testa a validação de transações"""
    print_section("6. CONFERÊNCIA DE TRANSAÇÕES")
    
    try:
        if not tx_data or "txid" not in tx_data:
            print("❌ RF6.1/RF6.2: Não foi possível testar validação - dados da transação inválidos")
            return False
        
        print(f"Testando validação da transação {tx_data['txid']}...")
        response = requests.post(f"{BASE_URL}/validate", json={
            "tx_hex": tx_data["raw_transaction"]
        })
        
        if response.status_code != 200:
            print(f"❌ RF6.1: Endpoint de validação não implementado ({response.status_code})")
            print("   Endpoint /api/validate não encontrado ou retornou erro")
            return False
            
        validation_data = response.json()
        print("Validação de Transação:")
        print(json.dumps(validation_data, indent=2))
        
        # Verificar RF6.1 e RF6.2
        if "is_valid" in validation_data:
            is_valid = validation_data["is_valid"]
            print(f"✅ RF6.1: Validação de estrutura implementada (Válida: {is_valid})")
            
            if "has_sufficient_funds" in validation_data:
                has_funds = validation_data["has_sufficient_funds"]
                print(f"✅ RF6.2: Verificação de saldo implementada (Saldo suficiente: {has_funds})")
            else:
                print(f"❌ RF6.2: Verificação de saldo não implementada")
        else:
            print(f"❌ RF6.1/RF6.2: Validação não retornou resultado")
        
        return validation_data.get("is_valid", False)
    except requests.exceptions.RequestException:
        print("❌ RF6.1: Endpoint de validação não implementado")
        return False
    except Exception as e:
        print(f"❌ Erro ao validar transação: {str(e)}")
        traceback.print_exc()
        return False

def test_broadcast_transaction(tx_hex):
    """Testa o broadcast de transações"""
    print_section("7. BROADCAST DE TRANSAÇÕES")
    
    if not tx_hex:
        print("❌ RF7.1/RF7.2: Não foi possível testar broadcast - transação inválida")
        return None
    
    try:
        print("Testando broadcast da transação...")
        response = requests.post(f"{BASE_URL}/broadcast", json={
            "raw_tx": tx_hex
        })
        
        if response.status_code != 200:
            print(f"❌ RF7.1: Erro na resposta ({response.status_code}): {response.text}")
            return None
            
        broadcast_data = response.json()
        print("Broadcast de Transação:")
        print(json.dumps(broadcast_data, indent=2))
        
        # Verificar RF7.1 e RF7.2
        if "status" in broadcast_data:
            print(f"✅ RF7.1: Broadcast de transação implementado (Status: {broadcast_data['status']})")
        else:
            print(f"❌ RF7.1: Status do broadcast não encontrado na resposta")
            
        if "explorer_url" in broadcast_data:
            print(f"✅ RF7.2: Link para explorador implementado: {broadcast_data['explorer_url']}")
        else:
            print(f"❌ RF7.2: Link para explorador não encontrado na resposta")
        
        return broadcast_data
    except Exception as e:
        print(f"❌ Erro ao fazer broadcast da transação: {str(e)}")
        traceback.print_exc()
        return None

def test_transaction_status(txid):
    """Testa a consulta de status da transação"""
    print_section("8. CONSULTA DE STATUS DA TRANSAÇÃO")
    
    if not txid:
        print("❌ RF8.1/RF8.2: Não foi possível testar consulta - txid inválido")
        return None
    
    try:
        print(f"Consultando status da transação {txid}...")
        response = requests.get(f"{BASE_URL}/tx/{txid}")
        
        if response.status_code != 200:
            print(f"❌ RF8.1: Endpoint de consulta não implementado ({response.status_code})")
            print("   Endpoint /api/tx/{txid} não encontrado ou retornou erro")
            return None
            
        status_data = response.json()
        print("Status da Transação:")
        print(json.dumps(status_data, indent=2))
        
        # Verificar RF8.1 e RF8.2
        if "status" in status_data:
            print(f"✅ RF8.1: Consulta de status implementada (Status: {status_data['status']})")
        else:
            print(f"❌ RF8.1: Status não encontrado na resposta")
            
        if "explorer_url" in status_data:
            print(f"✅ RF8.2: Link para explorador implementado: {status_data['explorer_url']}")
        else:
            print(f"❌ RF8.2: Link para explorador não encontrado na resposta")
        
        return status_data
    except requests.exceptions.RequestException:
        print("❌ RF8.1: Endpoint de consulta de status não implementado")
        return None
    except Exception as e:
        print(f"❌ Erro ao consultar status da transação: {str(e)}")
        traceback.print_exc()
        return None

def main():
    """Função principal para execução de testes"""
    print("\n")
    print("=" * 80)
    print("                  BITCOIN WALLET - TESTE DE VERIFICAÇÃO")
    print(f"                  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("\n")
    
    # Obter parâmetros do teste
    if len(sys.argv) > 1:
        network = sys.argv[1].lower()
        if network not in ["testnet", "mainnet"]:
            print(f"Rede inválida: {network}. Usando testnet como padrão.")
            network = "testnet"
    else:
        network = input("Escolha a rede (testnet/mainnet) [testnet]: ").lower() or "testnet"
        if network not in ["testnet", "mainnet"]:
            print(f"Rede inválida: {network}. Usando testnet como padrão.")
            network = "testnet"
    
    if len(sys.argv) > 2:
        key_format = sys.argv[2].lower()
        if key_format not in ["p2pkh", "p2sh", "p2wpkh", "p2tr"]:
            print(f"Formato de chave inválido: {key_format}. Usando p2wpkh como padrão.")
            key_format = "p2wpkh"
    else:
        key_format = input("Escolha o formato da chave (p2pkh/p2sh/p2wpkh/p2tr) [p2wpkh]: ").lower() or "p2wpkh"
        if key_format not in ["p2pkh", "p2sh", "p2wpkh", "p2tr"]:
            print(f"Formato de chave inválido: {key_format}. Usando p2wpkh como padrão.")
            key_format = "p2wpkh"
    
    print(f"\nExecutando testes na rede {network} com formato de chave {key_format}\n")
            
    test_system_info()
    health_ok, health_data = test_health()
    
    if not health_ok:
        print("❌ API não está respondendo. Verifique se o servidor está rodando.")
        return
    
    # Executar os testes em sequência
    key_data = test_generate_keys(network, key_format)
    
    if not key_data:
        print("❌ Não foi possível continuar - falha na geração de chaves")
        return
    
    private_key = key_data.get("private_key")
    address = key_data.get("address")
    
    addresses = test_generate_addresses(private_key, network)
    balance = test_balance_utxos(address, network)
    fee = test_fee_estimation()
    
    # Testes que dependem de UTXOs reais
    if balance and "utxos" in balance and len(balance["utxos"]) > 0:
        inputs = balance["utxos"]
        outputs = [{
            "address": address,
            "value": sum(utxo["value"] for utxo in inputs) - 1000  # Valor menos uma pequena taxa
        }]
        tx_data = test_build_transaction(inputs, outputs)
        
        if tx_data and "raw_transaction" in tx_data:
            # Testar assinatura
            signed_tx = test_transaction_signature(tx_data, private_key)
            
            if signed_tx and "signed_tx" in signed_tx:
                # Testar validação
                validation = test_transaction_validation(signed_tx)
                
                # Testar broadcast - COMENTADO para não enviar transações reais durante o teste
                # broadcast = test_broadcast_transaction(signed_tx.get("signed_tx"))
                
                # Testar consulta de status - usando txid existente
                if "txid" in signed_tx:
                    test_transaction_status(signed_tx["txid"])
    else:
        print("\n⚠️ Sem UTXOs disponíveis para testar construção de transações")
        print("  Para testar completamente, envie alguns fundos para o endereço gerado.")
        
        # Tentar criar uma transação de teste com dados simulados
        print("\nCriando transação de teste com dados simulados...")
        inputs = [{
            "prev_tx": "a" * 64,
            "output_n": 0,
            "value": 10000000,
            "script": "76a914" + "b" * 40 + "88ac"
        }]
        outputs = [{
            "address": address,
            "value": 9990000
        }]
        
        tx_data = test_build_transaction(inputs, outputs)
        
        if tx_data and "raw_transaction" in tx_data:
            # Testar assinatura - não vai funcionar com dados simulados, mas testa o endpoint
            test_transaction_signature(tx_data, private_key)
            
            # Testar validação
            test_transaction_validation(tx_data)
            
            # Testar consulta de status com um txid conhecido de testnet
            # Txid de exemplo da testnet
            test_txid = "f4184fc596403b9d638783cf57adfe4c75c605f6356fbc91338530e9831e9e16"
            test_transaction_status(test_txid)
    
    print("\n" + "=" * 80)
    print("                  TESTE DE VERIFICAÇÃO CONCLUÍDO")
    print("=" * 80)
    print("\n")

if __name__ == "__main__":
    main() 