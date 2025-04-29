import os
import sys
import shutil
import subprocess
from pathlib import Path

def clean_build():
    """Limpa diretórios de build anteriores"""
    dirs_to_clean = ['build', 'dist']
    files_to_clean = ['*.spec']
    
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
    
    for pattern in files_to_clean:
        for file in Path('.').glob(pattern):
            file.unlink()

def build_executable():
    """Gera o executável usando PyInstaller"""
    try:
        # Instala dependências necessárias
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
        
        # Configuração do PyInstaller
        pyinstaller_command = [
            'pyinstaller',
            '--onefile',
            '--name', 'bitcoin-wallet',
            '--add-data', 'app:app',
            '--hidden-import=uvicorn.logging',
            '--hidden-import=uvicorn.loops',
            '--hidden-import=uvicorn.loops.auto',
            '--hidden-import=uvicorn.protocols',
            '--hidden-import=uvicorn.protocols.http',
            '--hidden-import=uvicorn.protocols.http.auto',
            '--hidden-import=uvicorn.protocols.websockets',
            '--hidden-import=uvicorn.protocols.websockets.auto',
            '--hidden-import=uvicorn.lifespan',
            '--hidden-import=uvicorn.lifespan.on',
            'app/main.py'
        ]
        
        # Executa o PyInstaller
        subprocess.run(pyinstaller_command, check=True)
        
        print("\nExecutável gerado com sucesso!")
        print(f"Localização: {os.path.abspath('dist/bitcoin-wallet')}")
        
    except subprocess.CalledProcessError as e:
        print(f"Erro ao gerar executável: {e}")
        sys.exit(1)

if __name__ == '__main__':
    print("Iniciando build do Bitcoin Wallet...")
    clean_build()
    build_executable() 