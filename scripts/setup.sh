#!/bin/bash
# Script configurador principal com integração ao config_envs.sh

HOSTNAME=$(hostname)

base_path="/home/$HOSTNAME"
path_main="$base_path/CMA-Gateway-de-Dados/src/"
path_collect="$base_path/Reconcile-CMA-Gateway-de-Dados/"
env_cma_gateway="$path_main/.env"
env_reconcile="$path_collect/.env"

function exibir_menu() {
    clear
    echo "***********************************************************************"
    echo " BEM-VINDO(A) AO CONFIGURADOR GERAL DO GATEWAY"
    echo "***********************************************************************"
    echo ""
    echo "📡 Host detectado: $HOSTNAME"
    echo ""
    echo "Digite o número correspondente à configuração que deseja fazer:"
    echo "[1] - Configurar Interface de Rede"
    echo "[2] - Configurar CMA WEB"
    echo "[3] - Configurar Servidor de Notificação"
    echo "[4] - Iniciar Gateway de Dados"
    echo "[5] - Configurar Variáveis Complementares"
    echo "[6] - Configurar Servidor de Logs"
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

function ler_variavel_yn() {
    local VAR=$1
    local ARQUIVO=$2
    local VAR_FORMATADA=$3

    local VALOR_ATUAL_COM_ASPAS=$(grep -E "^$VAR=" "$ARQUIVO" | cut -d '=' -f2-)
    local VALOR_SEM_ASPAS=$(echo "$VALOR_ATUAL_COM_ASPAS" | sed 's/^"//;s/"$//')

    [[ "$VALOR_SEM_ASPAS" == "true" ]] && VALOR_SEM_ASPAS="y"
    [[ "$VALOR_SEM_ASPAS" == "false" ]] && VALOR_SEM_ASPAS="n"

    while true; do
        echo ""
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
        echo "$VAR=$VALOR_FINAL" >> "$ARQUIVO"
    fi
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

        local valido=true
        case "$TIPO_VALIDACAO" in
            ip)
                if ! validar_ip "$NOVO_VALOR"; then
                    echo "❌ IP inválido. Tente novamente."; valido=false
                fi
                ;;
            ip_list)
                for ip in $NOVO_VALOR; do
                    if ! validar_ip "$ip"; then
                        echo "❌ IP inválido na lista: $ip"; valido=false; break
                    fi
                done
                ;;
            url)
                if ! validar_url "$NOVO_VALOR"; then
                    echo "❌ URL inválida. Deve começar com http:// ou https://"; valido=false
                fi
                ;;
        esac
        [[ "$valido" == true ]] && break
    done

    if [[ "$VAR" == "GATEWAY_NAME" || "$NOVO_VALOR" == *" "* || "$NOVO_VALOR" == *'"'* ]]; then
        NOVO_VALOR="\"$NOVO_VALOR\""
    fi

    for ARQUIVO in "${ARQUIVOS[@]}"; do
        if grep -qE "^$VAR=" "$ARQUIVO"; then
            sed -i "s|^$VAR=.*|$VAR=$NOVO_VALOR|" "$ARQUIVO"
        else
            echo "$VAR=$NOVO_VALOR" >> "$ARQUIVO"
        fi
    done
}
function configurar_servidor_logs() {
    echo "Configurar Servidor de Logs... (Digite 'q' para voltar a qualquer momento)"
    read -p "Pressione Enter para continuar ou 'q' para voltar: " opcao
    [[ "$opcao" == "q" || "$opcao" == "Q" ]] && return

    echo "Configurar Servidor de Logs..."
    ler_variavel "LOG_SERVER_HOST" "$env_cma_gateway" "$env_reconcile" "Host do Servidor de Logs" "ip"
    ler_variavel "LOG_SERVER_PORT" "$env_cma_gateway" "$env_reconcile" "Porta do Servidor de Logs"
    
    echo "✅ Configurações do Servidor de Logs atualizadas com sucesso."

    echo "🔄 Atualizando configuração do Fluent Bit..."
    if /home/cma/CMA-Gateway-de-Dados/scripts/atualizar_fluentbit_conf.sh; then
        echo "✅ Arquivo fluent-bit.conf atualizado com sucesso!"
    else
        echo "⚠️ Erro ao atualizar o arquivo fluent-bit.conf!"
    fi

    read -p "Pressione Enter para continuar..."
    sleep 2
}


function configurar_interfaces_fisicas() {
    echo "🔧 Configurar Interfaces de Rede (ETH1 a ETHF)"
    echo ""
    echo "📋 Parâmetros atuais:"

    # Mapeia nomes lógicos (apresentação) para reais
    for i in {0..4}; do
        iface_real="ETH$i"
        case $i in
            0) iface_logico="ETH1 (RJ45)";;
            1) iface_logico="ETH2 (RJ45)";;
            2) iface_logico="ETH3 (Óptica)";;
            3) iface_logico="ETH4 (Óptica)";;
            4) iface_logico="ETHF (RJ45)";;
        esac

        ip=$(grep -E "^${iface_real}_IP=" "$env_cma_gateway" | cut -d '=' -f2-)
        dhcp=$(grep -E "^${iface_real}_DHCP=" "$env_cma_gateway" | cut -d '=' -f2-)
        echo "  [$i] - $iface_logico → IP=${ip:-N/D}, DHCP=${dhcp:-N/D}"
    done

    echo ""
    read -p "Digite o número da interface que deseja configurar [0-4] ou 'q' para voltar: " num_iface
    if [[ "$num_iface" == "q" || "$num_iface" == "Q" ]]; then
        return
    elif ! [[ "$num_iface" =~ ^[0-4]$ ]]; then
        echo "❌ Entrada inválida."
        read -p "Pressione Enter para continuar..."
        return
    fi

    iface_real="ETH${num_iface}"

    case $num_iface in
        0) iface_logico="ETH1 (eth0 - RJ45)";;
        1) iface_logico="ETH2 (eth1 - RJ45)";;
        2) iface_logico="ETH3 (eth2 - Óptica)";;
        3) iface_logico="ETH4 (eth3 - Óptica)";;
        4) iface_logico="ETHF (eth4 - RJ45)";;
    esac

    echo ""
    echo "💻 Configurando $iface_logico ... (Tecle Enter para manter o valor atual)"

    ler_variavel_yn "${iface_real}_DHCP" "$env_cma_gateway" "Usar DHCP?"
    ler_variavel_yn "${iface_real}_DHCP_SERVER" "$env_cma_gateway" "Ativar como Servidor DHCP?"
    ler_variavel "${iface_real}_IP" "$env_cma_gateway" "Endereço IP" "ip"
    ler_variavel "${iface_real}_MASK" "$env_cma_gateway" "Máscara de Rede" "ip"
    ler_variavel "${iface_real}_GW" "$env_cma_gateway" "Gateway" "ip"
    ler_variavel "${iface_real}_DNS" "$env_cma_gateway" "DNS (separado por espaço)" "ip_list"
    ler_variavel "${iface_real}_DHCP_RANGE_START" "$env_cma_gateway" "DHCP Início do Range" "ip"
    ler_variavel "${iface_real}_DHCP_RANGE_END" "$env_cma_gateway" "DHCP Fim do Range" "ip"

    echo ""
    echo "🚀 Aplicando nova configuração de rede..."
    sudo $base_path/CMA-Gateway-de-Dados/scripts/static_ip_all_final.sh
    echo "✅ Configurações de $iface_logico atualizadas com sucesso."
    read -p "Pressione Enter para continuar..."
    sleep 2    
}

function configurar_reconcile() {
    echo "Configurar CMA WEB... (Tecle Enter para manter a informação atual ou digite 'q' para voltar)"
    read -p "Pressione Enter para continuar ou 'q' para voltar: " opcao
    [[ "$opcao" == "q" || "$opcao" == "Q" ]] && return

    ler_variavel "GWTDADOS_HOST" "$env_reconcile" "HOST CMA WEB" "url"
    ler_variavel "GWTDADOS_USERNAME" "$env_reconcile" "USUÁRIO CMA WEB"
    ler_variavel "GWTDADOS_PASSWORD" "$env_reconcile" "SENHA CMA WEB"
    ler_variavel "GATEWAY_NAME" "$env_reconcile" "NOME DO GATEWAY"
    echo "... Aguarde enquanto o Gateway é verificado no CMA Web ..."
    if [ -d "$path_collect" ]; then
        cd "$path_collect" || return
        uv run python -m app.collect_cma_web && \
        uv run python -m app.reconcile2.main
    else
        echo "❌ Caminho não encontrado: $path_collect"
    fi
    read -p "Pressione Enter para continuar..."
    sleep 2
}

function submenu_rabbitmq() {
    local servidor=$1
    local sufixo=$2
    local arquivo1=$3
    local arquivo2=$4

    echo "Configurar parâmetros do Servidor de Notificação $servidor..."
    ler_variavel "RABBIT_HOST$sufixo" "$arquivo1" "$arquivo2" "HOST"
    ler_variavel "RABBIT_PORT$sufixo" "$arquivo1" "$arquivo2" "PORTA"
    ler_variavel "RABBIT_USER$sufixo" "$arquivo1" "$arquivo2" "USUÁRIO"
    ler_variavel "RABBIT_PASS$sufixo" "$arquivo1" "$arquivo2" "SENHA"
    ler_variavel "RABBIT_CAMINHO$sufixo" "$arquivo1" "$arquivo2" "EXCHANGE"
    ler_variavel "RABBIT_TOPICO$sufixo" "$arquivo1" "$arquivo2" "QUEUE"
    ler_variavel "RABBIT_CHAVE$sufixo" "$arquivo1" "$arquivo2" "ROUTING KEY"
    echo "✅ Configurações do Servidor $servidor atualizadas com sucesso."
}

function configurar_rabbitmq() {
    while true; do
        clear
        echo "***********************************************************************"
        echo "  CONFIGURAR SERVIDORES DE NOTIFICAÇÃO"
        echo "***********************************************************************"
        echo "[1] - Configurar envio de health check"
        echo "[2] - Configurar envio de leituras"
        echo "[0] - Voltar ao menu principal"
        echo ""
        read -p "Selecione a opção desejada: " opcao_rabbit

        case "$opcao_rabbit" in
            1) submenu_rabbitmq "1" "" "$env_cma_gateway" "$env_reconcile" ;;
            2) submenu_rabbitmq "2" "_2" "$env_cma_gateway" "$env_reconcile" ;;
            0) break ;;
            *) echo "❌ Opção inválida."; sleep 1 ;;
        esac
        read -p "Pressione Enter para continuar..."
    done
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

function ler_valor_compartilhado() {
    local VAR_FORMATADA="$1"
    shift

    if (( $# % 2 != 0 )); then
        echo "❌ Erro: número inválido de argumentos para variáveis e arquivos"
        return 1
    fi

    local -a pares=("$@")
    local BASE_VAR="${pares[0]}"
    local BASE_ARQ="${pares[1]}"

    local VALOR_ATUAL=$(grep -E "^$BASE_VAR=" "$BASE_ARQ" 2>/dev/null | cut -d '=' -f2- | sed 's/^"//;s/"$//')
    echo ""
    read -e -p "➤ $VAR_FORMATADA [$VALOR_ATUAL]: " NOVO_VALOR
    NOVO_VALOR="${NOVO_VALOR:-$VALOR_ATUAL}"
    [[ $NOVO_VALOR == *" "* || $NOVO_VALOR == *'"'* ]] && NOVO_VALOR="\"$NOVO_VALOR\""

    for ((i = 0; i < ${#pares[@]}; i+=2)); do
        local VAR="${pares[$i]}"
        local ARQ="${pares[$i+1]}"

        if grep -q "^$VAR=" "$ARQ"; then
            sed "s|^$VAR=.*|$VAR=$NOVO_VALOR|" "$ARQ" > "${ARQ}.tmp" && mv "${ARQ}.tmp" "$ARQ"
        else
            echo "$VAR=$NOVO_VALOR" >> "$ARQ"
        fi
    done
}

function configurar_variaveis_complementares() {
    echo "Configurar Variáveis Complementares (.env)... (Digite 'q' para voltar a qualquer momento)"
    read -p "Pressione Enter para continuar ou 'q' para voltar: " opcao
    [[ "$opcao" == "q" || "$opcao" == "Q" ]] && return
    echo "Configurar Variáveis Complementares (.env)..."

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
        1) configurar_interfaces_fisicas ;;
        2) configurar_reconcile ;;
        3) configurar_rabbitmq ;;
        4) executar_gateway ;;
        5) configurar_variaveis_complementares ;;
        6) configurar_servidor_logs ;;
        0) echo "Saindo..."; exit 0 ;;
        *) echo "Opção inválida."; sleep 2 ;;
    esac

done

