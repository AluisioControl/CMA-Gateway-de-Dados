#!/bin/bash
# Script configurador com validação, entrada visível e compatível

path_main="C:/Users/Caval/OneDrive/Documentos/CMA-Gateway-de-Dados/src/"
path_collect="C:/Users/Caval/OneDrive/Documentos/Reconcile-CMA-Gateway-de-Dados/"
env_cma_gateway="C:/Users/Caval/OneDrive/Documentos/CMA-Gateway-de-Dados/src/.env"
env_reconcile="C:/Users/Caval/OneDrive/Documentos/Reconcile-CMA-Gateway-de-Dados/.env"

function exibir_menu() {
    clear
    echo "***********************************************************************"
    echo " BEM-VINDO(A) AO CONFIGURADOR GERAL DO GATEWAY"
    echo "***********************************************************************"
    echo ""
    echo "Digite o número correspondente à configuração que deseja fazer:"
    echo "[1] - Configurar Interface de Rede"
    echo "[2] - Configurar CMA WEB"
    echo "[3] - Configurar Servidor de Notificação"
    echo "[4] - Iniciar Gateway de Dados"
    echo "[0] - Sair"
    echo ""
}

function validar_ip() {
    local ip="$1"
    if [[ $ip =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
        IFS='.' read -r -a octetos <<< "$ip"
        for octeto in "${octetos[@]}"; do
            if ((octeto < 0 || octeto > 255)); then
                return 1
            fi
        done
        return 0
    fi
    return 1
}

function validar_url() {
    local url="$1"
    [[ $url =~ ^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$ ]]
}

function ler_variavel() {
    local VAR=$1
    local ARQUIVO=$2
    local VAR_FORMATADA=$3
    local TIPO_VALIDACAO=$4

    local VALOR_ATUAL_COM_ASPAS=$(grep -E "^$VAR=" "$ARQUIVO" | cut -d '=' -f2-)
    local VALOR_SEM_ASPAS=$(echo "$VALOR_ATUAL_COM_ASPAS" | sed 's/^"//;s/"$//')

    while true; do
        echo ""
        read -e -p "➤ $VAR_FORMATADA [$VALOR_SEM_ASPAS]: " NOVO_VALOR
        NOVO_VALOR="${NOVO_VALOR:-$VALOR_SEM_ASPAS}"

        case "$TIPO_VALIDACAO" in
            ip)
                if validar_ip "$NOVO_VALOR"; then break
                else echo "❌ IP inválido. Tente novamente."; fi
                ;;
            url)
                if validar_url "$NOVO_VALOR"; then break
                else echo "❌ URL inválida. Deve começar com http:// ou https://"; fi
                ;;
            *)
                break
                ;;
        esac
    done

    [[ $NOVO_VALOR == *" "* || $NOVO_VALOR == *'"'* ]] && NOVO_VALOR="\"$NOVO_VALOR\""

    if grep -qE "^$VAR=" "$ARQUIVO"; then
        sed -i "s|^$VAR=.*|$VAR=$NOVO_VALOR|" "$ARQUIVO"
    else
        echo "$VAR=$NOVO_VALOR" >> "$ARQUIVO"
    fi
}

function configurar_placa_de_rede() {
    echo "Configurar Interface de Rede... (Tecle Enter para manter a informação atual)"
    ler_variavel "ip" "$env_cma_gateway" "IP" "ip"
    ler_variavel "mascara" "$env_cma_gateway" "MÁSCARA" "ip"
    ler_variavel "gateway" "$env_cma_gateway" "GATEWAY" "ip"
    ler_variavel "dns" "$env_cma_gateway" "DNS" "ip"
    echo "✅ Configurações da interface de rede atualizadas com sucesso."
    read -p "Pressione Enter para continuar..."
    sleep 2
}

function configurar_reconcile() {
    echo "Configurar CMA WEB... (Tecle Enter para manter a informação atual)"
    ler_variavel "GWTDADOS_HOST" "$env_reconcile" "HOST CMA WEB" "url"
    ler_variavel "GWTDADOS_USERNAME" "$env_reconcile" "USUÁRIO CMA WEB"
    ler_variavel "GWTDADOS_PASSWORD" "$env_reconcile" "SENHA CMA WEB"
    ler_variavel "GATEWAY_NAME" "$env_reconcile" "NOME DO GATEWAY"
    echo "... Aguarde enquanto o Gateway é verificado no CMA Web ..."
    #local path_collect="C:/Users/Caval/OneDrive/Documentos/Reconcile-CMA-Gateway-de-Dados/"
    if [ -d "$path_collect" ]; then
        cd "$path_collect" || exit 1
        uv run python -m app.collect_cma_web
    else
        echo "❌ Caminho não encontrado: $path_collect"
    fi
    read -p "Pressione Enter para continuar..."
    sleep 2
}

function configurar_rabbitmq() {
    echo "Configurar Servidor de Notificação... (Tecle Enter para manter a informação atual)"
    ler_variavel "RABBIT_HOST" "$env_cma_gateway" "HOST"
    ler_variavel "RABBIT_PORT" "$env_cma_gateway" "PORTA"
    ler_variavel "RABBIT_USER" "$env_cma_gateway" "USUÁRIO"
    ler_variavel "RABBIT_PASS" "$env_cma_gateway" "SENHA"
    ler_variavel "RABBIT_CAMINHO" "$env_cma_gateway" "EXCHANGE"
    ler_variavel "RABBIT_TOPICO" "$env_cma_gateway" "QUEUE"
    ler_variavel "RABBIT_CHAVE" "$env_cma_gateway" "ROUTING KEY"
    echo "✅ Configurações do Servidor de Notificação atualizadas com sucesso."
    read -p "Pressione Enter para continuar..."
    sleep 2
}

function executar_gateway() {
    echo "Executando CMA Gateway..."
    #local caminho="C:/Users/Caval/OneDrive/Documentos/CMA-Gateway-de-Dados/src"
    if [ -d "$path_main" ]; then
        cd "$path_main" || exit 1
        uv run python main.py
    else
        echo "❌ Caminho não encontrado: $path_main"
    fi
    exit
}

# Loop principal
while true; do
    exibir_menu
    read -p "Opção: " opcao
    case $opcao in
        1) configurar_placa_de_rede ;;
        2) configurar_reconcile ;;
        3) configurar_rabbitmq ;;
        4) executar_gateway ;;
        0) echo "Saindo..."; exit 0 ;;
        *) echo "Opção inválida."; sleep 2 ;;
    esac
done
