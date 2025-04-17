#!/bin/bash

LOG_FILE="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede.log"
ENV_FILE="/home/cma/CMA-Gateway-de-Dados/src/.env"
STATE_DIR="/home/cma/CMA-Gateway-de-Dados/logs/ativar-rede"
LAST_INTERFACE_FILE="$STATE_DIR/ultima_interface"
INSTALLER_YAML="/etc/netplan/99-installer-config.yaml"

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

if [[ -z "$ip" || -z "$mascara" || -z "$gateway" || -z "$dns" ]]; then
    echo "❌ Variáveis ip, mascara, gateway ou dns não definidas no .env"
    exit 1
fi

if ! [[ "$mascara" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
    echo "❌ Máscara de sub-rede inválida: $mascara"
    exit 1
fi

CIDR=$(mask_to_cidr "$mascara")
if [ -z "$CIDR" ]; then
    echo "❌ Falha ao converter a máscara $mascara para CIDR"
    exit 1
fi
IP_CIDR="${ip}/${CIDR}"

interfaces=$(ls /sys/class/net | grep -E '^eth|^en' | grep -v lo)

echo "🔄 Ativando interfaces..."
for iface in $interfaces; do
    ip link set "$iface" up
    sleep 0.5
done

echo "🔍 Buscando interface com cabo conectado..."
for iface in $interfaces; do
    carrier="/sys/class/net/$iface/carrier"
    if [ -f "$carrier" ] && [ "$(cat $carrier)" -eq 1 ]; then
        echo "✅ Cabo conectado em $iface"

        # Verifica se a interface mudou
        iface_changed=true
        if [ -f "$LAST_INTERFACE_FILE" ]; then
            last_iface=$(cat "$LAST_INTERFACE_FILE")
            if [ "$iface" = "$last_iface" ]; then
                echo "🔁 Interface já configurada anteriormente: $iface"
                echo "✅ Nada a fazer. A mesma interface está em uso."
                echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
                exit 0
            else
                echo "🔄 Interface alterada de $last_iface para $iface"
            fi
        else
            echo "📄 Nenhuma interface anterior registrada ainda."
        fi

        # Atualiza o registro da interface usada
        echo "$iface" > "$LAST_INTERFACE_FILE"

        # Desativa Netplan padrão do instalador
        if [ -f "$INSTALLER_YAML" ]; then
            echo "📦 Backup do arquivo do instalador..."
            mv "$INSTALLER_YAML" "${INSTALLER_YAML}.bkp"
        fi

        echo "🧹 Removendo Netplans antigos..."
        rm -f /etc/netplan/99-*.yaml

        config_file="/etc/netplan/99-$iface.yaml"
        echo "📝 Criando $config_file"

        {
            echo "network:"
            echo "  version: 2"
            echo "  ethernets:"
            echo "    $iface:"
            echo "      addresses:"
            echo "        - $IP_CIDR"
            echo "      dhcp6: false"
            echo "      routes:"
            echo "        - to: default"
            echo "          via: $gateway"
            echo "      nameservers:"
            echo "        addresses:"
            for d in $dns; do
                echo "          - $d"
            done
            echo "        search: []"
            echo "      optional: true"
        } > "$config_file"

        chmod 600 "$config_file"

        echo "🔎 Validando com netplan generate..."
        if netplan generate; then
            echo "✅ Configuração válida. Aplicando..."
            netplan apply

            echo "🌐 Testando conectividade com o gateway..."
            if ping -c 2 -W 1 "$gateway" > /dev/null; then
                echo "✅ Gateway alcançado com sucesso."
            else
                echo "⚠️ Sem resposta do gateway."
            fi

            echo "✅ Interface $iface configurada com IP $IP_CIDR"
            echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
            exit 0
        else
            echo "❌ Falha ao validar YAML"
            exit 1
        fi
    fi
done

echo "⚠️ Nenhuma interface com cabo detectado."
echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
exit 1
