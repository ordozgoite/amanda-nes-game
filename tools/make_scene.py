#!/usr/bin/env python3
"""
Desenha a cena da Pizza Crek dentro das regras do NES.

A tela e pintada pixel a pixel num canvas de 256x240, mas usando so
indices de cor 0-3. Depois o canvas e fatiado em tiles de 8x8, os tiles
repetidos sao reaproveitados, e cada bloco de 16x16 pixels recebe uma das
4 paletas de fundo. E exatamente o que o console faz.
"""
import sys
sys.path.insert(0, "tools")
from make_chr import FONT, encode_tile, BLANK

W, H = 256, 240

# ---- as 4 paletas de fundo (cor 0 e sempre o preto comum) ----
PALETAS = [
    [0x0F, 0x06, 0x16, 0x30],   # 0 vinho / vermelho / branco  -> banda, porta, banco
    [0x0F, 0x16, 0x27, 0x36],   # 1 vermelho / ambar / creme   -> CREK, luz, bandeja, chao
    [0x0F, 0x17, 0x37, 0x30],   # 2 marrom / areia / branco    -> tijolo, azulejo
    [0x0F, 0x09, 0x19, 0x24],   # 3 verde escuro / verde / rosa -> plantas, neon
]

# paletas de sprite da Amanda -- exportadas porque o minigame (make_jogo.py)
# reaproveita as mesmas, pra ela ficar identica nas duas cenas. PERNAS so
# fica exportada por causa do minigame: na pizzaria as pernas da Amanda
# passaram a reaproveitar a paleta do TRONCO (ver make_sprites.py), o que
# libertou a paleta 3 pro torso do Victor.
PALETA_SPRITE_CABECA = [0x0F, 0x0F, 0x36, 0x24]   # cabelo preto, laco rosa
PALETA_SPRITE_TRONCO = [0x0F, 0x0F, 0x36, 0x0F]   # vestido preto
PALETA_SPRITE_VICTOR = [0x0F, 0x0F, 0x37, 0x02]   # cabeca: cabelo preto; pernas (em pe):
                                                    # short preto, canela 0x37, crocs azul 0x02
PALETA_SPRITE_VICTOR_TORSO = [0x0F, 0x3C, 0x37, 0x10]   # torso: o logo da Nike, ciano
PALETA_SPRITE_PERNAS = [0x0F, 0x0F, 0x0F, 0x0F]   # vestido, sapatos, cabelo -- tudo preto

px   = [[0] * W for _ in range(H)]        # indice de cor por pixel
attr = [[2] * 16 for _ in range(15)]      # paleta por bloco de 16x16

# ------------------------------------------------------------------ pincel

def rect(x, y, w, h, c):
    for j in range(max(0, y), min(H, y + h)):
        for i in range(max(0, x), min(W, x + w)):
            px[j][i] = c

def rrect(x, y, w, h, c):
    """Retangulo com os cantos comidos -- da a impressao de forma arredondada."""
    for j in range(max(0, y), min(H, y + h)):
        dy = min(j - y, y + h - 1 - j)
        corte = 2 if dy == 0 else (1 if dy == 1 else 0)
        for i in range(max(0, x + corte), min(W, x + w - corte)):
            px[j][i] = c

def circulo(cx, cy, r, c):
    for j in range(max(0, cy - r), min(H, cy + r + 1)):
        for i in range(max(0, cx - r), min(W, cx + r + 1)):
            if (i - cx) ** 2 + (j - cy) ** 2 <= r * r:
                px[j][i] = c

def anel(cx, cy, r, esp, c):
    for j in range(max(0, cy - r), min(H, cy + r + 1)):
        for i in range(max(0, cx - r), min(W, cx + r + 1)):
            d = (i - cx) ** 2 + (j - cy) ** 2
            if (r - esp) ** 2 <= d <= r * r:
                px[j][i] = c

def texto(s, x, y, c):
    """Escreve com a fonte 5x7, 6px por letra."""
    for n, ch in enumerate(s.upper()):
        linhas = FONT.get(ch)
        if not linhas:
            continue
        for j, linha in enumerate(linhas):
            for i, p in enumerate(linha):
                if p == 'X':
                    px[y + j][x + n * 6 + i] = c

def paleta(col, row, cols, rows, p):
    """Marca a paleta de uma regiao, em tiles (col/row sao pares)."""
    for r in range(row // 2, (row + rows + 1) // 2):
        for c in range(col // 2, (col + cols + 1) // 2):
            if 0 <= r < 15 and 0 <= c < 16:
                attr[r][c] = p

# gerador pseudoaleatorio proprio, pra folhagem sempre igual entre execucoes
_seed = 20260830
def rnd(n):
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return (_seed >> 8) % n

# ================================================================== CENA

def desenhar():
    # ---------------------------------------------------------- estrutura
    # banda escura do topo (o painel de menu da loja)
    rect(0, 0, W, 6 * 8, 1)
    paleta(0, 0, 32, 6, 0)

    # ------------------------------------------------ parede de plantas
    paleta(0, 2, 12, 10, 3)
    folhagem(0, 2 * 8, 12 * 8, 10 * 8)
    neon_coracao(2 * 8, 4 * 8)

    # ------------------------------------------------ parede de azulejo
    rect(12 * 8, 6 * 8, 20 * 8, 6 * 8, 3)          # branco
    paleta(12, 6, 20, 6, 2)
    for n, j in enumerate(range(6 * 8, 12 * 8, 8)):
        rect(12 * 8, j, 20 * 8, 1, 2)              # rejunte bege, fiada alternada
        desloc = 8 if n % 2 else 0
        for i in range(12 * 8 + desloc, 32 * 8, 16):
            rect(i, j, 1, 8, 2)

    # placa pequena na parede, como as da loja
    rect(28 * 8, 7 * 8, 3 * 8, 2 * 8, 1)
    rect(28 * 8 + 2, 7 * 8 + 2, 3 * 8 - 4, 2 * 8 - 4, 3)
    for k in range(3):
        rect(28 * 8 + 5, 7 * 8 + 5 + k * 3, 3 * 8 - 10, 1, 1)

    # ------------------------------------------------------- porta vermelha
    paleta(14, 6, 6, 6, 0)
    rect(14 * 8, 6 * 8, 6 * 8, 6 * 8, 1)           # batente escuro
    rect(14 * 8 + 3, 6 * 8, 6 * 8 - 6, 6 * 8, 2)   # folha vermelha
    rect(14 * 8 + 3, 6 * 8, 2, 6 * 8, 3)           # quina iluminada
    circulo(17 * 8, 8 * 8 + 6, 12, 1)              # a janelinha redonda
    circulo(17 * 8, 8 * 8 + 6, 10, 3)
    rect(19 * 8 - 4, 9 * 8 + 4, 3, 8, 1)           # macaneta

    # ------------------------------------------------------- painel de TV
    paleta(26, 2, 6, 2, 1)
    rect(26 * 8, 2 * 8, 6 * 8, 2 * 8, 1)
    rect(26 * 8 + 2, 2 * 8 + 2, 6 * 8 - 4, 2 * 8 - 4, 3)
    rect(26 * 8 + 5, 2 * 8 + 5, 12, 6, 2)          # vulto de imagem na tela
    rect(26 * 8 + 21, 2 * 8 + 7, 16, 4, 2)

    # ------------------------------------------------ a placa PIZZA CREK
    # metade de cima na paleta 0 (branco sobre vermelho),
    # metade de baixo na paleta 1 (ambar sobre vermelho)
    paleta(16, 2, 8, 2, 0)
    paleta(16, 4, 8, 2, 1)
    rect(16 * 8, 2 * 8, 8 * 8, 2 * 8, 2)
    rect(16 * 8, 4 * 8, 8 * 8, 2 * 8, 1)
    rect(16 * 8, 2 * 8, 8 * 8, 1, 1)
    rect(16 * 8, 2 * 8, 1, 2 * 8, 1)
    rect(24 * 8 - 1, 2 * 8, 1, 2 * 8, 1)
    texto("PIZZA", 16 * 8 + 17, 2 * 8 + 5, 3)      # branco
    texto("CREK",  16 * 8 + 20, 4 * 8 + 4, 2)      # ambar
    rect(16 * 8 + 19, 4 * 8 + 13, 26, 1, 3)

    # ------------------------------------------------------------- balcao
    paleta(12, 12, 20, 2, 1)
    rect(12 * 8, 12 * 8, 20 * 8, 2 * 8, 1)         # frente vermelha
    rect(12 * 8, 12 * 8, 20 * 8, 6, 3)             # tampo claro
    rect(12 * 8, 12 * 8 + 6, 20 * 8, 1, 2)
    rect(12 * 8, 12 * 8 + 11, 20 * 8, 1, 3)        # a fita de LED quente
    rect(12 * 8, 12 * 8 + 12, 20 * 8, 2, 2)

    paleta(12, 14, 20, 4, 2)                       # frente de tijolo
    rect(12 * 8, 14 * 8, 20 * 8, 4 * 8, 2)
    for n, j in enumerate(range(14 * 8, 18 * 8, 8)):
        rect(12 * 8, j, 20 * 8, 1, 1)
        desloc = 8 if n % 2 else 0
        for i in range(12 * 8 + desloc, 32 * 8, 16):
            rect(i, j, 1, 8, 1)
    rect(12 * 8, 18 * 8 - 3, 20 * 8, 3, 1)         # sombra na base

    # --------------------------------------------------- banco vermelho
    paleta(0, 12, 12, 6, 0)
    rect(0, 12 * 8, 12 * 8, 3 * 8, 2)              # encosto
    rect(0, 12 * 8, 12 * 8, 2, 3)                  # brilho na quina de cima
    for i in range(10, 12 * 8, 26):                # gomos do estofado
        rect(i, 12 * 8 + 3, 2, 3 * 8 - 6, 1)
    rect(0, 15 * 8 - 3, 12 * 8, 3, 1)              # vinco encosto/assento
    rect(0, 15 * 8, 12 * 8, 2 * 8, 2)              # assento
    rect(0, 15 * 8 + 1, 12 * 8, 2, 3)
    rect(0, 17 * 8, 12 * 8, 8, 1)                  # base escura

    # --------------------------------------------------------------- chao
    rect(0, 18 * 8, W, H - 18 * 8, 3)              # creme
    paleta(0, 18, 32, 12, 1)
    for j in range(18 * 8 + 11, H, 16):            # juntas do piso
        rect(0, j, W, 1, 2)
    for i in range(8, W, 32):
        rect(i, 18 * 8, 1, H - 18 * 8, 2)

    # ------------------------------------------------- mesa e cadeira ao fundo
    mesa(3 * 8, 18 * 8 + 4, 6 * 8, 2)
    cadeira(9 * 8 + 4, 18 * 8 - 2)

    # --------------------------------------- mesa da frente, com a bandeja
    paleta(16, 22, 14, 6, 1)
    rect(16 * 8, 22 * 8, 14 * 8, 5 * 8, 2)         # tampo de madeira clara
    rect(16 * 8, 22 * 8, 14 * 8, 3, 3)             # quina iluminada
    rect(16 * 8, 27 * 8 - 5, 14 * 8, 5, 1)         # sombra da borda
    bandeja(19 * 8, 22 * 8 + 8)
    guardanapos(27 * 8 + 4, 22 * 8 + 6)

    cadeira(13 * 8 + 4, 21 * 8 + 4)                # cadeiras em volta
    cadeira(30 * 8 + 2, 21 * 8 + 4)


def folhagem(x, y, w, h):
    """Parede de plantas: um retalho de 32x32 desenhado uma vez e repetido.

    Repetir e o que segura o numero de tiles unicos dentro do limite do
    console -- folhagem toda aleatoria gastaria 120 tiles sozinha.
    """
    retalho = [[1] * 32 for _ in range(32)]
    for _ in range(150):
        fx, fy = rnd(32), rnd(32)
        c = 2 if rnd(3) else 1
        comp = rnd(3) + 3
        for k in range(comp):                      # folha: risco curto em diagonal
            for e in range(2):
                retalho[(fy + k) % 32][(fx + k // 2 + e) % 32] = c
    for _ in range(40):                            # sombras entre as folhas
        fx, fy = rnd(32), rnd(32)
        for k in range(rnd(2) + 2):
            retalho[(fy + k) % 32][(fx + k) % 32] = 0
    for j in range(h):
        for i in range(w):
            px[y + j][x + i] = retalho[j % 32][i % 32]


def neon_coracao(x, y):
    """O coracao de neon rosa da parede -- 24x24, tubo de 2px."""
    rect(x - 2, y - 2, 28, 28, 0)                  # o vidro apaga a folhagem
    for lado in (0, 1):
        anel(x + 6 + lado * 11, y + 8, 6, 3, 3)
    for k in range(11):                            # o V que fecha embaixo
        for e in range(3):
            px[y + 9 + k][x + 1 + k + e] = 3
            px[y + 9 + k][x + 22 - k - e] = 3
    rect(x + 4, y + 2, 4, 2, 3)                    # brilhinho no tubo


def mesa(x, y, larg, alt_tampo):
    """Mesa quadrada vista de frente. O pe e preto, como o das fotos."""
    rect(x, y, larg, 7, 2)                         # tampo de madeira clara
    rect(x, y, larg, alt_tampo, 3)                 # quina iluminada
    rect(x, y + 7, larg, 2, 0)                     # sombra sob o tampo
    rect(x + larg // 2 - 2, y + 9, 5, 16, 0)       # coluna
    rect(x + larg // 2 - 10, y + 23, 21, 3, 0)     # base


def cadeira(x, y):
    """Cadeira preta de metal. Preto e a cor 0, comum a todas as paletas."""
    rect(x, y, 16, 14, 0)                          # encosto
    rect(x + 3, y + 3, 10, 8, 3)                   # vazado, mostra o chao
    rect(x + 7, y + 3, 2, 8, 0)                    # travessa do meio
    rect(x - 2, y + 15, 20, 4, 0)                  # assento
    rect(x, y + 19, 3, 10, 0)                      # pernas
    rect(x + 13, y + 19, 3, 10, 0)
    rect(x + 1, y + 27, 14, 2, 0)                  # travessa de baixo


def bandeja(x, y):
    """A bandeja vermelha com dois rolinhos -- o detalhe que entrega o lugar."""
    rrect(x, y, 8 * 8, 30, 1)                      # bandeja vermelha
    rect(x + 3, y + 2, 8 * 8 - 6, 1, 2)            # borda com brilho
    for n, (ox, oy) in enumerate(((3, 4), (9, 16))):
        rrect(x + ox, y + oy, 50, 10, 3)           # o rolo, massa clara
        rect(x + ox + 2, y + oy + 1, 46, 2, 2)     # tostado por cima
        for k in range(3):                         # manchas de forno
            rect(x + ox + 8 + k * 12 + n * 4, y + oy + 4 + (k % 2) * 3, 4, 3, 2)
        rrect(x + ox + 34, y + oy - 2, 16, 14, 3)  # a manga de papel, abracando
        rect(x + ox + 36, y + oy + 1, 12, 3, 1)    # tarjinha vermelha da marca
        rect(x + ox + 36, y + oy + 6, 12, 2, 2)


def guardanapos(x, y):
    """Porta-guardanapos de acrilico em cima da mesa."""
    rect(x, y, 20, 16, 0)                          # moldura escura
    rect(x + 2, y + 2, 16, 12, 3)                  # guardanapos
    rect(x + 2, y + 7, 16, 1, 2)


# ================================================================== dialogo
#
# O balao de fala vive no FUNDO, nao em sprites: sao tiles escritos na
# nametable durante o vblank. Por isso a fonte precisa estar na CHR da
# CENA -- a do menu nao esta carregada aqui.
#
# As letras sao escuras sobre branco (o contrario do menu), usando a
# paleta 2 do fundo: cor 1 = marrom, cor 3 = branco.

DLG_BASE   = 204                      # A-Z ficam em 204..229
DLG_BRANCO = 230                      # fundo do balao, e tambem o espaco
DLG_EXCL   = 231
DLG_ACENTO = {"E_": 232}              # so E-circunflexo (de "voce", usado 5x)
DLG_VIRGULA = 233
DLG_INTERR  = 234
DLG_CORACAO = 235                     # a reacao da Amanda, sem letra nenhuma
DLG_PONTO   = 236                     # ponto final e reticencias (repetido 3x)
DLG_BORDA  = 237                      # 237..244: SE, S, SD, E, D, IE, I, ID
MINI_BASE  = 245                      # 245..255: nome de quem fala, fonte menor

# Nao ha mais orcamento de tile pra A-agudo nem Ç alem do que o dialogo de
# verdade usa -- a cena ja ocupa 204/256 tiles sozinha, e cada acento custa
# um tile inteiro. "ESTA"/"VARIOS" ficam sem acento (so apareciam uma vez
# cada); "VOCE" com Ê fica, porque aparece cinco vezes. Se um dialogo
# futuro precisar de mais acentos, e so somar de volta e reequilibrar os
# numeros acima.
ACENTUADAS = {
 "E_": ["..X..", ".X.X.", "XXXXX", "X....", "XXXX.", "X....", "XXXXX"],
}

# O coracaozinho que fecha a caixa da Amanda quando ela so reage, sem
# palavra -- um emoji de verdade nao existe no NES, e "<3" pediria mais um
# glifo (o "<") sem sobrar tile pra ele; um coracao desenhado direto e mais
# barato e mais bonito.
CORACAO_GLIFO = [
    ".X.X.",
    "XXXXX",
    "XXXXX",
    ".XXX.",
    "..X..",
    ".....",
    ".....",
]

def glifo_caixa(linhas):
    """Letra escura sobre fundo branco."""
    out = ["".join("1" if c == "X" else "3" for c in l) + "333" for l in linhas]
    while len(out) < 8:
        out.append("3" * 8)
    return encode_tile(out)

# A etiqueta com o nome de quem fala ("VICTOR:", "AMANDA:") usa uma fonte
# a parte, desenhada menor de proposito -- 4x5 pixels, com bastante margem
# em volta, contra os 5x7 quase sem margem da fonte grande. So os glifos
# que os dois nomes realmente precisam.
MINI_FONT = {
    "V": ["X..X", "X..X", "X..X", ".XX.", "..X."],
    "I": [".XX.", ".XX.", ".XX.", ".XX.", ".XX."],
    "C": [".XXX", "X...", "X...", "X...", ".XXX"],
    "T": ["XXXX", ".XX.", ".XX.", ".XX.", ".XX."],
    "O": [".XX.", "X..X", "X..X", "X..X", ".XX."],
    "R": ["XXX.", "X..X", "XXX.", "X.X.", "X..X"],
    "A": [".XX.", "X..X", "XXXX", "X..X", "X..X"],
    "M": ["X..X", "XXXX", "X..X", "X..X", "X..X"],
    "N": ["X..X", "XX.X", "X.XX", "X..X", "X..X"],
    "D": ["XXX.", "X..X", "X..X", "X..X", "XXX."],
    ":": ["....", ".XX.", "....", ".XX.", "...."],
}
MINI_ORDEM = sorted(MINI_FONT)   # ordem fixa: so precisa bater tile <-> indice

def glifo_mini(linhas):
    """Letra escura sobre fundo branco, 4x5 numa margem de 8x8 -- por isso
    fica visivelmente menor que glifo_caixa (5x7 quase sem margem)."""
    out = ["3" * 8, "3" * 8]                          # margem de cima
    for l in linhas:
        out.append("3" + "".join("1" if c == "X" else "3" for c in l) + "333")
    out.append("3" * 8)                               # margem de baixo
    return encode_tile(out)

def mini_tiles(texto):
    return [MINI_BASE + MINI_ORDEM.index(ch) for ch in texto]

def tiles_borda():
    """As 8 pecas da moldura: cantos e lados."""
    def caixa(cima, baixo, esq, dir_):
        g = [["3"] * 8 for _ in range(8)]
        if cima:  g[0] = ["1"] * 8
        if baixo: g[7] = ["1"] * 8
        for y in range(8):
            if esq:  g[y][0] = "1"
            if dir_: g[y][7] = "1"
        return encode_tile(["".join(r) for r in g])
    return [caixa(1,0,1,0), caixa(1,0,0,0), caixa(1,0,0,1),
            caixa(0,0,1,0),                 caixa(0,0,0,1),
            caixa(0,1,1,0), caixa(0,1,0,0), caixa(0,1,0,1)]

def tiles_dialogo():
    """Devolve {indice: tile} com fonte, moldura e fundo do balao."""
    t = {}
    for ch, linhas in FONT.items():
        if "A" <= ch <= "Z":
            t[DLG_BASE + ord(ch) - ord("A")] = glifo_caixa(linhas)
    t[DLG_BRANCO] = encode_tile(["3" * 8] * 8)
    t[DLG_EXCL]   = glifo_caixa(FONT["!"])
    t[DLG_VIRGULA] = glifo_caixa(FONT[","])
    t[DLG_INTERR]  = glifo_caixa(FONT["?"])
    t[DLG_PONTO]   = glifo_caixa(FONT["."])
    t[DLG_CORACAO] = glifo_caixa(CORACAO_GLIFO)
    for k, i in DLG_ACENTO.items():
        t[i] = glifo_caixa(ACENTUADAS[k])
    for n, tile in enumerate(tiles_borda()):
        t[DLG_BORDA + n] = tile
    for n, ch in enumerate(MINI_ORDEM):
        t[MINI_BASE + n] = glifo_mini(MINI_FONT[ch])
    return t

def para_tiles(texto):
    """Converte uma linha de texto nos numeros de tile correspondentes."""
    fora = []
    for ch in texto:
        if ch == " ":   fora.append(DLG_BRANCO)
        elif ch == "!": fora.append(DLG_EXCL)
        elif ch == ",": fora.append(DLG_VIRGULA)
        elif ch == "?": fora.append(DLG_INTERR)
        elif ch == ".": fora.append(DLG_PONTO)
        elif ch == "\x02": fora.append(DLG_CORACAO)   # sentinela: o coracaozinho
        elif ch == "\xCA": fora.append(DLG_ACENTO["E_"])
        elif "A" <= ch <= "Z": fora.append(DLG_BASE + ord(ch) - ord("A"))
        else: raise ValueError(f"sem tile pra {ch!r}")
    return fora

# O dialogo e uma sequencia de caixas de bala -- uma fecha e a proxima
# abre. Cada caixa tem UM falante so; a posicao na tela segue quem fala
# (Victor sempre perto da cabeca dele, Amanda perto de onde ela fica
# parada -- ver caixa_pag_tab/falante_tab em src/jogo.s). Cada linha tem
# no maximo 14 caracteres, a largura util do balao.
#
# "NAO" e "TO" ficam sem acento (em vez de "NÃO"/"TÔ") porque o balao so
# tem orcamento de tile pra Á e Ê -- as duas que o resto do texto usa de
# verdade. Dar Ã e Ô de presente pra essas duas palavras estouraria os
# 256 tiles da cena (ver DLG_BASE acima).
GRUPOS_FALA = [
    (0, ["NOSSA... VOC\xCA", "ESTA MUITO", "BONITA."]),
    (0, ["DESCULPA VIR", "DE CROCS,", "RSRS."]),
    (1, ["VEM, SENTA", "AQUI DO MEU", "LADO!"]),   # PARTE_SENTAR: ver main()
    (0, ["ME CONTA, O", "QUE VOC\xCA GOSTA", "DE FAZER?"]),
    (1, ["EU SOU", "PROFESSORA,", "PEDAGOGA... E", "TO FAZENDO", "PSICOLOGIA."]),
    (1, ["E VOC\xCA?"]),
    (0, ["EU SOU", "PROGRAMADOR..."]),
    (0, ["E FALO VARIOS", "IDIOMAS..."]),
    (1, ["      \x02"]),                        # so a reacao dela, sem palavra
    (0, ["BORA PEDIR AS", "PIZZAS?"]),
    (1, ["VAMOS! VOU", "PEDIR UM", "COMBO DE TRES."]),
    (0, ["NOSSA! VOC\xCA", "BATE BEM DE", "PRATO, HEIN?"]),
    (1, ["VOC\xCA AINDA", "NAO VIU NADA,", "RSRS."]),
]
FALANTE_GRUPO = [falante for falante, _ in GRUPOS_FALA]
FALA = [linha for _, grupo in GRUPOS_FALA for linha in grupo]

# depois que ESSA parte fecha (o convite "vem, senta aqui do meu lado!"),
# o assembly anima a Amanda indo se sentar antes de abrir a proxima caixa
# -- ver PARTE_SENTAR/senta_fase em src/jogo.s
PARTE_SENTAR = 2

# ================================================================== saida

def fatiar():
    """Quebra o canvas em tiles, reaproveitando os repetidos."""
    tiles, indice, nametable = [], {}, []
    for tr in range(30):
        for tc in range(32):
            chave = tuple(tuple(px[tr * 8 + j][tc * 8 + i] for i in range(8))
                          for j in range(8))
            if chave not in indice:
                indice[chave] = len(tiles)
                tiles.append(chave)
            nametable.append(indice[chave])
    return tiles, nametable

def codificar(tile):
    lo, hi = [], []
    for linha in tile:
        b0 = b1 = 0
        for x, c in enumerate(linha):
            if c & 1: b0 |= 1 << (7 - x)
            if c & 2: b1 |= 1 << (7 - x)
        lo.append(b0); hi.append(b1)
    return bytes(lo + hi)

def bytes_de_atributo():
    saida = []
    for br in range(8):
        for bc in range(8):
            v = 0
            for q, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
                r, c = br * 2 + dr, bc * 2 + dc
                p = attr[r][c] if r < 15 and c < 16 else 0
                v |= p << (q * 2)
            saida.append(v)
    return bytes(saida)

def main():
    desenhar()
    tiles, nametable = fatiar()
    print(f"tiles unicos: {len(tiles)} / 256")
    if len(tiles) > 256:
        print("!! passou do limite -- precisa repetir mais padroes")

    chr_data = bytearray(16 * 256)              # table 0 vazia (sera dos sprites)
    for t in tiles:
        chr_data += codificar(t)
    chr_data += bytes(16 * (256 - len(tiles)))
    open("build/cena.chr", "wb").write(bytes(chr_data))

    # bloco enxuto pra CHR-RAM: cena + fonte e moldura do balao
    bruto = bytearray()
    for t in tiles:
        bruto += codificar(t)
    dlg = tiles_dialogo()
    assert len(tiles) <= min(dlg), f"cena com {len(tiles)} tiles invade o dialogo"
    bruto += bytes(16 * (min(dlg) - len(tiles)))          # buraco ate DLG_BASE
    for i in range(min(dlg), max(dlg) + 1):
        bruto += dlg.get(i, BLANK)
    paginas = (len(bruto) + 255) // 256
    bruto += bytes(paginas * 256 - len(bruto))
    open("build/chr_cena.bin", "wb").write(bytes(bruto))
    print(f"CHR da cena: build/chr_cena.bin ({len(bruto)} bytes, {paginas} paginas)")
    globals()["_paginas"] = paginas

    pal = bytearray()
    for p in PALETAS:
        pal += bytes(p)
    # paletas de sprite (ver tools/make_sprites.py). Slot 3 e o torso do
    # Victor -- as pernas da Amanda agora reaproveitam o slot 1 (tronco).
    pal += bytes(PALETA_SPRITE_CABECA)
    pal += bytes(PALETA_SPRITE_TRONCO)
    pal += bytes(PALETA_SPRITE_VICTOR)
    pal += bytes(PALETA_SPRITE_VICTOR_TORSO)
    open("build/cena.pal", "wb").write(bytes(pal[:32]))
    open("build/cena.nam", "wb").write(bytes(nametable) + bytes_de_atributo())

    # ---- previa em PNG, com as cores reais do NES ----
    from screenshot import NES_RGB
    from PIL import Image
    img = Image.new("RGB", (W, H))
    p = img.load()
    for y in range(H):
        for x in range(W):
            pal = PALETAS[attr[min(y // 16, 14)][min(x // 16, 15)]]
            p[x, y] = NES_RGB[pal[px[y][x]] & 0x3F]
    img.resize((W * 3, H * 3), Image.NEAREST).save("build/cena-pizzacrek.png")
    print("build/cena-pizzacrek.png")

    # o texto do balao, ja convertido em numeros de tile
    paginas = _paginas
    linhas = ["; gerado por tools/make_scene.py -- nao edite a mao", ""]
    for n, txt in enumerate(FALA):
        assert len(txt) <= 14, f"linha {n} tem {len(txt)} chars (max 14)"
        bs = ", ".join(f"${v:02X}" for v in para_tiles(txt))
        linhas.append(f"fala{n}:  .byte {bs}, $00   ; {txt}")
    linhas += ["", "fala_lo:  .byte " + ", ".join(f"<fala{n}" for n in range(len(FALA))),
               "fala_hi:  .byte " + ", ".join(f">fala{n}" for n in range(len(FALA))), ""]
    # a etiqueta com o nome de quem fala, na fonte mini -- aparece inteira
    # de uma vez (nao letra a letra como a fala) quando a caixa abre
    for nome, texto in (("nome_victor", "VICTOR:"), ("nome_amanda", "AMANDA:")):
        bs = ", ".join(f"${v:02X}" for v in mini_tiles(texto))
        linhas.append(f"{nome}:  .byte {bs}   ; {texto}")
    linhas.append("")
    # cada grupo (caixa) sabe onde comeca e onde termina dentro de FALA, e
    # quem fala nele -- o assembly nunca reconta isso na mao
    inicios, fins, pos = [], [], 0
    for _, g in GRUPOS_FALA:
        inicios.append(pos)
        pos += len(g)
        fins.append(pos)
    linhas += ["inicio_fala_tab: .byte " + ", ".join(str(v) for v in inicios),
               "fim_fala_tab:    .byte " + ", ".join(str(v) for v in fins),
               "falante_tab:     .byte " + ", ".join(str(v) for v in FALANTE_GRUPO), ""]
    linhas += [f"; quantas paginas de 256 bytes a CHR da cena ocupa -- o assembly",
               f"; le daqui em vez de ter o numero escrito na mao",
               f"PAGINAS_CENA  = {paginas}",
               f"N_FALAS       = {len(FALA)}",
               f"N_PARTES      = {len(GRUPOS_FALA)}",
               f"PARTE_SENTAR  = {PARTE_SENTAR}",
               f"TILE_BRANCO   = ${DLG_BRANCO:02X}",
               f"TILE_BORDA    = ${DLG_BORDA:02X}", ""]
    open("build/dialogo.inc", "w").write("\n".join(linhas))
    print(f"build/dialogo.inc  ({len(FALA)} linhas de fala)")

if __name__ == "__main__":
    main()
