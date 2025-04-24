#!/bin/bash

LOG_FILE="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede.log"
ENV_FILE="/home/cma/CMA-Gateway-de-Dados/src/.env"
STATE_DIR="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede"
INSTALLER_YAML="/etc/netplan/99-installer-config.yaml"
NETPLAN_FILE="/etc/netplan/99-cabeadas.yaml"
DHCP_DEFAULT="/etc/default/isc-dhcp-server"
DHCP_CONF="/etc/dhcp/dhcpd.conf"

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
dhcp_servers=()

for iface in $interfaces; do
    carrier="/sys/class/net/$iface/carrier"
    if [ -f "$carrier" ] && [ "$(cat $carrier)" -eq 1 ]; then
        echo "✅ Cabo detectado em $iface"
        IFACE_ENV=$(echo "$iface" | tr '[:lower:]' '[:upper:]')

        dhcp_var="${IFACE_ENV}_DHCP"
        dhcp_server_var="${IFACE_ENV}_DHCP_SERVER"
        ip_var="${IFACE_ENV}_IP"
        mask_var="${IFACE_ENV}_MASK"
        gw_var="${IFACE_ENV}_GW"
        dns_var="${IFACE_ENV}_DNS"
        range_start_var="${IFACE_ENV}_DHCP_RANGE_START"
        range_end_var="${IFACE_ENV}_DHCP_RANGE_END"

        dhcp_val="${!dhcp_var}"
        dhcp_server_val="${!dhcp_server_var}"
        ip_val="${!ip_var}"
        mask_val="${!mask_var}"
        gw_val="${!gw_var}"
        dns_val="${!dns_var}"
        range_start="${!range_start_var}"
        range_end="${!range_end_var}"

        if [[ "$dhcp_val" == "true" ]]; then
            echo "📡 Interface $iface será configurada com DHCP (cliente)"
            configured_interfaces+=("$iface:dhcp")
        elif [[ "$dhcp_server_val" == "true" ]]; then
            CIDR=$(mask_to_cidr "$mask_val")
            IP_CIDR="${ip_val}/${CIDR}"
            echo "🖧 Interface $iface será IP fixo e servidor DHCP ($IP_CIDR)"
            configured_interfaces+=("$iface:static:$IP_CIDR:$gw_val:$dns_val")
            dhcp_servers+=("$iface:$ip_val:$mask_val:$range_start:$range_end:$dns_val")
        elif [[ -n "$ip_val" && -n "$mask_val" && -n "$gw_val" && -n "$dns_val" ]]; then
            CIDR=$(mask_to_cidr "$mask_val")
            IP_CIDR="${ip_val}/${CIDR}"
            echo "📌 Interface $iface será configurada com IP $IP_CIDR"
            configured_interfaces+=("$iface:static:$IP_CIDR:$gw_val:$dns_val")
        else
            echo "⚠️ Variáveis insuficientes para $iface"
        fi
    fi
done

if [ ${#configured_interfaces[@]} -eq 0 ]; then
    echo "⚠️ Nenhuma interface com cabo e configuração válida encontrada."
    echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
    exit 0
fi

# DHCP Server: instalar e configurar
if [ ${#dhcp_servers[@]} -gt 0 ]; then
    echo "📦 Instalando isc-dhcp-server (se necessário)..."
    apt install -y isc-dhcp-server

    echo "🔧 Atualizando $DHCP_DEFAULT com interfaces..."
    interfaces_line=$(printf "%s " "${dhcp_servers[@]}" | cut -d: -f1 | xargs)
    echo "INTERFACESv4=\"$interfaces_line\"" | tee "$DHCP_DEFAULT"

    echo "📝 Gerando $DHCP_CONF..."
    echo "# dhcpd.conf gerado por static_ip.sh" > "$DHCP_CONF"
    for entry in "${dhcp_servers[@]}"; do
        IFS=':' read -r iface ip mask start end dns <<< "$entry"
        network=$(ipcalc "$ip" "$mask" | grep Network | cut -d: -f2 | awk '{print $1}')
        netmask=$(ipcalc "$ip" "$mask" | grep Netmask | head -n1 | awk '{print $2}')
        echo "" >> "$DHCP_CONF"
        echo "subnet $network netmask $netmask {" >> "$DHCP_CONF"
        echo "  range $start $end;" >> "$DHCP_CONF"
        echo "  option routers $ip;" >> "$DHCP_CONF"
        echo "  option domain-name-servers $dns;" >> "$DHCP_CONF"
        echo "}" >> "$DHCP_CONF"
    done
fi

# Netplan
[ -f "$INSTALLER_YAML" ] && mv "$INSTALLER_YAML" "${INSTALLER_YAML}.bkp"
rm -f /etc/netplan/99-*.yaml

echo "📝 Criando $NETPLAN_FILE"
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

echo "🔎 Validando Netplan..."
if netplan generate; then
    echo "✅ Aplicando Netplan..."
    netplan apply
else
    echo "❌ Erro na validação Netplan"
    exit 1
fi

# Reinicia DHCP server
if [ ${#dhcp_servers[@]} -gt 0 ]; then
    echo "🔄 Reiniciando isc-dhcp-server..."
    systemctl restart isc-dhcp-server
    systemctl enable isc-dhcp-server
fi

echo "✅ Todas interfaces configuradas com sucesso!"
echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
