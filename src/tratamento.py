"""
Etapa 2: tratamento dos dados.

Decisões tomadas (e o motivo de cada uma):

1. Calendário: só ficam os dias em que o Ibovespa tem cotação, ou seja,
   os pregões da B3. Assim todos os ativos usam as mesmas datas.

2. Valores faltantes: se um ativo não tem preço em um pregão, repetimos o
   último preço conhecido (forward fill), por no máximo 5 pregões seguidos.
   Repetir o último preço equivale a dizer "o ativo não negociou, então o
   retorno do dia foi zero", que é a hipótese mais neutra.
   Nunca preenchemos com o preço seguinte (backward fill), porque isso
   usaria uma informação que ainda não existia naquela data.

3. Início da série: as linhas do começo em que algum ativo ainda não tem
   preço são removidas, para todos os ativos cobrirem o mesmo período.
"""

import pandas as pd

LIMITE_PREENCHIMENTO = 5
BURACO_GRANDE = 5


def filtrar_pregoes(precos, benchmark):
    # Mantém só os dias em que o benchmark tem cotação (dias de pregão).
    dias_com_pregao = precos[benchmark].notna()
    precos_filtrados = precos[dias_com_pregao]
    return precos_filtrados


def medir_maior_buraco(serie):
    # Conta a maior sequência de dias seguidos sem preço, depois que o
    # ativo já começou a ser negociado.
    serie_valida = serie.loc[serie.first_valid_index():]
    maior = 0
    atual = 0
    for valor in serie_valida:
        if pd.isna(valor):
            atual = atual + 1
            if atual > maior:
                maior = atual
        else:
            atual = 0
    return maior


def gerar_relatorio_qualidade(precos):
    # Monta uma tabela com a qualidade dos dados de cada ativo:
    # quantos dias faltam, quando a série começa e o maior buraco.
    linhas = []
    for ativo in precos.columns:
        serie = precos[ativo]
        if serie.notna().sum() == 0:
            linha = {
                "ativo": ativo,
                "dias_com_preco": 0,
                "dias_faltantes": len(serie),
                "primeira_data": None,
                "maior_buraco": len(serie),
            }
        else:
            linha = {
                "ativo": ativo,
                "dias_com_preco": int(serie.notna().sum()),
                "dias_faltantes": int(serie.isna().sum()),
                "primeira_data": serie.first_valid_index().date(),
                "maior_buraco": medir_maior_buraco(serie),
            }
        linhas.append(linha)

    relatorio = pd.DataFrame(linhas).set_index("ativo")
    return relatorio


def avisar_problemas(relatorio):
    # Imprime um aviso para cada ativo vazio ou com buraco grande.
    # Devolve a lista dos ativos vazios, que precisam sair da análise.
    ativos_vazios = []
    for ativo in relatorio.index:
        if relatorio.loc[ativo, "dias_com_preco"] == 0:
            print("  AVISO:", ativo, "veio vazio e será removido da análise")
            ativos_vazios.append(ativo)
        elif relatorio.loc[ativo, "maior_buraco"] > BURACO_GRANDE:
            print("  AVISO:", ativo, "tem um buraco de",
                  relatorio.loc[ativo, "maior_buraco"], "pregões seguidos")
    if len(ativos_vazios) == 0:
        print("  Nenhum ticker veio vazio.")
    return ativos_vazios


def preencher_faltantes(precos):
    # Repete o último preço conhecido nos dias sem cotação (forward fill),
    # limitado a poucos dias para não esconder um buraco grande.
    precos_preenchidos = precos.ffill(limit=LIMITE_PREENCHIMENTO)
    return precos_preenchidos


def tratar_precos(precos_brutos, benchmark):
    # Aplica todo o tratamento dos preços e devolve a tabela limpa
    # junto com o relatório de qualidade.
    precos = filtrar_pregoes(precos_brutos, benchmark)
    relatorio = gerar_relatorio_qualidade(precos)
    ativos_vazios = avisar_problemas(relatorio)
    precos = precos.drop(columns=ativos_vazios)
    precos = preencher_faltantes(precos)

    linhas_antes = len(precos)
    precos = precos.dropna()
    linhas_removidas = linhas_antes - len(precos)
    print("  Linhas removidas por ainda terem valor faltante:", linhas_removidas)
    return precos, relatorio


def alinhar_cdi(cdi_bruto, datas_pregao):
    # Calcula o retorno do CDI entre um pregão e o seguinte.
    #
    # O CDI rende em todo dia útil bancário, e esse calendário não é
    # idêntico ao da B3. Para não perder nenhum dia de rendimento, montamos
    # primeiro um índice acumulado do CDI e depois medimos a variação desse
    # índice entre as datas de pregão.
    taxa_diaria = cdi_bruto["cdi_pct_dia"] / 100

    # cumprod = produto acumulado: multiplica (1 + taxa) dia após dia.
    indice = (1 + taxa_diaria).cumprod()
    # shift(1): a taxa de um dia rende até o dia útil seguinte, então o
    # índice de uma data só inclui as taxas dos dias anteriores a ela.
    indice = indice.shift(1).fillna(1.0)

    # Leva o índice para as datas de pregão. Se o pregão cair em um dia sem
    # CDI, vale o último índice conhecido.
    indice_nos_pregoes = indice.reindex(datas_pregao, method="ffill")

    # pct_change = variação percentual em relação à linha anterior.
    retorno_cdi = indice_nos_pregoes.pct_change().dropna()
    retorno_cdi.name = "cdi"
    return retorno_cdi
