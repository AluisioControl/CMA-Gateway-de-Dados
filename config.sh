#!/bin/bash
#
# OBS: Instalar o pacote 'crudini' 
# sudo apt-get install -y crudini
#
CONFIG_FILE="src/config.ini"
#
# Função para exibir as configurações atuais
# Exibe as configurações atuais de uma seção do arquivo de configuração
#
# Args:
#     $1 (str): O nome da seção a ser exibida
#
# Returns:
#     None

display_config() {
    local section=$1
    echo "*************************************************"
    echo " Bem-vindo ao configurador de $section"
    echo "*************************************************"
    echo "As configurações atuais são:"
    
    # Obtém todas as chaves da seção e exibe seus valores
    local keys=($(crudini --get "$CONFIG_FILE" "$section" | cut -d '=' -f1))
    for key in "${keys[@]}"; do
        value=$(crudini --get "$CONFIG_FILE" "$section" "$key" 2>/dev/null)
        echo "$key = $value"
    done
    echo "--------------------------------------------------------------"
}

# Função para atualizar configurações
# Atualiza as configurações de uma seção do arquivo de configuração
#
# Args:
#     $1 (str): O nome da seção a ser atualizada
#
# Returns:
#     None
update_config() {
    local section=$1

    # Verifica se a seção existe no arquivo de configuração
    if ! crudini --get "$CONFIG_FILE" "$section" &>/dev/null; then
        echo "Erro: A seção '$section' não foi encontrada no arquivo de configuração!"
        exit 1
    fi

    local keys=($(crudini --get "$CONFIG_FILE" "$section" | cut -d '=' -f1))
    for key in "${keys[@]}"; do
        current_value=$(crudini --get "$CONFIG_FILE" "$section" "$key" 2>/dev/null)
        read -p "Digite o novo valor para $key (atual: $current_value): " value
        crudini --set "$CONFIG_FILE" "$section" "$key" "$value"
    done
    
    if [[ $section = "config_rede" ]]; then
        function validar_ip() {
            local ip=$1
            local regex='^([0-9]{1,3}\.){3}[0-9]{1,3}$'
            if [[ $ip =~ $regex ]]; then
                IFS='.' read -r -a octets <<< "$ip"
                for octet in "${octets[@]}"; do
                    if (( octet < 0 || octet > 255 )); then
                        return 1
                    fi
                done
                return 0
            fi
            return 1
        }

        function configurar_rede() {
            local ip=$1
            local mascara=$2
            local gateway=$3

            # Configura a rede para Linux e usa Netplan para persistir as configurações
            if [[ $(uname) == "Linux" ]]; then
                # Verifica se o arquivo de configuração do Netplan existe
                if [ ! -f "/etc/netplan/01-netcfg.yaml" ]; then
                    echo "Arquivo de configuração Netplan não encontrado!"
                    exit 1
                fi
                
                # Cria ou atualiza as configurações no arquivo Netplan
                echo "network:" > /etc/netplan/01-netcfg.yaml
                echo "  version: 2" >> /etc/netplan/01-netcfg.yaml
                echo "  renderer: networkd" >> /etc/netplan/01-netcfg.yaml
                echo "  ethernets:" >> /etc/netplan/01-netcfg.yaml
                echo "    eth0:" >> /etc/netplan/01-netcfg.yaml
                echo "      dhcp4: false" >> /etc/netplan/01-netcfg.yaml
                echo "      addresses: [$ip/$mascara]" >> /etc/netplan/01-netcfg.yaml
                echo "      routes:" >> /etc/netplan/01-netcfg.yaml
                echo "        - to: default" >> /etc/netplan/01-netcfg.yaml
                echo "          via: $gateway" >> /etc/netplan/01-netcfg.yaml

                # Ajusta as permissões para garantir que o arquivo não seja acessível por outros
                sudo chmod 600 /etc/netplan/01-netcfg.yaml

                # Aplica as novas configurações do Netplan
                sudo netplan apply

                # Exibe mensagem de sucesso
                echo "Configuração aplicada com sucesso!"
            else
                echo "Sistema operacional não suportado!"
                exit 1
            fi
        }

        if [[ ! -f $CONFIG_FILE ]]; then
            echo "Arquivo de configuração não encontrado!"
            exit 1
        fi

        IP=$(awk -F '=' '/ip/ {print $2}' $CONFIG_FILE | tr -d ' ')
        MASCARA=$(awk -F '=' '/mascara/ {print $2}' $CONFIG_FILE | tr -d ' ')
        GATEWAY=$(awk -F '=' '/gateway/ {print $2}' $CONFIG_FILE | tr -d ' ')

        if [[ -z $IP || -z $MASCARA || -z $GATEWAY ]]; then
            echo "Erro: Um ou mais parâmetros de rede estão ausentes no arquivo de configuração!"
            exit 1
        fi

        if ! validar_ip $IP || ! validar_ip $MASCARA || ! validar_ip $GATEWAY; then
            echo "Erro: Um ou mais parâmetros de rede são inválidos!"
            exit 1
        fi

        configurar_rede $IP $MASCARA $GATEWAY
    fi
}

# Função principal do menu de configuração
#
# Mostra ao usuário todas as opções de configuração e permite que ele escolha
# quaisquer alterações que deseja fazer.
#
# Args:
#     None
#
# Returns:
#     None
menu() {
    while true; do
        echo "***********************************************************************"
        echo " BEM-VINDO(A) AO CONFIGURADOR DO GATEWAY CMA WEB"
        echo "***********************************************************************"
        echo ""
        echo "Digite o número correspondente à configuração que deseja fazer:"
        echo "[1] - Configurar placa de rede"
        echo "[2] - Configurar o nome do Gateway"
        echo "[3] - Configurar parâmetros do RabbitMq"
        echo "[4] - Executar o CMA Gateway"
        echo "[0] - Sair"
        read -p "Opção: " option

        case $option in
            1)
                section="config_placa_rede"
                ;;
            2)
                section="config_cma_gateway"
                ;;
            3)
                section="config_rabbitmq"
                ;;
            4)
                cd src
                python3 main.py 
                ;;
            0)
                echo "Saindo..."
                exit 0
                ;;
            *)
                echo "Opção inválida, tente novamente."
                continue
                ;;
        esac

        display_config "$section"
        while true; do
            read -p "Deseja fazer alterações? (S/N): " choice
            case $choice in
                [Ss])
                    update_config "$section"
                    echo "Configurações atualizadas!"
                    echo ""
                    echo ""
                    break
                    ;;
                [Nn])
                    break
                    ;;
                *)
                    echo "Digite S - Sim ou N - Não"
                    ;;
            esac
        done
    done
}

# Verifica se todas as variáveis estão preenchidas, se sim, inicia o script python principal
if ! grep -q "=" "$CONFIG_FILE" || grep -q "= *$" "$CONFIG_FILE"; then
    echo ""
    echo "**** ATENÇÃO: Há configurações incompletas!  ****"
    echo " Revise todas as configurações antes de continuar."
else
    menu
fi


