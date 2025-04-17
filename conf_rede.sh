#!/bin/bash

LOG_FILE="/var/log/ativar-rede.log"
ENV_FILE="CMA-Gateway-de-Dados/src/.env"
STATE_DIR="/var/lib/ativar-rede"
LAST_INTERFACE_FILE="$STATE_DIR/ultima_interface"

# Função para converter máscara de rede para CIDR
mask_to_cidr() {
    local mask=$1
    IFS=. read -r i1 i2 i3 i4 <<< "$mask"
    echo "$(( (i1<<24 | i2<<16 | i3<<8 | i4) ))" | awk '{for(i=0;i<32;i++)if(!($1&(1<<(31-i))))break;print i}'
}

# Prepara diretório de estado e log
sudo mkdir -p "$STATE_DIR"
sudo touch "$LOG_FILE"
sudo chmod 644 "$LOG_FILE"
exec >> "$LOG_FILE" 2>&1

echo "============================="
echo "🕓 $(date '+%Y-%m-%d %H:%M:%S') - Iniciando script de ativação de rede"

# Carrega .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "❌ Arquivo .env não encontrado em $ENV_FILE"
    exit 1
fi

# Verifica variáveis
if [[ -z "$ip" || -z "$mascara" || -z "$gateway" || -z "$dns" ]]; then
    echo "❌ Variáveis ip, mascara, gateway ou dns não definidas no .env"
    exit 1
fi

# Converte máscara para CIDR
CIDR=$(mask_to_cidr "$mascara")
IP_CIDR="${ip}/${CIDR}"

default_renderer="networkd"
interfaces=$(ls /sys/class/net | grep -E '^eth|^en' | grep -v lo)

# Ativa todas as interfaces com fio
echo "🔄 Ativando todas as interfaces para detectar cabo..."
for iface in $interfaces; do
    sudo ip link set "$iface" up
    sleep 0.5
done

# Busca a primeira interface com cabo conectado
echo "🔍 Verificando interfaces com cabo..."
for iface in $interfaces; do
    carrier_file="/sys/class/net/$iface/carrier"

    if [ -f "$carrier_file" ] && [ "$(cat $carrier_file)" -eq 1 ]; then
        echo "✅ Cabo conectado na interface: $iface"

        # Verifica se é a mesma da última vez
        if [ -f "$LAST_INTERFACE_FILE" ]; then
            last_iface=$(cat "$LAST_INTERFACE_FILE")
            if [ "$iface" = "$last_iface" ]; then
                echo "🔁 Interface já configurada anteriormente: $iface. Nada será feito."
                exit 0
            fi
        fi

        echo "💾 Gravando interface atual para comparação futura: $iface"
        echo "$iface" | sudo tee "$LAST_INTERFACE_FILE" > /dev/null

        # Limpa configurações antigas
        echo "🧹 Removendo Netplans antigos..."
        sudo rm -f /etc/netplan/99-*.yaml

        # Gera nova configuração
        config_file="/etc/netplan/99-$iface.yaml"
        echo "📝 Criando $config_file"

        sudo tee "$config_file" > /dev/null <<EOF
network:
  version: 2
  renderer: $default_renderer
  ethernets:
    $iface:
      dhcp4: false
      addresses: [$IP_CIDR]
      nameservers:
        addresses: [$dns]
      routes:
        - to: 0.0.0.0/0
          via: $gateway
      optional: true
EOF

        sudo chmod 600 "$config_file"

        echo "🔎 Validando com netplan generate..."
        if sudo netplan generate; then
            echo "✅ Configuração válida. Aplicando..."
            sudo netplan apply
            echo "✅ Interface $iface configurada com IP: $IP_CIDR"
            exit 0
        else
            echo "❌ Falha ao validar YAML"
            exit 1
        fi
    fi
done

echo "⚠️ Nenhuma interface com cabo detectado."
exit 1
