"""
sharpe-b3: análise de rentabilidade e risco de ações da B3.

Roda todas as etapas em sequência:
coleta, tratamento, métricas, correlação, gráficos, tabela resumo e conclusões.

Uso: python main.py
"""

import os
from datetime import date

import pandas as pd

from src import coleta, conclusoes, graficos, metricas, tratamento

TICKERS = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA", "BBAS3.SA",
    "WEGE3.SA", "ABEV3.SA", "MGLU3.SA", "RENT3.SA", "SUZB3.SA",
    "^BVSP",
]
BENCHMARK = "IBOV"
ANOS = 5
ATIVOS_VOLATILIDADE_MOVEL = ["PETR4", "MGLU3"]

# Mude para True para ignorar os CSVs salvos e baixar tudo de novo.
FORCAR_DOWNLOAD = False

PASTA_BRUTOS = os.path.join("data", "brutos")
PASTA_TRATADOS = os.path.join("data", "tratados")
PASTA_OUTPUTS = "outputs"


def criar_pastas():
    # Garante que as pastas de dados e de resultados existem.
    for pasta in [PASTA_BRUTOS, PASTA_TRATADOS, PASTA_OUTPUTS]:
        os.makedirs(pasta, exist_ok=True)


def definir_periodo():
    # Período da análise: de hoje até 5 anos atrás.
    data_fim = date.today()
    data_inicio = data_fim.replace(year=data_fim.year - ANOS)
    return data_inicio, data_fim


def main():
    criar_pastas()
    graficos.configurar_estilo()
    data_inicio, data_fim = definir_periodo()

    print("1. Coleta")
    precos_brutos = coleta.obter_precos(
        TICKERS, data_inicio, data_fim,
        os.path.join(PASTA_BRUTOS, "precos_brutos.csv"), FORCAR_DOWNLOAD)
    cdi_bruto = coleta.obter_cdi(
        data_inicio, data_fim,
        os.path.join(PASTA_BRUTOS, "cdi_bruto.csv"), FORCAR_DOWNLOAD)

    print("2. Tratamento")
    precos, relatorio = tratamento.tratar_precos(precos_brutos, BENCHMARK)
    retornos_cdi = tratamento.alinhar_cdi(cdi_bruto, precos.index)
    print(relatorio.to_string())
    precos.to_csv(os.path.join(PASTA_TRATADOS, "precos_tratados.csv"))
    retornos_cdi.to_csv(os.path.join(PASTA_TRATADOS, "cdi_tratado.csv"))
    relatorio.to_csv(os.path.join(PASTA_TRATADOS, "relatorio_qualidade.csv"))

    print("3. Métricas")
    retornos = metricas.calcular_retorno_simples(precos)
    retornos_log = metricas.calcular_retorno_log(precos)
    retornos.to_csv(os.path.join(PASTA_TRATADOS, "retornos_simples.csv"))
    retornos_log.to_csv(os.path.join(PASTA_TRATADOS, "retornos_log.csv"))
    tabela, cdi_anualizado = metricas.montar_tabela_resumo(
        precos, retornos_cdi, BENCHMARK)

    print("4. Correlação")
    correlacao = metricas.calcular_matriz_correlacao(retornos)
    correlacao.round(4).to_csv(os.path.join(PASTA_OUTPUTS, "correlacao.csv"))

    print("5. Gráficos")
    base_100 = metricas.calcular_base_100(precos)
    drawdown = metricas.calcular_curva_drawdown(precos)
    volatilidade_movel = metricas.calcular_volatilidade_movel(retornos, janela=21)
    graficos.plotar_retorno_acumulado(
        base_100, BENCHMARK,
        os.path.join(PASTA_OUTPUTS, "01_retorno_acumulado.png"))
    graficos.plotar_drawdown(
        drawdown, tabela, BENCHMARK,
        os.path.join(PASTA_OUTPUTS, "02_drawdown.png"))
    graficos.plotar_heatmap_correlacao(
        correlacao, os.path.join(PASTA_OUTPUTS, "03_correlacao.png"))
    graficos.plotar_risco_retorno(
        tabela, cdi_anualizado, BENCHMARK,
        os.path.join(PASTA_OUTPUTS, "04_risco_retorno.png"))
    graficos.plotar_volatilidade_movel(
        volatilidade_movel, ATIVOS_VOLATILIDADE_MOVEL, BENCHMARK,
        os.path.join(PASTA_OUTPUTS, "05_volatilidade_movel.png"))

    print("6. Tabela resumo (ordenada por Sharpe)")
    tabela.round(4).to_csv(os.path.join(PASTA_OUTPUTS, "tabela_resumo.csv"))
    with pd.option_context("display.width", 200, "display.float_format",
                           "{:.4f}".format):
        print(tabela)
    print("  CDI anualizado no período: {:.4f}".format(cdi_anualizado))

    print("7. Conclusões")
    periodo = "{} a {}".format(precos.index[0].strftime("%d/%m/%Y"),
                               precos.index[-1].strftime("%d/%m/%Y"))
    observacoes = conclusoes.gerar_conclusoes(
        tabela, correlacao, retornos, cdi_anualizado, BENCHMARK)
    conclusoes.salvar_conclusoes(
        observacoes, periodo, os.path.join(PASTA_OUTPUTS, "conclusoes.md"))
    print("  Período:", periodo)
    for observacao in observacoes:
        print("  " + observacao)


if __name__ == "__main__":
    main()
