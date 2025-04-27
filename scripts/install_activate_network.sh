#!/bin/bash

SERVICE_PATH="/etc/systemd/system/ativar-rede.service"
TIMER_PATH="/etc/systemd/system/ativar-rede.timer"
SCRIPT_PATH="/home/cma/CMA-Gateway-de-Dados/scripts/static_ip_all_final.sh"
LOG_FILE="/var/log/ativar-rede.log"

echo "🔧 Instalando serviço systemd para o script: $SCRIPT_PATH"

# Verifica se o script existe
if [ ! -f "$SCRIPT_PATH" ]; then
    echo "❌ Script não encontrado em: $SCRIPT_PATH"
    exit 1
fi

# Cria o .service
echo "📄 Criando $SERVICE_PATH"
sudo tee "$SERVICE_PATH" > /dev/null <<EOF
[Unit]
Description=Executa o script de ativação de rede com IP estático
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart=$SCRIPT_PATH
WorkingDirectory=/home/cma/CMA-Gateway-de-Dados/scripts
StandardOutput=journal
StandardError=journal
EOF

# Cria o .timer
echo "⏱️  Criando $TIMER_PATH"
sudo tee "$TIMER_PATH" > /dev/null <<EOF
[Unit]
Description=Timer para ativar rede com IP estático a cada minuto

[Timer]
OnBootSec=30
OnUnitActiveSec=1min
AccuracySec=5s
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Ativa e inicia o serviço e o timer
echo "🔄 Recarregando systemd..."
sudo systemctl daemon-reexec
sudo systemctl daemon-reload

echo "📌 Ativando serviço e timer..."
sudo systemctl enable ativar-rede.service
sudo systemctl enable ativar-rede.timer
sudo systemctl start ativar-rede.timer

# Executa manualmente uma primeira vez
echo "🚀 Executando o script agora para teste..."
sudo bash "$SCRIPT_PATH"


# Aguarda alguns segundos para o log ser gerado
sleep 2

# Exibe status e logs
echo -e "\n📋 Status do timer:"
systemctl list-timers --all | grep ativar-rede

echo -e "\n📄 Últimas linhas do log do script:"
sudo tail -n 20 "$LOG_FILE"
