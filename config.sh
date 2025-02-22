#!/bin/bash

CONFIG_FILE="src/config.ini"

# Função para exibir as configurações atuais
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
update_config() {
    local section=$1
    local keys=($(crudini --get "$CONFIG_FILE" "$section" | cut -d '=' -f1))
    for key in "${keys[@]}"; do
        current_value=$(crudini --get "$CONFIG_FILE" "$section" "$key" 2>/dev/null)
        read -p "Digite o novo valor para $key (atual: $current_value): " value
        crudini --set "$CONFIG_FILE" "$section" "$key" "$value"
    done
}

# Função principal para menu
menu() {
    while true; do
        echo "***********************************************************************"
        echo " BEM-VINDO(A) AO CONFIGURADOR DO GATWAY CMA WEB"
        echo "***********************************************************************"
        echo ""
        echo "Digite o número correspondente à configuração que deseja fazer:"
        echo "[1] - Configurar placa de rede"
        echo "[2] - Configurar o nome do Gateway"
        echo "[3] - Configurar parâmetros do RabbitMq"
        echo "[0] - Sair"
        read -p "Opção: " option

        case $option in
            1)
                section="config_rede"
                ;;
            2)
                section="config_cma_gateway"
                ;;
            3)
                section="config_rabbitmq"
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
    echo "ATENÇÃO: Há configurações incompletas!"
else
    cd src
    python3 run.py &
fi

menu

