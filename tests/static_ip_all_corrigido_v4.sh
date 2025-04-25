
#!/usr/bin/env bash

LOG_FILE="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede.log"
ENV_FILE="/home/cma/CMA-Gateway-de-Dados/src/.env"
STATE_DIR="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede"
INSTALLER_YAML="/etc/netplan/99-installer-config.yaml"
NETPLAN_FILE="/etc/netplan/99-cabeadas.yaml"
DHCP_DEFAULT="/etc/default/isc-dhcp-server"
DHCP_CONF="/etc/dhcp/dhcpd.conf"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ Por favor, execute como root (use sudo)${NC}"
  exit 1
fi

mask_to_network() {
    local ip="$1" mask="$2"
    IFS=. read -r i1 i2 i3 i4 <<< "$ip"
    IFS=. read -r m1 m2 m3 m4 <<< "$mask"
    printf "%d.%d.%d.%d\n" "$((i1 & m1))" "$((i2 & m2))" "$((i3 & m3))" "$((i4 & m4))"
}

mask_to_cidr() {
    local mask=$1
    IFS=. read -r o1 o2 o3 o4 <<< "$mask"
    echo "$(( (o1<<24 | o2<<16 | o3<<8 | o4) ))" | awk '{ for (i=0;i<32;i++) if (!(and($1,2^(31-i)))) break; print i; }'
}

sanitize_dns_list() {
    local raw_list="$1" sanitized=""
    for dns in $raw_list; do
        if [[ $dns =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
            sanitized+="${sanitized:+, }$dns"
        fi
    done
    echo "$sanitized"
}

mkdir -p "$STATE_DIR"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"
exec 3>&1 1>>"$LOG_FILE" 2>&1

interfaces=$(ls /sys/class/net | grep -E '^eth|^en' | grep -v lo)

configured_interfaces=()
dhcp_servers=()

echo "🔄 Ativando interfaces físicas..."
for iface in $interfaces; do
    ip link set "$iface" up
    sleep 0.3
done

echo "🔍 Verificando interfaces com cabo conectado..."
if [ -f "$ENV_FILE" ]; then
  set -a
  . "$ENV_FILE"
  set +a

  for iface in $interfaces; do
    carrier="/sys/class/net/$iface/carrier"
    if [ -f "$carrier" ] && [ "$(cat "$carrier")" -eq 1 ]; then
        echo "✅ Cabo detectado em $iface"
        IFACE_ENV=$(echo "$iface" | tr '[:lower:]' '[:upper:]')

        eval "dhcp_val=\${${IFACE_ENV}_DHCP}"
        eval "dhcp_server_val=\${${IFACE_ENV}_DHCP_SERVER}"
        eval "ip_val=\${${IFACE_ENV}_IP}"
        eval "mask_val=\${${IFACE_ENV}_MASK}"
        eval "gw_val=\${${IFACE_ENV}_GW}"
        eval "dns_val=\${${IFACE_ENV}_DNS}"
        eval "range_start=\${${IFACE_ENV}_DHCP_RANGE_START}"
        eval "range_end=\${${IFACE_ENV}_DHCP_RANGE_END}"

        if [[ "$dhcp_val" == "true" ]]; then
            echo "📡 Interface $iface será configurada com DHCP (cliente)"
            configured_interfaces+=("$iface:dhcp")
        elif [[ "$dhcp_server_val" == "true" ]]; then
            CIDR=$(mask_to_cidr "$mask_val")
            IP_CIDR="${ip_val}/${CIDR}"
            network=$(mask_to_network "$ip_val" "$mask_val")
            sanitized_dns=$(sanitize_dns_list "$dns_val")

            echo "🖧 Interface $iface será IP fixo e servidor DHCP ($IP_CIDR)"
            configured_interfaces+=("$iface:static:$IP_CIDR:$gw_val:$dns_val")
            dhcp_servers+=("$iface:$network:$mask_val:$range_start:$range_end:$sanitized_dns:$ip_val")
        elif [[ -n "$ip_val" && -n "$mask_val" && -n "$gw_val" && -n "$dns_val" ]]; then
            CIDR=$(mask_to_cidr "$mask_val")
            IP_CIDR="${ip_val}/${CIDR}"
            echo "📌 Interface $iface será configurada com IP $IP_CIDR"
            configured_interfaces+=("$iface:static:$IP_CIDR:$gw_val:$dns_val")
        else
            echo -e "${RED}⚠️ Variáveis insuficientes para $iface${NC}"
        fi
    fi
  done
else
  echo -e "${RED}❌ Arquivo .env não encontrado em $ENV_FILE${NC}"
  exit 1
fi

rm -f /etc/netplan/99-*.yaml
[ -f "$INSTALLER_YAML" ] && mv "$INSTALLER_YAML" "$INSTALLER_YAML.bkp"

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

if [ ${#dhcp_servers[@]} -gt 0 ]; then
    echo "📦 Instalando isc-dhcp-server (se necessário)..."
    apt install -y isc-dhcp-server

    echo "🔧 Atualizando $DHCP_DEFAULT com interfaces..."
    interfaces_line=$(printf "%s " "${dhcp_servers[@]}" | cut -d: -f1 | xargs)
    echo "INTERFACESv4=\"$interfaces_line\"" > "$DHCP_DEFAULT"

    echo "📝 Gerando $DHCP_CONF..."
    echo "# dhcpd.conf gerado por static_ip_all.sh" > "$DHCP_CONF"
    for entry in "${dhcp_servers[@]}"; do
        IFS=':' read -r iface network mask start end dns router <<< "$entry"
        sanitized_dns=$(sanitize_dns_list "$dns")
        {
            echo ""
            echo "# Bloco gerado para $iface"
            echo "subnet $network netmask $mask {"
            echo "  range $start $end;"
            echo "  option routers $router;"
            echo "  option domain-name-servers $sanitized_dns;"
            echo "}"
        } >> "$DHCP_CONF"
    done

    echo "🔎 Validando $DHCP_CONF..."
    if dhcpd -t; then
        echo -e "${GREEN}✅ dhcpd.conf válido. Reiniciando servidor...${NC}"
        systemctl restart isc-dhcp-server
        systemctl enable isc-dhcp-server
    else
        echo -e "${RED}❌ Erro no dhcpd.conf. Verifique manualmente.${NC}"
        exit 1
    fi
fi

echo "🔎 Validando Netplan..."
if netplan generate; then
    echo -e "${GREEN}✅ Aplicando Netplan...${NC}"
    netplan apply
else
    echo -e "${RED}❌ Erro na validação Netplan${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Todas interfaces configuradas com sucesso!${NC}"
echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
