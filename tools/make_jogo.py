#!/usr/bin/env python3
"""
Desenha o cenario do minigame: pizzas crek caem do ceu e a Amanda anda
embaixo pra pegar. E uma tela nova, separada da pizzaria -- so reaproveita
a mesma altura de chao (CHAO_Y), pra Amanda ficar na mesma posicao vertical
das duas cenas, e o mesmo visual de ladrilho embaixo, de continuidade.

Mesma tecnica do make_scene.py: canvas 256x240 com indice de cor 0-3,
fatiado em tiles de 8x8 e paleta por bloco de 16x16. Mas aqui sao QUATRO
telas (nao uma so): a de jogo em si, e mais tres telas de aviso que o
assembly troca por cima dela --
  - intro:   "PEGUE N PIZZAS!" / "DESVIE DAS PIMENTAS!", antes da primeira
             pizza cair (senao quem joga pela primeira vez nao entende que
             e um minigame)
  - vitoria: "PARABENS!", quando alcanca PONTOS_MIN
  - derrota: retrato triste da Amanda (um "zoom" na cabeca dela, grande
             demais pro sprite normal -- por isso vira desenho de fundo,
             nao sprite) + "NAO FOI DESSA VEZ, TENTE DE NOVO", quando
             alcanca ERROS_MAX
Todas as quatro compartilham o MESMO conjunto de tiles (CHR carregada uma
vez so); so a disposicao (nametable) muda a cada troca de tela, que e bem
mais barato que recarregar CHR de novo.
"""
import sys
sys.path.insert(0, "tools")
from make_chr import FONT, encode_tile, BLANK
from make_scene import (PALETA_SPRITE_CABECA, PALETA_SPRITE_TRONCO,
                         PALETA_SPRITE_PERNAS)

W, H = 256, 240
CHAO_Y = 192   # tem que bater com CHAO_Y em src/jogo.s

# checa_vitoria/checa_derrota em src/jogo.s leem essas duas daqui (jogo.inc)
# em vez de duplicar o numero a mao -- e o texto da intro/vitoria tambem
# precisa saber PONTOS_MIN pra escrever "PEGUE N PIZZAS!" certo.
PONTOS_MIN = 30
ERROS_MAX  = 3          # tres vidas: pedido do Victor, pra ficar mais dificil

# A barra de pontos vale DUAS pizzas por tile (vazio / meio / cheio): um
# tile por pizza nao cabe -- a barra comeca na coluna 8 e 30 tiles passariam
# da borda da tela (e a TV de tubo ja corta as ultimas colunas).
assert PONTOS_MIN % 2 == 0, "a barra usa meio tile por pizza"
BARRA_TILES = PONTOS_MIN // 2
assert 8 + BARRA_TILES <= 30, "a barra passaria da area segura da tela"

# ------------------------------------------------ a curva de dificuldade
# Tudo anda junto com a FRACAO da barra (igual a musica, ver VEL_JOGO em
# make_song.py), nao com o numero bruto de pontos -- o jeito antigo
# (pontos/4) batia no teto de velocidade com 8 pizzas e dali em diante o
# jogo ficava igual ate o fim. O assembly so indexa estas tabelas com
# jogo_pontos (0..PONTOS_MIN).
ESPERA_INI, ESPERA_FIM = 90, 64   # quadros entre um objeto e o proximo
VEL_INI, VEL_FIM       = 16, 48   # queda em 1/16 de pixel por quadro (1 -> 3 px)
SALTO_MAX              = 80       # distancia maxima entre uma pizza e a anterior
PIMENTA_DESDE          = 6        # antes disso so cai pizza: primeiro aprende a pegar
PIMENTA_CHANCE_INI     = 0.25     # chance de uma pimenta acompanhar a pizza, logo
PIMENTA_CHANCE_FIM     = 0.50     # que comecam... e no fim da barra

# A Amanda anda 1 pixel por quadro, e duas pizzas seguidas chegam no chao
# `espera` quadros uma depois da outra -- entao a distancia entre elas nao
# pode passar de `espera` (menos uma folga pra ela reagir), senao a pizza
# fica fisicamente impossivel de alcancar. Quando a espera encurta, o salto
# encurta junto.
FOLGA_REACAO = 12

def _interp(a, b, p):
    return a + (b - a) * p / PONTOS_MIN

ESPERA_TAB  = [round(_interp(ESPERA_INI, ESPERA_FIM, p)) for p in range(PONTOS_MIN + 1)]
VEL_TAB     = [round(_interp(VEL_INI, VEL_FIM, p)) for p in range(PONTOS_MIN + 1)]
SALTO_TAB   = [min(SALTO_MAX, e - FOLGA_REACAO) for e in ESPERA_TAB]
# chance em 1/256 (o assembly compara com um byte aleatorio)
PIMENTA_TAB = [0 if p < PIMENTA_DESDE else
               round(256 * (PIMENTA_CHANCE_INI + (PIMENTA_CHANCE_FIM - PIMENTA_CHANCE_INI)
                            * (p - PIMENTA_DESDE) / (PONTOS_MIN - PIMENTA_DESDE)))
               for p in range(PONTOS_MIN + 1)]
assert max(VEL_TAB) + 15 < 256 and max(PIMENTA_TAB) < 256
assert all(s > 0 for s in SALTO_TAB)

# ------------------------------------------------ a pimenta, em paralelo
# A pimenta nasce NO MESMO QUADRO que uma pizza, mas nunca grudada nela
# (centro a PIMENTA_LONGE px ou mais): se caissem juntas, pegar a pizza
# seria levar a pimenta -- derrota ou derrota. Ela mira a coluna da PROXIMA
# pizza e cai mais devagar, pra chegar la depois que a Amanda pegou esta e
# antes da proxima: quem corre pra baixo da proxima e fica parado leva na
# cabeca; quem espera do lado ela passar, pega. Na mesma velocidade da
# pizza ela seria enfeite -- chegaria no chao junto com a pizza, numa
# coluna onde a Amanda nem esta (ver a armadilha no CLAUDE.md).
PIMENTA_LONGE = 24
# a pimenta tem que ter sumido (passado do pe dela) FOLGA_PIMENTA quadros
# antes da proxima pizza entrar na faixa de captura -- o tempo de entrar
NASCE_Y       = 26                 # logo abaixo da faixa vermelha do topo
CAPTURA_Y_MIN = CHAO_Y - 4         # a pizza conta a partir daqui...
CAPTURA_Y_MAX = CHAO_Y + 24        # ...ate aqui (faixa generosa, e presente)
PIMENTA_Y_MIN = CHAO_Y - 12        # a pimenta doi do cabelo...
PIMENTA_Y_MAX = CHAO_Y + 16        # ...ate o pe; daqui pra baixo, some
FOLGA_PIMENTA = 20

def _vel_pimenta(p):
    chega_pizza = (CAPTURA_Y_MIN - NASCE_Y) * 16 / VEL_TAB[p]   # quadros
    some = chega_pizza + ESPERA_TAB[p] - FOLGA_PIMENTA
    return round((PIMENTA_Y_MAX - NASCE_Y) * 16 / some)
VEL_PIMENTA_TAB = [_vel_pimenta(p) for p in range(PONTOS_MIN + 1)]
# mais lenta que a pizza, senao chegaria ANTES dela (em cima da Amanda
# que esta indo pegar a pizza desta batida)
assert all(vp < v for vp, v in zip(VEL_PIMENTA_TAB, VEL_TAB))

# Quantos objetos caem ao mesmo tempo, no pior caso (toda batida com
# pimenta). A pimenta lenta fica mais tempo na tela, entao precisa de
# mais espacos que os 3 de quando ela so trocava de lugar com a pizza. Cabe no limite de 8 sprites por linha: as pizzas
# ficam `espera` quadros uma da outra (>= 64 px na vertical), as pimentas
# tambem -- numa linha so cruzam a Amanda (2), uma pizza (2) e no maximo
# duas pimentas (1 cada).
def _vida(vel, ate):
    return (ate - NASCE_Y) * 16 / vel
PZ_N = max(-(-_vida(VEL_TAB[p], CAPTURA_Y_MAX) // ESPERA_TAB[p])
           + -(-_vida(VEL_PIMENTA_TAB[p], PIMENTA_Y_MAX) // ESPERA_TAB[p])
           for p in range(PONTOS_MIN + 1))
PZ_N = int(PZ_N)
assert PZ_N <= 6, "os espacos de objeto passariam do orcamento de OAM"

PALETAS = [
    [0x0F, 0x06, 0x16, 0x30],   # 0 faixa vermelha do topo (titulo + HUD)
    [0x0F, 0x03, 0x13, 0x30],   # 1 ceu do entardecer, com estrelinhas
    [0x0F, 0x17, 0x27, 0x36],   # 2 chao, mesmo tom da pizzaria
    [0x0F, 0x0F, 0x37, 0x21],   # 3 retrato triste da Amanda: cabelo preto,
]                               #   pele 0x37 (mesma do Victor), lagrima azul

px   = [[1] * W for _ in range(H)]
attr = [[1] * 16 for _ in range(15)]

def novo_canvas():
    global px, attr
    px   = [[1] * W for _ in range(H)]
    attr = [[1] * 16 for _ in range(15)]

def rect(x, y, w, h, c):
    for j in range(max(0, y), min(H, y + h)):
        for i in range(max(0, x), min(W, x + w)):
            px[j][i] = c

def texto(s, x, y, c):
    for n, ch in enumerate(s.upper()):
        linhas = FONT.get(ch)
        if not linhas:
            continue
        for j, linha in enumerate(linhas):
            for i, p in enumerate(linha):
                if p == 'X':
                    px[y + j][x + n * 6 + i] = c

def texto_centro(s, y, c):
    texto(s, (W - len(s) * 6) // 2, y, c)

def paleta(col, row, cols, rows, p):
    for r in range(row // 2, (row + rows + 1) // 2):
        for c in range(col // 2, (col + cols + 1) // 2):
            if 0 <= r < 15 and 0 <= c < 16:
                attr[r][c] = p

# gerador pseudoaleatorio proprio, pras estrelinhas ficarem sempre iguais
_seed = 20260901
def rnd(n):
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return (_seed >> 8) % n

# UMA lista de estrelas so, reaproveitada nas 4 telas -- se cada tela
# sorteasse a sua, os tiles do ceu quase nunca bateriam entre elas e o
# orcamento de 256 tiles estourava rapido (foi o que aconteceu, ver commit)
ESTRELAS_JOGO = [(rnd(W), 34 + rnd(CHAO_Y - 34 - 8)) for _ in range(28)]

# ============================================================ retrato triste
#
# Uma cabeca GRANDE da Amanda (6x6 tiles = 48x48px), tipo um "zoom" no
# rosto dela -- bem maior que o sprite normal (16x16), que e pequeno demais
# pra mostrar expressao. Reaproveita o mesmo desenho conceitual do sprite
# dela (cabelo preto descendo, lacinho rosa, rosto estreito), so que agora
# com espaco de sobra pra sobrancelhas caidas, boca virada pra baixo e uma
# lagrima -- nada disso cabe num sprite de 16px.

def linha(*segs):
    s = "".join(c * n for c, n in segs)
    assert len(s) == 48, f"linha com {len(s)} chars: {s!r}"
    return s

RETRATO_TRISTE = [
    linha(('.',10), ('1',16), ('.',10), ('1',6), ('.',6)),   # cabelo (laco funde
    linha(('.',8), ('1',20), ('.',8), ('1',8), ('.',4)),      # com o cabelo aqui --
    linha(('.',6), ('1',24), ('.',18)),
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),     # testa
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',4), ('1',2), ('2',6),         # sobrancelhas
          ('1',2), ('2',4), ('1',5), ('.',15)),                 # (finas, retas)
    linha(('.',5), ('1',5), ('2',3), ('1',3), ('2',6),
          ('1',3), ('2',3), ('1',5), ('.',15)),                 # olhos
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',4), ('4',2), ('2',6),
          ('4',2), ('2',4), ('1',5), ('.',15)),                 # bochecha+lagrima
    linha(('.',5), ('1',5), ('2',4), ('4',2), ('2',6),
          ('4',2), ('2',4), ('1',5), ('.',15)),                 # lagrima escorrendo
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',7), ('1',4), ('2',7),          # boca: centro em
          ('1',5), ('.',15)),                                   # cima (o resto da
    linha(('.',5), ('1',5), ('2',6), ('1',2), ('2',2),          # boca: cantos
          ('1',2), ('2',6), ('1',5), ('.',15)),                  # embaixo -- frown de verdade
    linha(('.',5), ('1',6), ('2',16), ('1',6), ('.',15)),      # queixo
    linha(('.',6), ('1',8), ('2',8), ('1',8), ('.',18)),
    linha(('.',48)),
]

def cor4_para_palheta():
    """RETRATO_TRISTE usa '4' pra lagrima -- reaproveita o indice 3 (azul)."""
    return {c: c for c in "0123"} | {'4': '3'}

# a mesma cabeca, feliz: sem lagrima (o indice 3 da paleta 3 e compartilhado
# com o retrato triste -- so cabe UMA cor extra, ver make_jogo.py no topo
# do arquivo -- entao aqui a felicidade e so cabelo+pele, sem cor a mais) e
# a boca com as pontas em cima, centro embaixo -- um sorriso de verdade.
RETRATO_FELIZ = [
    linha(('.',10), ('1',16), ('.',10), ('1',6), ('.',6)),
    linha(('.',8), ('1',20), ('.',8), ('1',8), ('.',4)),
    linha(('.',6), ('1',24), ('.',18)),
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),        # testa
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',4), ('1',2), ('2',6),            # sobrancelhas
          ('1',2), ('2',4), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',3), ('1',3), ('2',6),
          ('1',3), ('2',3), ('1',5), ('.',15)),                   # olhos
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),         # bochecha (sem lagrima)
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',18), ('1',5), ('.',15)),
    linha(('.',5), ('1',5), ('2',6), ('1',2), ('2',2),            # boca: cantos em
          ('1',2), ('2',6), ('1',5), ('.',15)),                    # cima (sorriso)
    linha(('.',5), ('1',5), ('2',7), ('1',4), ('2',7),
          ('1',5), ('.',15)),                                     # boca: centro embaixo
    linha(('.',5), ('1',6), ('2',16), ('1',6), ('.',15)),        # queixo
    linha(('.',6), ('1',8), ('2',8), ('1',8), ('.',18)),
    linha(('.',48)),
]

def desenha_retrato(retrato, x0, y0):
    """x0/y0 em pixels, tem que cair em multiplo de 16 (bloco de atributo).
    O retrato tem 48 de largura mas so 16 linhas -- cada linha vira 3, pra
    ficar 48x48 quadrado (o mesmo "zoom" pixelado grosso que o resto do
    jogo ja usa)."""
    assert x0 % 16 == 0 and y0 % 16 == 0, "retrato precisa cair em bloco de atributo"
    troca = cor4_para_palheta()
    for j, linha_str in enumerate(retrato):
        for rep in range(3):
            y = y0 + j * 3 + rep
            for i, ch in enumerate(linha_str):
                if ch == '.':
                    continue
                px[y][x0 + i] = int(troca[ch])
    paleta(x0 // 8, y0 // 8, 6, 6, 3)

# ================================================================== cena

def fundo_comum(titulo):
    """O que as quatro telas tem em comum: faixa vermelha, ceu, chao."""
    rect(0, 0, W, 32, 1)                        # faixa vermelha (4 linhas)
    paleta(0, 0, 32, 4, 0)
    texto(titulo, 8, 4, 3)

    paleta(0, 4, 32, (CHAO_Y - 32) // 8, 1)      # ceu do entardecer
    for x, y in ESTRELAS_JOGO:
        px[y][x] = 3

    rect(0, CHAO_Y, W, H - CHAO_Y, 3)            # chao, igual a pizzaria
    paleta(0, CHAO_Y // 8, 32, (H - CHAO_Y) // 8, 2)
    for j in range(CHAO_Y + 11, H, 16):
        rect(0, j, W, 1, 2)
    for i in range(8, W, 32):
        rect(i, CHAO_Y, 1, H - CHAO_Y, 2)

def desenhar_jogando():
    novo_canvas()
    fundo_comum("PIZZA CREK")
    # HUD: "PONTOS" com uma barra de PONTOS_MIN segmentos (comeca vazia) e
    # "VIDAS" com ERROS_MAX iconezinhos (comeca cheia) -- o assembly
    # redesenha os tiles dessas duas linhas conforme o jogo anda (ver
    # desenha_barra/desenha_vidas em src/jogo.s); aqui so preparamos o
    # estado inicial.
    texto("PONTOS", 8, 17, 3)
    texto("VIDAS", 8, 25, 3)
    return capturar()

# A intro mostra uma pizza e uma pimenta de verdade (sprites, na paleta
# delas -- o fundo nao tem o vermelho/laranja certo nessa faixa) do lado
# esquerdo das linhas que falam de cada uma: ela nunca viu a pimenta antes,
# e "PIMENTA" escrito sozinho nao diz qual objeto e. O assembly so copia
# as posicoes daqui (INTRO_* em jogo.inc).
INTRO_PIZZAS   = f"PEGUE {PONTOS_MIN} PIZZAS!"
INTRO_PIZZAS_Y = 82
INTRO_PIMENTA  = "DESVIE DAS PIMENTAS!"
INTRO_PIMENTA_Y = 114
ICONE_RESPIRO  = 6               # pixels entre o icone e a primeira letra

def x_do_texto(s):
    return (W - len(s) * 6) // 2

INTRO_PIZZA_X   = x_do_texto(INTRO_PIZZAS) - ICONE_RESPIRO - 16
INTRO_PIMENTA_X = x_do_texto(INTRO_PIMENTA) - ICONE_RESPIRO - 8
# o sprite aparece uma linha abaixo do y da OAM, por isso o -1; a pimenta
# (16 de altura) fica centrada nas letras (7 de altura)
INTRO_PIZZA_OAM_Y   = INTRO_PIZZAS_Y - 1
INTRO_PIMENTA_OAM_Y = INTRO_PIMENTA_Y - 4 - 1

def desenhar_intro():
    novo_canvas()
    fundo_comum("PIZZA CREK")
    texto_centro(INTRO_PIZZAS, INTRO_PIZZAS_Y, 3)
    texto_centro("NAO DEIXE CAIR!", 98, 3)
    texto_centro(INTRO_PIMENTA, INTRO_PIMENTA_Y, 3)
    texto_centro("APERTE B PRA COMECAR", 138, 3)
    return capturar()

def desenhar_vitoria():
    novo_canvas()
    fundo_comum("PIZZA CREK")
    desenha_retrato(RETRATO_FELIZ, 96, 48)
    texto_centro("PARABENS!", 120, 3)
    texto_centro("APERTE B PRA CONTINUAR", 138, 3)
    return capturar()

def desenhar_derrota():
    novo_canvas()
    fundo_comum("PIZZA CREK")
    desenha_retrato(RETRATO_TRISTE, 96, 48)
    texto_centro("NAO FOI DESSA VEZ", 120, 3)
    texto_centro("APERTE B PRA TENTAR DE NOVO", 138, 3)
    return capturar()

def capturar():
    return [row[:] for row in px], [row[:] for row in attr]

# ============================================================== HUD dinamico
#
# Os tiles que o assembly troca em tempo real (ver desenha_barra/
# desenha_vidas). Ficam num intervalo reservado no fim da lista de tiles,
# igual o DIG_BASE de antes -- endereco fixo, nao sujeito a deduplicacao.

def glifo_barra(cheias):
    # cheias = quantas das 2 pizzas desse tile ja foram pegas (0, 1 ou 2):
    # cada pizza acende a metade do tile, da esquerda pra direita
    cor = '3' * (4 * cheias) + '1' * (8 - 4 * cheias)
    linhas = [cor] * 6 + ["11111111"] * 2
    return encode_tile(linhas)

def glifo_vida(cheia):
    # um coracaozinho simples de 8x8 (cheio = rosa, vazio = so contorno)
    if cheia:
        rows = [".11.11..", "1111111.", "1111111.", ".11111..",
                "..111...", "...1....", "........", "........"]
        return encode_tile([r.replace('1', '3') for r in rows])
    rows = [".11.11..", "1......1", "1......1", ".1....1.",
            "..1..1..", "...11...", "........", "........"]
    return encode_tile(rows)

UI_TILES = {
    "BARRA_VAZIA": glifo_barra(0),
    "BARRA_CHEIA": glifo_barra(2),
    "VIDA_CHEIA":  glifo_vida(True),
    "VIDA_VAZIA":  glifo_vida(False),
    "BARRA_MEIA":  glifo_barra(1),
}

# ================================================================== saida

def fatiar(px_local, attr_local, tiles, indice):
    """Reaproveita 'tiles'/'indice' entre as quatro telas -- assim CHR e
    carregada uma vez so, e cada tela so referencia os indices que precisa."""
    nametable = []
    for tr in range(30):
        for tc in range(32):
            chave = tuple(tuple(px_local[tr * 8 + j][tc * 8 + i] for i in range(8))
                          for j in range(8))
            if chave not in indice:
                indice[chave] = len(tiles)
                tiles.append(chave)
            nametable.append(indice[chave])
    return nametable

def codificar(tile):
    lo, hi = [], []
    for linha in tile:
        b0 = b1 = 0
        for x, c in enumerate(linha):
            if c & 1: b0 |= 1 << (7 - x)
            if c & 2: b1 |= 1 << (7 - x)
        lo.append(b0); hi.append(b1)
    return bytes(lo + hi)

def bytes_de_atributo(attr_local):
    saida = []
    for br in range(8):
        for bc in range(8):
            v = 0
            for q, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
                r, c = br * 2 + dr, bc * 2 + dc
                p = attr_local[r][c] if r < 15 and c < 16 else 0
                v |= p << (q * 2)
            saida.append(v)
    return bytes(saida)

def main():
    tiles, indice = [], {}
    telas = {
        "jogo":    desenhar_jogando(),
        "intro":   desenhar_intro(),
        "vitoria": desenhar_vitoria(),
        "derrota": desenhar_derrota(),
    }

    nametables = {}
    attrs = {}
    for nome, (px_local, attr_local) in telas.items():
        nametables[nome] = fatiar(px_local, attr_local, tiles, indice)
        attrs[nome] = bytes_de_atributo(attr_local)

    print(f"tiles unicos (4 telas): {len(tiles)} / 256")

    UI_BASE = len(tiles)
    ui_ordem = ["BARRA_VAZIA", "BARRA_CHEIA", "VIDA_CHEIA", "VIDA_VAZIA",
                "BARRA_MEIA"]
    assert UI_BASE + len(ui_ordem) <= 256, \
        f"cenario do jogo com {UI_BASE} tiles + {len(ui_ordem)} do HUD estoura 256"

    bruto = bytearray()
    for t in tiles:
        bruto += codificar(t)
    for nome in ui_ordem:
        bruto += UI_TILES[nome]
    paginas = (len(bruto) + 255) // 256
    bruto += bytes(paginas * 256 - len(bruto))
    open("build/chr_jogo.bin", "wb").write(bytes(bruto))
    print(f"CHR do jogo: build/chr_jogo.bin ({len(bruto)} bytes, {paginas} paginas)")

    pal = bytearray()
    for p in PALETAS:
        pal += bytes(p)
    pal += bytes(PALETA_SPRITE_CABECA)                  # 0: Amanda, cabeca
    pal += bytes(PALETA_SPRITE_TRONCO)                  # 1: Amanda, tronco
    pal += bytes([0x0F, 0x27, 0x16, 0x30])              # 2: a pizza (crosta/molho/queijo)
    pal += bytes(PALETA_SPRITE_PERNAS)                  # 3: Amanda, pernas
    open("build/jogo.pal", "wb").write(bytes(pal[:32]))

    for nome in telas:
        arq = "jogo.nam" if nome == "jogo" else f"jogo_{nome}.nam"
        open(f"build/{arq}", "wb").write(bytes(nametables[nome]) + attrs[nome])

    from screenshot import NES_RGB
    from PIL import Image
    for nome, (px_local, attr_local) in telas.items():
        img = Image.new("RGB", (W, H))
        p = img.load()
        for y in range(H):
            for x in range(W):
                pal2 = PALETAS[attr_local[min(y // 16, 14)][min(x // 16, 15)]]
                p[x, y] = NES_RGB[pal2[px_local[y][x]] & 0x3F]
        img.resize((W * 3, H * 3), Image.NEAREST).save(f"build/jogo-cena-{nome}.png")
        print(f"build/jogo-cena-{nome}.png")

    linhas = ["; gerado por tools/make_jogo.py -- nao edite a mao", "",
              f"PAGINAS_JOGO = {paginas}",
              f"PONTOS_MIN   = {PONTOS_MIN}",
              f"ERROS_MAX    = {ERROS_MAX}",
              f"BARRA_TILES  = {BARRA_TILES}",
              f"UI_BASE      = ${UI_BASE:02X}",
              f"PIMENTA_DESDE = {PIMENTA_DESDE}",
              f"PIMENTA_LONGE = {PIMENTA_LONGE}",
              f"PZ_N          = {PZ_N}",
              f"NASCE_Y       = {NASCE_Y}",
              f"CAPTURA_Y_MIN = {CAPTURA_Y_MIN}",
              f"CAPTURA_Y_MAX = {CAPTURA_Y_MAX}",
              f"PIMENTA_Y_MIN = {PIMENTA_Y_MIN}",
              f"PIMENTA_Y_MAX = {PIMENTA_Y_MAX}",
              f"INTRO_PIZZA_X       = {INTRO_PIZZA_X}",
              f"INTRO_PIZZA_OAM_Y   = {INTRO_PIZZA_OAM_Y}",
              f"INTRO_PIMENTA_X     = {INTRO_PIMENTA_X}",
              f"INTRO_PIMENTA_OAM_Y = {INTRO_PIMENTA_OAM_Y}", "",
              "; a curva de dificuldade, indexada por jogo_pontos (0..PONTOS_MIN)",
              "espera_tab:  .byte " + ", ".join(map(str, ESPERA_TAB)),
              "vel_tab:     .byte " + ", ".join(map(str, VEL_TAB)),
              "salto_tab:   .byte " + ", ".join(map(str, SALTO_TAB)),
              "pimenta_tab: .byte " + ", ".join(map(str, PIMENTA_TAB)),
              "vel_pimenta_tab: .byte " + ", ".join(map(str, VEL_PIMENTA_TAB)), ""]
    open("build/jogo.inc", "w").write("\n".join(linhas))
    print(f"build/jogo.inc")

if __name__ == "__main__":
    main()
