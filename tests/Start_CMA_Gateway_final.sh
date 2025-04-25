#!/bin/bash
# Script configurador principal com integração ao config_envs.sh

#path_main="/home/cma/CMA-Gateway-de-Dados/src/"
#path_collect="/home/cma/Reconcile-CMA-Gateway-de-Dados/"
#env_cma_gateway="/home/cma/CMA-Gateway-de-Dados/src/.env"
#env_reconcile="/home/cma/Reconcile-CMA-Gateway-de-Dados/.env"

path_main="C:/Users/Caval/OneDrive/Documentos/CMA-Gateway-de-Dados/src/"
path_collect="C:/Users/Caval/OneDrive/Documentos/Reconcile-CMA-Gateway-de-Dados/"
env_cma_gateway="C:/Users/Caval/OneDrive/Documentos/CMA-Gateway-de-Dados/src/.env"
env_reconcile="C:/Users/Caval/OneDrive/Documentos/Reconcile-CMA-Gateway-de-Dados/.env"

function exibir_menu() {
    clear

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

function validar_url() {
    local url="$1"
    [[ $url =~ ^https?://[a-zA-Z0-9.-]+(:[0-9]+)?(/.*)?$ ]]

function ler_variavel_yn() {
    local VAR=$1
    local ARQUIVO=$2
    local VAR_FORMATADA=$3

    local VALOR_ATUAL_COM_ASPAS=$(grep -E "^$VAR=" "$ARQUIVO" | cut -d '=' -f2-)
    local VALOR_SEM_ASPAS=$(echo "$VALOR_ATUAL_COM_ASPAS" | sed 's/^"//;s/"$//')

    [[ "$VALOR_SEM_ASPAS" == "true" ]] && VALOR_SEM_ASPAS="y"
    [[ "$VALOR_SEM_ASPAS" == "false" ]] && VALOR_SEM_ASPAS="n"

    while true; do
        read -e -p "➤ $VAR_FORMATADA (y/n) [${VALOR_SEM_ASPAS}]: " NOVO
        NOVO="${NOVO:-$VALOR_SEM_ASPAS}"

        case "$NOVO" in
            y|Y) VALOR_FINAL="true"; break ;;
            n|N) VALOR_FINAL="false"; break ;;
            *) echo "❌ Entrada inválida. Use apenas y ou n."; continue ;;
        esac
    done

    if grep -qE "^$VAR=" "$ARQUIVO"; then
        sed -i "s|^$VAR=.*|$VAR=$VALOR_FINAL|" "$ARQUIVO"
    else
    fi

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

    if [[ "$VAR" == "GATEWAY_NAME" ]]; then
        NOVO_VALOR="\"$NOVO_VALOR\""
    elif [[ $NOVO_VALOR == *" "* || $NOVO_VALOR == *'"'* ]]; then
        NOVO_VALOR="\"$NOVO_VALOR\""
    fi

    for ARQUIVO in "${ARQUIVOS[@]}"; do
        if grep -qE "^$VAR=" "$ARQUIVO"; then
            sed -i "s|^$VAR=.*|$VAR=$NOVO_VALOR|" "$ARQUIVO"
        else
        fi
    done


    for i in {0..4}; do
        iface="ETH$i"
        grep -E "^${iface}_" "$env_cma_gateway" | sed 's/^/     /'
    done

    read -p "Digite o número da interface que deseja configurar [0-4]: " num_iface
    if ! [[ "$num_iface" =~ ^[0-4]$ ]]; then
        read -p "Pressione Enter para voltar ao menu..."
        return
    fi

    iface="ETH${num_iface}"

    ler_variavel_yn "${iface}_DHCP" "$env_cma_gateway" "Usar DHCP?"
    ler_variavel_yn "${iface}_DHCP_SERVER" "$env_cma_gateway" "Ativar como Servidor DHCP?"
    ler_variavel "${iface}_IP" "$env_cma_gateway" "Endereço IP" "ip"
    ler_variavel "${iface}_MASK" "$env_cma_gateway" "Máscara de Rede" "ip"
    ler_variavel "${iface}_GW" "$env_cma_gateway" "Gateway" "ip"
    ler_variavel "${iface}_DNS" "$env_cma_gateway" "DNS (separado por espaço)" "ip_list"
    ler_variavel "${iface}_DHCP_RANGE_START" "$env_cma_gateway" "DHCP Início do Range" "ip"
    ler_variavel "${iface}_DHCP_RANGE_END" "$env_cma_gateway" "DHCP Fim do Range" "ip"

    read -p "Pressione Enter para continuar..."
    sleep 2
    for i in {0..4}; do
        iface="ETH$i"

        ler_variavel_yn "${iface}_DHCP" "$env_cma_gateway" "Usar DHCP?"
        ler_variavel_yn "${iface}_DHCP_SERVER" "$env_cma_gateway" "Ativar como Servidor DHCP?"
        ler_variavel "${iface}_IP" "$env_cma_gateway" "Endereço IP" "ip"
        ler_variavel "${iface}_MASK" "$env_cma_gateway" "Máscara de Rede" "ip"
        ler_variavel "${iface}_GW" "$env_cma_gateway" "Gateway" "ip"
        ler_variavel "${iface}_DNS" "$env_cma_gateway" "DNS (separado por espaço)" "ip"
        ler_variavel "${iface}_DHCP_RANGE_START" "$env_cma_gateway" "DHCP Início do Range" "ip"
        ler_variavel "${iface}_DHCP_RANGE_END" "$env_cma_gateway" "DHCP Fim do Range" "ip"
    done
    read -p "Pressione Enter para continuar..."
    sleep 2
} {
    ler_variavel "ip" "$env_cma_gateway" "IP" "ip"
    ler_variavel "mascara" "$env_cma_gateway" "MÁSCARA" "ip"
    ler_variavel "gateway" "$env_cma_gateway" "GATEWAY" "ip"
    ler_variavel "dns" "$env_cma_gateway" "DNS" "ip"
    read -p "Pressione Enter para continuar..."
    sleep 2

function configurar_reconcile() {
    ler_variavel "GWTDADOS_HOST" "$env_reconcile" "HOST CMA WEB" "url"
    ler_variavel "GWTDADOS_USERNAME" "$env_reconcile" "USUÁRIO CMA WEB"
    ler_variavel "GWTDADOS_PASSWORD" "$env_reconcile" "SENHA CMA WEB"
    ler_variavel "GATEWAY_NAME" "$env_reconcile" "NOME DO GATEWAY"
    if [ -d "$path_collect" ]; then
        cd "$path_collect" || exit 1
        uv run python -m app.collect_cma_web
    else
    fi
    read -p "Pressione Enter para continuar..."
    sleep 2

function configurar_rabbitmq() {
    ler_variavel "RABBIT_HOST" "$env_cma_gateway" "$env_reconcile" "HOST"
    ler_variavel "RABBIT_PORT" "$env_cma_gateway" "$env_reconcile" "PORTA"
    ler_variavel "RABBIT_USER" "$env_cma_gateway" "$env_reconcile" "USUÁRIO"
    ler_variavel "RABBIT_PASS" "$env_cma_gateway" "$env_reconcile" "SENHA"
    ler_variavel "RABBIT_CAMINHO" "$env_cma_gateway" "$env_reconcile" "EXCHANGE"
    ler_variavel "RABBIT_TOPICO" "$env_cma_gateway" "$env_reconcile" "QUEUE"
    ler_variavel "RABBIT_CHAVE" "$env_cma_gateway" "$env_reconcile" "ROUTING KEY"
    read -p "Pressione Enter para continuar..."
    sleep 2

function executar_gateway() {
    if [ -d "$path_main" ]; then
        cd "$path_main" || exit 1
        uv run python main.py
    else
    fi
    read -p "Pressione Enter para continuar..."
    sleep 2

function ler_valor_compartilhado() {
    local VAR_FORMATADA="$1"
    shift

    if (( $# % 2 != 0 )); then
        return 1
    fi

    local -a pares=("$@")
    local BASE_VAR="${pares[0]}"
    local BASE_ARQ="${pares[1]}"

    local VALOR_ATUAL=$(grep -E "^$BASE_VAR=" "$BASE_ARQ" 2>/dev/null | cut -d '=' -f2- | sed 's/^"//;s/"$//')
    read -e -p "➤ $VAR_FORMATADA [$VALOR_ATUAL]: " NOVO_VALOR
    NOVO_VALOR="${NOVO_VALOR:-$VALOR_ATUAL}"
    [[ $NOVO_VALOR == *" "* || $NOVO_VALOR == *'"'* ]] && NOVO_VALOR="\"$NOVO_VALOR\""

    for ((i = 0; i < ${#pares[@]}; i+=2)); do
        local VAR="${pares[$i]}"
        local ARQ="${pares[$i+1]}"

        if grep -q "^$VAR=" "$ARQ"; then
            sed "s|^$VAR=.*|$VAR=$NOVO_VALOR|" "$ARQ" > "${ARQ}.tmp" && mv "${ARQ}.tmp" "$ARQ"
        else
        fi
    done

function configurar_variaveis_complementares() {

    ler_valor_compartilhado "URL Base do SCADA" \
        URL_BASE "$env_cma_gateway" \
        SCADALTS_HOST "$env_reconcile"

    ler_valor_compartilhado "Usuário SCADA-LTS" \
        username "$env_cma_gateway" \
        SCADALTS_USERNAME "$env_reconcile"

    ler_valor_compartilhado "Senha SCADA-LTS" \
        password "$env_cma_gateway" \
        SCADALTS_PASSWORD "$env_reconcile"

        # CMA Gateway
    ler_variavel "DATABASE_URL" "$env_cma_gateway" "URL do Banco de Dados"
    ler_variavel "LOG_LINUX" "$env_cma_gateway" "Caminho do Log"
    ler_variavel "HEALTH_CHECK_INTERVAL" "$env_cma_gateway" "Intervalo Health Check (s)"
    ler_variavel "STATUS_SERVER_CHECK_INTERVAL" "$env_cma_gateway" "Intervalo de Verificação de Status (s)"

    # Reconcile
    ler_variavel "SQLITE_MIDDLEWARE_PATH" "$env_reconcile" "Caminho SQLite Middleware"
    ler_variavel "DEBUG" "$env_reconcile" "Modo Debug (True/False)"
    ler_variavel "MAX_PAGE_SIZE" "$env_reconcile" "Tamanho Máximo por Página"
    ler_variavel "MAX_PARALLEL_REQUESTS" "$env_reconcile" "Máximo de Requisições Paralelas"
    ler_variavel "MAX_RETRIES" "$env_reconcile" "Máximo de ReTentativas"
    ler_variavel "SCADALTS_DELETE_TYPE" "$env_reconcile" "Tipo de Exclusão (soft/hard)"

    read -p "Pressione Enter para continuar..."
    sleep 2


# Loop principal
while true; do
    exibir_menu
    read -p "Opção: " opcao
    case $opcao in
        2) configurar_reconcile ;;
        3) configurar_rabbitmq ;;
        4) executar_gateway ;;
        5) configurar_variaveis_complementares ;;
        0) echo "Saindo..."; exit 0 ;;
        *) echo "Opção inválida."; sleep 2 ;;
    esac
done
