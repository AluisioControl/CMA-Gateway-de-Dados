
import os
from dotenv import load_dotenv
import logging
import logging.handlers

# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

# Localização do arquivo de log 
LOG_LINUX   = os.getenv("LOG_LINUX")
LOG_WINDOWS = os.getenv("LOG_WINDOWS")

# Configuração do logging
log_formatter = logging.Formatter('[GATEWAY-CMA] %(asctime)s - %(levelname)s - %(funcName)s - %(message)s')

# Para salvar no arquivo em vez de usar SysLogHandler
log_handler = logging.FileHandler(LOG_LINUX)
log_handler.setFormatter(log_formatter)
logger = logging.getLogger()
logger.addHandler(log_handler)
logger.setLevel(logging.WARNING)  # Configura o nível mínimo para WARNING

# Teste de log
# logger.error("TESTE DE ERRO")
# logger.warning("TESTE DE WARNING")
# logger.error(f"Erro ao criar item: {e}")


