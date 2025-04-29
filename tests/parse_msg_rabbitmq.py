import json

# Lê o arquivo com as mensagens brutas (strings JSON)
with open("mensagens_gateway.json", "r") as f:
    mensagens_str = json.load(f)

mensagens_formatadas = []

# Para cada string JSON da lista
for msg in mensagens_str:
    try:
        dados = json.loads(msg)  # Transforma string em dict

        # 🧠 Aqui você adapta conforme os dados disponíveis em cada mensagem
        estrutura = {
            "gateways": {
                "timestamp": "1742284800.0000002",
                "gateway_id": 2,
                "gateway_name": "TesteGateway",
                "gateway_ip": "192.168.100.222",
                "SE_id": 3,
                "SE": "Manguaguá",
                "SE_Region": "MGG"
            },
            "sensors": {
                "hardware_id": 5,
                "hardware_name": "Cubículo 01",
                "sap_id": 1000,
                "type": "CUBICULO",
                "model": None,
                "sensor_id": 8,
                "sensor_name": "Brax_001",
                "sensor_model": "DPTU01",
                "sensor_ip": "192.168.0.102",
                "sensor_protocol": "MODBUS",
                "manufacturer_id": 2,
                "manufacturer_name": "Brax",
                "sensor_tags": '[{"id": 19, "name": "Cubículo", "value": "outdoor"}]'
            },
            "registers": {
                "register_id": 5,
                "register_name": "reg_0001",
                "register": 0,
                "phase": None,
                "circuitBreakerManeuverType": None,
                "bushingSide": None,
                "register_type_id": 1,
                "register_type": "Grandeza Analogica",
                "sensor_type_id": 2,
                "sensor_type": "Umidade",
                "register_tags": '[{"id": 8, "name": "Umidade", "value": "01"}]',
                "register_value": 9.67
            }
        }

        mensagens_formatadas.append(estrutura)

    except json.JSONDecodeError as e:
        print(f"❌ Erro ao decodificar JSON: {e}")
        continue

# Salvar arquivo formatado
with open("mensagens_gateway_formatadas.json", "w", encoding="utf-8") as f:
    json.dump(mensagens_formatadas, f, indent=4, ensure_ascii=False)

print("✅ Mensagens formatadas salvas em 'mensagens_gateway_formatadas.json'")
