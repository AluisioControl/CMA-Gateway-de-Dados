import pycurl
from io import BytesIO


def execute_request(url, headers):
    response_buffer = BytesIO()
    c = pycurl.Curl()

    try:
        c.setopt(c.URL, url)
        c.setopt(c.FOLLOWLOCATION, True)
        c.setopt(c.HTTPHEADER, headers)
        c.setopt(c.WRITEFUNCTION, response_buffer.write)
        c.perform()
        status_code = c.getinfo(c.RESPONSE_CODE)
        print(f'Status Code: {status_code}')
        response_data = response_buffer.getvalue().decode('utf-8')
        return status_code, response_data

    except:
        return 404, "Erro ao conectar no Scada! Verifique a conexão!"

    finally:
        c.close()


###########################################
# Auth user
###########################################
auth_url = 'http://localhost:8080/Scada-LTS/api/auth/admin/admin'
auth_cookie = 'JSESSIONID=5DED757668A95F764E21E34DA175D132'
auth_headers = [f'Cookie: {auth_cookie}']
autth_code_response, auth_data_response = execute_request(
    auth_url, auth_headers)
print(f'Auth Code Response: {autth_code_response}')
print(f'Auth Data Response: {auth_data_response}')


###########################################
# Get value
###########################################
data_url = 'http://localhost:8080/Scada-LTS/api/point_value/getValue/DP_319182'
data_cookie = 'JSESSIONID=9AAE249BA860C6CF02650365A0E6DB39'
data_headers = [
    'Accept: application/json',
    f'Cookie: {data_cookie}'
]
data_code_response, data_response = execute_request(data_url, data_headers)
print(f'Data Code Response: {data_code_response}')
print(f'Data Response: {data_response}')
