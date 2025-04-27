#!/bin/bash

SCRIPT_PATH="/home/cma/Scripts/exec_reconcile.sh"
SERVICE_NAME="exec_reconcile"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
TIMER_FILE="/etc/systemd/system/${SERVICE_NAME}.timer"

echo "🔧 Instalando timer systemd para: $SCRIPT_PATH"

# Verifica se o script existe
if [ ! -f "$SCRIPT_PATH" ]; then
  echo "❌ Erro: script não encontrado em $SCRIPT_PATH"
  exit 1
fi

# Garante permissão de execução
chmod +x "$SCRIPT_PATH"

# Cria o serviço
echo "📄 Criando $SERVICE_FILE"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Executa o script exec_reconcile.sh

[Service]
Type=oneshot
ExecStart=$SCRIPT_PATH
EOF

# Cria o timer
echo "⏱️  Criando $TIMER_FILE"
sudo tee "$TIMER_FILE" > /dev/null <<EOF
[Unit]
Description=Executa o script exec_reconcile.sh a cada 30 minutos

[Timer]
OnBootSec=5min
OnUnitActiveSec=30min
Unit=${SERVICE_NAME}.service
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Recarrega systemd
echo "🔄 Recarregando systemd..."
sudo systemctl daemon-reload

# Ativa e inicia o timer
echo "🚀 Ativando e iniciando o timer..."
sudo systemctl enable --now "${SERVICE_NAME}.timer"

# Verifica status
echo "✅ Timer instalado. Status atual:"
systemctl list-timers --all | grep "$SERVICE_NAME"
