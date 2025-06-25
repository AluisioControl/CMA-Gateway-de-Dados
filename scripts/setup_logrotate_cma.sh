#!/bin/bash

USER="cma"
GROUP="cma"
CONFIG_PATH="/etc/logrotate.d/cma_gateway_logs"
LOG_DIR_CMA="/home/cma/CMA-Gateway-de-Dados/logs"
LOG_DIR_RECONCILE="/home/cma/Reconcile-CMA-Gateway-de-Dados/logs"

echo "🔧 Criando configuração de logrotate em $CONFIG_PATH..."

sudo tee "$CONFIG_PATH" > /dev/null <<EOF
$LOG_DIR_CMA/cma_gateway.log {
    size 1G
    rotate 3
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su $USER $GROUP
}

$LOG_DIR_RECONCILE/scadalts_errors.log {
    size 1G
    rotate 3
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su $USER $GROUP
}

$LOG_DIR_RECONCILE/scadalts_info_warning.log {
    size 1G
    rotate 3
    compress
    delaycompress
    missingok
    notifempty
    copytruncate
    su $USER $GROUP
}
EOF

echo "✅ Configuração criada com sucesso."

echo "🚀 Testando logrotate manualmente..."
sudo logrotate -f "$CONFIG_PATH"

echo "✅ Logrotate testado. Verifique os arquivos nos diretórios:"
echo "   - $LOG_DIR_CMA"
echo "   - $LOG_DIR_RECONCILE"
