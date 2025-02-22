import json


def reads_json_data(json_data):
    parsed_data = json.loads(json_data)
    return parsed_data.get("value")


# JSON do Scada
json_data = '''
{
    "id": 86,
    "value": 123456,
    "formattedValue": null,
    "ts": null,
    "name": "Teste",
    "xid": "DP_480034",
    "type": null,
    "textRenderer": {
        "suffix": "",
        "typeName": "textRendererPlain",
        "metaText": "",
        "def": {
            "id": 0,
            "name": "textRendererPlain",
            "exportName": "PLAIN",
            "nameKey": "textRenderer.plain",
            "supportedDataTypes": [
                1,
                4,
                2,
                3
            ]
        },
        "colour": null
    },
    "chartColour": null
}
'''

print(reads_json_data(json_data))
