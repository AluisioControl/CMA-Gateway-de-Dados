# Gateway de dados

Repositório pra projeto com Instituto Atlântico e ISA CTEEP


## Requisitos

Antes de iniciar, certifique-se de que o gerenciador de pacotes `uv` está instalado. Caso não esteja, utilize o seguinte comando para instalá-lo:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## Instalação de Dependências

A instalação das dependências é necessária apenas na primeira execução ou quando houver alterações nas mesmas.

```bash
uv sync
```

## Para rodar o configurador, abra o terminal no mesmo diretório do script e digite:
```bash
    ./configurator.sh
```

### Iniciar a aplicação do Gateway de Dados

Para coletar as informações da API CMA_WEB, execute:

```bash
    uv run python src/main.py
```

## Para rodar as rotinas de testes digite no diretório 'tests':
```bash
  python3 -m pytest -s -v
```

## Para acompanhar o log de eventos (erro ou warning):
```bash
- No Windows: C:\middleware_log.log
- No linux: logs/middleware_log.log ou execute ./syslog_verify dentro da pasta 'scripts'
``` 
