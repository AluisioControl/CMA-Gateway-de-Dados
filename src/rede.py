###############################################################
# rede.py
# ------------------------------------------------------------
# Arquivo de funções de rede
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2025
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################

import configparser
import os
import platform
import subprocess

def validar_ip(ip):

    """
    Valida se o endere o IP informado   um endere o IP v lido.
    
    Um endere o IP v lido   formado por quatro n meros entre 0 e 255, separados por pontos.
    
    :param ip: O endere o IP a ser validado
    :return: True se o endere o IP for v lido, False caso contr rio
    """

    partes = ip.split('.')
    return len(partes) == 4 and all(p.isdigit() and 0 <= int(p) <= 255 for p in partes)

def configurar_rede(ip, mascara, gateway):

    """
    Configura a rede do sistema com o endere o IP, mascara e gateway informados.
    
    :param ip: O endere o IP a ser configurado
    :param mascara: A mascara de sub-rede a ser configurada
    :param gateway: O endere o do gateway a ser configurado
    :return: True se a configura o for bem sucedida, False caso contr rio
    """

    sistema = platform.system()
    
    if sistema == "Windows":
        comando = f'netsh interface ip set address name="Ethernet" static {ip} {mascara} {gateway}'
    elif sistema == "Linux":
        comando = f'sudo ifconfig eth0 {ip} netmask {mascara} && sudo route add default gw {gateway} eth0'
    else:
        print("Sistema operacional não suportado!")
        return False
    
    try:
        subprocess.run(comando, shell=True, check=True)
        print("Configuração aplicada com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print("Erro ao aplicar configuração:", e)
        return False

def main():

    """
    Função principal que lê as configurações de rede a partir de um arquivo INI e aplica a configuração.

    A função verifica se a seção [config_rede] existe no arquivo de configuração e obtém os parâmetros
    IP, máscara e gateway. Em seguida, valida cada parâmetro e, se todos forem válidos, chama a função
    configurar_rede para aplicar as configurações. Se algum parâmetro estiver faltando ou for inválido, 
    a função imprime uma mensagem de erro.

    Raises:
        KeyError: Se um dos parâmetros de rede estiver faltando no arquivo de configuração.
    """ 

    config = configparser.ConfigParser()
    config.read("config.ini")
    
    if "config_rede" not in config:
        print("Seção [config_rede] não encontrada no arquivo de configuração!")
        return
    
    try:
        ip = config["config_rede"]["ip"].strip()
        mascara = config["config_rede"]["mascara"].strip()
        gateway = config["config_rede"]["gateway"].strip()
        
        if not all(map(validar_ip, [ip, mascara, gateway])):
            print("Erro: Um ou mais parâmetros de rede são inválidos!")
            return
        
        configurar_rede(ip, mascara, gateway)
    except KeyError as e:
        print(f"Erro: Parâmetro faltando no arquivo de configuração: {e}")
    
if __name__ == "__main__":
    main()
