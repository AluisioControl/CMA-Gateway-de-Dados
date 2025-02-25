# Gateway de dados

Repositório pra projeto com Instituto Atlântico e ISA CTEEP


## Para instalar dependências:  
```bash
  sudo apt-get install -y crudini
  pip3 install -r requirements.txt
```

## Para rodar o configurador, abra o terminal no mesmo diretório do script e digite:
```bash
    ./config.sh
```

## Para rodar as rotinas de testes digite no diretório 'tests':
```bash
  python3 -m pytest -s -v
```

## Para acompanhar o log de eventos (erro ou warning):
```bash
- No Windows: C:\middleware_log.log
- No linux: logs/middleware_log.log
``` 
