#!/bin/bash

# Caminhos definidos
ENV_FILE="/home/cma/CMA-Gateway-de-Dados/src/.env"
CONF_FILE="/home/cma/Loki/fluent-bit.conf"

# Carrega variáveis do .env
if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "❌ Arquivo .env não encontrado: $ENV_FILE"
    exit 1
fi

# Verificação das variáveis
if [ -z "$LOG_SERVER_HOST" ] || [ -z "$LOG_SERVER_PORT" ]; then
    echo "❌ Variáveis LOKI_HOST ou LOKI_PORT não definidas no .env"
    exit 1
fi

# Teste de conectividade (opcional, mas recomendado)
if ! curl -s --connect-timeout 3 "https://$LOG_SERVER_HOST:$LOG_SERVER_PORT/loki/api/v1/status/buildinfo" | grep -q "version"; then
    echo "⚠️  Não foi possível conectar ao Loki em https://$LOG_SERVER_HOST:$LOG_SERVER_PORT"
    echo "Verifique se o servidor está acessível e se o certificado é válido."
    # exit 1  # Descomente esta linha se quiser abortar o script caso o teste falhe
else
    echo "✅ Conectividade com Loki verificada!"
fi

# Atualiza ou insere o bloco OUTPUT loki
awk -v host="$LOG_SERVER_HOST" -v port="$LOG_SERVER_PORT" '
BEGIN { skip=0; output_written=0 }
/^\[OUTPUT\]/ { block=""; skip=0 }
/^\[OUTPUT\]/, /^\[/ {
    block = block $0 "\n"
    if ($0 ~ /name[ \t]+loki/) {
        skip=1
    }
    next
}
/^\[/ && output_written==0 && skip==1 {
    print "[OUTPUT]"
    print "    name   loki"
    print "    match  service.**"
    print "    host   " host
    print "    port   " port
    print "    tls    on"
    print "    tls.verify off"
    print "    labels agent=fluent-bit,service_name=$service_name,log_type=$log_type"
    print "    remove_keys service_name,log_type"
    output_written=1
}
skip==0 { print }
END {
    if (output_written==0) {
        print "[OUTPUT]"
        print "    name   loki"
        print "    match  service.**"
        print "    host   " host
        print "    port   " port
        print "    tls    on"
        print "    tls.verify off"
        print "    labels agent=fluent-bit,service_name=$service_name,log_type=$log_type"
        print "    remove_keys service_name,log_type"
    }
}
' "$CONF_FILE" > "${CONF_FILE}.tmp" && mv "${CONF_FILE}.tmp" "$CONF_FILE"

echo "✅ Arquivo fluent-bit.conf atualizado com sucesso."

# Reinício do Fluent Bit — modifique se estiver usando outro modo de execução
if systemctl list-units --type=service | grep -q fluent-bit; then
    sudo systemctl restart fluent-bit && echo "✅ Serviço Fluent Bit reiniciado."
else
    echo "⚠️  Serviço fluent-bit não detectado pelo systemd. Reinicie manualmente se necessário."
fi
