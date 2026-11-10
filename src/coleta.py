"""
Etapa 1: coleta dos dados brutos.

- Preços: Yahoo Finance, pela biblioteca yfinance (fechamento ajustado).
- CDI: API do Banco Central (SGS, série 12), taxa em % ao dia.

Os dados baixados ficam salvos em CSV. Se o arquivo já existe, ele é lido
do disco em vez de baixar tudo de novo.
"""

import os

import pandas as pd
import requests
import yfinance as yf

URL_SGS = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo}/dados"
CODIGO_CDI = 12


def limpar_nome_ticker(ticker):
    # Tira o sufixo .SA e troca ^BVSP por IBOV, para os nomes ficarem legíveis.
    if ticker == "^BVSP":
        nome = "IBOV"
    else:
        nome = ticker.replace(".SA", "")
    return nome


def baixar_precos(tickers, data_inicio, data_fim):
    # Baixa o fechamento ajustado de cada ticker e junta tudo em uma tabela
    # (uma coluna por ativo, uma linha por dia).
    series = {}
    for ticker in tickers:
        dados = yf.download(
            ticker,
            start=data_inicio,
            end=data_fim,
            auto_adjust=False,
            progress=False,
            multi_level_index=False,
        )
        if dados.empty:
            print("  AVISO: o ticker", ticker, "veio vazio do Yahoo")
        else:
            # "Adj Close" é o fechamento ajustado por dividendos, JCP,
            # desdobramentos e grupamentos.
            series[limpar_nome_ticker(ticker)] = dados["Adj Close"]

    precos = pd.DataFrame(series)
    precos.index.name = "data"
    return precos


def baixar_cdi(data_inicio, data_fim):
    # Baixa a taxa diária do CDI (em % ao dia) na API do Banco Central.
    url = URL_SGS.format(codigo=CODIGO_CDI)
    parametros = {
        "formato": "json",
        "dataInicial": data_inicio.strftime("%d/%m/%Y"),
        "dataFinal": data_fim.strftime("%d/%m/%Y"),
    }
    resposta = requests.get(url, params=parametros, timeout=60)
    resposta.raise_for_status()
    registros = resposta.json()

    datas = []
    taxas = []
    for registro in registros:
        datas.append(pd.to_datetime(registro["data"], format="%d/%m/%Y"))
        taxas.append(float(registro["valor"]))

    cdi = pd.DataFrame({"cdi_pct_dia": taxas}, index=datas)
    cdi.index.name = "data"
    return cdi


def ler_csv_com_datas(caminho):
    # Lê um CSV salvo por este projeto, usando a coluna "data" como índice.
    tabela = pd.read_csv(caminho, index_col="data", parse_dates=True)
    return tabela


def obter_precos(tickers, data_inicio, data_fim, caminho, forcar_download=False):
    # Devolve os preços brutos: lê do CSV se ele já existe, senão baixa e salva.
    if os.path.exists(caminho) and not forcar_download:
        print("  Preços lidos do cache:", caminho)
        precos = ler_csv_com_datas(caminho)
    else:
        print("  Baixando preços do Yahoo Finance...")
        precos = baixar_precos(tickers, data_inicio, data_fim)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        precos.to_csv(caminho)
    return precos


def obter_cdi(data_inicio, data_fim, caminho, forcar_download=False):
    # Devolve o CDI bruto: lê do CSV se ele já existe, senão baixa e salva.
    if os.path.exists(caminho) and not forcar_download:
        print("  CDI lido do cache:", caminho)
        cdi = ler_csv_com_datas(caminho)
    else:
        print("  Baixando CDI do Banco Central...")
        cdi = baixar_cdi(data_inicio, data_fim)
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        cdi.to_csv(caminho)
    return cdi
