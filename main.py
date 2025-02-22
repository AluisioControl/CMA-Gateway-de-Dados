###############################################################
# main.py
# ------------------------------------------------------------
# Arquivo principal da API do Middleware
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2024
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################

from sqlalchemy import create_engine, Column, Integer, String, Float, select
from sqlalchemy.exc import SQLAlchemyError
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import *
import sqlite3
from fastapi import FastAPI
from datetime import datetime
from functions import *
from contextlib import asynccontextmanager
from dotenv import load_dotenv
import os


# Carrega as variáveis do arquivo .env
load_dotenv()

# ------------------------------------------------------------
# Inicialização do app
# ------------------------------------------------------------

#inicialização das threads principais
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Inicialização
    await database.connect()
    start_service_checker()


    yield  # Aguarda até o término do ciclo de vida do app

    # Finalização
    await database.disconnect()
    stop_event.set()  # Sinaliza a thread para parar

# Configuração/ Instaciação da API
app = FastAPI(
    title="API Teste - CMA WEB",
    description="Esta API permite realizar operações CRUD em um banco de dados SQLite e dispara mensagens conforme alterações.",
    version="1.0.0",
    lifespan=lifespan
)

# Definição do servidor onde irá rodar a aplicação
origins = [
    "http://localhost:8000",
]

# Prevenção de erro de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ------------------------------------------------------------
# Endpoints da API
# ------------------------------------------------------------

@app.get(
    "/cma_status",
    tags=["CMA"],
    response_model=str,
    summary="Serviço CMA",
    description="Verifica se o servidor CMA está online ou offline",
)

async def get_service_status():
    return str(get_server_status_cma())

@app.get(
    "/scada_status",
    tags=["SCADA"],
    response_model=str,
    summary="Serviço SCADA-LTS",
    description="Verifica se o servidor SCADA-LTS está online ou offline",
)

async def get_service_status():
    return str(get_server_status_scada()) 

###########################################################
################### CMA GATEWAY API #######################
###########################################################

@app.post(
    "/Cadastro_Gateway/",
    tags=["Cadastro Gateway"],
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: cma_gateway_API):
    """
    Adiciona um novo Gateway ao banco de dados.

    - **xid_gateway**: Identificador Gateway
    - **subestacao**: Nome da subestação
    - **regional**: Nome da regional
    - **host**: identificação do host (xxx.xxx.xxx.xxx)
    - **status: definição do status (false ou true)
    """
    async with database.transaction():
        query = cma_gateway.__table__.insert().values(
            xid_gateway=item.xid_gateway,
            subestacao=item.subestacao,
            regional=item.regional,
            host=item.host,
            status=item.status
        )
        try:
            item_id = await database.execute(query)
            return {"id": item_id, "message": "Item criado com sucesso!"}
        except sqlite3.IntegrityError as e:
            logger.error(f"Erro ao criar item: {e}")
            # Verifica se o erro é devido à violação de UNIQUE constraint
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Item com este ID já existe no banco de dados.",
                )
            raise HTTPException(
                status_code=500, detail="Erro inesperado ao criar item."
            )


@app.get(
    "/Cadastro_Gateway/{item_id}",
    tags=["Cadastro Gateway"],
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: str):
    """
    Retorna os detalhes de um Gateway pelo ID.

    - **item_id**: ID do item
    """
    query = cma_gateway.__table__.select().where(
        cma_gateway.__table__.c.xid_gateway == item_id)
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Cadastro_Gateway/{item_id}",
    tags=["Cadastro Gateway"],
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: str, item: cma_gateway_API):
    """
    Atualiza os detalhes de um Gateway existente.

    - **xid_gateway**: Identificador Gateway
    - **subestacao**: Nome da subestação
    - **regional**: Nome da regional
    - **host**: identificação do host (xxx.xxx.xxx.xxx)
    - **status: definição do status (0 ou 1)
    """
    query = (
        cma_gateway.__table__.update()
        .where(cma_gateway.__table__.c.xid_gateway == item_id)
        .values(
            xid_gateway=item.xid_gateway,
            subestacao=item.subestacao,
            regional=item.regional,
            host=item.host,
            status=item.status
        )
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Cadastro_Gateway/{item_id}",
    tags=["Cadastro Gateway"],
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: str):
    """
    Exclui um Gateway do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = cma_gateway.__table__.delete().where(
        cma_gateway.__table__.c.xid_gateway == item_id)
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")



###########################################################
################## EQUIPAMENTOS MODBUS IP #################
###########################################################

@app.post(
    "/Equipamentos_Modbus_IP/",
    tags=["Equipamentos Modbus IP"],
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datasource_modbus_ip_API):
    """
    Adiciona um novo Equipamento ao banco de dados.

    - **xid_equip**: XID do Equipamento
    - **updatePeriodType**: Valor de update
    - **transportType**: Valor de transportType
    - **maxReadBitCount**: Valor de maxReadBitCount
    - **maxReadRegisterCount**: valor de maxReadRegisterCount
    - **maxWriteRegisterCount**: Valor de maxWriteRegisterCount
    - **host**: Identificação do host (xxx.xxx.xxx.xxx)
    - **port**: Número da porta
    - **retries**: Valor de tentativas
    - **timeout**: Valor de timeout
    - **updatePeriods**: Valor de updatePeriods
    """

    async with database.transaction():
        query = datasource_modbus_ip.__table__.insert().values(
            xid_equip=item.xid_equip,
            xid_gateway=item.xid_gateway,
            fabricante=item.fabricante,
            marca=item.marca,
            modelo=item.modelo,
            type=item.type,
            sap_id=item.sap_id,
            enabled=item.enabled,
            updatePeriodType=item.updatePeriodType,
            maxReadBitCount=item.maxReadBitCount,
            maxReadRegisterCount=item.maxReadRegisterCount,
            maxWriteRegisterCount=item.maxWriteRegisterCount,
            host=item.host,
            port=item.port,
            retries=item.retries,
            timeout=item.timeout,
            updatePeriods=item.updatePeriods,
        )

        try:
            item_id = await database.execute(query)

            raw_data = (
                'callCount=1\n'
                'page=/Scada-LTS/import_project.htm\n'
                'httpSessionId=\n'
                'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
                'c0-scriptName=EmportDwr\n'
                'c0-methodName=importData\n'
                'c0-id=0\n'
                'c0-param0=string:{"dataSources":[{"xid":"' +
                str(item.xid_equip) + '", '
                '"type":"MODBUS_IP", "alarmLevels":{"POINT_WRITE_EXCEPTION":"URGENT", '
                '"DATA_SOURCE_EXCEPTION":"URGENT", "POINT_READ_EXCEPTION":"URGENT"}, '
                '"updatePeriodType":"' + str(item.updatePeriodType) + '", '
                '"transportType":"TCP", '
                '"contiguousBatches":false, "createSlaveMonitorPoints":false, '
                '"createSocketMonitorPoint":false, '
                '"enabled":' + str(item.enabled).lower() + ', '
                '"encapsulated":false, '
                '"host":"' + str(item.host) + '", '
                f'"maxReadBitCount":{item.maxReadBitCount}, '
                f'"maxReadRegisterCount":{item.maxReadRegisterCount}, '
                f'"maxWriteRegisterCount":{item.maxWriteRegisterCount}, '
                '"name":"' + str(item.xid_equip) + '", '
                f'"port":{item.port}, '
                '"quantize":false, '
                f'"retries":{item.retries}, '
                f'"timeout":{item.timeout}, '
                f'"updatePeriods":{item.updatePeriods}'
                '}]}\n'
                'batchId=8\n'
            )
            auth_ScadaLTS()
            send_data_to_scada(raw_data)
            return {"id": item_id, "message": "Item criado com sucesso!"}

        except sqlite3.IntegrityError as e:
            # Verifica se o erro é devido à violação de UNIQUE constraint
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Item com este ID já existe no banco de dados.",
                )
            raise HTTPException(
                status_code=500, detail="Erro inesperado ao criar item."
            )


@app.get(
    "/Equipamentos_Modbus_IP/{item_id}",
    tags=["Equipamentos Modbus IP"],
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: str):
    """
    Retorna os detalhes de um Equipamento pelo ID.

    - **xid_equip**: ID do item
    """
    query = datasource_modbus_ip.__table__.select().where(
        datasource_modbus_ip.__table__.c.xid_equip == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário

@app.put(
    "/Equipamentos_Modbus_IP/{item_id}",
    tags=["Equipamentos Modbus IP"],
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: str, item: datasource_modbus_ip_API):
    """
    Atualiza os detalhes de um Equipamento existente.

    - **xid_equip**: XID do Equipamento
    - **updatePeriodType**: Valor de update
    - **transportType**: Valor de transportType
    - **maxReadBitCount**: Valor de maxReadBitCount
    - **maxReadRegisterCount**: valor de maxReadRegisterCount
    - **maxWriteRegisterCount**: Valor de maxWriteRegisterCount
    - **host**: Identificação do host (xxx.xxx.xxx.xxx)
    - **port**: Número da porta
    - **retries**: Valor de tentativas
    - **timeout**: Valor de timeout
    - **updatePeriods**: Valor de updatePeriods
    """
    query = (
        datasource_modbus_ip.__table__.update()
        .where(datasource_modbus_ip.__table__.c.xid_equip == item_id)
        .values(
            xid_equip=item.xid_equip,
            xid_gateway=item.xid_gateway,
            fabricante=item.fabricante,
            marca=item.marca,
            modelo=item.modelo,
            type=item.type,
            sap_id=item.sap_id,
            enabled=item.enabled,
            updatePeriodType=item.updatePeriodType,
            maxReadBitCount=item.maxReadBitCount,
            maxReadRegisterCount=item.maxReadRegisterCount,
            maxWriteRegisterCount=item.maxWriteRegisterCount,
            host=item.host,
            port=item.port,
            retries=item.retries,
            timeout=item.timeout,
            updatePeriods=item.updatePeriods,
        )
    )
    result = await database.execute(query)

    if result:
        raw_data = (
            'callCount=1\n'
            'page=/Scada-LTS/import_project.htm\n'
            'httpSessionId=\n'
            'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
            'c0-scriptName=EmportDwr\n'
            'c0-methodName=importData\n'
            'c0-id=0\n'
            'c0-param0=string:{"dataSources":[{"xid":"' +
            str(item.xid_equip) + '", '
            '"type":"MODBUS_IP", "alarmLevels":{"POINT_WRITE_EXCEPTION":"URGENT", '
            '"DATA_SOURCE_EXCEPTION":"URGENT", "POINT_READ_EXCEPTION":"URGENT"}, '
            '"updatePeriodType":"' + str(item.updatePeriodType) + '", '
            '"transportType":"TCP", '
            '"contiguousBatches":false, "createSlaveMonitorPoints":false, '
            '"createSocketMonitorPoint":false, '
            '"enabled":' + str(item.enabled).lower() + ', '
            '"encapsulated":false, '
            '"host":"' + str(item.host) + '", '
            f'"maxReadBitCount":{item.maxReadBitCount}, '
            f'"maxReadRegisterCount":{item.maxReadRegisterCount}, '
            f'"maxWriteRegisterCount":{item.maxWriteRegisterCount}, '
            '"name":"' + str(item.xid_equip) + '", '
            f'"port":{item.port}, '
            '"quantize":false, '
            f'"retries":{item.retries}, '
            f'"timeout":{item.timeout}, '
            f'"updatePeriods":{item.updatePeriods}'
            '}]}\n'
            'batchId=8\n'
        )
        auth_ScadaLTS()
        send_data_to_scada(raw_data)
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")

@app.delete(
    "/Equipamentos_Modbus_IP/{item_id}",
    tags=["Equipamentos Modbus IP"],
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: str):
    """
    Exclui um Equipamento do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datasource_modbus_ip.__table__.delete().where(
        datasource_modbus_ip.__table__.c.xid_equip == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")



###########################################################
################## REGISTRADORES MODBUS ###################
###########################################################

@app.post(
    "/Registradores_Modbus_IP/",
    tags=["Registradores Modbus IP"],
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datapoints_modbus_ip_API):
    """
    Adiciona um novo Registrador ao banco de dados.

    - **xid_sensor**: Identificador xid_sensor
    - **range**: Valor do range
    - **modbusDataType**: Tipo de dado do modbus
    - **additive**: Valor additive
    - **offset**: Valor do offset
    - **bit**: Valor do bit
    - **charset**: Tipo de charset
    - **multiplier**: Valor de multiplier
    - **slaveId**: Valor de slaveId
    - **enabled**: Valor enabled
    - **nome**: Infformação do nome
    - **tipo**: Tipo
    - **classificacao**: Classificação
    """
    async with database.transaction():
        query = datapoints_modbus_ip.__table__.insert().values(
            xid_sensor=item.xid_sensor,
            xid_equip=item.xid_equip,
            range=item.range,
            modbusDataType=item.modbusDataType,
            additive=item.additive,
            offset=item.offset,
            bit=item.bit,
            multiplier=item.multiplier,
            slaveId=item.slaveId,
            enabled=item.enabled,
            nome=item.nome,
            tipo=item.tipo,
            classificacao=item.classificacao,
        )
        try:
            item_id = await database.execute(query)
            raw_data = (
                'callCount=1\n'
                'page=/Scada-LTS/import_project.htm\n'
                'httpSessionId=\n'
                'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
                'c0-scriptName=EmportDwr\n'
                'c0-methodName=importData\n'
                'c0-id=0\n'
                'c0-param0=string:{"dataPoints":[{"xid":"' +
                str(item.xid_sensor) + '",'
                '"loggingType":"ON_CHANGE",'
                '"intervalLoggingPeriodType":"MINUTES",'
                '"intervalLoggingType":"INSTANT",'
                '"purgeType":"YEARS",'
                '"pointLocator":{"range":"' + str(item.range) + '",'
                '"modbusDataType":"' + str(item.modbusDataType) + '",'
                f'"additive":{item.additive},'
                f'"bit":{item.bit},'
                '"charset":"ASCII",'
                f'"multiplier":{item.multiplier},'
                f'"offset":{item.offset},'
                '"registerCount":0,"settableOverride":false,'
                f'"slaveId":{item.slaveId},'
                '"slaveMonitor":false,"socketMonitor":false},'
                '"eventDetectors":[],"engineeringUnits":"","purgeStrategy":"PERIOD",'
                '"chartColour":null,"chartRenderer":null,"dataSourceXid":"' +
                str(item.xid_equip) + '",'
                '"defaultCacheSize":1,"description":null,"deviceName":"' +
                str(item.xid_sensor) + '",'
                '"discardExtremeValues":false,"discardHighLimit":1.7976931348623157,'
                '"discardLowLimit":-1.7976931348623157,'
                '"enabled":' + str(item.enabled).lower() + ', '
                '"eventTextRenderer"'
                ':{"type":"EVENT_NONE"},"intervalLoggingPeriod":15,"name":"' +
                str(item.nome) + '","purgePeriod":1,'
                '"purgeValuesLimit":100,"textRenderer":{"type":"PLAIN","suffix":""},"tolerance":0}]}\n'
                'batchId=8\n'
            )
            auth_ScadaLTS()
            send_data_to_scada(raw_data)
            return {"id": item_id, "message": "Item criado com sucesso!"}
        except sqlite3.IntegrityError as e:
            # Verifica se o erro é devido à violação de UNIQUE constraint
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Item com este ID já existe no banco de dados.",
                )
            raise HTTPException(
                status_code=500, detail="Erro inesperado ao criar item."
            )

@app.get(
    "/Registradores_Modbus_IP/{item_id}",
    tags=["Registradores Modbus IP"],
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: str):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = datapoints_modbus_ip.__table__.select().where(
        datapoints_modbus_ip.__table__.c.xid_sensor == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário

@app.put(
    "/Registradores_Modbus_IP/{item_id}",
    tags=["Registradores Modbus IP"],
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: str, item: datapoints_modbus_ip_API):
    """
    Atualiza os detalhes de um item existente.

    - **xid_sensor**: Identificador xid_sensor
    - **range**: Valor do range
    - **modbusDataType**: Tipo de dado do modbus
    - **additive**: Valor additive
    - **offset**: Valor do offset
    - **bit**: Valor do bit
    - **charset**: Tipo de charset
    - **multiplier**: Valor de multiplier
    - **slaveId**: Valor de slaveId
    - **enabled**: Valor enabled
    - **nome**: Infformação do nome
    - **tipo**: Tipo
    - **classificacao**: Classificação
    """
    query = (
        datapoints_modbus_ip.__table__.update()
        .where(datapoints_modbus_ip.__table__.c.xid_sensor == item_id)
        .values(
            xid_sensor=item.xid_sensor,
            xid_equip=item.xid_equip,
            range=item.range,
            modbusDataType=item.modbusDataType,
            additive=item.additive,
            offset=item.offset,
            bit=item.bit,
            multiplier=item.multiplier,
            slaveId=item.slaveId,
            enabled=item.enabled,
            nome=item.nome,
            tipo=item.tipo,
            classificacao=item.classificacao,
        )
    )
    result = await database.execute(query)

    if result:
        raw_data = (
            'callCount=1\n'
            'page=/Scada-LTS/import_project.htm\n'
            'httpSessionId=\n'
            'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
            'c0-scriptName=EmportDwr\n'
            'c0-methodName=importData\n'
            'c0-id=0\n'
            'c0-param0=string:{"dataPoints":[{"xid":"' +
            str(item.xid_sensor) + '",'
            '"loggingType":"ON_CHANGE",'
            '"intervalLoggingPeriodType":"MINUTES",'
            '"intervalLoggingType":"INSTANT",'
            '"purgeType":"YEARS",'
            '"pointLocator":{"range":"' + str(item.range) + '",'
            '"modbusDataType":"' + str(item.modbusDataType) + '",'
            f'"additive":{item.additive},'
            f'"bit":{item.bit},'
            '"charset":"ASCII",'
            f'"multiplier":{item.multiplier},'
            f'"offset":{item.offset},'
            '"registerCount":0,"settableOverride":false,'
            f'"slaveId":{item.slaveId},'
            '"slaveMonitor":false,"socketMonitor":false},'
            '"eventDetectors":[],"engineeringUnits":"","purgeStrategy":"PERIOD",'
            '"chartColour":null,"chartRenderer":null,"dataSourceXid":"' +
            str(item.xid_equip) + '",'
            '"defaultCacheSize":1,"description":null,"deviceName":"' +
            str(item.xid_sensor) + '",'
            '"discardExtremeValues":false,"discardHighLimit":1.7976931348623157,'
            '"discardLowLimit":-1.7976931348623157,'
            '"enabled":' + str(item.enabled).lower() + ', '
            '"eventTextRenderer"'
            ':{"type":"EVENT_NONE"},"intervalLoggingPeriod":15,"name":"' +
            str(item.nome) + '","purgePeriod":1,'
            '"purgeValuesLimit":100,"textRenderer":{"type":"PLAIN","suffix":""},"tolerance":0}]}\n'
            'batchId=8\n'
        )
        auth_ScadaLTS()
        send_data_to_scada(raw_data)
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")

@app.delete(
    "/Registradores_Modbus_IP/{item_id}",
    tags=["Registradores Modbus IP"],
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: str):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datapoints_modbus_ip.__table__.delete().where(
        datapoints_modbus_ip.__table__.c.xid_sensor == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")



###########################################################
##################### EQUIPAMENTOS DNP3 ###################
###########################################################

@app.post(
    "/Equipamentos_DNP3/",
    tags=["Equipamentos DNP3"],
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datasource_dnp3_API):
    """
    Adiciona um novo item ao banco de dados.

    - **xid_equip**: Valor de xid_equip
    - **eventsPeriodType**: Valor de eventsPeriodType
    - **host**: Identificação do host
    - **port**: Valor da porta
    - **rbePollPeriods**: Valor de rbePollPeriods
    - **retries**: Valor de retries
    - **slaveAddress**: Valor de slaveAddress
    - **sourceAddress**: Valor de sourceAddress
    - **staticPollPeriods**: Valor de staticPollPeriods
    - **synchPeriods**: Valor de  synchPeriods
    - **timeout**: Valor de timeout
    """
    async with database.transaction():
        query = datasource_dnp3.__table__.insert().values(
            xid_equip=item.xid_equip,
            xid_gateway=item.xid_gateway,
            fabricante=item.fabricante,
            marca=item.marca,
            modelo=item.modelo,
            type=item.type,
            sap_id=item.sap_id,
            enabled=item.enabled,
            eventsPeriodType=item.eventsPeriodType,
            host=item.host,
            port=item.port,
            rbePollPeriods=item.rbePollPeriods,
            retries=item.retries,
            slaveAddress=item.slaveAddress,
            sourceAddress=item.sourceAddress,
            staticPollPeriods=item.staticPollPeriods,
            timeout=item.timeout,
        )
        try:
            item_id = await database.execute(query)
            raw_data = (
                'callCount=1\n'
                'page=/Scada-LTS/import_project.htm\n'
                'httpSessionId=\n'
                'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
                'c0-scriptName=EmportDwr\n'
                'c0-methodName=importData\n'
                'c0-id=0\n'
                'c0-param0=string:{"dataSources":[{"xid":"' +
                str(item.xid_equip) + '",'
                '"type":"' + str(item.type) + '",'
                '"alarmLevels":{"DATA_SOURCE_EXCEPTION":"URGENT","POINT_READ_EXCEPTION":"URGENT"},'
                '"eventsPeriodType":"' + str(item.eventsPeriodType) + '",'
                '"enabled":' + str(item.enabled).lower() +','
                '"host":"' + str(item.host) + '","name":"' +
                str(item.xid_equip) + '",'
                f'"port":{item.port},'
                '"quantize":false,'
                f'"rbePollPeriods":{item.rbePollPeriods},'
                f'"retries":{item.retries},'
                f'"slaveAddress":{item.slaveAddress},'
                f'"sourceAddress":{item.sourceAddress},'
                f'"staticPollPeriods":{item.staticPollPeriods},'
                f'"synchPeriods":30,'
                '"timeout":800}]}\n'
                'batchId=8\n'
            )
            auth_ScadaLTS()
            send_data_to_scada(raw_data)
            return {"id": item_id, "message": "Item criado com sucesso!"}
        except sqlite3.IntegrityError as e:
            # Verifica se o erro é devido à violação de UNIQUE constraint
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Item com este ID já existe no banco de dados.",
                )
            raise HTTPException(
                status_code=500, detail="Erro inesperado ao criar item."
            )

@app.get(
    "/Equipamentos_DNP3/{item_id}",
    tags=["Equipamentos DNP3"],
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: str):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = datasource_dnp3.__table__.select().where(
        datasource_dnp3.__table__.c.xid_equip == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário

@app.put(
    "/Equipamentos_DNP3/{item_id}",
    tags=["Equipamentos DNP3"],
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: str, item: datasource_dnp3_API):
    """
    Atualiza os detalhes de um item existente.

    - **xid_equip**: Valor de xid_equip
    - **eventsPeriodType**: Valor de eventsPeriodType
    - **host**: Identificação do host
    - **port**: Valor da porta
    - **rbePollPeriods**: Valor de rbePollPeriods
    - **retries**: Valor de retries
    - **slaveAddress**: Valor de slaveAddress
    - **sourceAddress**: Valor de sourceAddress
    - **staticPollPeriods**: Valor de staticPollPeriods
    - **synchPeriods**: Valor de  synchPeriods
    - **timeout**: Valor de timeout
    """
    query = (
        datasource_dnp3.__table__.update()
        .where(datasource_dnp3.__table__.c.xid_equip == item_id)
        .values(
            xid_equip=item.xid_equip,
            xid_gateway=item.xid_gateway,
            fabricante=item.fabricante,
            marca=item.marca,
            modelo=item.modelo,
            type=item.type,
            sap_id=item.sap_id,
            enabled=item.enabled,
            eventsPeriodType=item.eventsPeriodType,
            host=item.host,
            port=item.port,
            rbePollPeriods=item.rbePollPeriods,
            retries=item.retries,
            slaveAddress=item.slaveAddress,
            sourceAddress=item.sourceAddress,
            staticPollPeriods=item.staticPollPeriods,
            timeout=item.timeout,
        )
    )
    result = await database.execute(query)
    if result:
        raw_data = (
            'callCount=1\n'
            'page=/Scada-LTS/import_project.htm\n'
            'httpSessionId=\n'
            'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
            'c0-scriptName=EmportDwr\n'
            'c0-methodName=importData\n'
            'c0-id=0\n'
            'c0-param0=string:{"dataSources":[{"xid":"' +
            str(item.xid_equip) + '",'
            '"type":"' + str(item.type) + '",'
            '"alarmLevels":{"DATA_SOURCE_EXCEPTION":"URGENT","POINT_READ_EXCEPTION":"URGENT"},'
            '"eventsPeriodType":"' + str(item.eventsPeriodType) + '",'
            '"enabled":' + str(item.enabled).lower() +','
            '"host":"' + str(item.host) + '","name":"' +
            str(item.xid_equip) + '",'
            f'"port":{item.port},'
            '"quantize":false,'
            f'"rbePollPeriods":{item.rbePollPeriods},'
            f'"retries":{item.retries},'
            f'"slaveAddress":{item.slaveAddress},'
            f'"sourceAddress":{item.sourceAddress},'
            f'"staticPollPeriods":{item.staticPollPeriods},'
            f'"synchPeriods":30,'
            '"timeout":800}]}\n'
            'batchId=8\n'
        )
        auth_ScadaLTS()
        send_data_to_scada(raw_data)
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")

@app.delete(
    "/Equipamentos_DNP3/{item_id}",
    tags=["Equipamentos DNP3"],
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: str):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datasource_dnp3.__table__.delete().where(
        datasource_dnp3.__table__.c.xid_equip == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")



###########################################################
######### SENSORES REGISTRADORES DNP3 DATAPOINTS ##########
###########################################################

@app.post(
    "/Registradores_DNP3/",
    tags=["Registradores DNP3"],
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datapoints_dnp3_API):
    """
    Adiciona um novo item ao banco de dados.

    - **xid_sensor**: Identificação do sensor
    - **dnp3DataType**:  Valor dnp3DataType
    - **controlCommand**: Valor de controlCommand
    - **index**: Valor Index
    - **timeoff**: Valor timeoff
    - **timeon**: Valor timeon
    """
    async with database.transaction():
        query = datapoints_dnp3.__table__.insert().values(
            xid_sensor=item.xid_sensor,
            xid_equip=item.xid_equip,
            dnp3DataType=item.dnp3DataType,
            controlCommand=item.controlCommand,
            index=item.index,
            timeoff=item.timeoff,
            timeon=item.timeon,
            enabled=item.enabled,
            nome=item.nome,
            tipo=item.tipo,
            classificacao=item.classificacao,
        )
        try:
            item_id = await database.execute(query)
            raw_data = (
                'callCount=1\n'
                'page=/Scada-LTS/import_project.htm\n'
                'httpSessionId=\n'
                'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
                'c0-scriptName=EmportDwr\n'
                'c0-methodName=importData\n'
                'c0-id=0\n'
                'c0-param0=string:{"dataPoints":[{"xid":"' +
                str(item.xid_sensor) + '",'
                '"loggingType":"ON_CHANGE",'
                '"intervalLoggingPeriodType":"MINUTES","intervalLoggingType":"INSTANT",'
                '"purgeType":"YEARS","pointLocator":{"additive":0.0,'
                f'"controlCommand":{item.controlCommand},'
                f'"dnp3DataType":{item.dnp3DataType},'
                f'"index":{item.index},'
                '"multiplier":1.0,"operateMode":2,"settable":false,'
                f'"timeOff":{item.timeoff},'
                f'"timeOn":{item.timeon}'
                '},"eventDetectors":[],"engineeringUnits":"",'
                '"purgeStrategy":"PERIOD","chartColour":null,"chartRenderer":null,'
                '"dataSourceXid":"' +
                str(item.xid_equip) +
                '","defaultCacheSize":1,"description":null,'
                '"deviceName":"' + str(item.xid_sensor) +
                '","discardExtremeValues":false,'
                '"discardHighLimit":1.7976931348623157,"discardLowLimit":-1.7976931348623157,'
                '"enabled":' + str(item.enabled).lower() +','
                '"eventTextRenderer":{"type":"EVENT_NONE"},"intervalLoggingPeriod":15,'
                '"name":"' +
                str(item.xid_sensor) +
                '","purgePeriod":1,"purgeValuesLimit":100,"textRenderer":'
                '{"type":"PLAIN","suffix":""},"tolerance":0.0}]}\n'
                'batchId=8\n'
            )
            return {"id": item_id, "message": "Item criado com sucesso!"}
        except sqlite3.IntegrityError as e:
            # Verifica se o erro é devido à violação de UNIQUE constraint
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Item com este ID já existe no banco de dados.",
                )
            raise HTTPException(
                status_code=500, detail="Erro inesperado ao criar item."
            )

@app.get(
    "/Registradores_DNP3/{item_id}",
    tags=["Registradores DNP3"],
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: str):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = datapoints_dnp3.__table__.select().where(
        datapoints_dnp3.__table__.c.xid_sensor == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário

@app.put(
    "/Registradores_DNP3/{item_id}",
    tags=["Registradores DNP3"],
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: str, item: datapoints_dnp3_API):
    """
    Atualiza os detalhes de um item existente.

    - **xid_sensor**: Identificação do sensor
    - **dnp3DataType**:  Valor dnp3DataType
    - **controlCommand**: Valor de controlCommand
    - **index**: Valor Index
    - **timeoff**: Valor timeoff
    - **timeon**: Valor timeon
    """
    query = (
        datapoints_dnp3.__table__.update()
        .where(datapoints_dnp3.__table__.c.xid_sensor == item_id)
        .values(
            xid_sensor=item.xid_sensor,
            xid_equip=item.xid_equip,
            dnp3DataType=item.dnp3DataType,
            controlCommand=item.controlCommand,
            index=item.index,
            timeoff=item.timeoff,
            timeon=item.timeon,
            enabled=item.enabled,
            nome=item.nome,
            tipo=item.tipo,
            classificacao=item.classificacao,
        )
    )
    result = await database.execute(query)
    if result:
        raw_data = (
            'callCount=1\n'
            'page=/Scada-LTS/import_project.htm\n'
            'httpSessionId=\n'
            'scriptSessionId=D15BC242A0E69D4251D5585A07806324697\n'
            'c0-scriptName=EmportDwr\n'
            'c0-methodName=importData\n'
            'c0-id=0\n'
            'c0-param0=string:{"dataPoints":[{"xid":"' +
            str(item.xid_sensor) + '",'
            '"loggingType":"ON_CHANGE",'
            '"intervalLoggingPeriodType":"MINUTES","intervalLoggingType":"INSTANT",'
            '"purgeType":"YEARS","pointLocator":{"additive":0.0,'
            f'"controlCommand":{item.controlCommand},'
            f'"dnp3DataType":{item.dnp3DataType},'
            f'"index":{item.index},'
            '"multiplier":1.0,"operateMode":2,"settable":false,'
            f'"timeOff":{item.timeoff},'
            f'"timeOn":{item.timeon}'
            '},"eventDetectors":[],"engineeringUnits":"",'
            '"purgeStrategy":"PERIOD","chartColour":null,"chartRenderer":null,'
            '"dataSourceXid":"' +
            str(item.xid_equip) + '","defaultCacheSize":1,"description":null,'
            '"deviceName":"' + str(item.xid_sensor) +
            '","discardExtremeValues":false,'
            '"discardHighLimit":1.7976931348623157,"discardLowLimit":-1.7976931348623157,'
            '"enabled":' + str(item.enabled).lower() +','
            '"eventTextRenderer":{"type":"EVENT_NONE"},"intervalLoggingPeriod":15,'
            '"name":"' +
            str(item.xid_sensor) +
            '","purgePeriod":1,"purgeValuesLimit":100,"textRenderer":'
            '{"type":"PLAIN","suffix":""},"tolerance":0.0}]}\n'
            'batchId=8\n'
        )
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")

@app.delete(
    "/Registradores_DNP3/{item_id}",
    tags=["Registradores DNP3"],
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: str):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datapoints_dnp3.__table__.delete().where(
        datapoints_dnp3.__table__.c.xid_sensor == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")



###########################################################
##################### TAGS EQUIPAMENTOS ###################
###########################################################

@app.post(
    "/Tags_equipamentos/",
    tags=["Tags equipamentos"],
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: eqp_tags_API):
    """
    Adiciona um novo item ao banco de dados.

    - **xid_equip**: Ideintificador xid_equip
    - **nome**: Nome
    - **valor**: Valor
    """
    async with database.transaction():
        query = eqp_tags.__table__.insert().values(
            xid_equip=item.xid_equip, nome=item.nome, valor=item.valor
        )
        try:
            item_id = await database.execute(query)
            return {"id": item_id, "message": "Item criado com sucesso!"}
        except sqlite3.IntegrityError as e:
            # Verifica se o erro é devido à violação de UNIQUE constraint
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Item com este ID já existe no banco de dados.",
                )
            raise HTTPException(
                status_code=500, detail="Erro inesperado ao criar item."
            )

@app.get(
    "/Tags_equipamentos/{item_id}",
    tags=["Tags equipamentos"],
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: str):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = eqp_tags.__table__.select().where(
        eqp_tags.__table__.c.xid_equip == item_id)
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário

@app.put(
    "/Tags_equipamentos/{item_id}",
    tags=["Tags equipamentos"],
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: str, item: eqp_tags_API):
    """
    Atualiza os detalhes de um item existente.

    - **xid_equip**: Ideintificador xid_equip
    - **nome**: Nome
    - **valor**: Valor
    """
    query = (
        eqp_tags.__table__.update()
        .where(eqp_tags.__table__.c.xid_equip == item_id)
        .values(xid_equip=item.xid_equip, nome=item.nome, valor=item.valor)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")

@app.delete(
    "/Tags_equipamentos/{item_id}",
    tags=["Tags equipamentos"],
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: str):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = eqp_tags.__table__.delete().where(
        eqp_tags.__table__.c.xid_equip == item_id)
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")



###########################################################
####################### TAGS SENSORES #####################
###########################################################

@app.post(
    "/Tags_sensores/",
    tags=["Tags sensores"],
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: dp_tags_API):
    """
    Adiciona um novo item ao banco de dados.

    - **xid_sensor**:
    - **nome**:
    - **valor**:
    """
    async with database.transaction():
        query = dp_tags.__table__.insert().values(
            xid_sensor=item.xid_sensor, nome=item.nome, valor=item.valor
        )
        try:
            item_id = await database.execute(query)
            return {"id": item_id, "message": "Item criado com sucesso!"}
        except sqlite3.IntegrityError as e:
            # Verifica se o erro é devido à violação de UNIQUE constraint
            if "UNIQUE constraint failed" in str(e):
                raise HTTPException(
                    status_code=400,
                    detail="Item com este ID já existe no banco de dados.",
                )
            raise HTTPException(
                status_code=500, detail="Erro inesperado ao criar item."
            )

@app.get(
    "/Tags_sensores/{item_id}",
    tags=["Tags sensores"],
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: str):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = dp_tags.__table__.select().where(
        dp_tags.__table__.c.xid_sensor == item_id)
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário

@app.put(
    "/Tags_sensores/{item_id}",
    tags=["Tags sensores"],
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: str, item: dp_tags_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        dp_tags.__table__.update()
        .where(dp_tags.__table__.c.xid_sensor == item_id)
        .values(xid_sensor=item.xid_sensor, nome=item.nome, valor=item.valor)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")

@app.delete(
    "/Tags_sensores/{item_id}",
    tags=["Tags sensores"],
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: str):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = dp_tags.__table__.delete().where(
        dp_tags.__table__.c.xid_sensor == item_id)
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


