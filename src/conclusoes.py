"""
Etapa 7: conclusões.

O texto é montado a partir dos números calculados, então ele continua
correto se os dados forem atualizados.
"""


def formatar_pct(valor):
    # Formata um número como percentual no padrão brasileiro (12,3%).
    texto = "{:.1f}%".format(valor * 100).replace(".", ",")
    return texto


def formatar_numero(valor):
    # Formata um número com duas casas e vírgula decimal.
    texto = "{:.2f}".format(valor).replace(".", ",")
    return texto


def formatar_mes(data):
    # Formata uma data como mês/ano (03/2023).
    texto = data.strftime("%m/%Y")
    return texto


def achar_pares_extremos(correlacao, benchmark):
    # Procura o par de ações mais correlacionado e o menos correlacionado.
    # O benchmark fica de fora, porque ele é formado pelas próprias ações.
    acoes = []
    for ativo in correlacao.columns:
        if ativo != benchmark:
            acoes.append(ativo)

    maior_valor = -2.0
    menor_valor = 2.0
    maior_par = None
    menor_par = None
    for i in range(len(acoes)):
        for j in range(i + 1, len(acoes)):
            valor = correlacao.loc[acoes[i], acoes[j]]
            if valor > maior_valor:
                maior_valor = valor
                maior_par = (acoes[i], acoes[j])
            if valor < menor_valor:
                menor_valor = valor
                menor_par = (acoes[i], acoes[j])

    resultado = {
        "maior_par": maior_par,
        "maior_valor": maior_valor,
        "menor_par": menor_par,
        "menor_valor": menor_valor,
    }
    return resultado


def contar_acima_do_cdi(tabela, benchmark):
    # Conta quantas ações tiveram Sharpe positivo, ou seja, renderam
    # mais do que o CDI no período.
    quantidade = 0
    for ativo in tabela.index:
        if ativo != benchmark and tabela.loc[ativo, "sharpe"] > 0:
            quantidade = quantidade + 1
    return quantidade


def gerar_conclusoes(tabela, correlacao, retornos, cdi_anualizado, benchmark):
    # Monta a lista de observações em texto a partir das métricas.
    acoes = tabela.drop(index=benchmark)
    pior_dia = retornos[benchmark].idxmin()
    melhor = acoes.index[0]
    pior = acoes.index[-1]
    maior_queda = acoes["drawdown_maximo"].idxmin()
    mais_volatil = acoes["volatilidade_anualizada"].idxmax()
    menos_volatil = acoes["volatilidade_anualizada"].idxmin()
    maior_beta = acoes["beta"].idxmax()
    menor_beta = acoes["beta"].idxmin()
    pares = achar_pares_extremos(correlacao, benchmark)
    acima_do_cdi = contar_acima_do_cdi(tabela, benchmark)

    observacoes = []

    observacoes.append(
        "1. Melhor relação risco/retorno: {} teve o maior Sharpe ({}), com "
        "retorno anualizado de {} e volatilidade de {}. No outro extremo, {} "
        "teve o pior Sharpe ({}).".format(
            melhor,
            formatar_numero(acoes.loc[melhor, "sharpe"]),
            formatar_pct(acoes.loc[melhor, "retorno_anualizado"]),
            formatar_pct(acoes.loc[melhor, "volatilidade_anualizada"]),
            pior,
            formatar_numero(acoes.loc[pior, "sharpe"]),
        )
    )

    observacoes.append(
        "2. Comparação com o CDI: a taxa livre de risco rendeu {} ao ano no "
        "período. {} das {} ações tiveram Sharpe positivo (renderam mais que "
        "o CDI), e o Ibovespa rendeu {} ao ano (Sharpe de {}).".format(
            formatar_pct(cdi_anualizado),
            acima_do_cdi,
            len(acoes),
            formatar_pct(tabela.loc[benchmark, "retorno_anualizado"]),
            formatar_numero(tabela.loc[benchmark, "sharpe"]),
        )
    )

    observacoes.append(
        "3. Maior drawdown: {} caiu {} entre o pico de {} e o fundo de {}. "
        "Para comparação, o drawdown máximo do Ibovespa foi de {}, e o pior "
        "dia do índice foi {} ({}).".format(
            maior_queda,
            formatar_pct(abs(acoes.loc[maior_queda, "drawdown_maximo"])),
            formatar_mes(acoes.loc[maior_queda, "data_pico"]),
            formatar_mes(acoes.loc[maior_queda, "data_fundo"]),
            formatar_pct(abs(tabela.loc[benchmark, "drawdown_maximo"])),
            pior_dia.strftime("%d/%m/%Y"),
            formatar_pct(retornos[benchmark].min()),
        )
    )

    observacoes.append(
        "4. Correlação: o par mais correlacionado foi {} e {} ({}), e o menos "
        "correlacionado foi {} e {} ({}). Pares com correlação baixa são os "
        "que mais ajudam a diversificar uma carteira.".format(
            pares["maior_par"][0],
            pares["maior_par"][1],
            formatar_numero(pares["maior_valor"]),
            pares["menor_par"][0],
            pares["menor_par"][1],
            formatar_numero(pares["menor_valor"]),
        )
    )

    observacoes.append(
        "5. Risco: {} foi a ação mais volátil ({} ao ano) e {} a menos volátil "
        "({}). O maior beta foi o de {} ({}) e o menor o de {} ({}).".format(
            mais_volatil,
            formatar_pct(acoes.loc[mais_volatil, "volatilidade_anualizada"]),
            menos_volatil,
            formatar_pct(acoes.loc[menos_volatil, "volatilidade_anualizada"]),
            maior_beta,
            formatar_numero(acoes.loc[maior_beta, "beta"]),
            menor_beta,
            formatar_numero(acoes.loc[menor_beta, "beta"]),
        )
    )

    return observacoes


def salvar_conclusoes(observacoes, periodo, caminho):
    # Grava as observações em um arquivo Markdown.
    linhas = []
    linhas.append("# Conclusões")
    linhas.append("")
    linhas.append("Período analisado: " + periodo)
    linhas.append("")
    for observacao in observacoes:
        linhas.append(observacao)
        linhas.append("")

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write("\n".join(linhas))
