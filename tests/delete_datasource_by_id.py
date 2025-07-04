import pycurl
from io import BytesIO
from dotenv import load_dotenv
import os
from logger import logger
from scadalts import auth_ScadaLTS

# Carrega variáveis do .env
load_dotenv()
URL_BASE = os.getenv("URL_BASE", "http://localhost:8080")

def delete_datasource_by_id(id_datasource):
    """
    Envia uma requisição POST ao Scada-LTS para deletar um datasource específico pelo ID.
    
    Args:
        id_datasource (int): ID numérico do datasource no Scada-LTS.
    
    Returns:
        bool: True se a exclusão foi bem-sucedida, False caso contrário.
    """
    url = f"{URL_BASE}/Scada-LTS/dwr/call/plaincall/DataSourceListDwr.deleteDataSource.dwr"
    buffer = BytesIO()

    raw_data = (
        f"callCount=1\n"
        f"page=/Scada-LTS/data_sources.shtm\n"
        f"httpSessionId=\n"
        f"scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n"
        f"c0-scriptName=DataSourceListDwr\n"
        f"c0-methodName=deleteDataSource\n"
        f"c0-id=0\n"
        f"c0-param0=number:{id_datasource}\n"
        f"batchId=8\n"
    )

    try:
        c = pycurl.Curl()
        c.setopt(pycurl.URL, url)
        c.setopt(pycurl.POST, 1)
        c.setopt(pycurl.COOKIEFILE, "cookies")  # Usa cookie de sessão já autenticado
        c.setopt(pycurl.POSTFIELDS, raw_data)
        c.setopt(pycurl.WRITEDATA, buffer)
        c.perform()

        status_code = c.getinfo(pycurl.RESPONSE_CODE)
        c.close()

        response = buffer.getvalue().decode('utf-8')
        print(f"Status code: {status_code}")
        print(f"Resposta:\n{response}")

        if status_code == 200 and "excluído" in response.lower():
            logger.info(f"Datasource ID {id_datasource} excluído com sucesso.")
            return True
        else:
            logger.warning(f"Falha ao excluir datasource ID {id_datasource}. Resposta: {response}")
            return False
    except Exception as e:
        logger.error(f"Erro ao excluir datasource ID {id_datasource}: {e}")
        return False
