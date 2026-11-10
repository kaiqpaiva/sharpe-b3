"""
Etapa 5: visualizações.

Com 10 ações mais o Ibovespa, uma cor por ativo deixaria os gráficos
ilegíveis. Por isso os gráficos de retorno acumulado e de drawdown usam
"pequenos múltiplos": um painel por ação, todos com a mesma escala, e o
Ibovespa em cinza como referência em cada painel.
"""

import math

import matplotlib

matplotlib.use("Agg")  # Gera os arquivos de imagem sem abrir janelas.

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import PercentFormatter

# Cores usadas em todos os gráficos.
COR_FUNDO = "#fcfcfb"
COR_TEXTO = "#0b0b0b"
COR_TEXTO_SECUNDARIO = "#52514e"
COR_EIXO = "#898781"
COR_GRADE = "#e1e0d9"
COR_ATIVO = "#2a78d6"
COR_ATIVO_2 = "#eb6834"
COR_BENCHMARK = "#898781"

COLUNAS_POR_LINHA = 5


def configurar_estilo():
    # Define o visual padrão: fundo claro, grade discreta, sem bordas sobrando.
    plt.rcParams["font.family"] = ["Segoe UI", "DejaVu Sans"]
    plt.rcParams["font.size"] = 10
    plt.rcParams["figure.facecolor"] = COR_FUNDO
    plt.rcParams["axes.facecolor"] = COR_FUNDO
    plt.rcParams["savefig.facecolor"] = COR_FUNDO
    plt.rcParams["text.color"] = COR_TEXTO
    plt.rcParams["axes.labelcolor"] = COR_TEXTO_SECUNDARIO
    plt.rcParams["axes.edgecolor"] = COR_GRADE
    plt.rcParams["xtick.color"] = COR_EIXO
    plt.rcParams["ytick.color"] = COR_EIXO
    plt.rcParams["axes.spines.top"] = False
    plt.rcParams["axes.spines.right"] = False
    plt.rcParams["axes.grid"] = True
    plt.rcParams["grid.color"] = COR_GRADE
    plt.rcParams["grid.linewidth"] = 0.6
    plt.rcParams["legend.frameon"] = False


def listar_acoes(colunas, benchmark):
    # Devolve os nomes das colunas sem o benchmark.
    acoes = []
    for coluna in colunas:
        if coluna != benchmark:
            acoes.append(coluna)
    return acoes


def criar_paineis(quantidade):
    # Cria uma grade de painéis com a mesma escala nos eixos e
    # esconde os painéis que sobrarem.
    numero_linhas = math.ceil(quantidade / COLUNAS_POR_LINHA)
    figura, eixos = plt.subplots(
        numero_linhas,
        COLUNAS_POR_LINHA,
        figsize=(15, 3.3 * numero_linhas),
        sharex=True,
        sharey=True,
    )
    eixos = eixos.flatten()
    for posicao in range(quantidade, len(eixos)):
        eixos[posicao].set_visible(False)
    return figura, eixos


def girar_datas(eixo):
    # Inclina os rótulos de data para não encavalarem.
    for rotulo in eixo.get_xticklabels():
        rotulo.set_rotation(45)
        rotulo.set_horizontalalignment("right")


def titular_painel(eixo, titulo, detalhe):
    # Escreve o nome do ativo à esquerda e um número de destaque à direita.
    eixo.set_title(titulo, loc="left", fontsize=11, fontweight="bold")
    eixo.set_title(detalhe, loc="right", fontsize=9, color=COR_TEXTO_SECUNDARIO)


def salvar_figura(figura, caminho):
    # Salva a figura em PNG e libera a memória.
    figura.savefig(caminho, dpi=150, bbox_inches="tight")
    plt.close(figura)


def plotar_retorno_acumulado(base_100, benchmark, caminho):
    # Um painel por ação: a ação em azul contra o Ibovespa em cinza,
    # os dois começando em 100.
    acoes = listar_acoes(base_100.columns, benchmark)
    figura, eixos = criar_paineis(len(acoes))

    for posicao in range(len(acoes)):
        acao = acoes[posicao]
        eixo = eixos[posicao]
        eixo.axhline(100, color=COR_EIXO, linewidth=0.8, linestyle=":")
        eixo.plot(base_100.index, base_100[benchmark], color=COR_BENCHMARK,
                  linewidth=1.2, label="Ibovespa")
        eixo.plot(base_100.index, base_100[acao], color=COR_ATIVO,
                  linewidth=1.8, label="Ação")
        valor_final = base_100[acao].iloc[-1]
        titular_painel(eixo, acao, "final: {:.0f}".format(valor_final))
        girar_datas(eixo)

    marcas, rotulos = eixos[0].get_legend_handles_labels()
    figura.legend(marcas, rotulos, loc="upper right", ncol=2,
                  bbox_to_anchor=(0.99, 1.0))
    figura.suptitle("Retorno acumulado contra o Ibovespa (base 100)",
                    x=0.01, ha="left", fontsize=14, fontweight="bold")
    figura.tight_layout()
    salvar_figura(figura, caminho)


def plotar_drawdown(drawdown, tabela, benchmark, caminho):
    # Um painel por ação com a curva de drawdown (área azul), o Ibovespa
    # em cinza e um ponto marcando o fundo da pior queda.
    acoes = listar_acoes(drawdown.columns, benchmark)
    figura, eixos = criar_paineis(len(acoes))

    for posicao in range(len(acoes)):
        acao = acoes[posicao]
        eixo = eixos[posicao]
        eixo.fill_between(drawdown.index, drawdown[acao], 0, color=COR_ATIVO,
                          alpha=0.25, linewidth=0)
        eixo.plot(drawdown.index, drawdown[acao], color=COR_ATIVO,
                  linewidth=1.2, label="Ação")
        eixo.plot(drawdown.index, drawdown[benchmark], color=COR_BENCHMARK,
                  linewidth=1.0, label="Ibovespa")

        data_fundo = drawdown[acao].idxmin()
        valor_fundo = tabela.loc[acao, "drawdown_maximo"]
        eixo.scatter([data_fundo], [valor_fundo], color=COR_ATIVO, s=36,
                     edgecolor=COR_FUNDO, linewidth=1.5, zorder=3)
        detalhe = "{:.0%} em {}".format(valor_fundo, data_fundo.strftime("%m/%Y"))
        titular_painel(eixo, acao, detalhe)
        eixo.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
        girar_datas(eixo)

    marcas, rotulos = eixos[0].get_legend_handles_labels()
    figura.legend(marcas, rotulos, loc="upper right", ncol=2,
                  bbox_to_anchor=(0.99, 1.0))
    figura.suptitle("Drawdown: queda em relação ao pico anterior",
                    x=0.01, ha="left", fontsize=14, fontweight="bold")
    figura.tight_layout()
    salvar_figura(figura, caminho)


def escolher_escala_de_cor(correlacao):
    # Se todas as correlações são positivas, usa um azul só, do claro ao
    # escuro, de 0 a 1. Se houver negativas, usa vermelho e azul com cinza
    # no zero, de -1 a 1.
    menor_valor = correlacao.min().min()
    if menor_valor >= 0:
        cores = ["#f3f7fd", "#cde2fb", "#6da7ec", "#2a78d6", "#0d366b"]
        minimo = 0.0
    else:
        cores = ["#e34948", "#f0efec", "#2a78d6"]
        minimo = -1.0
    mapa = LinearSegmentedColormap.from_list("correlacao", cores)
    return mapa, minimo


def plotar_heatmap_correlacao(correlacao, caminho):
    # Matriz de correlação como mapa de calor, com o valor em cada célula.
    mapa, minimo = escolher_escala_de_cor(correlacao)
    nomes = list(correlacao.columns)
    quantidade = len(nomes)

    figura, eixo = plt.subplots(figsize=(9, 7.5))
    imagem = eixo.imshow(correlacao.values, cmap=mapa, vmin=minimo, vmax=1.0)

    for linha in range(quantidade):
        for coluna in range(quantidade):
            valor = correlacao.values[linha, coluna]
            if valor > 0.6:
                cor_do_numero = "#ffffff"
            else:
                cor_do_numero = COR_TEXTO
            eixo.text(coluna, linha, "{:.2f}".format(valor), ha="center",
                      va="center", fontsize=9, color=cor_do_numero)

    eixo.set_xticks(range(quantidade))
    eixo.set_yticks(range(quantidade))
    eixo.set_xticklabels(nomes, rotation=45, ha="right")
    eixo.set_yticklabels(nomes)
    eixo.tick_params(length=0, colors=COR_TEXTO_SECUNDARIO)
    eixo.grid(False)

    # Linhas finas na cor do fundo para separar as células.
    for posicao in range(quantidade + 1):
        eixo.axhline(posicao - 0.5, color=COR_FUNDO, linewidth=2)
        eixo.axvline(posicao - 0.5, color=COR_FUNDO, linewidth=2)
    for lado in ["left", "bottom"]:
        eixo.spines[lado].set_visible(False)

    barra = figura.colorbar(imagem, ax=eixo, fraction=0.046, pad=0.03)
    barra.outline.set_visible(False)
    barra.set_label("Correlação")
    eixo.set_title("Correlação dos retornos diários", loc="left",
                   fontsize=14, fontweight="bold", pad=12)
    figura.tight_layout()
    salvar_figura(figura, caminho)


def caixas_se_sobrepoem(caixa_a, caixa_b):
    # Diz se dois retângulos (x0, y0, x1, y1) se sobrepõem.
    separadas = (
        caixa_a[2] < caixa_b[0] or caixa_b[2] < caixa_a[0]
        or caixa_a[3] < caixa_b[1] or caixa_b[3] < caixa_a[1]
    )
    return not separadas


def montar_caixa_rotulo(ponto, texto, posicao):
    # Calcula o retângulo (em pixels) que o rótulo ocuparia ao lado do ponto.
    largura = 13 * len(texto)
    altura = 24
    if posicao["ha"] == "left":
        x0 = ponto[0] + posicao["dx"]
    else:
        x0 = ponto[0] + posicao["dx"] - largura
    if posicao["va"] == "bottom":
        y0 = ponto[1] + posicao["dy"]
    else:
        y0 = ponto[1] + posicao["dy"] - altura
    caixa = (x0, y0, x0 + largura, y0 + altura)
    return caixa


def rotular_pontos(eixo, nomes, pontos_em_dados):
    # Escreve o nome de cada ponto, testando quatro posições (direita em
    # cima, direita embaixo, esquerda em cima, esquerda embaixo) e usando
    # a primeira que não bate em outro ponto nem em outro rótulo.
    posicoes = [
        {"dx": 12, "dy": 8, "ha": "left", "va": "bottom"},
        {"dx": 12, "dy": -8, "ha": "left", "va": "top"},
        {"dx": -12, "dy": 8, "ha": "right", "va": "bottom"},
        {"dx": -12, "dy": -8, "ha": "right", "va": "top"},
    ]

    caixas_ocupadas = []
    pontos_em_pixels = []
    for ponto in pontos_em_dados:
        pixel = eixo.transData.transform(ponto)
        pontos_em_pixels.append(pixel)
        caixas_ocupadas.append((pixel[0] - 11, pixel[1] - 11,
                                pixel[0] + 11, pixel[1] + 11))

    for indice in range(len(nomes)):
        escolhida = posicoes[0]
        achou = False
        for posicao in posicoes:
            if not achou:
                caixa = montar_caixa_rotulo(pontos_em_pixels[indice],
                                            nomes[indice], posicao)
                livre = True
                for ocupada in caixas_ocupadas:
                    if caixas_se_sobrepoem(caixa, ocupada):
                        livre = False
                if livre:
                    escolhida = posicao
                    achou = True

        caixas_ocupadas.append(montar_caixa_rotulo(
            pontos_em_pixels[indice], nomes[indice], escolhida))
        eixo.annotate(nomes[indice], pontos_em_dados[indice],
                      xytext=(escolhida["dx"], escolhida["dy"]),
                      textcoords="offset pixels", ha=escolhida["ha"],
                      va=escolhida["va"], fontsize=10, color=COR_TEXTO)


def plotar_risco_retorno(tabela, cdi_anualizado, benchmark, caminho):
    # Dispersão com a volatilidade no eixo X e o retorno anualizado no Y.
    # A linha tracejada marca o CDI: acima dela o Sharpe é positivo.
    # dpi igual ao do arquivo salvo, para as contas em pixels valerem.
    figura, eixo = plt.subplots(figsize=(10, 6.5), dpi=150)

    nomes = []
    pontos = []
    for ativo in tabela.index:
        x = tabela.loc[ativo, "volatilidade_anualizada"]
        y = tabela.loc[ativo, "retorno_anualizado"]
        if ativo == benchmark:
            eixo.scatter([x], [y], color=COR_TEXTO, marker="D", s=70, zorder=3)
        else:
            eixo.scatter([x], [y], color=COR_ATIVO, s=70, zorder=3)
        nomes.append(ativo)
        pontos.append((x, y))

    eixo.axhline(cdi_anualizado, color=COR_EIXO, linewidth=1.2, linestyle="--")
    eixo.axhline(0, color=COR_GRADE, linewidth=1.0)
    eixo.annotate("CDI ({:.1%} a.a.)".format(cdi_anualizado),
                  (0.995, cdi_anualizado), xycoords=("axes fraction", "data"),
                  xytext=(0, 5), textcoords="offset points", ha="right",
                  fontsize=9, color=COR_TEXTO_SECUNDARIO)

    eixo.xaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    eixo.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    eixo.set_xlabel("Volatilidade anualizada")
    eixo.set_ylabel("Retorno anualizado")
    eixo.set_title("Risco x retorno", loc="left", fontsize=14,
                   fontweight="bold", pad=12)
    eixo.margins(x=0.08, y=0.08)
    figura.tight_layout()
    # Os rótulos vêm por último, porque a posição deles depende do
    # tamanho final do gráfico.
    rotular_pontos(eixo, nomes, pontos)
    salvar_figura(figura, caminho)


def plotar_volatilidade_movel(volatilidade_movel, ativos, benchmark, caminho):
    # Volatilidade móvel de 21 pregões de dois ativos, com o Ibovespa
    # em cinza como referência.
    cores = [COR_ATIVO, COR_ATIVO_2]
    figura, eixo = plt.subplots(figsize=(11, 5.5))

    eixo.plot(volatilidade_movel.index, volatilidade_movel[benchmark],
              color=COR_BENCHMARK, linewidth=1.3, label="Ibovespa")
    for posicao in range(len(ativos)):
        ativo = ativos[posicao]
        eixo.plot(volatilidade_movel.index, volatilidade_movel[ativo],
                  color=cores[posicao], linewidth=1.6, label=ativo)

    eixo.yaxis.set_major_formatter(PercentFormatter(xmax=1, decimals=0))
    eixo.set_ylabel("Volatilidade anualizada")
    eixo.set_ylim(bottom=0)
    # Legenda acima do gráfico, para não cobrir as linhas.
    eixo.legend(loc="lower right", bbox_to_anchor=(1.0, 1.0), ncol=3)
    eixo.set_title("Volatilidade móvel de 21 pregões", loc="left",
                   fontsize=14, fontweight="bold", pad=12)
    figura.tight_layout()
    salvar_figura(figura, caminho)
