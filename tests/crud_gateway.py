from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from databases import Database

# Configuração do SQLite e SQLAlchemy
DATABASE_URL = "sqlite:///./test_crud.db"
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI(
    title="API Teste - Control Engenharia",
    description="Esta API permite realizar operações CRUD em um banco de dados SQLite e dispara mensagens conforme alterações.",
    version="1.0.0",
)


###########################################################
# CMA GATEWAY API
###########################################################
# Modelo do banco de dados
class cma_gateway(Base):
    __tablename__ = "cma_gateway"
    id = Column(Integer, primary_key=True, index=True)
    subestacao = Column(String, index=True)
    regional = Column(String, index=True)
    host = Column(String, index=True)
    status = Column(Integer, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class cma_gateway_API(BaseModel):
    subestacao: str = Field(..., description="", example="")
    regional: str = Field(..., description="", example="")
    host: str = Field(..., description="Informe o IP", example="")
    status: bool = Field(..., description="", example=0)


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(cma_gateway, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(cma_gateway, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(cma_gateway, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Cadastro_Gateway/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: cma_gateway_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = cma_gateway.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Cadastro_Gateway/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = cma_gateway.__table__.select().where(cma_gateway.__table__.c.id == item_id)
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Cadastro_Gateway/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: cma_gateway_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        cma_gateway.__table__.update()
        .where(cma_gateway.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Cadastro_Gateway/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = cma_gateway.__table__.delete().where(cma_gateway.__table__.c.id == item_id)
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


###########################################################
# EQUIPAMENTOS API
###########################################################
# Modelo do banco de dados
class eqp_protocol(Base):
    __tablename__ = "EQP_protocol"
    xid_equip = Column(String, primary_key=True, index=True)
    fabricante = Column(String, index=True)
    marca = Column(String, index=True)
    modelo = Column(String, index=True)
    protocolo = Column(String, index=True)
    sap_id = Column(String, index=True)
    status = Column(Integer, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class eqp_protocol_API(BaseModel):
    xid_equip: str = Field(..., description="", example="")
    fabricante: str = Field(..., description="", example="")
    marca: str = Field(..., description="", example="")
    modelo: str = Field(..., description="", example="")
    protocolo: str = Field(..., description="", example="MODBUS_IP")
    sap_id: str = Field(..., description="", example="")
    status: bool = Field(..., description="", example=False)


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(eqp_protocol, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(eqp_protocol, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(eqp_protocol, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Equipamentos/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: eqp_protocol_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = eqp_protocol.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Equipamentos/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = eqp_protocol.__table__.select().where(
        eqp_protocol.__table__.c.id == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Equipamentos/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: eqp_protocol_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        eqp_protocol.__table__.update()
        .where(eqp_protocol.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Equipamentos/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = eqp_protocol.__table__.delete().where(
        eqp_protocol.__table__.c.id == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


###########################################################
# EQUIPAMENTOS MODBUS DATASOURCE API
###########################################################
# Modelo do banco de dados
class datasource_modbus_ip(Base):
    __tablename__ = "EQP_MODBUS_IP"
    xid_equip = Column(String, primary_key=True, index=True)
    updatePeriodType = Column(String, index=True)
    transportType = Column(String, index=True)
    maxReadBitCount = Column(Integer, index=True)
    maxReadRegisterCount = Column(Integer, index=True)
    maxWriteRegisterCount = Column(Integer, index=True)
    host = Column(String, index=True)
    port = Column(Integer, index=True)
    retries = Column(Integer, index=True)
    timeout = Column(Integer, index=True)
    updatePeriods = Column(Integer, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class datasource_modbus_ip_API(BaseModel):
    xid_equip: str = Field(..., description="", example="")
    updatePeriodType: str = Field(..., description="", example="MINUTES")
    transportType: str = Field(..., description="", example="TCP")
    maxReadBitCount: int = Field(..., description="", example=2000)
    maxReadRegisterCount: int = Field(..., description="", example=125)
    maxWriteRegisterCount: int = Field(..., description="", example=120)
    host: str = Field(..., description="", example="")
    port: int = Field(..., description="", example=502)
    retries: int = Field(..., description="", example=2)
    timeout: int = Field(..., description="", example=500)
    updatePeriods: int = Field(..., description="", example=5)


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(datasource_modbus_ip, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(datasource_modbus_ip, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(datasource_modbus_ip, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Equipamentos Modbus IP/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datasource_modbus_ip_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = datasource_modbus_ip.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Equipamentos Modbus IP/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = datasource_modbus_ip.__table__.select().where(
        datasource_modbus_ip.__table__.c.id == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Equipamentos Modbus IP/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: datasource_modbus_ip_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        datasource_modbus_ip.__table__.update()
        .where(datasource_modbus_ip.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Equipamentos Modbus IP/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datasource_modbus_ip.__table__.delete().where(
        datasource_modbus_ip.__table__.c.id == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


###########################################################
# SENSORES REGISTRADORES MODBUS DATAPOINTS API
###########################################################
# Modelo do banco de dados
class datapoints_modbus_ip(Base):
    __tablename__ = "DP_MODBUS_IP"
    xid_sensor = Column(String, primary_key=True, index=True)
    range = Column(String, index=True)
    modbusDataType = Column(String, index=True)
    additive = Column(Integer, index=True)
    offset = Column(Integer, index=True)
    bit = Column(Integer, index=True)
    charset = Column(String, index=True)
    multiplier = Column(Integer, index=True)
    offset = Column(Integer, index=True)
    slaveId = Column(Integer, index=True)
    enabled = Column(Integer, index=True)
    nome = Column(String, index=True)
    tipo = Column(String, index=True)
    classificacao = Column(String, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class datapoints_modbus_ip_API(BaseModel):
    xid_sensor: str = Field(..., description="", example="")
    range: str = Field(..., description="", example="")
    modbusDataType: str = Field(..., description="", example="")
    additive: int = Field(..., description="", example="")
    offset: int = Field(..., description="", example="")
    bit: int = Field(..., description="", example="")
    charset: str = Field(..., description="", example="")
    multiplier: int = Field(..., description="", example="")
    offset: int = Field(..., description="", example="")
    slaveId: int = Field(..., description="", example="")
    enabled: int = Field(..., description="", example="")
    nome: str = Field(..., description="", example="")
    tipo: str = Field(..., description="", example="")
    classificacao: str = Field(..., description="", example="")


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(datapoints_modbus_ip, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(datapoints_modbus_ip, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(datapoints_modbus_ip, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Registradores Modbus IP/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datapoints_modbus_ip_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = datapoints_modbus_ip.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Registradores Modbus IP/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = datapoints_modbus_ip.__table__.select().where(
        datapoints_modbus_ip.__table__.c.id == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Registradores Modbus IP/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: datapoints_modbus_ip_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        datapoints_modbus_ip.__table__.update()
        .where(datapoints_modbus_ip.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Registradores Modbus IP/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datapoints_modbus_ip.__table__.delete().where(
        datapoints_modbus_ip.__table__.c.id == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


###########################################################
# EQUIPAMENTOS DNP3 DATASOURCE API
###########################################################
# Modelo do banco de dados
class datasource_dnp3(Base):
    __tablename__ = "EQP_DNP3"
    xid_equip = Column(String, primary_key=True, index=True)
    eventsPeriodType = Column(String, index=True)
    host = Column(String, index=True)
    port = Column(Integer, index=True)
    rbePollPeriods = Column(Integer, index=True)
    retries = Column(Integer, index=True)
    slaveAddress = Column(Integer, index=True)
    sourceAddress = Column(Integer, index=True)
    staticPollPeriods = Column(Integer, index=True)
    synchPeriods = Column(Integer, index=True)
    timeout = Column(Integer, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class datasource_dnp3_API(BaseModel):
    xid_equip: str = Field(..., description="", example="")
    eventsPeriodType: str = Field(..., description="", example="")
    host: str = Field(..., description="", example="")
    port: int = Field(..., description="", example="")
    rbePollPeriods: int = Field(..., description="", example="")
    retries: int = Field(..., description="", example="")
    slaveAddress: int = Field(..., description="", example="")
    sourceAddress: int = Field(..., description="", example="")
    staticPollPeriods: int = Field(..., description="", example="")
    synchPeriods: int = Field(..., description="", example="")
    timeout: int = Field(..., description="", example="")


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(datasource_dnp3, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(datasource_dnp3, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(datasource_dnp3, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Equipamentos DNP3/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datasource_dnp3_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = datasource_dnp3.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Equipamentos DNP3/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = datasource_dnp3.__table__.select().where(
        datasource_dnp3.__table__.c.id == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Equipamentos DNP3/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: datasource_dnp3_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        datasource_dnp3.__table__.update()
        .where(datasource_dnp3.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Equipamentos DNP3/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datasource_dnp3.__table__.delete().where(
        datasource_dnp3.__table__.c.id == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


###########################################################
# SENSORES REGISTRADORES DNP3 DATAPOINTS API
###########################################################
# Modelo do banco de dados
class datapoints_dnp3(Base):
    __tablename__ = "DP_DNP3"
    xid_sensor = Column(String, primary_key=True, index=True)
    dnp3DataType = Column(Integer, index=True)
    controlCommand = Column(Integer, index=True)
    index = Column(Integer, index=True)
    timeoff = Column(Integer, index=True)
    timeon = Column(Integer, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class datapoints_dnp3_API(BaseModel):
    xid_sensor: str = Field(..., description="", example="")
    dnp3DataType: int = Field(..., description="", example="")
    controlCommand: int = Field(..., description="", example="")
    index: int = Field(..., description="", example="")
    timeoff: int = Field(..., description="", example="")
    timeon: int = Field(..., description="", example="")


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(datapoints_dnp3, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(datapoints_dnp3, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(datapoints_dnp3, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Registradores DNP3/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: datapoints_dnp3_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = datapoints_dnp3.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Registradores DNP3/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = datapoints_dnp3.__table__.select().where(
        datapoints_dnp3.__table__.c.id == item_id
    )
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Registradores DNP3/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: datapoints_dnp3_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        datapoints_dnp3.__table__.update()
        .where(datapoints_dnp3.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Registradores DNP3/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = datapoints_dnp3.__table__.delete().where(
        datapoints_dnp3.__table__.c.id == item_id
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


###########################################################
# TAGS EQUIPAMENTOS
###########################################################
# Modelo do banco de dados
class eqp_tags(Base):
    __tablename__ = "EQP_TAGS"
    id = Column(String, primary_key=True, index=True)
    xid_equip = Column(String, index=True)
    nome = Column(String, index=True)
    valor = Column(String, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class eqp_tags_API(BaseModel):
    xid_equip: str = Field(..., description="", example="")
    nome: str = Field(..., description="", example="")
    valor: str = Field(..., description="", example="")


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(eqp_tags, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(eqp_tags, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(eqp_tags, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Tags equipamentos/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: eqp_tags_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = eqp_tags.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Tags equipamentos/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = eqp_tags.__table__.select().where(eqp_tags.__table__.c.id == item_id)
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Tags equipamentos/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: eqp_tags_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        eqp_tags.__table__.update()
        .where(eqp_tags.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Tags equipamentos/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = eqp_tags.__table__.delete().where(eqp_tags.__table__.c.id == item_id)
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


###########################################################
# TAGS SENSORES
###########################################################
# Modelo do banco de dados
class dp_tags(Base):
    __tablename__ = "DP_TAGS"
    id = Column(String, primary_key=True, index=True)
    xid_sensor = Column(String, index=True)
    nome = Column(String, index=True)
    valor = Column(String, index=True)


Base.metadata.create_all(bind=engine)


# Modelo de entrada para FastAPI
class dp_tags_API(BaseModel):
    xid_sensor: str = Field(..., description="", example="")
    nome: str = Field(..., description="", example="")
    valor: str = Field(..., description="", example="")


# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(dp_tags, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)


@event.listens_for(dp_tags, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)


@event.listens_for(dp_tags, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)


# Endpoints CRUD
@app.post(
    "/Tags sensores/",
    response_model=dict,
    summary="Criar um item",
    description="Adiciona um novo item ao banco de dados.",
)
async def create_item(item: dp_tags_API):
    """
    Adiciona um novo item ao banco de dados.

    - **name**: Nome do item
    - **description**: Descrição do item
    """
    async with database.transaction():
        query = dp_tags.__table__.insert().values(
            name=item.name, description=item.description
        )
        item_id = await database.execute(query)
        return {"id": item_id, "message": "Item criado com sucesso!"}


@app.get(
    "/Tags sensores/{item_id}",
    response_model=dict,
    summary="Buscar um item",
    description="Obtém um item pelo ID.",
)
async def read_item(item_id: int):
    """
    Retorna os detalhes de um item pelo ID.

    - **item_id**: ID do item
    """
    query = dp_tags.__table__.select().where(dp_tags.__table__.c.id == item_id)
    item = await database.fetch_one(query)
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado")
    return dict(item)  # Converte o Record em um dicionário


@app.put(
    "/Tags sensores/{item_id}",
    response_model=dict,
    summary="Atualizar um item",
    description="Atualiza os detalhes de um item existente.",
)
async def update_item(item_id: int, item: dp_tags_API):
    """
    Atualiza os detalhes de um item existente.

    - **item_id**: ID do item a ser atualizado
    - **name**: Novo nome do item
    - **description**: Nova descrição do item
    """
    query = (
        dp_tags.__table__.update()
        .where(dp_tags.__table__.c.id == item_id)
        .values(name=item.name, description=item.description)
    )
    result = await database.execute(query)
    if result:
        return {"message": "Item atualizado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


@app.delete(
    "/Tags sensores/{item_id}",
    response_model=dict,
    summary="Deletar um item",
    description="Exclui um item pelo ID.",
)
async def delete_item(item_id: int):
    """
    Exclui um item do banco de dados pelo ID.

    - **item_id**: ID do item a ser excluído
    """
    query = dp_tags.__table__.delete().where(dp_tags.__table__.c.id == item_id)
    result = await database.execute(query)
    if result:
        return {"message": "Item deletado com sucesso!"}
    else:
        raise HTTPException(status_code=404, detail="Item não encontrado")


# Inicialização do banco de dados ao iniciar o app
@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


# Comando para rodar o servidor
# uvicorn crud_api:app --reload
