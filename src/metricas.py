"""
Etapa 3 e 4: métricas de retorno e risco, e correlação.

Convenção: 252 é o número aproximado de pregões em um ano.
"""

import numpy as np
import pandas as pd

DIAS_UTEIS_ANO = 252


def calcular_retorno_simples(precos):
    # Retorno simples: (preço de hoje / preço de ontem) - 1.
    # pct_change faz essa conta para cada linha em relação à anterior.
    # A primeira linha fica vazia (não tem dia anterior), por isso o dropna.
    retornos = precos.pct_change().dropna()
    return retornos


def calcular_retorno_log(precos):
    # Retorno logarítmico: ln(preço de hoje / preço de ontem).
    # shift(1) desloca a série uma linha para baixo, trazendo o preço de ontem.
    # Vantagem: retornos log de vários dias podem ser somados.
    retornos = np.log(precos / precos.shift(1)).dropna()
    return retornos


def calcular_retorno_acumulado(precos_ativo):
    # Retorno total do período: (último preço / primeiro preço) - 1.
    preco_inicial = precos_ativo.iloc[0]
    preco_final = precos_ativo.iloc[-1]
    retorno = preco_final / preco_inicial - 1
    return retorno


def anualizar_retorno(retorno_acumulado, numero_dias):
    # Transforma o retorno do período todo em uma taxa equivalente por ano,
    # usando juros compostos: (1 + acumulado) ^ (252 / dias) - 1.
    retorno_anual = (1 + retorno_acumulado) ** (DIAS_UTEIS_ANO / numero_dias) - 1
    return retorno_anual


def calcular_volatilidade_anualizada(retornos_ativo):
    # Volatilidade: desvio padrão dos retornos diários, levado para a
    # escala anual multiplicando pela raiz de 252.
    volatilidade = retornos_ativo.std() * np.sqrt(DIAS_UTEIS_ANO)
    return volatilidade


def calcular_curva_drawdown(precos):
    # Drawdown: quanto o preço está abaixo do maior valor já atingido.
    # cummax guarda, em cada dia, o maior preço visto até aquele dia.
    pico_ate_o_dia = precos.cummax()
    drawdown = precos / pico_ate_o_dia - 1
    return drawdown


def calcular_drawdown_maximo(precos_ativo):
    # Acha a pior queda do pico até o fundo, com as duas datas.
    drawdown = calcular_curva_drawdown(precos_ativo)
    data_fundo = drawdown.idxmin()
    # O pico é o maior preço antes do fundo.
    data_pico = precos_ativo.loc[:data_fundo].idxmax()
    resultado = {
        "valor": drawdown.min(),
        "data_pico": data_pico,
        "data_fundo": data_fundo,
    }
    return resultado


def calcular_cdi_acumulado(retornos_cdi):
    # Acumula o CDI do período com juros compostos.
    # prod multiplica todos os fatores (1 + retorno diário).
    cdi_acumulado = (1 + retornos_cdi).prod() - 1
    return cdi_acumulado


def calcular_sharpe(retorno_anualizado, cdi_anualizado, volatilidade_anualizada):
    # Sharpe: retorno acima do CDI dividido pela volatilidade.
    # Mostra quanto de prêmio o ativo entregou por unidade de risco.
    sharpe = (retorno_anualizado - cdi_anualizado) / volatilidade_anualizada
    return sharpe


def calcular_beta(retornos_ativo, retornos_mercado):
    # Beta: covariância do ativo com o mercado dividida pela variância
    # do mercado. Mede a sensibilidade do ativo aos movimentos do índice.
    covariancia = retornos_ativo.cov(retornos_mercado)
    variancia_mercado = retornos_mercado.var()
    beta = covariancia / variancia_mercado
    return beta


def calcular_matriz_correlacao(retornos):
    # Correlação de Pearson entre os retornos diários de cada par de ativos.
    # Vai de -1 (andam em sentidos opostos) a +1 (andam juntos).
    correlacao = retornos.corr()
    return correlacao


def calcular_volatilidade_movel(retornos, janela=21):
    # Volatilidade anualizada calculada em uma janela que desliza no tempo.
    # rolling(21) pega sempre os últimos 21 pregões (cerca de um mês).
    volatilidade = retornos.rolling(janela).std() * np.sqrt(DIAS_UTEIS_ANO)
    volatilidade = volatilidade.dropna()
    return volatilidade


def calcular_base_100(precos):
    # Reescala os preços para todos começarem em 100, o que permite
    # comparar ativos com preços muito diferentes no mesmo gráfico.
    base_100 = precos / precos.iloc[0] * 100
    return base_100


def montar_tabela_resumo(precos, retornos_cdi, benchmark):
    # Calcula todas as métricas de cada ativo e devolve uma tabela
    # ordenada pelo Sharpe, do maior para o menor.
    retornos = calcular_retorno_simples(precos)
    numero_dias = len(retornos)
    cdi_acumulado = calcular_cdi_acumulado(retornos_cdi)
    cdi_anualizado = anualizar_retorno(cdi_acumulado, numero_dias)

    linhas = []
    for ativo in precos.columns:
        retorno_acumulado = calcular_retorno_acumulado(precos[ativo])
        retorno_anualizado = anualizar_retorno(retorno_acumulado, numero_dias)
        volatilidade = calcular_volatilidade_anualizada(retornos[ativo])
        drawdown = calcular_drawdown_maximo(precos[ativo])
        sharpe = calcular_sharpe(retorno_anualizado, cdi_anualizado, volatilidade)
        beta = calcular_beta(retornos[ativo], retornos[benchmark])

        linha = {
            "ativo": ativo,
            "retorno_acumulado": retorno_acumulado,
            "retorno_anualizado": retorno_anualizado,
            "volatilidade_anualizada": volatilidade,
            "drawdown_maximo": drawdown["valor"],
            "data_pico": drawdown["data_pico"].date(),
            "data_fundo": drawdown["data_fundo"].date(),
            "sharpe": sharpe,
            "beta": beta,
        }
        linhas.append(linha)

    tabela = pd.DataFrame(linhas).set_index("ativo")
    tabela = tabela.sort_values("sharpe", ascending=False)
    return tabela, cdi_anualizado
