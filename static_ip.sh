#!/bin/bash

LOG_FILE="/var/log/ativar-rede.log"
ENV_FILE="/usr/local/bin/rede.env"
STATE_DIR="/var/lib/ativar-rede"
LAST_INTERFACE_FILE="$STATE_DIR/ultima_interface"
INSTALLER_YAML="/etc/netplan/99-installer-config.yaml"

# Função para converter máscara para CIDR
mask_to_cidr() {
    local mask=$1
    IFS=. read -r i1 i2 i3 i4 <<< "$mask"
    echo "$(( (i1<<24 | i2<<16 | i3<<8 | i4) ))" | awk '{for(i=0;i<32;i++)if(!($1&(1<<(31-i))))break;print i}'
}

# Criação dos diretórios de estado e log
sudo mkdir -p "$STATE_DIR"
sudo touch "$LOG_FILE"
sudo chmod 644 "$LOG_FILE"
exec >> "$LOG_FILE" 2>&1

echo "============================="
echo "🕓 $(date '+%Y-%m-%d %H:%M:%S') - Iniciando script de ativação de rede"

# Carrega variáveis do .env (espera: ip, mascara, gateway, dns)
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "❌ Arquivo .env não encontrado em $ENV_FILE"
    exit 1
fi

# Validação das variáveis obrigatórias
if [[ -z "$ip" || -z "$mascara" || -z "$gateway" || -z "$dns" ]]; then
    echo "❌ Variáveis ip, mascara, gateway ou dns não definidas no .env"
    exit 1
fi

# Validação básica da máscara
if ! [[ "$mascara" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}$ ]]; then
    echo "❌ Máscara de sub-rede inválida: $mascara"
    exit 1
fi

# Conversão de máscara para CIDR
CIDR=$(mask_to_cidr "$mascara")
if [ -z "$CIDR" ]; then
    echo "❌ Falha ao converter a máscara $mascara para CIDR"
    exit 1
fi
IP_CIDR="${ip}/${CIDR}"

# Interface cabeada
interfaces=$(ls /sys/class/net | grep -E '^eth|^en' | grep -v lo)

echo "🔄 Ativando interfaces..."
for iface in $interfaces; do
    sudo ip link set "$iface" up
    sleep 0.5
done

# Procura interface com cabo
echo "🔍 Buscando interface com cabo conectado..."
for iface in $interfaces; do
    carrier="/sys/class/net/$iface/carrier"
    if [ -f "$carrier" ] && [ "$(cat $carrier)" -eq 1 ]; then
        echo "✅ Cabo conectado em $iface"

        # Ignora se já foi usada
        if [ -f "$LAST_INTERFACE_FILE" ]; then
            last_iface=$(cat "$LAST_INTERFACE_FILE")
            if [ "$iface" = "$last_iface" ]; then
                echo "🔁 Interface já configurada anteriormente: $iface"
                echo "🕓 Conclusão: $(date '+%Y-%m-%d %H:%M:%S')"
                exit 0
            fi
        fi

        echo "$iface" | sudo tee "$LAST_INTERFACE_FILE" > /dev/null

        # Desativa YAML padrão do instalador
        if [ -f "$INSTALLER_YAML" ]; then
            echo "📦 Backup do arquivo do instalador..."
            sudo mv "$INSTALLER_YAML" "${INSTALLER_YAML}.bkp"
        fi

        echo "🧹 Removendo Netplans antigos..."
        sudo rm -f /etc/netplan/99-*.yaml

        # Geração do Netplan com estrutura compatível com Ubuntu 24.04
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
        } | sudo tee "$config_file" > /dev/null

        sudo chmod 600 "$config_file"

        echo "🔎 Validando com netplan generate..."
        if sudo netplan generate; then
            echo "✅ Configuração válida. Aplicando..."
            sudo netplan apply

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
