
#!/bin/bash

LOG_FILE="/var/log/exec_reconcile.log"
echo "🕓 $(date '+%Y-%m-%d %H:%M:%S') - Iniciando execução" >> "$LOG_FILE"

# Adiciona o diretório correto ao PATH
export PATH="$PATH:/home/cma/.local/bin"

# Detecta o caminho do uv
UV_PATH="$(command -v uv)"
if [ -z "$UV_PATH" ]; then
  echo "❌ uv não encontrado no PATH" >> "$LOG_FILE"
  exit 1
fi

cd /home/cma/Reconcile-CMA-Gateway-de-Dados || {
  echo "❌ Não foi possível entrar no diretório do projeto" >> "$LOG_FILE"
  exit 1
}

echo "🚀 Executando collect_cma_web..." >> "$LOG_FILE"
$UV_PATH run python -m app.collect_cma_web >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Erro ao executar app.collect_cma_web" >> "$LOG_FILE"
fi

echo "🚀 Executando reconcile2.main..." >> "$LOG_FILE"
$UV_PATH run python -m app.reconcile2.main >> "$LOG_FILE" 2>&1
if [ $? -ne 0 ]; then
    echo "❌ Erro ao executar app.reconcile2.main" >> "$LOG_FILE"
fi

echo "✅ Execução finalizada em $(date '+%Y-%m-%d %H:%M:%S')" >> "$LOG_FILE"
