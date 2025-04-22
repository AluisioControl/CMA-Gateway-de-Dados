#!/bin/bash
# Script configurador principal com integração ao config_envs.sh

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
    echo "[5] - Configurar Variáveis Complementares"
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
    shift
    local ARQUIVOS=()
    while [[ "$1" == *.env ]]; do
        ARQUIVOS+=("$1")
        shift
    done
    local VAR_FORMATADA=$1
    local TIPO_VALIDACAO=$2

    local VALOR_ATUAL_COM_ASPAS=$(grep -E "^$VAR=" "${ARQUIVOS[0]}" | cut -d '=' -f2-)
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

    [[ $NOVO_VALOR == *" "* || $NOVO_VALOR == *'"'* ]] && NOVO_VALOR=""$NOVO_VALOR""

    for ARQUIVO in "${ARQUIVOS[@]}"; do
        if grep -qE "^$VAR=" "$ARQUIVO"; then
            sed -i "s|^$VAR=.*|$VAR=$NOVO_VALOR|" "$ARQUIVO"
        else
            echo "$VAR=$NOVO_VALOR" >> "$ARQUIVO"
        fi
    done
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
    ler_variavel "RABBIT_HOST" "$env_cma_gateway" "$env_reconcile" "HOST"
    ler_variavel "RABBIT_PORT" "$env_cma_gateway" "$env_reconcile" "PORTA"
    ler_variavel "RABBIT_USER" "$env_cma_gateway" "$env_reconcile" "USUÁRIO"
    ler_variavel "RABBIT_PASS" "$env_cma_gateway" "$env_reconcile" "SENHA"
    ler_variavel "RABBIT_CAMINHO" "$env_cma_gateway" "$env_reconcile" "EXCHANGE"
    ler_variavel "RABBIT_TOPICO" "$env_cma_gateway" "$env_reconcile" "QUEUE"
    ler_variavel "RABBIT_CHAVE" "$env_cma_gateway" "$env_reconcile" "ROUTING KEY"
    echo "✅ Configurações do Servidor de Notificação atualizadas com sucesso."
    read -p "Pressione Enter para continuar..."
    sleep 2
}

function executar_gateway() {
    echo "Executando CMA Gateway..."
    if [ -d "$path_main" ]; then
        cd "$path_main" || exit 1
        uv run python main.py
    else
        echo "❌ Caminho não encontrado: $path_main"
    fi
    read -p "Pressione Enter para continuar..."
    sleep 2
}


function configurar_variaveis_complementares() {
    echo "Configurar Variáveis Complementares (.env)..."

    # CMA Gateway
    ler_variavel "DATABASE_URL" "$env_cma_gateway" "Diretório do Banco de Dados"
    ler_variavel "URL_BASE" "$env_cma_gateway" "Host SCADA-LTS (CMA Gateway)"
    ler_variavel "username" "$env_cma_gateway" "Usuário SCADA-LTS (CMA Gateway)"
    ler_variavel "password" "$env_cma_gateway" "Senha SCADA-LTS (CMA Gateway)"
    ler_variavel "LOG_LINUX" "$env_cma_gateway" "Diretório Log CMA Gateway"
    ler_variavel "HEALTH_CHECK_INTERVAL" "$env_cma_gateway" "Intervalo Health Check (s)"
    ler_variavel "STATUS_SERVER_CHECK_INTERVAL" "$env_cma_gateway" "Intervalo de Verificação de Status (s)"

    # Reconcile
    ler_variavel "SQLITE_MIDDLEWARE_PATH" "$env_reconcile" "Diretório do Banco de Dados"
    ler_variavel "SCADALTS_USERNAME" "$env_reconcile" "Usuário SCADA-LTS (Reconcile)"
    ler_variavel "SCADALTS_PASSWORD" "$env_reconcile" "Senha SCADA-LTS (Reconcile)"
    ler_variavel "SCADALTS_HOST" "$env_reconcile" "Host SCADA-LTS (Reconcile)"
    ler_variavel "DEBUG" "$env_reconcile" "Modo Debug (True/False)"
    ler_variavel "MAX_PAGE_SIZE" "$env_reconcile" "Tamanho Máximo por Página"
    ler_variavel "MAX_PARALLEL_REQUESTS" "$env_reconcile" "Máximo de Requisições Paralelas"
    ler_variavel "MAX_RETRIES" "$env_reconcile" "Máximo de ReTentativas"
    ler_variavel "SCADALTS_DELETE_TYPE" "$env_reconcile" "Tipo de Exclusão (soft/hard)"

    echo ""
    echo "✅ Variáveis complementares atualizadas com sucesso."
    read -p "Pressione Enter para continuar..."
    sleep 2
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
        5) configurar_variaveis_complementares ;;
        0) echo "Saindo..."; exit 0 ;;
        *) echo "Opção inválida."; sleep 2 ;;
    esac
done
