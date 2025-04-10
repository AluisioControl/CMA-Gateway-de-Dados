###############################################################
# models.py
# ------------------------------------------------------------
# Arquivo models do banco de dados e Middleware
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2024
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################
#from pydantic import  Field
from databases import Database
from sqlalchemy import create_engine, Column, Integer, String, event, Boolean, Float
#from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
import os

# Carregando as variáveis de ambiente do arquivo .env
load_dotenv()

# Configuração do banco de dados
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuração do SQLite e SQLAlchemy
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Função para disparar mensagens
def trigger_message(operation, target):
    print(f"A operação '{operation}' foi realizada no item: {target}")

###########################################################
##################### CMA GATEWAY #########################
###########################################################
class cma_gateway(Base):
    __tablename__ = "CMA_GD"
    xid_gateway = Column(String, primary_key=True, index=True)
    subestacao = Column(String, index=True)
    regional = Column(String, index=True)
    host = Column(String, index=True)
    status = Column(Boolean, index=True)
    id_gtw = Column(Integer, index=True)
    id_sub = Column(Integer, index=True)



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


###########################################################
################## EQUIPAMENTOS MODBUS IP #################
###########################################################
class datasource_modbus_ip(Base):
    __tablename__ = "EQP_MODBUS_IP"
    xid_equip = Column(String, primary_key=True, index=True)
    xid_gateway = Column(String, index=True)
    fabricante = Column(String, index=True)
    marca = Column(String, index=True)
    modelo = Column(String, index=True)
    #type = Column(String, index=True)
    sap_id = Column(String, index=True)
    enabled = Column(Boolean, index=True)
    updatePeriodType = Column(String, index=True)
    maxReadBitCount = Column(Integer, index=True)
    maxReadRegisterCount = Column(Integer, index=True)
    maxWriteRegisterCount = Column(Integer, index=True)
    host = Column(String, index=True)
    port = Column(Integer, index=True)
    retries = Column(Integer, index=True)
    timeout = Column(Integer, index=True)
    updatePeriods = Column(Integer, index=True)
    id_hdw = Column(Integer, index=True)
    name_hdw = Column(String, index=True)
    type = Column(String, index=True)
    model_sen = Column(String, index=True)
    name_sen = Column(String, index=True)
    id_man = Column(Integer, index=True)


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


###########################################################
################## REGISTRADORES MODBUS ###################
###########################################################
class datapoints_modbus_ip(Base):
    __tablename__ = "DP_MODBUS_IP"
    xid_sensor = Column(String, primary_key=True, index=True)
    xid_equip = Column(String, index=True)
    range = Column(String, index=True)
    modbusDataType = Column(String, index=True)
    additive = Column(Integer, index=True)
    offset = Column(Integer, index=True)
    bit = Column(Integer, index=True)
    multiplier = Column(Float, index=True)
    slaveId = Column(Integer, index=True)
    enabled = Column(Boolean, index=True)
    nome = Column(String, index=True)
    tipo = Column(String, index=True)
    classificacao = Column(String, index=True)
    phase = Column(String, index=True)
    circuitBreakerManeuverType_reg_mod = Column(String, index=True)
    bushingSide = Column(String, index=True)
    id_reg_reg_mod = Column(Integer, index=True)
    id_sen_reg_mod = Column(Integer, index=True)



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


###########################################################
##################### EQUIPAMENTOS DNP3 ###################
###########################################################
class datasource_dnp3(Base):
    __tablename__ = "EQP_DNP3"
    xid_equip = Column(String, primary_key=True, index=True)
    xid_gateway = Column(String, index=True)
    fabricante = Column(String, index=True)
    marca = Column(String, index=True)
    modelo = Column(String, index=True)
    type = Column(String, index=True)
    sap_id = Column(String, index=True)
    enabled = Column(Boolean, index=True)
    eventsPeriodType = Column(String, index=True)
    host = Column(String, index=True)
    port = Column(Integer, index=True)
    rbePollPeriods = Column(Integer, index=True)
    retries = Column(Integer, index=True)
    slaveAddress = Column(Integer, index=True)
    sourceAddress = Column(Integer, index=True)
    staticPollPeriods = Column(Integer, index=True)
    timeout = Column(Integer, index=True)



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


###########################################################
######### SENSORES REGISTRADORES DNP3 DATAPOINTS ##########
###########################################################
class datapoints_dnp3(Base):
    __tablename__ = "DP_DNP3"
    xid_sensor = Column(String, primary_key=True, index=True)
    xid_equip = Column(String, index=True)
    dnp3DataType = Column(Integer, index=True)
    controlCommand = Column(Integer, index=True)
    index = Column(Integer, index=True)
    timeoff = Column(Integer, index=True)
    timeon = Column(Integer, index=True)
    enabled = Column(Boolean, index=True)
    nome = Column(String, index=True)
    tipo = Column(String, index=True)
    classificacao = Column(String, index=True)
    


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


###########################################################
##################### TAGS EQUIPAMENTOS ###################
###########################################################
class eqp_tags(Base):
    __tablename__ = "EQP_TAGS"
    id = Column(Integer, primary_key=True, index=True)
    xid_equip = Column(String, index=True)
    nome = Column(String, index=True)
    valor = Column(String, index=True)


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


###########################################################
####################### TAGS SENSORES #####################
###########################################################
class dp_tags(Base):
    __tablename__ = "DP_TAGS"
    id = Column(Integer, primary_key=True, index=True)
    xid_sensor = Column(String, index=True)
    nome = Column(String, index=True)
    valor = Column(String, index=True)


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



###########################################################
####################### PERSISTENCE #####################
###########################################################
class persistence(Base):
    __tablename__ = "PERSISTENCE"
    id = Column(Integer, primary_key=True, index=True)
    content_data = Column(String, index=True)
    sended = Column(Boolean, index=True)


# Eventos do SQLAlchemy para capturar alterações
@event.listens_for(persistence, "after_insert")
def after_insert(mapper, connection, target):
    trigger_message("inclusão", target)

@event.listens_for(persistence, "after_update")
def after_update(mapper, connection, target):
    trigger_message("atualização", target)

@event.listens_for(persistence, "after_delete")
def after_delete(mapper, connection, target):
    trigger_message("deleção", target)
    
Base.metadata.create_all(bind=engine)
