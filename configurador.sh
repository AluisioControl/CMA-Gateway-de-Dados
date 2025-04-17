#!/bin/bash

env_cma_gateway="./CMA-Gateway-de-Dados-main/src/.env"
env_reconcile="./Reconcile-CMA-Gateway-de-Dados-main/.env"

function exibir_menu() {
    clear
    echo "***********************************************************************"
    echo " BEM-VINDO(A) AO CONFIGURADOR GERAL DO GATEWAY"
    echo "***********************************************************************"
    echo ""
    echo "Digite o número correspondente à configuração que deseja fazer:"
    echo "[1] - Configurar Interface de Rede"
    #echo "[2] - Configurar parâmetros do CMA Gateway"
    echo "[2] - Configurar CMA WEB"
    echo "[3] - Configurar Servidor de Notificação"
    echo "[4] - Iniciar Gateway de Dados"
    echo "[0] - Sair"
    echo ""
}

function ler_variavel() {
    local VAR=$1
    local ARQUIVO=$2
    local VAR_FORMATADA=$3
    
    # Obtém o valor exato como está no arquivo (incluindo aspas, se houver)
    local VALOR_ATUAL_COM_ASPAS=$(grep -E "^$VAR" "$ARQUIVO" | cut -d '=' -f2-)
    
    # Remove espaços iniciais para exibição
    local VALOR_EXIBIR=$(echo "$VALOR_ATUAL_COM_ASPAS" | sed 's/^[[:space:]]*//')
    
    # Remove aspas para exibição mais limpa
    local VALOR_SEM_ASPAS=$(echo "$VALOR_EXIBIR" | sed 's/^"//;s/"$//')
    
    read -p "$VAR_FORMATADA [$VALOR_SEM_ASPAS]: " NOVO_VALOR
    
    if [ -z "$NOVO_VALOR" ]; then
        # Se o usuário apenas pressionar Enter, mantém exatamente o valor original
        NOVO_VALOR="$VALOR_ATUAL_COM_ASPAS"
    else
        # Se for um novo valor com espaços ou já contém aspas, adiciona aspas
        if [[ $NOVO_VALOR == *" "* || $NOVO_VALOR == *"\""* ]]; then
            NOVO_VALOR="\"$NOVO_VALOR\""
        fi
    fi
    
    # Substitui ou adiciona a variável
    if grep -qE "^$VAR" "$ARQUIVO"; then
        sed -i "s|^$VAR=.*|$VAR=$NOVO_VALOR|" "$ARQUIVO"
    else
        echo "$VAR=$NOVO_VALOR" >> "$ARQUIVO"
    fi
}

function configurar_placa_de_rede() {
    echo "Configurar Interface de Rede... (Tecle Enter para manter a informação atual)"
    ler_variavel "ip" "$env_cma_gateway" "IP"
    ler_variavel "mascara" "$env_cma_gateway" "MÁSCARA"
    ler_variavel "gateway" "$env_cma_gateway" "GATEWAY"
    ler_variavel "dns" "$env_cma_gateway" "DNS"
    ./static_ip.sh
    echo "Configurações da interface de rede atualizadas com sucesso."
    sleep 2
}

function configurar_gateway() {
    echo "Configurando parâmetros do CMA Gateway... (Tecle Enter para manter a informação atual)"
    ler_variavel "GTW_NAME" "$env_cma_gateway" "NOME DO GATEWAY"
    ler_variavel "DATABASE_URL" "$env_cma_gateway" "URL DO BANCO DE DADOS"
    echo "Configurações do CMA Gateway atualizados com sucesso."
    sleep 2
}

function configurar_reconcile() {
    echo "Configurar CMA WEB... (Tecle Enter para manter a informação atual)"
    ler_variavel "GWTDADOS_HOST" "$env_reconcile" "HOST CMA WEB"
    ler_variavel "GWTDADOS_USERNAME" "$env_reconcile" "USUARIO CMA WEB"
    ler_variavel "GWTDADOS_PASSWORD" "$env_reconcile" "SENHA CMA WEB"
    ler_variavel "GATEWAY_NAME" "$env_reconcile" "NOME DO GATEWAY"
    echo "Configurações do CMA WEB atualizados com sucesso."
    sleep 2
}

function configurar_rabbitmq() {
    echo "Configurar Servidor de Notificação... (Tecle Enter para manter a informação atual)"
    ler_variavel "RABBIT_HOST" "$env_cma_gateway" "HOST"
    ler_variavel "RABBIT_PORT" "$env_cma_gateway" "PORTA"
    ler_variavel "RABBIT_USER" "$env_cma_gateway" "USUARIO"
    ler_variavel "RABBIT_PASS" "$env_cma_gateway" "SENHA"
    ler_variavel "RABBIT_CAMINHO" "$env_cma_gateway" "EXCHANGE"
    ler_variavel "RABBIT_TOPICO" "$env_cma_gateway" "QUEUE"
    ler_variavel "RABBIT_CHAVE" "$env_cma_gateway" "ROUTING KEY"
    echo "Configurações do Servidor de Notificação atualizados com sucesso."
    sleep 2
}

function executar_gateway() {
    echo "Executando CMA Gateway..."
    cd "CMA-Gateway-de-Dados-main/src" 
    sudo python3 main.py
    exit
}

# Loop principal
while true; do
    exibir_menu
    read -p "Opção: " opcao
    case $opcao in
        1) configurar_placa_de_rede ;;
        #2) configurar_gateway ;;
        2) configurar_reconcile ;;
        3) configurar_rabbitmq ;;
        4) executar_gateway ;;
        0) echo "Saindo..."; exit 0 ;;
        *) echo "Opção inválida."; sleep 2 ;;
    esac
done