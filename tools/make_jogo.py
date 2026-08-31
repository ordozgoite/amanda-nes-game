#!/usr/bin/env python3
"""
Desenha o cenario do minigame: pizzas crek caem do ceu e a Amanda anda
embaixo pra pegar. E uma tela nova, separada da pizzaria -- so reaproveita
a mesma altura de chao (CHAO_Y), pra Amanda ficar na mesma posicao vertical
das duas cenas, e o mesmo visual de ladrilho embaixo, de continuidade.

Mesma tecnica do make_scene.py: canvas 256x240 com indice de cor 0-3,
fatiado em tiles de 8x8 e paleta por bloco de 16x16.
"""
import sys
sys.path.insert(0, "tools")
from make_chr import FONT, encode_tile, BLANK
from make_scene import (PALETA_SPRITE_CABECA, PALETA_SPRITE_TRONCO,
                         PALETA_SPRITE_PERNAS)

W, H = 256, 240
CHAO_Y = 192   # tem que bater com CHAO_Y em src/jogo.s

PALETAS = [
    [0x0F, 0x06, 0x16, 0x30],   # 0 faixa vermelha do topo (banda + placar)
    [0x0F, 0x03, 0x13, 0x30],   # 1 ceu do entardecer, com estrelinhas
    [0x0F, 0x17, 0x27, 0x36],   # 2 chao, mesmo tom da pizzaria
    [0x0F, 0x27, 0x16, 0x30],   # 3 crosta/molho/queijo da pizza (fundo, nao usada no ceu)
]

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

# ================================================================== CENA

def desenhar():
    # faixa vermelha do topo: nome da loja a esquerda, placar a direita.
    # As colunas 28-29 (linha 0) e 28 (linha 1) ficam em branco de proposito
    # -- e onde o assembly escreve os digitos do placar, tile a tile.
    rect(0, 0, W, 24, 1)
    paleta(0, 0, 32, 3, 0)
    texto("PIZZA CREK", 8, 4, 3)
    texto("PONTOS", 160, 4, 3)
    texto("ERROS", 160, 13, 3)

    # ceu do entardecer, com estrelinhas espalhadas
    paleta(0, 3, 32, (CHAO_Y - 24) // 8, 1)
    for _ in range(50):
        x = rnd(W)
        y = 26 + rnd(CHAO_Y - 26 - 8)
        px[y][x] = 3

    # chao: mesma receita da pizzaria, pra Amanda pisar em algo familiar
    rect(0, CHAO_Y, W, H - CHAO_Y, 3)
    paleta(0, CHAO_Y // 8, 32, (H - CHAO_Y) // 8, 2)
    for j in range(CHAO_Y + 11, H, 16):
        rect(0, j, W, 1, 2)
    for i in range(8, W, 32):
        rect(i, CHAO_Y, 1, H - CHAO_Y, 2)


# ================================================================== placar
#
# Os digitos do placar sao tiles claros sobre a faixa vermelha do topo,
# escritos no fundo pelo assembly (como as letras do balao de dialogo).
# A paleta 0 (a mesma da faixa) tem cor 3 = branco -- e o que os digitos
# usam, com o resto do tile preenchido com a propria cor da faixa (cor 1),
# pra colar sem costura visivel.

DIG_BASE = 96   # 0-9 ficam em DIG_BASE..DIG_BASE+9

def glifo_digito(linhas):
    out = ["".join("3" if c == 'X' else "1" for c in l) + "111" for l in linhas]
    while len(out) < 8:
        out.append("1" * 8)
    return encode_tile(out)

def tiles_placar():
    return {DIG_BASE + n: glifo_digito(FONT[str(n)]) for n in range(10)}


# ================================================================== saida

def fatiar():
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

    dig = tiles_placar()
    assert len(tiles) <= DIG_BASE, \
        f"cenario do jogo com {len(tiles)} tiles invade o placar (DIG_BASE={DIG_BASE})"

    bruto = bytearray()
    for t in tiles:
        bruto += codificar(t)
    bruto += bytes(16 * (DIG_BASE - len(tiles)))       # buraco ate DIG_BASE
    for i in range(DIG_BASE, DIG_BASE + 10):
        bruto += dig[i]
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
    open("build/jogo.nam", "wb").write(bytes(nametable) + bytes_de_atributo())

    from screenshot import NES_RGB
    from PIL import Image
    img = Image.new("RGB", (W, H))
    p = img.load()
    for y in range(H):
        for x in range(W):
            pal2 = PALETAS[attr[min(y // 16, 14)][min(x // 16, 15)]]
            p[x, y] = NES_RGB[pal2[px[y][x]] & 0x3F]
    img.resize((W * 3, H * 3), Image.NEAREST).save("build/jogo-cena-minigame.png")
    print("build/jogo-cena-minigame.png")

    linhas = ["; gerado por tools/make_jogo.py -- nao edite a mao", "",
              f"PAGINAS_JOGO = {paginas}",
              f"DIG_BASE     = ${DIG_BASE:02X}", ""]
    open("build/jogo.inc", "w").write("\n".join(linhas))
    print(f"build/jogo.inc")

if __name__ == "__main__":
    main()
