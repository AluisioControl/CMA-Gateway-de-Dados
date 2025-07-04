#!/bin/bash

ENV_FILE="/home/cma/CMA-Gateway-de-Dados/src/.env"
CONF_FILE="/home/cma/fluent-bit.conf"
TEMP_FILE="/home/cma/fluent-bit.conf.tmp"

# Carrega .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "❌ .env não encontrado: $ENV_FILE"; exit 1
fi

if [ -z "$LOG_SERVER_HOST" ] || [ -z "$LOG_SERVER_PORT" ]; then
    echo "❌ Variáveis LOG_SERVER_HOST ou LOG_SERVER_PORT ausentes no .env"
    exit 1
fi

# Remove todos os blocos [OUTPUT] com name loki
awk '
BEGIN { output=1 }
/^\[OUTPUT\]/     { block=1; buffer="" }
/^\[OUTPUT\]/,/^\[.*\]/ {
    buffer = buffer $0 "\n"
    if ($0 ~ /name[ \t]+loki/) output=0
    if ($0 ~ /^\[.*\]/ && !($0 ~ /^\[OUTPUT\]/)) {
        if (output) printf "%s", buffer
        block=0; output=1
    }
    next
}
{ if (!block) print }
' "$CONF_FILE" > "$TEMP_FILE"

# Adiciona o novo bloco [OUTPUT] para Loki
cat <<EOF >> "$TEMP_FILE"

[OUTPUT]
    Name   loki
    Match  service.**
    Host   $LOG_SERVER_HOST
    Port   $LOG_SERVER_PORT
    TLS    On
    TLS.Verify Off
    Labels agent=fluent-bit,service_name=\$service_name,log_type=\$log_type
    Remove_Keys service_name,log_type
EOF

# Substitui o arquivo original
mv "$TEMP_FILE" "$CONF_FILE"
echo "✅ fluent-bit.conf atualizado com bloco único para Loki."

# Reinicia o serviço
if systemctl list-units --type=service | grep -q fluent-bit; then
    sudo systemctl restart fluent-bit && echo "✅ Serviço Fluent Bit reiniciado."
else
    echo "⚠️  Serviço fluent-bit não detectado. Reinicie manualmente se necessário."
fi

