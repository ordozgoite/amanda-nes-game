#!/usr/bin/env python3
"""
O letreiro entre o carro e as fotos: tela preta, sem musica, e o texto
"DEPOIS DISSO, O RESTO E HISTORIA." (com acento no E e no O) sendo
datilografado letra a letra, com um "tec" de maquina a cada uma. Quando
termina, um cursor fica piscando ate o B -- e so ai a musica comeca, junto
com a primeira foto (ver atualiza_letreiro em src/jogo.s).

As letras sao a fonte do menu em dobro (16x16, 4 tiles cada), igual o
"FELIZ 2 ANOS" da cena final. O assembly nao sabe nada de fonte: este
gerador ja entrega, por letra, onde ela cai na nametable, os 4 tiles, se
faz barulho, quanto esperar depois dela e onde fica o cursor.

Emite:
  build/chr_letreiro.bin      tiles do fundo (letras ja cortadas)
  build/chr_letreiro_spr.bin  o cursor (sprite)
  build/letreiro.nam          a tela COMPLETA, so pra conferir nos testes
  build/letreiro.pal
  build/letreiro.inc          as tabelas por letra
  build/letreiro.png          previa do texto completo
"""
import sys
sys.path.insert(0, "tools")
from make_chr import FONT

# Uma linha cabe 16 letras grandes; a frase vai em tres, quebrada onde a
# leitura respira. Sem acento no codigo: \xC9 e o E agudo, \xD3 o O agudo.
LINHAS = ["DEPOIS DISSO,", "O RESTO \xC9", "HIST\xD3RIA."]
LINHA_Y0 = 80              # pixel do topo da primeira linha (centraliza as 3)
LINHA_PASSO = 32           # uma linha de letra (16) + uma de respiro

FONTE = dict(FONT)
# a virgula da fonte pequena, dobrada, parece ponto: aqui ela ganha rabo
FONTE[","] = [".....", ".....", ".....", ".....", "..X..", "..X..", ".X..."]
# Com acento, a letra encolhe pra 6 linhas e o acento vai separado em
# cima. Na fonte pequena (7 linhas) o acento do O grudava na letra e sumia
# -- "HISTORIA" parecia sem acento nenhum.
LETRA_COM_ACENTO = {
    "\xC9": ["XXXXX", "X....", "XXXX.", "X....", "X....", "XXXXX"],
    "\xD3": [".XXX.", "X...X", "X...X", "X...X", "X...X", ".XXX."],
}

# o ritmo da maquina: um pouco irregular (gente digitando), pausa maior
# depois da virgula e na volta do carro pro comeco da linha seguinte
ESPERA_INICIO = 50         # quadros de tela preta antes da primeira letra
ESPERA_LETRA = [6, 8, 5, 7, 9, 6, 7, 5]
ESPERA_ESPACO = 6
ESPERA_VIRGULA = 22
ESPERA_LINHA = 30

PALETA_FUNDO = [0x0F, 0x00, 0x30, 0x30]      # preto, sombra cinza, letra branca
PALETA_CURSOR = [0x0F, 0x30, 0x30, 0x30]

W, H = 256, 240

def glifo_grande(ch):
    """16x16 em indices 0-2: a letra dobrada (10x14) com sombra 1px."""
    px = [[0] * 16 for _ in range(16)]
    if ch == " ":
        return px
    def poe(x, y):
        if px[y + 1][x + 1] == 0:
            px[y + 1][x + 1] = 1
        px[y][x] = 2
    # a base da letra fica sempre na linha 14 (15 e a sombra): a com
    # acento comeca 2px mais baixo porque tem uma linha a menos
    desenho, y0 = (LETRA_COM_ACENTO[ch], 3) if ch in LETRA_COM_ACENTO else (FONTE[ch], 1)
    for j, linha in enumerate(desenho):
        for i, c in enumerate(linha):
            if c == "X":
                for dy in range(2):
                    for dx in range(2):
                        poe(3 + i * 2 + dx, y0 + j * 2 + dy)
    if ch in LETRA_COM_ACENTO:          # o acento agudo, inclinado: / --
        for x, y in ((10, 0), (11, 0), (8, 1), (9, 1)):
            px[y][x] = 2                # sem sombra: com ela vira circunflexo
    return px

def corta(px, x0, y0):
    return tuple(tuple(px[y0 + j][x0 + i] for i in range(8)) for j in range(8))

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
    vazio = tuple(tuple(0 for _ in range(8)) for _ in range(8))
    tiles, indice = [vazio], {vazio: 0}      # tile 0 vazio: limpa_nametable usa 0
    def tile(t):
        if t not in indice:
            indice[t] = len(tiles)
            tiles.append(t)
        return indice[t]

    nt = [0] * 960
    letras = []          # (endereco, t0, t1, t2, t3, som, espera)
    cursor = []          # (x, y) do cursor ANTES de cada letra, e depois da ultima
    k = 0
    for n, frase in enumerate(LINHAS):
        assert len(frase) <= 16, f"linha larga demais: {frase!r}"
        col0 = (32 - len(frase) * 2) // 2
        lin = (LINHA_Y0 + n * LINHA_PASSO) // 8
        for i, ch in enumerate(frase):
            g = glifo_grande(ch)
            col = col0 + i * 2
            ts = [tile(corta(g, 0, 0)), tile(corta(g, 8, 0)),
                  tile(corta(g, 0, 8)), tile(corta(g, 8, 8))]
            nt[lin * 32 + col], nt[lin * 32 + col + 1] = ts[0], ts[1]
            nt[(lin + 1) * 32 + col], nt[(lin + 1) * 32 + col + 1] = ts[2], ts[3]
            if ch == " ":
                espera = ESPERA_ESPACO
            elif ch == ",":
                espera = ESPERA_VIRGULA
            else:
                espera = ESPERA_LETRA[k % len(ESPERA_LETRA)]
            if i == len(frase) - 1 and n < len(LINHAS) - 1:
                espera = ESPERA_LINHA
            cursor.append((col * 8, lin * 8))
            letras.append((0x2000 + lin * 32 + col, *ts, 0 if ch == " " else 1, espera))
            k += 1
        if n == len(LINHAS) - 1:
            cursor.append(((col0 + len(frase) * 2) * 8, lin * 8))
    assert len(tiles) <= 256 and len(letras) < 256

    bruto = b"".join(codificar(t) for t in tiles)
    paginas = (len(bruto) + 255) // 256
    bruto += bytes(paginas * 256 - len(bruto))
    open("build/chr_letreiro.bin", "wb").write(bruto)
    open("build/letreiro.nam", "wb").write(bytes(nt) + bytes(64))

    # o cursor: um traco grosso na base da letra (2 sprites lado a lado, o
    # mesmo tile), como o "_" de uma tela de terminal
    traco = tuple(tuple(1 if j >= 5 and i < 7 else 0 for i in range(8)) for j in range(8))
    spr = bytes(16) + codificar(traco)         # tile 0 vazio, tile 1 o traco
    spr += bytes(256 - len(spr))
    open("build/chr_letreiro_spr.bin", "wb").write(spr)

    open("build/letreiro.pal", "wb").write(
        bytes(PALETA_FUNDO * 4) + bytes(PALETA_CURSOR * 4))

    from screenshot import NES_RGB
    from PIL import Image
    img = Image.new("RGB", (W, H))
    p = img.load()
    for ty in range(30):
        for tx in range(32):
            t = tiles[nt[ty * 32 + tx]]
            for j in range(8):
                for i in range(8):
                    p[tx * 8 + i, ty * 8 + j] = NES_RGB[PALETA_FUNDO[t[j][i]]]
    img.resize((W * 2, H * 2), Image.NEAREST).save("build/letreiro.png")

    def tab(nome, vals):
        return f"{nome}: .byte " + ", ".join(str(v) for v in vals)
    L = ["; gerado por tools/make_letreiro.py -- nao edite a mao", "",
         f"PAGINAS_LETREIRO = {paginas}",
         f"LETREIRO_N = {len(letras)}",
         f"LETREIRO_INICIO = {ESPERA_INICIO}",
         "TILE_CURSOR = 1",
         "",
         '.segment "BANK0"',
         'chr_letreiro:     .incbin "chr_letreiro.bin"',
         'chr_letreiro_spr: .incbin "chr_letreiro_spr.bin"',
         '.segment "CODE"',
         "paletas_letreiro: .incbin \"letreiro.pal\"",
         "; por letra: onde cai (linha de cima e de baixo), os 4 tiles, se faz",
         "; barulho (espaco nao faz) e quantos quadros esperar depois dela",
         tab("let_hi", [a >> 8 for a, *_ in letras]),
         tab("let_lo", [a & 0xFF for a, *_ in letras]),
         tab("let_hi2", [(a + 32) >> 8 for a, *_ in letras]),
         tab("let_lo2", [(a + 32) & 0xFF for a, *_ in letras]),
         tab("let_t0", [l[1] for l in letras]),
         tab("let_t1", [l[2] for l in letras]),
         tab("let_t2", [l[3] for l in letras]),
         tab("let_t3", [l[4] for l in letras]),
         tab("let_som", [l[5] for l in letras]),
         tab("let_espera_tab", [l[6] for l in letras]),
         "; o cursor antes de cada letra (e depois da ultima): x e o y do sprite",
         tab("let_cur_x", [x for x, _ in cursor]),
         tab("let_cur_y", [y + 8 - 1 for _, y in cursor]),    # metade de baixo da celula; OAM guarda y-1
         ""]
    open("build/letreiro.inc", "w").write("\n".join(L))
    print(f"letreiro: {len(letras)} letras, {len(tiles)} tiles, {paginas} paginas")

if __name__ == "__main__":
    main()
