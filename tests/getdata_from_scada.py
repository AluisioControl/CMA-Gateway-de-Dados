import pycurl
from io import BytesIO

url = 'http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_319182'
cookie = 'JSESSIONID=9AAE249BA860C6CF02650365A0E6DB39'

response_buffer = BytesIO()
c = pycurl.Curl()

try:
    c.setopt(c.URL, url)
    c.setopt(c.FOLLOWLOCATION, True)
    c.setopt(c.HTTPHEADER, [
        'Accept: application/json',
        f'Cookie: {cookie}'
    ])
    c.setopt(c.WRITEFUNCTION, response_buffer.write)
    c.perform()
    status_code = c.getinfo(c.RESPONSE_CODE)
    print(f'Status Code: {status_code}')
    response_data = response_buffer.getvalue().decode('utf-8')
    print(f'Response Body: {response_data}')
except:
    print("Erro ao conectar no Scada! Verifique a conexão!")    
finally:
    c.close()
