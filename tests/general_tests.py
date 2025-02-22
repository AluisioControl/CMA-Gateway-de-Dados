###############################################################
# general_tests.py
# ------------------------------------------------------------
# Arquivo de excução dos testes do Middleware
# Author: Aluisio Cavalcante <aluisio@controlengenharia.eng.br>
# novembro de 2024
# TODOS OS DIREITOS RESERVADOS A CONTROL ENGENHARIA
# #############################################################
import logging
import threading
import time
import sys
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# import sqlite3
sys.path.append('./src')
from functions import *
from models import *
from main import app, database


# Configuração do banco de dados de teste
DATABASE_URL = "sqlite:///./test_db.db"
engine = create_engine(DATABASE_URL)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine)


##############################################################
# Testes dos endpoints da API
##############################################################

# Fixture para criar o banco de dados de teste
@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Fixture para fornecer uma sessão de banco de dados
@pytest.fixture(scope="function")
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


# Fixture para fornecer um cliente de teste
@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


# ------------------------------------------------------------
# Testes para os endpoints de status
# ------------------------------------------------------------

def test_get_cma_status(client):
    response = client.get("/cma_status")
    assert response.status_code == 200
    # Verifica se a resposta é válida
    assert response.json() in ["online", "offline"]


def test_get_scada_status(client):
    response = client.get("/scada_status")
    assert response.status_code == 200
    # Verifica se a resposta é válida
    assert response.json() in ["online", "offline"]


# ------------------------------------------------------------
# Testes para o endpoint de Cadastro de Gateway
# ------------------------------------------------------------

def test_create_gateway_success(client, db_session):
    gateway_data = {
        "xid_gateway": "gateway_test_01",
        "subestacao": "SE Teste",
        "regional": "Regional Teste",
        "host": "192.168.1.1",
        "status": True,
    }
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Item criado com sucesso!"

    # Verifica se o item foi realmente inserido no banco de dados
    item = db_session.query(cma_gateway).filter_by(
        xid_gateway="gateway_test_01").first()
    assert item is not None
    assert item.subestacao == "SE Teste"


def test_create_gateway_duplicate(client):
    gateway_data = {
        "xid_gateway": "gateway_test_01",
        "subestacao": "SE Teste",
        "regional": "Regional Teste",
        "host": "192.168.1.1",
        "status": True,
    }
    # Tenta criar o mesmo gateway novamente
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Item com este ID já existe no banco de dados."


def test_read_gateway(client):
    response = client.get("/Cadastro_Gateway/gateway_test_01")
    assert response.status_code == 200
    assert response.json()["xid_gateway"] == "gateway_test_01"
    assert response.json()["subestacao"] == "SE Teste"


def test_read_gateway_not_found(client):
    response = client.get("/Cadastro_Gateway/gateway_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_update_gateway(client, db_session):
    updated_data = {
        "xid_gateway": "gateway_test_01",
        "subestacao": "SE Atualizada",
        "regional": "Regional Atualizada",
        "host": "192.168.1.2",
        "status": False,
    }
    response = client.put(
        "/Cadastro_Gateway/gateway_test_01", json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Item atualizado com sucesso!"

    # Verifica se o item foi realmente atualizado no banco de dados
    item = db_session.query(cma_gateway).filter_by(
        xid_gateway="gateway_test_01").first()
    assert item.subestacao == "SE Atualizada"
    assert item.host == "192.168.1.2"


def test_update_gateway_not_found(client):
    updated_data = {
        "xid_gateway": "gateway_nao_existente",
        "subestacao": "SE Atualizada",
        "regional": "Regional Atualizada",
        "host": "192.168.1.2",
        "status": False,
    }
    response = client.put(
        "/Cadastro_Gateway/gateway_nao_existente", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_delete_gateway(client, db_session):
    response = client.delete("/Cadastro_Gateway/gateway_test_01")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deletado com sucesso!"

    # Verifica se o item foi realmente excluído do banco de dados
    item = db_session.query(cma_gateway).filter_by(
        xid_gateway="gateway_test_01").first()
    assert item is None


def test_delete_gateway_not_found(client):
    response = client.delete("/Cadastro_Gateway/gateway_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"

# ------------------------------------------------------------
# Testes para o endpoint de Equipamentos Modbus IP
# ------------------------------------------------------------


def test_create_equipamento_modbus_ip_success(client, db_session):
    # Primeiro, cria um gateway para associar ao equipamento
    gateway_data = {
        "xid_gateway": "gateway_equip_01",
        "subestacao": "SE Equip",
        "regional": "Regional Equip",
        "host": "192.168.1.3",
        "status": True,
    }
    client.post("/Cadastro_Gateway/", json=gateway_data)

    equip_data = {
        "xid_equip": "equip_modbus_test_01",
        "xid_gateway": "gateway_equip_01",
        "fabricante": "Fabricante Teste",
        "marca": "Marca Teste",
        "modelo": "Modelo Teste",
        "type": "MODBUS_IP",
        "sap_id": 12345,
        "enabled": True,
        "updatePeriodType": "SECONDS",
        "maxReadBitCount": 100,
        "maxReadRegisterCount": 50,
        "maxWriteRegisterCount": 25,
        "host": "192.168.1.4",
        "port": 502,
        "retries": 3,
        "timeout": 1000,
        "updatePeriods": 30,
    }
    response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Item criado com sucesso!"

    # Verifica se o item foi realmente inserido no banco de dados
    item = db_session.query(datasource_modbus_ip).filter_by(
        xid_equip="equip_modbus_test_01").first()
    assert item is not None
    assert item.fabricante == "Fabricante Teste"


def test_create_equipamento_modbus_ip_duplicate(client):
    equip_data = {
        "xid_equip": "equip_modbus_test_01",
        "xid_gateway": "gateway_equip_01",
        "fabricante": "Fabricante Teste",
        "marca": "Marca Teste",
        "modelo": "Modelo Teste",
        "type": "MODBUS_IP",
        "sap_id": 12345,
        "enabled": True,
        "updatePeriodType": "SECONDS",
        "maxReadBitCount": 100,
        "maxReadRegisterCount": 50,
        "maxWriteRegisterCount": 25,
        "host": "192.168.1.4",
        "port": 502,
        "retries": 3,
        "timeout": 1000,
        "updatePeriods": 30,
    }
    # Tenta criar o mesmo equipamento novamente
    response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Item com este ID já existe no banco de dados."


def test_read_equipamento_modbus_ip(client):
    response = client.get("/Equipamentos_Modbus_IP/equip_modbus_test_01")
    assert response.status_code == 200
    assert response.json()["xid_equip"] == "equip_modbus_test_01"
    assert response.json()["fabricante"] == "Fabricante Teste"


def test_read_equipamento_modbus_ip_not_found(client):
    response = client.get("/Equipamentos_Modbus_IP/equip_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_update_equipamento_modbus_ip(client, db_session):
    updated_data = {
        "xid_equip": "equip_modbus_test_01",
        "xid_gateway": "gateway_equip_01",
        "fabricante": "Fabricante Atualizado",
        "marca": "Marca Atualizada",
        "modelo": "Modelo Atualizado",
        "type": "MODBUS_IP",
        "sap_id": 67890,
        "enabled": False,
        "updatePeriodType": "MINUTES",
        "maxReadBitCount": 200,
        "maxReadRegisterCount": 100,
        "maxWriteRegisterCount": 50,
        "host": "192.168.1.5",
        "port": 503,
        "retries": 5,
        "timeout": 2000,
        "updatePeriods": 60,
    }
    response = client.put(
        "/Equipamentos_Modbus_IP/equip_modbus_test_01", json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Item atualizado com sucesso!"

    # Verifica se o item foi realmente atualizado no banco de dados
    item = db_session.query(datasource_modbus_ip).filter_by(
        xid_equip="equip_modbus_test_01").first()
    assert item.fabricante == "Fabricante Atualizado"
    assert item.host == "192.168.1.5"


def test_update_equipamento_modbus_ip_not_found(client):
    updated_data = {
        "xid_equip": "equip_nao_existente",
        "xid_gateway": "gateway_equip_01",
        "fabricante": "Fabricante Atualizado",
        "marca": "Marca Atualizada",
        "modelo": "Modelo Atualizado",
        "type": "MODBUS_IP",
        "sap_id": 67890,
        "enabled": False,
        "updatePeriodType": "MINUTES",
        "maxReadBitCount": 200,
        "maxReadRegisterCount": 100,
        "maxWriteRegisterCount": 50,
        "host": "192.168.1.5",
        "port": 503,
        "retries": 5,
        "timeout": 2000,
        "updatePeriods": 60,
    }
    response = client.put(
        "/Equipamentos_Modbus_IP/equip_nao_existente", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_delete_equipamento_modbus_ip(client, db_session):
    response = client.delete("/Equipamentos_Modbus_IP/equip_modbus_test_01")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deletado com sucesso!"

    # Verifica se o item foi realmente excluído do banco de dados
    item = db_session.query(datasource_modbus_ip).filter_by(
        xid_equip="equip_modbus_test_01").first()
    assert item is None


def test_delete_equipamento_modbus_ip_not_found(client):
    response = client.delete("/Equipamentos_Modbus_IP/equip_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"

# ------------------------------------------------------------
# Testes para o endpoint de Registradores Modbus
# ------------------------------------------------------------


def test_create_registrador_modbus_success(client, db_session):
    # Primeiro, cria um equipamento Modbus IP para associar ao registrador
    equip_data = {
        "xid_equip": "equip_modbus_test_02",
        "xid_gateway": "gateway_equip_01",
        "fabricante": "Fabricante Teste 2",
        "marca": "Marca Teste 2",
        "modelo": "Modelo Teste 2",
        "type": "MODBUS_IP",
        "sap_id": 54321,
        "enabled": True,
        "updatePeriodType": "SECONDS",
        "maxReadBitCount": 150,
        "maxReadRegisterCount": 75,
        "maxWriteRegisterCount": 35,
        "host": "192.168.1.6",
        "port": 504,
        "retries": 4,
        "timeout": 1500,
        "updatePeriods": 45,
    }
    client.post("/Equipamentos_Modbus_IP/", json=equip_data)

    registrador_data = {
        "xid_sensor": "sensor_modbus_test_01",
        "xid_equip": "equip_modbus_test_02",
        "range": "1-100",
        "modbusDataType": "INT",
        "additive": 0,
        "offset": 0,
        "bit": 0,
        "multiplier": 1,
        "slaveId": 1,
        "enabled": True,
        "nome": "Sensor Teste 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA",
    }
    response = client.post("/Registradores_Modbus_IP/", json=registrador_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Item criado com sucesso!"

    # Verifica se o item foi realmente inserido no banco de dados
    item = db_session.query(datapoints_modbus_ip).filter_by(
        xid_sensor="sensor_modbus_test_01").first()
    assert item is not None
    assert item.nome == "Sensor Teste 01"


def test_create_registrador_modbus_duplicate(client):
    registrador_data = {
        "xid_sensor": "sensor_modbus_test_01",
        "xid_equip": "equip_modbus_test_02",
        "range": "1-100",
        "modbusDataType": "INT",
        "additive": 0,
        "offset": 0,
        "bit": 0,
        "multiplier": 1,
        "slaveId": 1,
        "enabled": True,
        "nome": "Sensor Teste 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA",
    }
    # Tenta criar o mesmo registrador novamente
    response = client.post("/Registradores_Modbus_IP/", json=registrador_data)
    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Item com este ID já existe no banco de dados."


def test_read_registrador_modbus(client):
    response = client.get("/Registradores_Modbus_IP/sensor_modbus_test_01")
    assert response.status_code == 200
    assert response.json()["xid_sensor"] == "sensor_modbus_test_01"
    assert response.json()["nome"] == "Sensor Teste 01"


def test_read_registrador_modbus_not_found(client):
    response = client.get("/Registradores_Modbus_IP/sensor_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_update_registrador_modbus(client, db_session):
    updated_data = {
        "xid_sensor": "sensor_modbus_test_01",
        "xid_equip": "equip_modbus_test_02",
        "range": "101-200",
        "modbusDataType": "FLOAT",
        "additive": 10,
        "offset": 5,
        "bit": 1,
        "multiplier": 2,
        "slaveId": 2,
        "enabled": False,
        "nome": "Sensor Atualizado 01",
        "tipo": "SAIDA",
        "classificacao": "DIGITAL",
    }
    response = client.put(
        "/Registradores_Modbus_IP/sensor_modbus_test_01", json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Item atualizado com sucesso!"

    # Verifica se o item foi realmente atualizado no banco de dados
    item = db_session.query(datapoints_modbus_ip).filter_by(
        xid_sensor="sensor_modbus_test_01").first()
    assert item.nome == "Sensor Atualizado 01"
    assert item.modbusDataType == "FLOAT"


def test_update_registrador_modbus_not_found(client):
    updated_data = {
        "xid_sensor": "sensor_nao_existente",
        "xid_equip": "equip_modbus_test_02",
        "range": "101-200",
        "modbusDataType": "FLOAT",
        "additive": 10,
        "offset": 5,
        "bit": 1,
        "multiplier": 2,
        "slaveId": 2,
        "enabled": False,
        "nome": "Sensor Atualizado 01",
        "tipo": "SAIDA",
        "classificacao": "DIGITAL",
    }
    response = client.put(
        "/Registradores_Modbus_IP/sensor_nao_existente", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_delete_registrador_modbus(client, db_session):
    response = client.delete("/Registradores_Modbus_IP/sensor_modbus_test_01")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deletado com sucesso!"

    # Verifica se o item foi realmente excluído do banco de dados
    item = db_session.query(datapoints_modbus_ip).filter_by(
        xid_sensor="sensor_modbus_test_01").first()
    assert item is None


def test_delete_registrador_modbus_not_found(client):
    response = client.delete("/Registradores_Modbus_IP/sensor_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"

# ------------------------------------------------------------
# Testes para o endpoint de Equipamentos DNP3
# ------------------------------------------------------------


def test_create_equipamento_dnp3_success(client, db_session):
    # Primeiro, cria um gateway para associar ao equipamento DNP3
    gateway_data = {
        "xid_gateway": "gateway_dnp3_01",
        "subestacao": "SE DNP3",
        "regional": "Regional DNP3",
        "host": "192.168.1.7",
        "status": True,
    }
    client.post("/Cadastro_Gateway/", json=gateway_data)

    equip_data = {
        "xid_equip": "equip_dnp3_test_01",
        "xid_gateway": "gateway_dnp3_01",
        "fabricante": "Fabricante DNP3 Teste",
        "marca": "Marca DNP3 Teste",
        "modelo": "Modelo DNP3 Teste",
        "type": "DNP3_MASTER",
        "sap_id": 98765,
        "enabled": True,
        "eventsPeriodType": "SECONDS",
        "host": "192.168.1.8",
        "port": 20000,
        "rbePollPeriods": 30,
        "retries": 2,
        "slaveAddress": 10,
        "sourceAddress": 1,
        "staticPollPeriods": 60,
        "timeout": 5000
    }
    response = client.post("/Equipamentos_DNP3/", json=equip_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Item criado com sucesso!"

    # Verifica se o item foi realmente inserido no banco de dados
    item = db_session.query(datasource_dnp3).filter_by(
        xid_equip="equip_dnp3_test_01").first()
    assert item is not None
    assert item.fabricante == "Fabricante DNP3 Teste"


def test_create_equipamento_dnp3_duplicate(client):
    equip_data = {
        "xid_equip": "equip_dnp3_test_01",
        "xid_gateway": "gateway_dnp3_01",
        "fabricante": "Fabricante DNP3 Teste",
        "marca": "Marca DNP3 Teste",
        "modelo": "Modelo DNP3 Teste",
        "type": "DNP3_MASTER",
        "sap_id": 98765,
        "enabled": True,
        "eventsPeriodType": "SECONDS",
        "host": "192.168.1.8",
        "port": 20000,
        "rbePollPeriods": 30,
        "retries": 2,
        "slaveAddress": 10,
        "sourceAddress": 1,
        "staticPollPeriods": 60,
        "timeout": 5000
    }
    # Tenta criar o mesmo equipamento novamente
    response = client.post("/Equipamentos_DNP3/", json=equip_data)
    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Item com este ID já existe no banco de dados."


def test_read_equipamento_dnp3(client):
    response = client.get("/Equipamentos_DNP3/equip_dnp3_test_01")
    assert response.status_code == 200
    assert response.json()["xid_equip"] == "equip_dnp3_test_01"
    assert response.json()["fabricante"] == "Fabricante DNP3 Teste"


def test_read_equipamento_dnp3_not_found(client):
    response = client.get("/Equipamentos_DNP3/equip_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_update_equipamento_dnp3(client, db_session):
    updated_data = {
        "xid_equip": "equip_dnp3_test_01",
        "xid_gateway": "gateway_dnp3_01",
        "fabricante": "Fabricante DNP3 Atualizado",
        "marca": "Marca DNP3 Atualizada",
        "modelo": "Modelo DNP3 Atualizado",
        "type": "DNP3_MASTER",
        "sap_id": 12345,
        "enabled": False,
        "eventsPeriodType": "MINUTES",
        "host": "192.168.1.9",
        "port": 20001,
        "rbePollPeriods": 60,
        "retries": 3,
        "slaveAddress": 11,
        "sourceAddress": 2,
        "staticPollPeriods": 120,
        "timeout": 4000
    }
    response = client.put(
        "/Equipamentos_DNP3/equip_dnp3_test_01", json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Item atualizado com sucesso!"

    # Verifica se o item foi realmente atualizado no banco de dados
    item = db_session.query(datasource_dnp3).filter_by(
        xid_equip="equip_dnp3_test_01").first()
    assert item.fabricante == "Fabricante DNP3 Atualizado"
    assert item.host == "192.168.1.9"


def test_update_equipamento_dnp3_not_found(client):
    updated_data = {
        "xid_equip": "equip_nao_existente",
        "xid_gateway": "gateway_dnp3_01",
        "fabricante": "Fabricante DNP3 Atualizado",
        "marca": "Marca DNP3 Atualizada",
        "modelo": "Modelo DNP3 Atualizado",
        "type": "DNP3_MASTER",
        "sap_id": 12345,
        "enabled": False,
        "eventsPeriodType": "MINUTES",
        "host": "192.168.1.9",
        "port": 20001,
        "rbePollPeriods": 60,
        "retries": 3,
        "slaveAddress": 11,
        "sourceAddress": 2,
        "staticPollPeriods": 120,
        "timeout": 4000
    }
    response = client.put(
        "/Equipamentos_DNP3/equip_nao_existente", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_delete_equipamento_dnp3(client, db_session):
    response = client.delete("/Equipamentos_DNP3/equip_dnp3_test_01")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deletado com sucesso!"

    # Verifica se o item foi realmente excluído do banco de dados
    item = db_session.query(datasource_dnp3).filter_by(
        xid_equip="equip_dnp3_test_01").first()
    assert item is None


def test_delete_equipamento_dnp3_not_found(client):
    response = client.delete("/Equipamentos_DNP3/equip_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"

# ------------------------------------------------------------
# Testes para o endpoint de Registradores DNP3
# ------------------------------------------------------------


def test_create_registrador_dnp3_success(client, db_session):
    # Primeiro, cria um equipamento DNP3 para associar ao registrador
    equip_data = {
        "xid_equip": "equip_dnp3_test_02",
        "xid_gateway": "gateway_dnp3_01",
        "fabricante": "Fabricante DNP3 Teste 2",
        "marca": "Marca DNP3 Teste 2",
        "modelo": "Modelo DNP3 Teste 2",
        "type": "DNP3_MASTER",
        "sap_id": 56789,
        "enabled": True,
        "eventsPeriodType": "SECONDS",
        "host": "192.168.1.10",
        "port": 20002,
        "rbePollPeriods": 45,
        "retries": 1,
        "slaveAddress": 12,
        "sourceAddress": 3,
        "staticPollPeriods": 90,
        "timeout": 3000
    }
    client.post("/Equipamentos_DNP3/", json=equip_data)

    registrador_data = {
        "xid_sensor": "sensor_dnp3_test_01",
        "xid_equip": "equip_dnp3_test_02",
        "dnp3DataType": 1,
        "controlCommand": 0,
        "index": 0,
        "timeoff": 0,
        "timeon": 0,
        "enabled": True,
        "nome": "Sensor DNP3 Teste 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA"
    }
    response = client.post("/Registradores_DNP3/", json=registrador_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Item criado com sucesso!"

    # Verifica se o item foi realmente inserido no banco de dados
    item = db_session.query(datapoints_dnp3).filter_by(
        xid_sensor="sensor_dnp3_test_01").first()
    assert item is not None
    assert item.nome == "Sensor DNP3 Teste 01"


def test_create_registrador_dnp3_duplicate(client):
    registrador_data = {
        "xid_sensor": "sensor_dnp3_test_01",
        "xid_equip": "equip_dnp3_test_02",
        "dnp3DataType": 1,
        "controlCommand": 0,
        "index": 0,
        "timeoff": 0,
        "timeon": 0,
        "enabled": True,
        "nome": "Sensor DNP3 Teste 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA"
    }
    # Tenta criar o mesmo registrador novamente
    response = client.post("/Registradores_DNP3/", json=registrador_data)
    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Item com este ID já existe no banco de dados."


def test_read_registrador_dnp3(client):
    response = client.get("/Registradores_DNP3/sensor_dnp3_test_01")
    assert response.status_code == 200
    assert response.json()["xid_sensor"] == "sensor_dnp3_test_01"
    assert response.json()["nome"] == "Sensor DNP3 Teste 01"


def test_read_registrador_dnp3_not_found(client):
    response = client.get("/Registradores_DNP3/sensor_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_update_registrador_dnp3(client, db_session):
    updated_data = {
        "xid_sensor": "sensor_dnp3_test_01",
        "xid_equip": "equip_dnp3_test_02",
        "dnp3DataType": 2,
        "controlCommand": 1,
        "index": 1,
        "timeoff": 100,
        "timeon": 200,
        "enabled": False,
        "nome": "Sensor DNP3 Atualizado 01",
        "tipo": "SAIDA",
        "classificacao": "DIGITAL"
    }
    response = client.put(
        "/Registradores_DNP3/sensor_dnp3_test_01", json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Item atualizado com sucesso!"

    # Verifica se o item foi realmente atualizado no banco de dados
    item = db_session.query(datapoints_dnp3).filter_by(
        xid_sensor="sensor_dnp3_test_01").first()
    assert item.nome == "Sensor DNP3 Atualizado 01"
    assert item.dnp3DataType == 2


def test_update_registrador_dnp3_not_found(client):
    updated_data = {
        "xid_sensor": "sensor_nao_existente",
        "xid_equip": "equip_dnp3_test_02",
        "dnp3DataType": 2,
        "controlCommand": 1,
        "index": 1,
        "timeoff": 100,
        "timeon": 200,
        "enabled": False,
        "nome": "Sensor DNP3 Atualizado 01",
        "tipo": "SAIDA",
        "classificacao": "DIGITAL"
    }
    response = client.put(
        "/Registradores_DNP3/sensor_nao_existente", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_delete_registrador_dnp3(client, db_session):
    response = client.delete("/Registradores_DNP3/sensor_dnp3_test_01")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deletado com sucesso!"

    # Verifica se o item foi realmente excluído do banco de dados
    item = db_session.query(datapoints_dnp3).filter_by(
        xid_sensor="sensor_dnp3_test_01").first()
    assert item is None


def test_delete_registrador_dnp3_not_found(client):
    response = client.delete("/Registradores_DNP3/sensor_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"

# ------------------------------------------------------------
# Testes para o endpoint de Tags de Equipamentos
# ------------------------------------------------------------


def test_create_tag_equipamento_success(client, db_session):
    tag_data = {
        "xid_equip": "equip_tag_test_01",
        "nome": "Tag Equip Teste 01",
        "valor": "10"
    }
    response = client.post("/Tags_equipamentos/", json=tag_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Item criado com sucesso!"

    # Verifica se o item foi realmente inserido no banco de dados
    item = db_session.query(eqp_tags).filter_by(
        xid_equip="equip_tag_test_01").first()
    assert item is not None
    assert item.nome == "Tag Equip Teste 01"


def test_create_tag_equipamento_duplicate(client):
    tag_data = {
        "xid_equip": "equip_tag_test_01",
        "nome": "Tag Equip Teste 01",
        "valor": "10"
    }
    # Tenta criar a mesma tag novamente
    response = client.post("/Tags_equipamentos/", json=tag_data)
    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Item com este ID já existe no banco de dados."


def test_read_tag_equipamento(client):
    response = client.get("/Tags_equipamentos/equip_tag_test_01")
    assert response.status_code == 200
    assert response.json()["xid_equip"] == "equip_tag_test_01"
    assert response.json()["nome"] == "Tag Equip Teste 01"


def test_read_tag_equipamento_not_found(client):
    response = client.get("/Tags_equipamentos/equip_tag_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_update_tag_equipamento(client, db_session):
    updated_data = {
        "xid_equip": "equip_tag_test_01",
        "nome": "Tag Equip Atualizada 01",
        "valor": "20"
    }
    response = client.put(
        "/Tags_equipamentos/equip_tag_test_01", json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Item atualizado com sucesso!"

    # Verifica se o item foi realmente atualizado no banco de dados
    item = db_session.query(eqp_tags).filter_by(
        xid_equip="equip_tag_test_01").first()
    assert item.nome == "Tag Equip Atualizada 01"
    assert item.valor == "20"


def test_update_tag_equipamento_not_found(client):
    updated_data = {
        "xid_equip": "equip_tag_nao_existente",
        "nome": "Tag Equip Atualizada 01",
        "valor": "20"
    }
    response = client.put(
        "/Tags_equipamentos/equip_tag_nao_existente", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_delete_tag_equipamento(client, db_session):
    response = client.delete("/Tags_equipamentos/equip_tag_test_01")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deletado com sucesso!"

    # Verifica se o item foi realmente excluído do banco de dados
    item = db_session.query(eqp_tags).filter_by(
        xid_equip="equip_tag_test_01").first()
    assert item is None


def test_delete_tag_equipamento_not_found(client):
    response = client.delete("/Tags_equipamentos/equip_tag_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"

# ------------------------------------------------------------
# Testes para o endpoint de Tags de Sensores
# ------------------------------------------------------------


def test_create_tag_sensor_success(client, db_session):
    tag_data = {
        "xid_sensor": "sensor_tag_test_01",
        "nome": "Tag Sensor Teste 01",
        "valor": "50"
    }
    response = client.post("/Tags_sensores/", json=tag_data)
    assert response.status_code == 200
    assert "id" in response.json()
    assert response.json()["message"] == "Item criado com sucesso!"

    # Verifica se o item foi realmente inserido no banco de dados
    item = db_session.query(dp_tags).filter_by(
        xid_sensor="sensor_tag_test_01").first()
    assert item is not None
    assert item.nome == "Tag Sensor Teste 01"


def test_create_tag_sensor_duplicate(client):
    tag_data = {
        "xid_sensor": "sensor_tag_test_01",
        "nome": "Tag Sensor Teste 01",
        "valor": "50"
    }
    # Tenta criar a mesma tag novamente
    response = client.post("/Tags_sensores/", json=tag_data)
    assert response.status_code == 400
    assert response.json()[
        "detail"] == "Item com este ID já existe no banco de dados."


def test_read_tag_sensor(client):
    response = client.get("/Tags_sensores/sensor_tag_test_01")
    assert response.status_code == 200
    assert response.json()["xid_sensor"] == "sensor_tag_test_01"
    assert response.json()["nome"] == "Tag Sensor Teste 01"


def test_read_tag_sensor_not_found(client):
    response = client.get("/Tags_sensores/sensor_tag_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_update_tag_sensor(client, db_session):
    updated_data = {
        "xid_sensor": "sensor_tag_test_01",
        "nome": "Tag Sensor Atualizada 01",
        "valor": "60"
    }
    response = client.put(
        "/Tags_sensores/sensor_tag_test_01", json=updated_data)
    assert response.status_code == 200
    assert response.json()["message"] == "Item atualizado com sucesso!"

    # Verifica se o item foi realmente atualizado no banco de dados
    item = db_session.query(dp_tags).filter_by(
        xid_sensor="sensor_tag_test_01").first()
    assert item.nome == "Tag Sensor Atualizada 01"
    assert item.valor == "60"


def test_update_tag_sensor_not_found(client):
    updated_data = {
        "xid_sensor": "sensor_tag_nao_existente",
        "nome": "Tag Sensor Atualizada 01",
        "valor": "60"
    }
    response = client.put(
        "/Tags_sensores/sensor_tag_nao_existente", json=updated_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


def test_delete_tag_sensor(client, db_session):
    response = client.delete("/Tags_sensores/sensor_tag_test_01")
    assert response.status_code == 200
    assert response.json()["message"] == "Item deletado com sucesso!"

    # Verifica se o item foi realmente excluído do banco de dados
    item = db_session.query(dp_tags).filter_by(
        xid_sensor="sensor_tag_test_01").first()
    assert item is None


def test_delete_tag_sensor_not_found(client):
    response = client.delete("/Tags_sensores/sensor_tag_nao_existente")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item não encontrado"


##############################################################
# Testes para functions.py
##############################################################

@pytest.mark.asyncio
async def test_database_connection():
    # Testa a conexão e desconexão do banco de dados
    await database.connect()
    assert database.is_connected == True
    await database.disconnect()
    assert database.is_connected == False


def test_service_checker_status(client):
    # Verifica se a função atualiza os status corretamente
    # Esse teste depende do comportamento assíncrono e pode precisar de ajustes
    response_cma = client.get("/cma_status")
    response_scada = client.get("/scada_status")
    assert response_cma.json() in ["online", "offline"]
    assert response_scada.json() in ["online", "offline"]


def test_send_data_to_scada_success(client):
    # Simula o envio de dados para o Scada-LTS
    data = 'callCount=1\npage=/Scada-LTS/import_project.htm\nhttpSessionId=\nscriptSessionId=D15BC242A0E69D4251D5585A07806324697\nc0-scriptName=EmportDwr\nc0-methodName=importData\nc0-id=0\nc0-param0=string:{"dataSources":[{"xid":"TESTE_ENVIO_SCADA", "type":"MODBUS_IP", "alarmLevels":{"POINT_WRITE_EXCEPTION":"URGENT", "DATA_SOURCE_EXCEPTION":"URGENT", "POINT_READ_EXCEPTION":"URGENT"}, "updatePeriodType":"SECONDS", "transportType":"TCP", "contiguousBatches":false, "createSlaveMonitorPoints":false, "createSocketMonitorPoint":false, "enabled":true, "encapsulated":false, "host":"192.168.1.20", "maxReadBitCount":200, "maxReadRegisterCount":100, "maxWriteRegisterCount":50, "name":"TESTE_ENVIO_SCADA", "port":502, "quantize":false, "retries":3, "timeout":1000, "updatePeriods":30}]}\nbatchId=8\n'
    result = send_data_to_scada(data)
    assert result == True


def test_send_data_to_scada_failure(client):
    # Simula uma falha no envio de dados para o Scada-LTS
    data = 'callCount=1\npage=/Scada-LTS/import_project.htm\nhttpSessionId=\nscriptSessionId=D15BC242A0E69D4251D5585A07806324697\nc0-scriptName=EmportDwr\nc0-methodName=importData\nc0-id=0\nc0-param0=string:{"dataSources":[{"xid":"TESTE_ENVIO_SCADA_FALHA", "type":"MODBUS_IP", "alarmLevels":{"POINT_WRITE_EXCEPTION":"URGENT", "DATA_SOURCE_EXCEPTION":"URGENT", "POINT_READ_EXCEPTION":"URGENT"}, "updatePeriodType":"SECONDS", "transportType":"TCP", "contiguousBatches":false, "createSlaveMonitorPoints":false, "createSocketMonitorPoint":false, "enabled":true, "encapsulated":false, "host":"0.0.0.0", "maxReadBitCount":200, "maxReadRegisterCount":100, "maxWriteRegisterCount":50, "name":"TESTE_ENVIO_SCADA_FALHA", "port":502, "quantize":false, "retries":3, "timeout":1000, "updatePeriods":30}]}\nbatchId=8\n'
    result = send_data_to_scada(data)
    assert result == False


def test_auth_ScadaLTS_success(client):
    # Simula uma autenticação bem sucedida no Scada-LTS
    result = auth_ScadaLTS()
    assert result == True


def test_auth_ScadaLTS_failure(client):
    # Simula uma autenticação mal sucedida no Scada-LTS
    global LOGIN_SCADA
    global PASSWORD_SCADA
    current_login = LOGIN_SCADA
    current_password = PASSWORD_SCADA

    # Altera as credenciais para forçar um erro
    LOGIN_SCADA = 'wronguser'
    PASSWORD_SCADA = 'wrongpassword'

    result = auth_ScadaLTS()

    # Restaura as credenciais originais
    LOGIN_SCADA = current_login
    PASSWORD_SCADA = current_password

    assert result == False


##############################################################
# Testes para models.py
##############################################################

def test_cma_gateway_model(db_session):
    # Testa a criação de um objeto cma_gateway
    gateway = cma_gateway(xid_gateway="gateway_model_test", subestacao="SE Model Teste",
                          regional="Regional Model Teste", host="192.168.1.10", status=True)
    db_session.add(gateway)
    db_session.commit()

    # Verifica se o objeto foi criado corretamente
    retrieved_gateway = db_session.query(cma_gateway).filter_by(
        xid_gateway="gateway_model_test").first()
    assert retrieved_gateway is not None
    assert retrieved_gateway.subestacao == "SE Model Teste"


def test_datasource_modbus_ip_model(db_session):
    # Testa a criação de um objeto datasource_modbus_ip
    # Primeiro, cria um gateway para associar ao equipamento
    gateway = cma_gateway(xid_gateway="gateway_equip_model_01", subestacao="SE Equip Model",
                          regional="Regional Equip Model", host="192.168.1.11", status=True)
    db_session.add(gateway)
    db_session.commit()

    equip = datasource_modbus_ip(xid_equip="equip_modbus_model_test", xid_gateway="gateway_equip_model_01", fabricante="Fabricante Model Teste", marca="Marca Model Teste", modelo="Modelo Model Teste", type="MODBUS_IP",
                                 sap_id=123456, enabled=True, updatePeriodType="SECONDS", maxReadBitCount=100, maxReadRegisterCount=50, maxWriteRegisterCount=25, host="192.168.1.12", port=502, retries=3, timeout=1000, updatePeriods=30)
    db_session.add(equip)
    db_session.commit()

    # Verifica se o objeto foi criado corretamente
    retrieved_equip = db_session.query(datasource_modbus_ip).filter_by(
        xid_equip="equip_modbus_model_test").first()
    assert retrieved_equip is not None
    assert retrieved_equip.fabricante == "Fabricante Model Teste"


def test_datapoints_modbus_ip_model(db_session):
    # Testa a criação de um objeto datapoints_modbus_ip
    # Primeiro, cria um equipamento para associar ao registrador
    equip = datasource_modbus_ip(xid_equip="equip_modbus_model_test_02", xid_gateway="gateway_equip_model_01", fabricante="Fabricante Model Teste 02", marca="Marca Model Teste 02", modelo="Modelo Model Teste 02", type="MODBUS_IP",
                                 sap_id=654321, enabled=True, updatePeriodType="SECONDS", maxReadBitCount=150, maxReadRegisterCount=75, maxWriteRegisterCount=35, host="192.168.1.13", port=503, retries=4, timeout=1500, updatePeriods=45)
    db_session.add(equip)
    db_session.commit()

    registrador = datapoints_modbus_ip(xid_sensor="sensor_modbus_model_test", xid_equip="equip_modbus_model_test_02", range="1-200", modbusDataType="INT",
                                       additive=0, offset=0, bit=0, multiplier=1, slaveId=1, enabled=True, nome="Sensor Model Teste", tipo="ENTRADA", classificacao="ANALOGICA")
    db_session.add(registrador)
    db_session.commit()

    # Verifica se o objeto foi criado corretamente
    retrieved_registrador = db_session.query(datapoints_modbus_ip).filter_by(
        xid_sensor="sensor_modbus_model_test").first()
    assert retrieved_registrador is not None
    assert retrieved_registrador.nome == "Sensor Model Teste"


def test_datasource_dnp3_model(db_session):
    # Testa a criação de um objeto datasource_dnp3
    # Primeiro, cria um gateway para associar ao equipamento
    gateway = cma_gateway(xid_gateway="gateway_dnp3_model_01", subestacao="SE DNP3 Model",
                          regional="Regional DNP3 Model", host="192.168.1.14", status=True)
    db_session.add(gateway)
    db_session.commit()

    equip = datasource_dnp3(xid_equip="equip_dnp3_model_test", xid_gateway="gateway_dnp3_model_01", fabricante="Fabricante DNP3 Model Teste", marca="Marca DNP3 Model Teste", modelo="Modelo DNP3 Model Teste",
                            type="DNP3_MASTER", sap_id=987654, enabled=True, eventsPeriodType="SECONDS", host="192.168.1.15", port=20000, rbePollPeriods=30, retries=2, slaveAddress=10, sourceAddress=1, staticPollPeriods=60, timeout=5000)
    db_session.add(equip)
    db_session.commit()

    # Verifica se o objeto foi criado corretamente
    retrieved_equip = db_session.query(datasource_dnp3).filter_by(
        xid_equip="equip_dnp3_model_test").first()
    assert retrieved_equip is not None
    assert retrieved_equip.fabricante == "Fabricante DNP3 Model Teste"


def test_datapoints_dnp3_model(db_session):
    # Testa a criação de um objeto datapoints_dnp3
    # Primeiro, cria um equipamento para associar ao registrador
    equip = datasource_dnp3(xid_equip="equip_dnp3_model_test_02", xid_gateway="gateway_dnp3_model_01", fabricante="Fabricante DNP3 Model Teste 02", marca="Marca DNP3 Model Teste 02", modelo="Modelo DNP3 Model Teste 02",
                            type="DNP3_MASTER", sap_id=456789, enabled=True, eventsPeriodType="SECONDS", host="192.168.1.16", port=20001, rbePollPeriods=45, retries=1, slaveAddress=12, sourceAddress=3, staticPollPeriods=90, timeout=3000)
    db_session.add(equip)
    db_session.commit()

    registrador = datapoints_dnp3(xid_sensor="sensor_dnp3_model_test", xid_equip="equip_dnp3_model_test_02", dnp3DataType=1, controlCommand=0,
                                  index=0, timeoff=0, timeon=0, enabled=True, nome="Sensor DNP3 Model Teste", tipo="ENTRADA", classificacao="ANALOGICA")
    db_session.add(registrador)
    db_session.commit()

    # Verifica se o objeto foi criado corretamente
    retrieved_registrador = db_session.query(datapoints_dnp3).filter_by(
        xid_sensor="sensor_dnp3_model_test").first()
    assert retrieved_registrador is not None
    assert retrieved_registrador.nome == "Sensor DNP3 Model Teste"


def test_eqp_tags_model(db_session):
    # Testa a criação de um objeto eqp_tags
    tag = eqp_tags(xid_equip="equip_tag_model_test",
                   nome="Tag Equip Model Teste", valor="30")
    db_session.add(tag)
    db_session.commit()

    # Verifica se o objeto foi criado corretamente
    retrieved_tag = db_session.query(eqp_tags).filter_by(
        xid_equip="equip_tag_model_test").first()
    assert retrieved_tag is not None
    assert retrieved_tag.nome == "Tag Equip Model Teste"


def test_dp_tags_model(db_session):
    # Testa a criação de um objeto dp_tags
    tag = dp_tags(xid_sensor="sensor_tag_model_test",
                  nome="Tag Sensor Model Teste", valor="70")
    db_session.add(tag)
    db_session.commit()

    # Verifica se o objeto foi criado corretamente
    retrieved_tag = db_session.query(dp_tags).filter_by(
        xid_sensor="sensor_tag_model_test").first()
    assert retrieved_tag is not None
    assert retrieved_tag.nome == "Tag Sensor Model Teste"


# ###########################################################
# Testes de Integração
# ------------------------------------------------------------
# Os testes de integração irão testar a interação entre
# diferentes partes do sistema.
# ###########################################################

def test_integration_create_gateway_and_equipamento_modbus_ip(client, db_session):
    # Cria um gateway
    gateway_data = {
        "xid_gateway": "gateway_integration_01",
        "subestacao": "SE Integração",
        "regional": "Regional Integração",
        "host": "192.168.1.100",
        "status": True,
    }
    gateway_response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert gateway_response.status_code == 200

    # Cria um equipamento Modbus IP associado ao gateway
    equip_data = {
        "xid_equip": "equip_integration_01",
        "xid_gateway": "gateway_integration_01",
        "fabricante": "Fabricante Integração",
        "marca": "Marca Integração",
        "modelo": "Modelo Integração",
        "type": "MODBUS_IP",
        "sap_id": 10000,
        "enabled": True,
        "updatePeriodType": "SECONDS",
        "maxReadBitCount": 100,
        "maxReadRegisterCount": 50,
        "maxWriteRegisterCount": 25,
        "host": "192.168.1.101",
        "port": 502,
        "retries": 3,
        "timeout": 1000,
        "updatePeriods": 30,
    }
    equip_response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
    assert equip_response.status_code == 200

    # Verifica se o equipamento foi criado corretamente e está associado ao gateway correto
    equip = db_session.query(datasource_modbus_ip).filter_by(
        xid_equip="equip_integration_01").first()
    assert equip is not None
    assert equip.xid_gateway == "gateway_integration_01"


def test_integration_create_equipamento_modbus_ip_and_registrador(client, db_session):
    # Cria um equipamento Modbus IP
    equip_data = {
        "xid_equip": "equip_integration_02",
        "xid_gateway": "gateway_integration_01",
        "fabricante": "Fabricante Integração 2",
        "marca": "Marca Integração 2",
        "modelo": "Modelo Integração 2",
        "type": "MODBUS_IP",
        "sap_id": 20000,
        "enabled": True,
        "updatePeriodType": "SECONDS",
        "maxReadBitCount": 100,
        "maxReadRegisterCount": 50,
        "maxWriteRegisterCount": 25,
        "host": "192.168.1.102",
        "port": 502,
        "retries": 3,
        "timeout": 1000,
        "updatePeriods": 30,
    }
    equip_response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
    assert equip_response.status_code == 200

    # Cria um registrador associado ao equipamento
    registrador_data = {
        "xid_sensor": "sensor_integration_01",
        "xid_equip": "equip_integration_02",
        "range": "0-100",
        "modbusDataType": "INT",
        "additive": 0,
        "offset": 0,
        "bit": 0,
        "multiplier": 1,
        "slaveId": 1,
        "enabled": True,
        "nome": "Sensor Integração 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA",
    }
    registrador_response = client.post(
        "/Registradores_Modbus_IP/", json=registrador_data)
    assert registrador_response.status_code == 200

    # Verifica se o registrador foi criado corretamente e está associado ao equipamento correto
    registrador = db_session.query(datapoints_modbus_ip).filter_by(
        xid_sensor="sensor_integration_01").first()
    assert registrador is not None
    assert registrador.xid_equip == "equip_integration_02"


def test_integration_create_gateway_and_equipamento_dnp3(client, db_session):
    # Cria um gateway
    gateway_data = {
        "xid_gateway": "gateway_integration_02",
        "subestacao": "SE Integração DNP3",
        "regional": "Regional Integração DNP3",
        "host": "192.168.1.103",
        "status": True,
    }
    gateway_response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert gateway_response.status_code == 200

    # Cria um equipamento DNP3 associado ao gateway
    equip_data = {
        "xid_equip": "equip_integration_dnp3_01",
        "xid_gateway": "gateway_integration_02",
        "fabricante": "Fabricante Integração DNP3",
        "marca": "Marca Integração DNP3",
        "modelo": "Modelo Integração DNP3",
        "type": "DNP3_MASTER",
        "sap_id": 30000,
        "enabled": True,
        "eventsPeriodType": "SECONDS",
        "host": "192.168.1.104",
        "port": 20000,
        "rbePollPeriods": 30,
        "retries": 2,
        "slaveAddress": 10,
        "sourceAddress": 1,
        "staticPollPeriods": 60,
        "timeout": 5000
    }
    equip_response = client.post("/Equipamentos_DNP3/", json=equip_data)
    assert equip_response.status_code == 200

    # Verifica se o equipamento foi criado corretamente e está associado ao gateway correto
    equip = db_session.query(datasource_dnp3).filter_by(
        xid_equip="equip_integration_dnp3_01").first()
    assert equip is not None
    assert equip.xid_gateway == "gateway_integration_02"


def test_integration_create_equipamento_dnp3_and_registrador(client, db_session):
    # Cria um equipamento DNP3
    equip_data = {
        "xid_equip": "equip_integration_dnp3_02",
        "xid_gateway": "gateway_integration_02",
        "fabricante": "Fabricante Integração DNP3 2",
        "marca": "Marca Integração DNP3 2",
        "modelo": "Modelo Integração DNP3 2",
        "type": "DNP3_MASTER",
        "sap_id": 40000,
        "enabled": True,
        "eventsPeriodType": "SECONDS",
        "host": "192.168.1.105",
        "port": 20000,
        "rbePollPeriods": 30,
        "retries": 2,
        "slaveAddress": 10,
        "sourceAddress": 1,
        "staticPollPeriods": 60,
        "timeout": 5000
    }
    equip_response = client.post("/Equipamentos_DNP3/", json=equip_data)
    assert equip_response.status_code == 200

    # Cria um registrador associado ao equipamento
    registrador_data = {
        "xid_sensor": "sensor_integration_dnp3_01",
        "xid_equip": "equip_integration_dnp3_02",
        "dnp3DataType": 1,
        "controlCommand": 0,
        "index": 0,
        "timeoff": 0,
        "timeon": 0,
        "enabled": True,
        "nome": "Sensor Integração DNP3 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA"
    }
    registrador_response = client.post(
        "/Registradores_DNP3/", json=registrador_data)
    assert registrador_response.status_code == 200

    # Verifica se o registrador foi criado corretamente e está associado ao equipamento correto
    registrador = db_session.query(datapoints_dnp3).filter_by(
        xid_sensor="sensor_integration_dnp3_01").first()
    assert registrador is not None
    assert registrador.xid_equip == "equip_integration_dnp3_02"

    # Remover os gateways criados para os testes de integração
    db_session.query(cma_gateway).filter(
        cma_gateway.xid_gateway.like('gateway_integration%')).delete()
    db_session.commit()


# ############################################################
# Testes de Performance
# ------------------------------------------------------------
# Os testes de performance irão medir o tempo de resposta
# da API para diferentes operações.
# ############################################################


def test_performance_create_gateway(client):
    # Mede o tempo de resposta para criar um gateway
    gateway_data = {
        "xid_gateway": "gateway_performance_01",
        "subestacao": "SE Performance",
        "regional": "Regional Performance",
        "host": "192.168.1.150",
        "status": True,
    }
    start_time = time.time()
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    end_time = time.time()
    assert response.status_code == 200
    assert end_time - start_time < 0.5  # Verifica se a operação levou menos de 500ms


def test_performance_create_equipamento_modbus_ip(client):
    # Mede o tempo de resposta para criar um equipamento Modbus IP
    equip_data = {
        "xid_equip": "equip_performance_01",
        "xid_gateway": "gateway_performance_01",
        "fabricante": "Fabricante Performance",
        "marca": "Marca Performance",
        "modelo": "Modelo Performance",
        "type": "MODBUS_IP",
        "sap_id": 50000,
        "enabled": True,
        "updatePeriodType": "SECONDS",
        "maxReadBitCount": 100,
        "maxReadRegisterCount": 50,
        "maxWriteRegisterCount": 25,
        "host": "192.168.1.151",
        "port": 502,
        "retries": 3,
        "timeout": 1000,
        "updatePeriods": 30,
    }
    start_time = time.time()
    response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
    end_time = time.time()
    assert response.status_code == 200
    # Verifica se a operação levou menos de 1s (considerando a comunicação com o Scada-LTS)
    assert end_time - start_time < 1


def test_performance_create_registrador_modbus_ip(client):
    # Mede o tempo de resposta para criar um registrador Modbus IP
    registrador_data = {
        "xid_sensor": "sensor_performance_01",
        "xid_equip": "equip_performance_01",
        "range": "0-100",
        "modbusDataType": "INT",
        "additive": 0,
        "offset": 0,
        "bit": 0,
        "multiplier": 1,
        "slaveId": 1,
        "enabled": True,
        "nome": "Sensor Performance 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA",
    }
    start_time = time.time()
    response = client.post("/Registradores_Modbus_IP/", json=registrador_data)
    end_time = time.time()
    assert response.status_code == 200
    # Verifica se a operação levou menos de 1s (considerando a comunicação com o Scada-LTS)
    assert end_time - start_time < 1


def test_performance_create_equipamento_dnp3(client):
    # Mede o tempo de resposta para criar um equipamento DNP3
    equip_data = {
        "xid_equip": "equip_performance_dnp3_01",
        "xid_gateway": "gateway_performance_01",
        "fabricante": "Fabricante Performance DNP3",
        "marca": "Marca Performance DNP3",
        "modelo": "Modelo Performance DNP3",
        "type": "DNP3_MASTER",
        "sap_id": 60000,
        "enabled": True,
        "eventsPeriodType": "SECONDS",
        "host": "192.168.1.152",
        "port": 20000,
        "rbePollPeriods": 30,
        "retries": 2,
        "slaveAddress": 10,
        "sourceAddress": 1,
        "staticPollPeriods": 60,
        "timeout": 5000
    }
    start_time = time.time()
    response = client.post("/Equipamentos_DNP3/", json=equip_data)
    end_time = time.time()
    assert response.status_code == 200
    # Verifica se a operação levou menos de 1s (considerando a comunicação com o Scada-LTS)
    assert end_time - start_time < 1


def test_performance_create_registrador_dnp3(client):
    # Mede o tempo de resposta para criar um registrador DNP3
    registrador_data = {
        "xid_sensor": "sensor_performance_dnp3_01",
        "xid_equip": "equip_performance_dnp3_01",
        "dnp3DataType": 1,
        "controlCommand": 0,
        "index": 0,
        "timeoff": 0,
        "timeon": 0,
        "enabled": True,
        "nome": "Sensor Performance DNP3 01",
        "tipo": "ENTRADA",
        "classificacao": "ANALOGICA"
    }
    start_time = time.time()
    response = client.post("/Registradores_DNP3/", json=registrador_data)
    end_time = time.time()
    assert response.status_code == 200
    # Verifica se a operação levou menos de 1s (considerando a comunicação com o Scada-LTS)
    assert end_time - start_time < 1


def test_performance_read_gateway(client):
    # Mede o tempo de resposta para ler um gateway
    start_time = time.time()
    response = client.get("/Cadastro_Gateway/gateway_performance_01")
    end_time = time.time()
    assert response.status_code == 200
    assert end_time - start_time < 0.5  # Verifica se a operação levou menos de 500ms


def test_performance_update_gateway(client):
    # Mede o tempo de resposta para atualizar um gateway
    updated_data = {
        "xid_gateway": "gateway_performance_01",
        "subestacao": "SE Performance Atualizada",
        "regional": "Regional Performance Atualizada",
        "host": "192.168.1.153",
        "status": False,
    }
    start_time = time.time()
    response = client.put(
        "/Cadastro_Gateway/gateway_performance_01", json=updated_data)
    end_time = time.time()
    assert response.status_code == 200
    assert end_time - start_time < 0.5  # Verifica se a operação levou menos de 500ms


def test_performance_delete_gateway(client, db_session):
    # Mede o tempo de resposta para deletar um gateway
    start_time = time.time()
    response = client.delete("/Cadastro_Gateway/gateway_performance_01")
    end_time = time.time()
    assert response.status_code == 200
    assert end_time - start_time < 0.5  # Verifica se a operação levou menos de 500ms

    # Limpa os dados criados para os testes de performance
    db_session.query(cma_gateway).filter(
        cma_gateway.xid_gateway.like('gateway_performance%')).delete()
    db_session.query(datasource_modbus_ip).filter(
        datasource_modbus_ip.xid_equip.like('equip_performance%')).delete()
    db_session.query(datapoints_modbus_ip).filter(
        datapoints_modbus_ip.xid_sensor.like('sensor_performance%')).delete()
    db_session.query(datasource_dnp3).filter(
        datasource_dnp3.xid_equip.like('equip_performance_dnp3%')).delete()
    db_session.query(datapoints_dnp3).filter(
        datapoints_dnp3.xid_sensor.like('sensor_performance_dnp3%')).delete()
    db_session.commit()


# #############################################################
# Testes de Usabilidade
# ------------------------------------------------------------
# Os testes de usabilidade irão verificar se a API é fácil
# de usar e entender.
# #############################################################
def test_usability_api_documentation(client):
    # Verifica se a documentação da API está acessível
    response = client.get("/docs")
    assert response.status_code == 200


def test_usability_clear_error_messages(client):
    # Verifica se a API retorna mensagens de erro claras
    # Envia um corpo de requisição vazio
    response = client.post("/Cadastro_Gateway/", json={})
    assert response.status_code == 422
    assert "detail" in response.json()  # Verifica se há detalhes sobre o erro


def test_usability_consistent_response_format(client, db_session):
    # Verifica se a API retorna respostas em um formato consistente

    # Cria um gateway para garantir que exista um item para ser lido
    gateway_data = {
        "xid_gateway": "gateway_usability_01",
        "subestacao": "SE Usabilidade",
        "regional": "Regional Usabilidade",
        "host": "192.168.1.1",
        "status": True,
    }
    client.post("/Cadastro_Gateway/", json=gateway_data)

    # Faz uma requisição GET para obter um item
    response = client.get("/Cadastro_Gateway/gateway_usability_01")
    assert response.status_code == 200
    assert "xid_gateway" in response.json()
    assert "subestacao" in response.json()
    assert "regional" in response.json()
    assert "host" in response.json()
    assert "status" in response.json()

    # Deleta o gateway criado para o teste
    client.delete("/Cadastro_Gateway/gateway_usability_01")


def test_usability_easy_to_understand_endpoints(client):
    # Verifica se os endpoints da API são fáceis de entender
    # Verifica se a rota para criar um gateway existe
    assert "/Cadastro_Gateway/" in app.routes[4].path
    # Verifica se a rota para ler um gateway existe
    assert "/Cadastro_Gateway/{item_id}" in app.routes[5].path
    # Verifica se a rota para criar um equipamento Modbus IP existe
    assert "/Equipamentos_Modbus_IP/" in app.routes[8].path

# #################################################################
# Testes de Regressão
# ------------------------------------------------------------
# Os testes de regressão irão verificar se novas mudanças não
# quebraram funcionalidades existentes.
# Para este exemplo, iremos reutilizar testes de outros
# conjuntos, como funcionalidade e performance.
# ################################################################


def test_regression_functionality(client):
    # Reutiliza testes de funcionalidade para garantir que as funcionalidades básicas ainda funcionam
    test_create_gateway_success(client, db_session)
    test_read_gateway(client)
    test_update_gateway(client, db_session)
    test_delete_gateway(client, db_session)


def test_regression_performance(client):
    # Reutiliza testes de performance para garantir que o desempenho ainda está dentro do aceitável
    test_performance_create_gateway(client)
    test_performance_read_gateway(client)
    test_performance_update_gateway(client)
    test_performance_delete_gateway(client, db_session)

# #################################################################
# Testes de Segurança para o endpoint Cadastro_Gateway
# -----------------------------------------------------------------
# Teste de SQL injector pela API, bem como verifica se há
# permissão para a execução de um Script malicioso
# #################################################################


def test_security_sql_injection_gateway(client):
    # Tenta injetar SQL malicioso na requisição
    malicious_data = {
        "xid_gateway": "' OR '1'='1",
        "subestacao": "SE Teste",
        "regional": "Regional Teste",
        "host": "192.168.1.1",
        "status": True,
    }
    response = client.post("/Cadastro_Gateway/", json=malicious_data)
    # Verifica se a API não retornou todos os dados ou causou um erro
    assert response.status_code != 200

    malicious_data = {
        "xid_gateway": "gateway_security_01",
        "subestacao": "' OR '1'='1",
        "regional": "Regional Teste",
        "host": "192.168.1.1",
        "status": True,
    }

    response = client.post("/Cadastro_Gateway/", json=malicious_data)
    # Verifica se a API não retornou todos os dados ou causou um erro
    assert response.status_code != 200

    malicious_data = {
        "xid_gateway": "gateway_security_01",
        "subestacao": "SE Teste",
        "regional": "' OR '1'='1",
        "host": "192.168.1.1",
        "status": True,
    }

    response = client.post("/Cadastro_Gateway/", json=malicious_data)
    # Verifica se a API não retornou todos os dados ou causou um erro
    assert response.status_code != 200

    malicious_data = {
        "xid_gateway": "gateway_security_01",
        "subestacao": "SE Teste",
        "regional": "Regional Teste",
        "host": "' OR '1'='1",
        "status": True,
    }

    response = client.post("/Cadastro_Gateway/", json=malicious_data)
    # Verifica se a API não retornou todos os dados ou causou um erro
    assert response.status_code != 200


def test_security_xss_gateway(client):
    # Tenta injetar script malicioso na requisição
    malicious_data = {
        "xid_gateway": "gateway_security_xss_01",
        "subestacao": "<script>alert('XSS')</script>",
        "regional": "Regional Teste",
        "host": "192.168.1.1",
        "status": True,
    }
    response = client.post("/Cadastro_Gateway/", json=malicious_data)
    # Verifica se o script foi salvo no banco, porem, não foi executado, retornando um codigo 200.
    assert response.status_code == 200
    # Verifica se a API não executou o script
    retrieved_data = client.get("/Cadastro_Gateway/gateway_security_xss_01")
    assert "<script>" not in retrieved_data.text and "</script>" not in retrieved_data.text

    # Deleta o gateway criado para o teste XSS
    client.delete("/Cadastro_Gateway/gateway_security_xss_01")


# ###############################################################
# Testes de Manutenibilidade
# ------------------------------------------------------------
# Os testes de manutenibilidade irão verificar se o código
# é fácil de manter e atualizar.
# ###############################################################
def test_manutenibility_code_style(client):
    # Verifica se o código segue as convenções de estilo do Python (PEP 8)
    import subprocess
    result = subprocess.run(["flake8", "."], capture_output=True, text=True)
    assert result.returncode == 0, f"Code style errors found:\n{result.stdout}"


def test_manutenibility_comments_and_docstrings(client):
    # Verifica se o código possui comentários e docstrings suficientes
    # Este teste é mais qualitativo e depende de uma revisão manual do código.
    # No entanto, podemos verificar se todas as funções e classes possuem docstrings.

    # Itera por todas as rotas da API
    for route in app.routes:
        if hasattr(route, "endpoint"):
            # Verifica se a função do endpoint possui docstring
            assert route.endpoint.__doc__ is not None, f"Missing docstring for endpoint: {route.path}"

    # Verifica se as funções no arquivo functions.py possuem docstring
    import functions
    for name, obj in vars(functions).items():
        if callable(obj) and obj.__module__ == functions.__name__:
            assert obj.__doc__ is not None, f"Missing docstring for function: {name} in functions.py"

    # Verifica se as classes no arquivo models.py possuem docstring
    import models
    for name, obj in vars(models).items():
        if isinstance(obj, type) and obj.__module__ == models.__name__:
            assert obj.__doc__ is not None, f"Missing docstring for class: {name} in models.py"


def test_manutenibility_modular_code(client):
    # Verifica se o código é modular e bem organizado
    # Este teste é mais qualitativo e depende de uma revisão manual do código.
    # Podemos verificar se as funções são curtas e coesas, e se as classes possuem responsabilidades claras.

    # Exemplo de verificação de tamanho de função (limite arbitrário de 50 linhas)
    import inspect
    import functions
    for name, obj in vars(functions).items():
        if callable(obj) and obj.__module__ == functions.__name__:
            lines = inspect.getsource(obj).splitlines()
            assert len(
                lines) <= 50, f"Function {name} in functions.py is too long ({len(lines)} lines)"

    # Exemplo de verificação de tamanho da rota (limite arbitrário de 50 linhas)
    for route in app.routes:
        if hasattr(route, "endpoint"):
            lines = inspect.getsource(route.endpoint).splitlines()
            assert len(
                lines) <= 50, f"Function {route.endpoint.__name__} in route {route.path} is too long ({len(lines)} lines)"


def test_manutenibility_no_duplicate_code(client):
    # Verifica se não há código duplicado
    # Este teste é mais qualitativo e depende de uma revisão manual do código.
    # Ferramentas como pylint podem ajudar a identificar código duplicado.
    import subprocess

    # Executa o pylint com o plugin pylint-fail-under para verificar a pontuação
    result = subprocess.run(["pylint", "--disable=R,C,W",
                            "--fail-under=8", "."], capture_output=True, text=True)

    # Verifica se a pontuação do pylint é maior ou igual a 8
    assert result.returncode == 0, f"Pylint found maintainability issues:\n{result.stdout}"


def test_manutenibility_test_coverage(client):
    # Verifica se a cobertura de testes é alta
    # Este teste depende da ferramenta coverage.py.
    import subprocess
    result = subprocess.run(
        ["coverage", "report", "--fail-under=80"], capture_output=True, text=True)
    assert result.returncode == 0, f"Test coverage is too low:\n{result.stdout}"


# #############################################################
# Testes de Escalabilidade
# ------------------------------------------------------------
# Os testes de escalabilidade irão verificar se a API pode
# lidar com um grande número de requisições.
# Para testar a escalabilidade, podemos usar ferramentas como o
# Locust ou o k6 para simular um grande número de usuários
# acessando a API.
# Aqui, faremos um teste simples usando multithreading para
# simular várias requisições simultâneas.
# #############################################################


def test_scalability_multiple_requests(client):
    # Testa a capacidade da API de lidar com múltiplas requisições simultâneas
    def create_gateway_thread(client, num):
        gateway_data = {
            "xid_gateway": f"gateway_scalability_{num}",
            "subestacao": f"SE Escalabilidade {num}",
            "regional": f"Regional Escalabilidade {num}",
            "host": f"192.168.1.{num}",
            "status": True,
        }
        response = client.post("/Cadastro_Gateway/", json=gateway_data)
        assert response.status_code == 200

    threads = []
    for i in range(10):  # Cria 10 gateways simultaneamente
        thread = threading.Thread(
            target=create_gateway_thread, args=(client, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Verifica se todos os gateways foram criados
    for i in range(10):
        response = client.get(f"/Cadastro_Gateway/gateway_scalability_{i}")
        assert response.status_code == 200
        # Deleta o gateway criado
        client.delete(f"/Cadastro_Gateway/gateway_scalability_{i}")


def test_scalability_multiple_requests_equip_modbus(client):
    # Testa a capacidade da API de lidar com múltiplas requisições simultâneas
    def create_equip_modbus_thread(client, num):
        equip_data = {
            "xid_equip": f"equip_scalability_{num}",
            "xid_gateway": f"gateway_scalability_0",
            "fabricante": f"Fabricante Escalabilidade {num}",
            "marca": f"Marca Escalabilidade {num}",
            "modelo": f"Modelo Escalabilidade {num}",
            "type": "MODBUS_IP",
            "sap_id": 10000+num,
            "enabled": True,
            "updatePeriodType": "SECONDS",
            "maxReadBitCount": 100,
            "maxReadRegisterCount": 50,
            "maxWriteRegisterCount": 25,
            "host": f"192.168.1.{num}",
            "port": 502,
            "retries": 3,
            "timeout": 1000,
            "updatePeriods": 30,
        }
        response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
        assert response.status_code == 200

    # Cria um gateway para o teste
    gateway_data = {
        "xid_gateway": f"gateway_scalability_0",
        "subestacao": f"SE Escalabilidade 0",
        "regional": f"Regional Escalabilidade 0",
        "host": f"192.168.1.0",
        "status": True,
    }
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert response.status_code == 200

    threads = []
    for i in range(10):  # Cria 10 equipamentos simultaneamente
        thread = threading.Thread(
            target=create_equip_modbus_thread, args=(client, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Verifica se todos os equipamentos foram criados
    for i in range(10):
        response = client.get(f"/Equipamentos_Modbus_IP/equip_scalability_{i}")
        assert response.status_code == 200
        # Deleta o equipamento criado
        client.delete(f"/Equipamentos_Modbus_IP/equip_scalability_{i}")

    # Deleta o gateway criado para o teste
    client.delete(f"/Cadastro_Gateway/gateway_scalability_0")


def test_scalability_time_response_multiple_requests(client):
    # Mede o tempo de resposta para múltiplas requisições simultâneas
    def create_gateway_thread(client, num):
        gateway_data = {
            "xid_gateway": f"gateway_time_scalability_{num}",
            "subestacao": f"SE Time Escalabilidade {num}",
            "regional": f"Regional Time Escalabilidade {num}",
            "host": f"192.168.2.{num}",
            "status": True,
        }
        start_time = time.time()
        response = client.post("/Cadastro_Gateway/", json=gateway_data)
        end_time = time.time()
        assert response.status_code == 200
        return end_time - start_time

    threads = []
    times = []
    for i in range(5):  # Cria 5 gateways simultaneamente
        thread = threading.Thread(
            target=create_gateway_thread, args=(client, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Captura os tempos de resposta
    for i in range(5):
        gateway_data = {
            "xid_gateway": f"gateway_time_scalability_{i}",
            "subestacao": f"SE Time Escalabilidade {i}",
            "regional": f"Regional Time Escalabilidade {i}",
            "host": f"192.168.2.{i}",
            "status": True,
        }
        start_time = time.time()
        response = client.post("/Cadastro_Gateway/", json=gateway_data)
        end_time = time.time()
        times.append(end_time - start_time)
        # Deleta o gateway criado
        client.delete(f"/Cadastro_Gateway/gateway_time_scalability_{i}")

    # Verifica se o tempo de resposta médio é aceitável
    average_time = sum(times) / len(times)
    print(f"Average response time for multiple requests: {average_time}")
    assert average_time < 1  # Verifica se o tempo de resposta médio é inferior a 1 segundo


# ################################################################
# Testes de Carga
# ------------------------------------------------------------
# Os testes de carga irão verificar como a API se comporta sob
# alta carga.
# Para testes de carga mais robustos, ferramentas como Locust
# ou k6 são recomendadas.
# Aqui, faremos um teste simples para criar um grande número
# de registros e verificar o comportamento da API.
# ################################################################
def test_load_create_many_gateways(client, db_session):
    # Testa a criação de um grande número de gateways
    num_gateways = 50
    for i in range(num_gateways):
        gateway_data = {
            "xid_gateway": f"gateway_load_{i}",
            "subestacao": f"SE Carga {i}",
            "regional": f"Regional Carga {i}",
            "host": f"192.168.3.{i}",
            "status": True,
        }
        response = client.post("/Cadastro_Gateway/", json=gateway_data)
        assert response.status_code == 200

    # Verifica se todos os gateways foram criados
    for i in range(num_gateways):
        response = client.get(f"/Cadastro_Gateway/gateway_load_{i}")
        assert response.status_code == 200

    # Limpa os dados criados
    db_session.query(cma_gateway).filter(
        cma_gateway.xid_gateway.like('gateway_load%')).delete()
    db_session.commit()


def test_load_create_many_equipamentos_modbus_ip(client, db_session):
    # Testa a criação de um grande número de equipamentos Modbus IP
    num_equipamentos = 50

    # Cria um gateway para os testes
    gateway_data = {
        "xid_gateway": f"gateway_load_equip_0",
        "subestacao": f"SE Carga Equip 0",
        "regional": f"Regional Carga Equip 0",
        "host": f"192.168.3.0",
        "status": True,
    }
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert response.status_code == 200

    for i in range(num_equipamentos):
        equip_data = {
            "xid_equip": f"equip_load_{i}",
            "xid_gateway": "gateway_load_equip_0",
            "fabricante": f"Fabricante Carga {i}",
            "marca": f"Marca Carga {i}",
            "modelo": f"Modelo Carga {i}",
            "type": "MODBUS_IP",
            "sap_id": 30000 + i,
            "enabled": True,
            "updatePeriodType": "SECONDS",
            "maxReadBitCount": 100,
            "maxReadRegisterCount": 50,
            "maxWriteRegisterCount": 25,
            "host": f"192.168.3.{i}",
            "port": 502,
            "retries": 3,
            "timeout": 1000,
            "updatePeriods": 30,
        }
        response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
        assert response.status_code == 200

    # Verifica se todos os equipamentos foram criados
    for i in range(num_equipamentos):
        response = client.get(f"/Equipamentos_Modbus_IP/equip_load_{i}")
        assert response.status_code == 200

     # Limpa os dados criados
    db_session.query(datasource_modbus_ip).filter(
        datasource_modbus_ip.xid_equip.like('equip_load%')).delete()
    db_session.query(cma_gateway).filter(
        cma_gateway.xid_gateway.like('gateway_load_equip%')).delete()
    db_session.commit()

# ################################################################
# Testes de Recuperação
# ------------------------------------------------------------
# Os testes de recuperação irá verificar se a API pode se
# recuperar de falhas.
# ################################################################


def test_recovery_database_reconnect(client, db_session):
    # Testa a recuperação da API após uma falha de conexão com o banco de dados

    # Força uma falha no banco (simulando uma queda do banco)
    db_session.close()

    # Tenta criar um gateway
    gateway_data = {
        "xid_gateway": "gateway_recovery_01",
        "subestacao": "SE Recuperação",
        "regional": "Regional Recuperação",
        "host": "192.168.4.1",
        "status": True,
    }

    response = None  # Inicializa a variável response
    try:
        response = client.post("/Cadastro_Gateway/", json=gateway_data)
    except Exception as e:
        print(f"Exceção capturada: {e}")

    assert response == None or response.status_code == 500

    # Reestabelece a conexão
    db_session.bind.engine.connect()

    # Tenta criar o gateway novamente
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert response.status_code == 200

    # Verifica se o gateway foi criado
    response = client.get("/Cadastro_Gateway/gateway_recovery_01")
    assert response.status_code == 200

    # Deleta o gateway criado
    client.delete("/Cadastro_Gateway/gateway_recovery_01")

# ################################################################
# Testes de Estresse
# ------------------------------------------------------------
# Os testes de estresse irão verificar como a API se comporta
# sob condições extremas.
# ################################################################


def test_stress_many_requests(client):
    # Testa a capacidade da API de lidar com um grande número de requisições em um curto período
    def create_gateway_thread(client, num):
        gateway_data = {
            "xid_gateway": f"gateway_stress_{num}",
            "subestacao": f"SE Estresse {num}",
            "regional": f"Regional Estresse {num}",
            "host": f"192.168.5.{num}",
            "status": True,
        }
        response = client.post("/Cadastro_Gateway/", json=gateway_data)
        assert response.status_code == 200

    threads = []
    for i in range(30):  # Cria 30 gateways em rápida sucessão
        thread = threading.Thread(
            target=create_gateway_thread, args=(client, i))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # Verifica se todos os gateways foram criados
    for i in range(30):
        response = client.get(f"/Cadastro_Gateway/gateway_stress_{i}")
        assert response.status_code == 200

    # Deleta os gateways criados
    for i in range(30):
        client.delete(f"/Cadastro_Gateway/gateway_stress_{i}")


def test_stress_large_payload(client, db_session):
    # Testa a capacidade da API de lidar com um payload grande
    long_string = "a" * 2000  # Cria uma string com 2000 caracteres
    gateway_data = {
        "xid_gateway": "gateway_stress_payload_01",
        "subestacao": long_string,
        "regional": "Regional Estresse Payload",
        "host": "192.168.6.1",
        "status": True,
    }
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert response.status_code == 200

    # Verifica se o gateway foi criado
    response = client.get("/Cadastro_Gateway/gateway_stress_payload_01")
    assert response.status_code == 200
    assert response.json()["subestacao"] == long_string

    # Deleta o gateway criado
    client.delete("/Cadastro_Gateway/gateway_stress_payload_01")


# ################################################################
# Testes de Desempenho de Longa Duração (Soak)
# ------------------------------------------------------------
# Os testes de desempenho de longa duração irão verificar a
# estabilidade da API ao longo do tempo.
# Esses testes podem levar várias horas ou dias para serem executados.
# Aqui, faremos um teste mais curto, executando operações por um
# período definido.
# ################################################################
def test_soak_create_and_delete_gateways(client):
    # Testa a estabilidade da API executando operações de criação e exclusão por um período
    end_time = time.time() + 120  # Executa por 2 minutos
    i = 0
    while time.time() < end_time:
        gateway_data = {
            "xid_gateway": f"gateway_soak_{i}",
            "subestacao": f"SE Soak {i}",
            "regional": f"Regional Soak {i}",
            "host": f"192.168.7.{i}",
            "status": True,
        }
        response = client.post("/Cadastro_Gateway/", json=gateway_data)
        assert response.status_code == 200

        response = client.delete(f"/Cadastro_Gateway/gateway_soak_{i}")
        assert response.status_code == 200
        i += 1
        time.sleep(1)  # Aguarda 1 segundo entre as operações


def test_soak_create_and_delete_equipamentos_modbus_ip(client):
    # Testa a estabilidade da API executando operações de criação e exclusão por um período

    # Cria um gateway para o teste
    gateway_data = {
        "xid_gateway": f"gateway_soak_equip_0",
        "subestacao": f"SE Soak Equip 0",
        "regional": f"Regional Soak Equip 0",
        "host": f"192.168.7.0",
        "status": True,
    }
    response = client.post("/Cadastro_Gateway/", json=gateway_data)
    assert response.status_code == 200

    end_time = time.time() + 120  # Executa por 2 minutos
    i = 0
    while time.time() < end_time:
        equip_data = {
            "xid_equip": f"equip_soak_{i}",
            "xid_gateway": "gateway_soak_equip_0",
            "fabricante": f"Fabricante Soak {i}",
            "marca": f"Marca Soak {i}",
            "modelo": f"Modelo Soak {i}",
            "type": "MODBUS_IP",
            "sap_id": 40000 + i,
            "enabled": True,
            "updatePeriodType": "SECONDS",
            "maxReadBitCount": 100,
            "maxReadRegisterCount": 50,
            "maxWriteRegisterCount": 25,
            "host": f"192.168.7.{i}",
            "port": 502,
            "retries": 3,
            "timeout": 1000,
            "updatePeriods": 30,
        }
        response = client.post("/Equipamentos_Modbus_IP/", json=equip_data)
        assert response.status_code == 200

        response = client.delete(f"/Equipamentos_Modbus_IP/equip_soak_{i}")
        assert response.status_code == 200
        i += 1
        time.sleep(1)  # Aguarda 1 segundo entre as operações

    # Deleta o gateway criado para o teste
    client.delete(f"/Cadastro_Gateway/gateway_soak_equip_0")

# ------------------------------------------------------------
# Fim dos Testes
# ------------------------------------------------------------


if __name__ == "__main__":
    # Configura o logging para salvar os resultados em um arquivo
    logging.basicConfig(filename='test_results.log', level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s')

    # Argumentos para o pytest
    pytest_args = [
        '-v',  # Modo verboso
        '--log-file=test_results.log',
        '--log-file-level=INFO',
        '--log-file-format=%(asctime)s - %(levelname)s - %(message)s',
        '--durations=10'  # Mostra os 10 testes mais lentos
    ]

    # Adiciona os testes ao script atual
    pytest_args.append(__file__)

    # Executa os testes com os argumentos especificados
    pytest_result = pytest.main(pytest_args)

    # Imprime o resultado no console
    if pytest_result == 0:
        print("\nTodos os testes passaram!")
        logging.info("Todos os testes passaram!")
    else:
        print("\nAlguns testes falharam. Verifique o arquivo test_results.log para mais detalhes.")
        logging.error("Alguns testes falharam.")
