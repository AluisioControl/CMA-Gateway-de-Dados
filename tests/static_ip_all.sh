#!/bin/bash

LOG_FILE="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede.log"
ENV_FILE="/home/cma/CMA-Gateway-de-Dados/src/.env"
STATE_DIR="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede"
INSTALLER_YAML="/etc/netplan/99-installer-config.yaml"
NETPLAN_FILE="/etc/netplan/99-cabeadas.yaml"

if [ "$EUID" -ne 0 ]; then
  echo "❌ Por favor, execute como root (use sudo)"
  exit 1
fi

mask_to_cidr() {
    local mask=$1
    IFS=. read -r o1 o2 o3 o4 <<< "$mask"
    local bin_mask=$(printf '%08d%08d%08d%08d\n' \
        "$(echo "obase=2; $o1" | bc)" \
        "$(echo "obase=2; $o2" | bc)" \
        "$(echo "obase=2; $o3" | bc)" \
        "$(echo "obase=2; $o4" | bc)")
    echo "$bin_mask" | grep -o "1" | wc -l
}

mkdir -p "$STATE_DIR"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "============================="
echo "🕓 $(date '+%Y-%m-%d %H:%M:%S') - Iniciando script de ativação de rede"

if [ -f "$ENV_FILE" ]; then
    set -o allexport
    source "$ENV_FILE"
    set +o allexport
else
    echo "❌ Arquivo .env não encontrado em $ENV_FILE"
    exit 1
fi

interfaces=$(ls /sys/class/net | grep -E '^eth|^en' | grep -v lo)

echo "🔄 Ativando interfaces físicas..."
for iface in $interfaces; do
    ip link set "$iface" up
    sleep 0.5
done

echo "🔍 Verificando interfaces com cabo conectado..."
configured_interfaces=()

for iface in $interfaces; do
    carrier="/sys/class/net/$iface/carrier"
    if [ -f "$carrier" ] && [ "$(cat $carrier)" -eq 1 ]; then
        echo "✅ Cabo detectado em $iface"
        IFACE_ENV=$(echo "$iface" | tr '[:lower:]' '[:upper:]')

        dhcp_var="${IFACE_ENV}_DHCP"
        ip_var="${IFACE_ENV}_IP"
        mask_var="${IFACE_ENV}_MASK"
        gw_var="${IFACE_ENV}_GW"
        dns_var="${IFACE_ENV}_DNS"

        dhcp_val="${!dhcp_var}"
        ip_val="${!ip_var}"
        mask_val="${!mask_var}"
        gw_val="${!gw_var}"
        dns_val="${!dns_var}"

        if [[ "$dhcp_val" == "true" ]]; then
            echo "📡 Interface $iface será configurada com DHCP"
            configured_interfaces+=("$iface:dhcp")
        elif [[ -n "$ip_val" && -n "$mask_val" && -n "$gw_val" && -n "$dns_val" ]]; then
            CIDR=$(mask_to_cidr "$mask_val")
            IP_CIDR="${ip_val}/${CIDR}"
            echo "📌 Interface $iface será configurada com IP $IP_CIDR"
            configured_interfaces+=("$iface:static:$IP_CIDR:$gw_val:$dns_val")
        else
            echo "⚠️ Variáveis insuficientes para configurar $iface no modo estático ou DHCP"
        fi
    fi
done

if [ ${#configured_interfaces[@]} -eq 0 ]; then
    echo "⚠️ Nenhuma interface com cabo e configuração válida encontrada."
    echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
    exit 0
fi

if [ -f "$INSTALLER_YAML" ]; then
    echo "📦 Backup do Netplan padrão..."
    mv "$INSTALLER_YAML" "${INSTALLER_YAML}.bkp"
fi

echo "🧹 Limpando Netplans antigos..."
rm -f /etc/netplan/99-*.yaml

echo "📝 Criando Netplan consolidado em $NETPLAN_FILE"
{
    echo "network:"
    echo "  version: 2"
    echo "  ethernets:"
    metric=100
    for config in "${configured_interfaces[@]}"; do
        IFS=':' read -r iface mode ip_cidr gw dns <<< "$config"
        echo "    $iface:"
        if [ "$mode" = "dhcp" ]; then
            echo "      dhcp4: true"
            echo "      dhcp6: false"
        else
            echo "      addresses:"
            echo "        - $ip_cidr"
            echo "      dhcp6: false"
            echo "      routes:"
            echo "        - to: default"
            echo "          via: $gw"
            echo "          metric: $metric"
            echo "      nameservers:"
            echo "        addresses:"
            for d in $dns; do
                echo "          - $d"
            done
            echo "        search: []"
            metric=$((metric + 100))
        fi
        echo "      optional: true"
    done
} > "$NETPLAN_FILE"

chmod 600 "$NETPLAN_FILE"

echo "🔎 Validando com netplan generate..."
if netplan generate; then
    echo "✅ Netplan válido. Aplicando..."
    netplan apply
else
    echo "❌ Falha na validação do Netplan"
    exit 1
fi

echo "✅ Interfaces configuradas com sucesso!"
echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
