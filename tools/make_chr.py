#!/usr/bin/env python3
"""
Gera o arquivo CHR (8 KB) do cartucho -- os "graficos" do NES.

O NES nao guarda imagens: guarda 512 tiles de 8x8 pixels, cada pixel com
4 cores possiveis (0 = fundo). Cada tile ocupa 16 bytes, em dois "planos"
de 1 bit -- um pro bit baixo da cor, outro pro bit alto.

Este arquivo gera os tiles de fundo da TELA DE TITULO (fonte + coracao) e
tambem serve de biblioteca: make_scene.py e make_sprites.py importam daqui
a fonte e o codificador de tiles.

A fonte usa o mapeamento  tile = ascii - $20,  entao o assembly so precisa
de um SBC #$20 pra escrever uma string na tela.
"""
import sys

# ---------------------------------------------------------------- helpers

def encode_tile(rows):
    """rows: 8 strings de 8 chars ('.' = cor 0, '1'/'2'/'3' = cores 1-3)."""
    lo, hi = [], []
    for r in rows:
        r = (r + "........")[:8]
        b0 = b1 = 0
        for x, ch in enumerate(r):
            c = 0 if ch == '.' else int(ch)
            bit = 7 - x
            if c & 1:
                b0 |= 1 << bit
            if c & 2:
                b1 |= 1 << bit
        lo.append(b0)
        hi.append(b1)
    return bytes(lo + hi)

BLANK = encode_tile(["........"] * 8)

def glyph(rows5x7):
    """Converte um glifo 5x7 ('.'/'X') em tile 8x8 com 1px de folga."""
    out = [r.replace('X', '1') + "..." for r in rows5x7]
    while len(out) < 8:
        out.append("........")
    return encode_tile(out)

# ---------------------------------------------------------------- fonte 5x7

FONT = {
 '0': [".XXX.","X...X","X..XX","X.X.X","XX..X","X...X",".XXX."],
 '1': ["..X..",".XX..","..X..","..X..","..X..","..X..",".XXX."],
 '2': [".XXX.","X...X","....X","...X.","..X..",".X...","XXXXX"],
 '3': ["XXXXX","...X.","..XX.","....X","....X","X...X",".XXX."],
 '4': ["...X.","..XX.",".X.X.","X..X.","XXXXX","...X.","...X."],
 '5': ["XXXXX","X....","XXXX.","....X","....X","X...X",".XXX."],
 '6': ["..XX.",".X...","X....","XXXX.","X...X","X...X",".XXX."],
 '7': ["XXXXX","....X","...X.","..X..",".X...",".X...",".X..."],
 '8': [".XXX.","X...X","X...X",".XXX.","X...X","X...X",".XXX."],
 '9': [".XXX.","X...X","X...X",".XXXX","....X","...X.",".XX.."],
 'A': [".XXX.","X...X","X...X","XXXXX","X...X","X...X","X...X"],
 'B': ["XXXX.","X...X","X...X","XXXX.","X...X","X...X","XXXX."],
 'C': [".XXX.","X...X","X....","X....","X....","X...X",".XXX."],
 'D': ["XXXX.","X...X","X...X","X...X","X...X","X...X","XXXX."],
 'E': ["XXXXX","X....","X....","XXXX.","X....","X....","XXXXX"],
 'F': ["XXXXX","X....","X....","XXXX.","X....","X....","X...."],
 'G': [".XXX.","X...X","X....","X.XXX","X...X","X...X",".XXX."],
 'H': ["X...X","X...X","X...X","XXXXX","X...X","X...X","X...X"],
 'I': ["XXXXX","..X..","..X..","..X..","..X..","..X..","XXXXX"],
 'J': ["....X","....X","....X","....X","X...X","X...X",".XXX."],
 'K': ["X...X","X..X.","X.X..","XX...","X.X..","X..X.","X...X"],
 'L': ["X....","X....","X....","X....","X....","X....","XXXXX"],
 'M': ["X...X","XX.XX","X.X.X","X.X.X","X...X","X...X","X...X"],
 'N': ["X...X","XX..X","X.X.X","X..XX","X...X","X...X","X...X"],
 'O': [".XXX.","X...X","X...X","X...X","X...X","X...X",".XXX."],
 'P': ["XXXX.","X...X","X...X","XXXX.","X....","X....","X...."],
 'Q': [".XXX.","X...X","X...X","X...X","X.X.X","X..X.",".XX.X"],
 'R': ["XXXX.","X...X","X...X","XXXX.","X.X..","X..X.","X...X"],
 'S': [".XXXX","X....","X....",".XXX.","....X","....X","XXXX."],
 'T': ["XXXXX","..X..","..X..","..X..","..X..","..X..","..X.."],
 'U': ["X...X","X...X","X...X","X...X","X...X","X...X",".XXX."],
 'V': ["X...X","X...X","X...X","X...X","X...X",".X.X.","..X.."],
 'W': ["X...X","X...X","X...X","X.X.X","X.X.X","XX.XX","X...X"],
 'X': ["X...X","X...X",".X.X.","..X..",".X.X.","X...X","X...X"],
 'Y': ["X...X","X...X",".X.X.","..X..","..X..","..X..","..X.."],
 'Z': ["XXXXX","....X","...X.","..X..",".X...","X....","XXXXX"],
 '!': ["..X..","..X..","..X..","..X..","..X..",".....","..X.."],
 '-': [".....",".....",".....","XXXXX",".....",".....","....."],
 ':': [".....","..X..","..X..",".....","..X..","..X..","....."],
 '.': [".....",".....",".....",".....",".....",".....","..X.."],
 '&': [".XX..","X..X.","X..X.",".XX..","X..X.","X...X",".XX.X"],
}

# ---------------------------------------------------------------- coracao

# 'o' = contorno (cor 1), '#' = preenchimento (cor 2), '*' = brilho (cor 3)
HEART = [
    "...ooo....ooo...",
    "..o###o..o###o..",
    ".o#*###oo#####o.",
    ".o#*##########o.",
    "o#*############o",
    "o##############o",
    "o##############o",
    ".o############o.",
    ".o############o.",
    "..o##########o..",
    "...o########o...",
    "....o######o....",
    ".....o####o.....",
    "......o##o......",
    ".......oo.......",
    "................",
]

CORES = {'.': '.', 'o': '1', '#': '2', '*': '3'}

def art(desenho):
    """Traduz o desenho legivel ('o#*') pros indices de cor ('123')."""
    for i, linha in enumerate(desenho):
        assert len(linha) == len(desenho[0]), f"linha {i} tem largura errada"
    return ["".join(CORES[c] for c in linha) for linha in desenho]

def split16(art16):
    """Quebra um desenho 16x16 nos 4 tiles 8x8 (TL, TR, BL, BR)."""
    return (
        [r[0:8]  for r in art16[0:8]],
        [r[8:16] for r in art16[0:8]],
        [r[0:8]  for r in art16[8:16]],
        [r[8:16] for r in art16[8:16]],
    )

# ---------------------------------------------------------------- montagem

HEART_TILE = 0x70          # precisa bater com o src/menu.s

def build_menu_bg():
    """So os tiles de fundo do menu: fonte + coracao, ate o tile $7F.

    Com CHR-RAM os graficos sao enviados em tempo de execucao, entao vale
    mandar so o que a tela usa -- 8 paginas em vez de 16.
    """
    t = [BLANK] * 128
    for ch, rows in FONT.items():
        idx = ord(ch) - 0x20
        if 0 <= idx < 128:
            t[idx] = glyph(rows)
    for i, quad in enumerate(split16(art(HEART))):
        t[HEART_TILE + i] = encode_tile(quad)
    return b"".join(t)

if __name__ == "__main__":
    bg = build_menu_bg()
    assert len(bg) == 2048, len(bg)
    open("build/chr_menu.bin", "wb").write(bg)
    print(f"CHR do menu: build/chr_menu.bin ({len(bg)} bytes, 8 paginas)")
