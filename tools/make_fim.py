#!/usr/bin/env python3
"""
Cena final: o Victor, a Amanda e o Hulk chegando andando num gramado, de
noite, e "FELIZ 2 ANOS DE NAMORO" acendendo no ceu. Daqui o jogo nao sai
mais -- e o fim (ver atualiza_fim em src/jogo.s).

Os tres sao sprites: Victor e Amanda sao os MESMOS desenhos da pizzaria
(folha de make_sprites.py, com as mesmas paletas), e o Hulk tambem mora
la. Este gerador so faz o fundo e as constantes de posicao.

Emite:
  build/chr_fim.bin   tiles do fundo (pattern table 1)
  build/fim.nam       nametable + atributos
  build/fim.pal       as 8 paletas (4 de fundo + 4 de sprite)
  build/fim.inc       PAGINAS_FIM, posicoes, a rampa do texto acendendo
  build/fim-cena.png  previa do fundo, pra olhar
"""
import math
import sys
sys.path.insert(0, "tools")
from make_chr import FONT

W, H = 256, 240

# O texto e as estrelas que caem nas linhas dele dividem a paleta 1: a
# estrela e o indice 3 em TODA paleta do ceu (0 e 1), entao continua
# acesa enquanto as letras (1 = sombra, 2 = letra) sobem do preto.
PALETAS = [
    [0x0F, 0x0F, 0x37, 0x30],   # 0 ceu: preto, lua creme, estrela branca
    [0x0F, 0x15, 0x25, 0x30],   # 1 texto: sombra vinho, letra rosa, estrela
    [0x0F, 0x09, 0x0A, 0x1A],   # 2 gramado de noite: escuro, medio, folhinha clara
    [0x0F, 0x0F, 0x0F, 0x0F],   # 3 (livre)
]

# o texto comeca apagado (as duas cores dele em preto) e acende em
# degraus -- o assembly so copia estes pares pra paleta 1, um por vez
RAMPA_TEXTO = [(0x0F, 0x0F), (0x0F, 0x05), (0x05, 0x15), (0x15, 0x25)]
assert RAMPA_TEXTO[-1] == tuple(PALETAS[1][1:3])

# As linhas do texto caem em blocos de atributo inteiros (16px), e a
# paleta 1 pega a LARGURA TODA dessas linhas -- assim a frase nao precisa
# comecar numa coluna par pra ficar centralizada.
TEXTO = [("FELIZ 2 ANOS", 32), ("DE NAMORO", 64)]

# O gramado sobe atras dos tres ate acima da cabeca deles: a Amanda e o
# Victor tem cabelo e roupa pretos, e o ceu tambem e preto -- com o ceu
# atras das cabecas eles sumiriam.
CHAO_Y = 208               # onde ficam os pes (y do pixel logo abaixo deles)
GRAMA_TOPO = 150           # o morrinho mais baixo; no meio ele sobe um pouco

# Os tres andam da esquerda ate o meio e param. O Hulk vai na frente. A
# distancia e a mesma pros tres (eles andam juntos), por isso so a
# posicao final de cada um e a caminhada sao parametros.
CAMINHADA = 96
FIM_VICTOR_X = 104
FIM_AMANDA_X = 124
FIM_HULK_X = 148

px = [[0] * W for _ in range(H)]
attr = [[0] * (W // 16) for _ in range(H // 16)]

def paleta(col, row, cols, rows, p):
    """col/row/cols/rows em TILES (nao pixels) -- ver armadilha no CLAUDE.md."""
    for r in range(row // 2, (row + rows + 1) // 2):
        for c in range(col // 2, (col + cols + 1) // 2):
            if 0 <= r < H // 16 and 0 <= c < W // 16:
                attr[r][c] = p

_seed = 20261013
def rnd(n):
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return (_seed >> 8) % n

def letra_grande(ch, x0, y0):
    """Glifo 5x7 da fonte do menu em dobro (10x14), com sombra 1px pra
    baixo e pra direita -- sem ela a letra rosa fica chapada no preto."""
    if ch == " ":
        return
    g = FONT[ch]
    for j, linha in enumerate(g):
        for i, c in enumerate(linha):
            if c != "X":
                continue
            for dy in range(2):
                for dx in range(2):
                    x, y = x0 + 3 + i * 2 + dx, y0 + 1 + j * 2 + dy
                    if px[y + 1][x + 1] == 0:
                        px[y + 1][x + 1] = 1
                    px[y][x] = 2

CORACAO = [
    ".XX.XX.",
    "XXXXXXX",
    "XXXXXXX",
    ".XXXXX.",
    "..XXX..",
    "...X...",
]

def coracao(x0, y0, escala=2):
    for j, linha in enumerate(CORACAO):
        for i, c in enumerate(linha):
            if c == "X":
                for dy in range(escala):
                    for dx in range(escala):
                        px[y0 + j * escala + dy][x0 + i * escala + dx] = 2

def grama_topo(x):
    # um morrinho bem suave, mais alto no meio (onde os tres param)
    return GRAMA_TOPO - int(8 * math.cos((x - 128) / 128 * math.pi / 2))

def desenhar():
    # estrelas so no ceu (acima de onde o morro mais alto chega) e fora do
    # texto e da lua -- indice 3 e branco nas paletas 0 e 1
    for _ in range(60):
        x, y = rnd(W), rnd(GRAMA_TOPO - 14)
        if any(ty <= y < ty + 18 for _, ty in TEXTO):
            continue
        if 186 <= x < 222 and 94 <= y < 130:
            continue
        px[y][x] = 3

    # a lua: um circulo amarelado com uma mordida (crescente)
    cx, cy, r = 204, 112, 12
    for y in range(cy - r, cy + r + 1):
        for x in range(cx - r, cx + r + 1):
            dentro = (x - cx) ** 2 + (y - cy) ** 2 <= r * r
            mordida = (x - cx + 6) ** 2 + (y - cy + 3) ** 2 <= (r - 1) ** 2
            if dentro and not mordida:
                px[y][x] = 2

    for frase, y in TEXTO:
        x0 = (W - len(frase) * 16) // 2
        for k, ch in enumerate(frase):
            letra_grande(ch, x0 + k * 16, y)
        paleta(0, y // 8, 32, 2, 1)
    # um coracao de cada lado da primeira linha
    largura = len(TEXTO[0][0]) * 16
    coracao((W - largura) // 2 - 18, TEXTO[0][1] + 2)
    coracao((W + largura) // 2 + 4, TEXTO[0][1] + 2)

    # o gramado: medio, com folhinhas claras e escuras espalhadas; a borda
    # de cima ganha uma linha clara pra recortar o morro contra o ceu
    for x in range(W):
        topo = grama_topo(x)
        for y in range(topo, H):
            px[y][x] = 2
        px[topo][x] = 3
    for _ in range(110):
        x = rnd(W)
        y = grama_topo(x) + 3 + rnd(H - grama_topo(x) - 3)
        px[y][x] = 3 if rnd(3) else 1
        if y + 1 < H and px[y][x] == 3:
            px[y + 1][x] = 3
    linha0 = (GRAMA_TOPO - 8) // 8 - 1
    paleta(0, linha0, 32, 30 - linha0, 2)

def fatiar():
    tiles, indice, nt = [], {}, []
    for tr in range(30):
        for tc in range(32):
            chave = tuple(tuple(px[tr * 8 + j][tc * 8 + i] for i in range(8)) for j in range(8))
            if chave not in indice:
                indice[chave] = len(tiles)
                tiles.append(chave)
            nt.append(indice[chave])
    return tiles, nt

def atributos():
    saida = []
    for br in range(8):
        for bc in range(8):
            v = 0
            for q, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
                r = br * 2 + dr
                p = attr[r][bc * 2 + dc] if r < H // 16 else 0
                v |= p << (q * 2)
            saida.append(v)
    return bytes(saida)

def codificar(tile):
    lo, hi = [], []
    for linha in tile:
        b0 = b1 = 0
        for x, c in enumerate(linha):
            if c & 1: b0 |= 1 << (7 - x)
            if c & 2: b1 |= 1 << (7 - x)
        lo.append(b0); hi.append(b1)
    return bytes(lo + hi)

def main():
    desenhar()
    tiles, nt = fatiar()
    assert len(tiles) <= 256, f"cena final com {len(tiles)} tiles (max 256)"
    bruto = b"".join(codificar(t) for t in tiles)
    paginas = (len(bruto) + 255) // 256
    bruto += bytes(paginas * 256 - len(bruto))
    open("build/chr_fim.bin", "wb").write(bruto)
    open("build/fim.nam", "wb").write(bytes(nt) + atributos())
    print(f"cena final: {len(tiles)} tiles, {paginas} paginas")

    # as paletas de sprite sao as da pizzaria: Victor e Amanda vem com as
    # cores de sempre, e o Hulk usa a 2 (a da cabeca do Victor) -- preto,
    # bege e cinza, exatamente as cores dele (ver make_sprites.py)
    cena = open("build/cena.pal", "rb").read()
    pal = bytearray()
    for i, p in enumerate(PALETAS):
        pal += bytes(p if i != 1 else [p[0], RAMPA_TEXTO[0][0], RAMPA_TEXTO[0][1], p[3]])
    pal += cena[16:32]
    open("build/fim.pal", "wb").write(bytes(pal))

    from screenshot import NES_RGB
    from PIL import Image
    img = Image.new("RGB", (W, H))
    p = img.load()
    for y in range(H):
        for x in range(W):
            p[x, y] = NES_RGB[PALETAS[attr[y // 16][x // 16]][px[y][x]] & 0x3F]
    img.resize((W * 2, H * 2), Image.NEAREST).save("build/fim-cena.png")

    def tab(nome, valores):
        return f"{nome}: .byte " + ", ".join(f"${v:02X}" for v in valores)
    linhas = ["; gerado por tools/make_fim.py -- nao edite a mao", "",
              f"PAGINAS_FIM = {paginas}",
              f"FIM_CHAO = {CHAO_Y}",
              f"FIM_CAMINHADA = {CAMINHADA}",
              f"FIM_VICTOR_X = {FIM_VICTOR_X}",
              f"FIM_AMANDA_X = {FIM_AMANDA_X}",
              f"FIM_HULK_X = {FIM_HULK_X}",
              f"FIM_RAMPA_N = {len(RAMPA_TEXTO)}",
              "",
              tab("fim_rampa1", [a for a, _ in RAMPA_TEXTO]),
              tab("fim_rampa2", [b for _, b in RAMPA_TEXTO]),
              ""]
    open("build/fim.inc", "w").write("\n".join(linhas))
    print("build/chr_fim.bin build/fim.nam build/fim.pal build/fim.inc build/fim-cena.png")

if __name__ == "__main__":
    main()
