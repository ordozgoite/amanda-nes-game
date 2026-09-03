#!/usr/bin/env python3
"""
Cena do carro: o pos-restaurante, indo pra casa. Por enquanto so a parte
visual -- carro parado numa posicao fixa (sprite, com os dois dentro),
predios e rua deslizando atras dele. A conversa entra num passo futuro.

O cartucho usa espelhamento vertical (ver HEADER em src/jogo.s) -- as
nametables $2000 e $2400 sao DUAS TELAS DIFERENTES lado a lado, que e
exatamente o que rolagem HORIZONTAL de hardware precisa (o assembly so
incrementa PPUSCROLL/o bit de nametable em PPUCTRL a cada quadro, ver
atualiza_scroll_carro no NMI). Este gerador desenha uma imagem de 512x240
-- as duas telas coladas -- que se repete em loop: cada elemento (predio,
tracejado da rua) tem um periodo que cabe um numero inteiro de vezes em
512px, entao quando o scroll da a volta (511 -> 0) a costura nunca aparece.
"""
import sys
sys.path.insert(0, "tools")
from make_chr import encode_tile, BLANK

W, H = 512, 240
NT_TILES_W = 32           # tiles por nametable (256px / 8)
N_NT = W // (NT_TILES_W * 8)   # 2 nametables

PALETAS = [
    [0x0F, 0x0F, 0x0F, 0x30],   # 0 ceu preto de meia-noite + estrelas brancas
    [0x0F, 0x04, 0x05, 0x27],   # 1 predios: 2 tons de roxo escuro + janela acesa (ambar)
    [0x0F, 0x00, 0x0F, 0x27],   # 2 calcada cinza / rua preta / faixa amarela
    [0x0F, 0x0F, 0x0F, 0x0F],   # 3 (livre por enquanto)
]

px   = [[0] * W for _ in range(H)]
attr = [[0] * (W // 16) for _ in range(H // 16)]

def rect(x, y, w, h, c):
    for j in range(max(0, y), min(H, y + h)):
        for i in range(max(0, x), min(W, x + w)):
            px[j][i % W] = c

def paleta(col, row, cols, rows, p):
    """col/row/cols/rows em tiles -- igual make_scene.py/make_jogo.py."""
    for r in range(row // 2, (row + rows + 1) // 2):
        for c in range(col // 2, (col + cols + 1) // 2):
            if 0 <= r < H // 16:
                attr[r][c % (W // 16)] = p

_seed = 20260902
def rnd(n):
    global _seed
    _seed = (_seed * 1103515245 + 12345) & 0x7FFFFFFF
    return (_seed >> 8) % n

# ============================================================== o cenario

def desenhar():
    # ceu preto, estrelas espalhadas (period=W, cada estrela so aparece uma
    # vez no loop inteiro -- nao precisa repetir em nenhuma fracao de 512)
    rect(0, 0, W, 176, 0)
    paleta(0, 0, W // 8, 22, 0)
    for _ in range(70):
        x, y = rnd(W), rnd(150)
        px[y][x] = 3

    # predios: unidade de 64px (8 vezes em 512), alternando os dois tons
    # de roxo pra dar uma nocao de profundidade mesmo sendo uma camada so
    UNI = 64
    for u in range(W // UNI):
        x0 = u * UNI
        tom = 1 if u % 2 == 0 else 2
        alt = 58 if u % 2 == 0 else 46          # altura alterna tambem
        largura = 48
        y0 = 176 - alt
        rect(x0 + 4, y0, largura, alt, tom)
        paleta(x0 // 8, y0 // 8, (largura + 8) // 8 + 1, (alt + 8) // 8, 1)
        for jy in range(y0 + 6, 172, 10):
            for jx in range(x0 + 8, x0 + 4 + largura - 4, 8):
                if ((jx + jy + u * 7) // 5) % 3 == 0:
                    rect(jx, jy, 4, 5, 3)

    # calcada e rua
    rect(0, 176, W, 12, 1)          # calcada -- cor 1 da paleta 2 (cinza)
    rect(0, 188, W, H - 188, 0)     # rua -- cor 0 (preto, o universal)
    paleta(0, 176 // 8, W // 8, (H - 176) // 8, 2)
    for x0 in range(0, W, 32):                  # faixa tracejada, period=32
        rect(x0, 210, 16, 3, 3)

def fatiar_nametable(px_local, attr_local, tiles, indice, col_tile_off):
    """Extrai UMA nametable (32 tiles de largura) a partir da coluna de
    tile col_tile_off do canvas grande -- tiles/indice sao compartilhados
    entre as N_NT chamadas, pra CHR nao duplicar o que se repete."""
    nametable = []
    for tr in range(30):
        for tc in range(NT_TILES_W):
            gx = (col_tile_off + tc) * 8
            chave = tuple(tuple(px_local[tr * 8 + j][(gx + i) % W] for i in range(8))
                          for j in range(8))
            if chave not in indice:
                indice[chave] = len(tiles)
                tiles.append(chave)
            nametable.append(indice[chave])
    return nametable

def atributos_nametable(attr_local, col_block_off):
    saida = []
    for br in range(8):
        for bc in range(8):
            v = 0
            for q, (dr, dc) in enumerate(((0, 0), (0, 1), (1, 0), (1, 1))):
                r = br * 2 + dr
                c = (col_block_off + bc * 2 + dc) % (W // 16)
                p = attr_local[r][c] if r < H // 16 else 0
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

# =================================================== o carro e quem ta nele
#
# Fica numa posicao FIXA na tela (sprite -- nao rola com o fundo). 5 tiles
# de largura por 4 de altura (40x32px), paleta propria (branco, pedido do
# Victor, com vidro azulado e detalhes pretos). As duas cabecas ficam numa
# paleta SEPARADA (a mesma paleta de sempre: cabelo preto, pele, laco rosa
# -- reaproveitada dos sprites da Amanda/Victor) e sao desenhadas por CIMA
# do vidro do carro, como uma camada a mais de sprite na mesma posicao.

def linha(*segs):
    s = "".join(c * n for c, n in segs)
    assert len(s) == 40, f"linha com {len(s)} chars: {s!r}"
    return s

CARRO = [
    # teto (tile-linha 0, pixels 0-7)
    linha(('.',12), ('1',16), ('.',12)),
    linha(('.',10), ('1',20), ('.',10)),
    linha(('.',8), ('1',2), ('3',20), ('1',2), ('.',8)),         # vidro comeca
    linha(('.',8), ('1',2), ('3',20), ('1',2), ('.',8)),
    linha(('.',8), ('1',2), ('3',20), ('1',2), ('.',8)),
    linha(('.',8), ('1',2), ('3',20), ('1',2), ('.',8)),
    linha(('.',8), ('1',2), ('3',20), ('1',2), ('.',8)),
    linha(('.',6), ('1',4), ('3',20), ('1',4), ('.',6)),         # base do vidro
    # carroceria (tile-linha 1, pixels 8-15)
    linha(('.',2), ('1',2), ('2',32), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',32), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',32), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',32), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',32), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',15), ('1',2), ('2',15), ('1',2), ('.',2)),  # porta
    linha(('.',2), ('1',2), ('2',32), ('1',2), ('.',2)),
    linha(('1',4), ('2',32), ('1',4)),                            # parachoque
    # carroceria embaixo + poco da roda (tile-linha 2, pixels 16-23)
    linha(('1',4), ('2',32), ('1',4)),
    linha(('.',2), ('1',2), ('2',32), ('1',2), ('.',2)),
    linha(('.',4), ('1',2), ('2',28), ('1',2), ('.',4)),
    linha(('.',4), ('1',2), ('2',28), ('1',2), ('.',4)),
    linha(('.',4), ('1',8), ('2',16), ('1',8), ('.',4)),
    linha(('.',4), ('1',10), ('2',12), ('1',10), ('.',4)),
    linha(('.',6), ('1',8), ('.',12), ('1',8), ('.',6)),
    linha(('.',6), ('1',8), ('.',12), ('1',8), ('.',6)),
    # rodas (tile-linha 3, pixels 24-31)
    linha(('.',6), ('1',8), ('.',12), ('1',8), ('.',6)),
    linha(('.',6), ('1',8), ('.',12), ('1',8), ('.',6)),
    linha(('.',6), ('1',8), ('.',12), ('1',8), ('.',6)),
    linha(('.',6), ('1',8), ('.',12), ('1',8), ('.',6)),
    linha(('.',40)),
    linha(('.',40)),
    linha(('.',40)),
    linha(('.',40)),
]

def cabeca_pequena(com_laco):
    """8x8, bem simplificada -- e so o que da pra caber no vidro do carro.
    '2' = pele, '3' = o laco da Amanda (mesma cor do sprite dela, ver
    PALETA_SPRITE_CABECA) -- e o que diferencia as duas silhuetas aqui,
    ja que nao ha espaco pra desenhar barba ou outro detalhe nessa escala."""
    if com_laco:
        rows = ["..131...", ".11111..", "1122211.", "1122211.",
                "1122211.", ".11111..", "..111...", "........"]
    else:
        rows = ["..111...", ".11111..", "1122211.", "1122211.",
                "1122211.", ".11111..", "..111...", "........"]
    return encode_tile([r[:8] for r in rows])

def main():
    desenhar()
    tiles, indice = [], {}
    nametables, atributos = [], []
    for nt in range(N_NT):
        col_off = nt * NT_TILES_W
        nametables.append(fatiar_nametable(px, attr, tiles, indice, col_off))
        atributos.append(atributos_nametable(attr, col_off * 2))

    print(f"tiles unicos (fundo, {N_NT} telas): {len(tiles)} / 256")

    bruto = bytearray()
    for t in tiles:
        bruto += codificar(t)
    paginas = (len(bruto) + 255) // 256
    bruto += bytes(paginas * 256 - len(bruto))
    open("build/chr_carro.bin", "wb").write(bytes(bruto))
    print(f"CHR do carro: build/chr_carro.bin ({len(bruto)} bytes, {paginas} paginas)")

    for nt in range(N_NT):
        open(f"build/carro_nt{nt}.nam", "wb").write(
            bytes(nametables[nt]) + atributos[nt])

    pal = bytearray()
    for p in PALETAS:
        pal += bytes(p)
    # paletas de sprite: 0 = carro (preto/branco/vidro azul), 1 = cabecas
    # (cabelo preto/pele/o "laco" so aparece na silhueta, sem cor extra)
    pal += bytes([0x0F, 0x0F, 0x30, 0x21])       # 0: carro branco
    pal += bytes([0x0F, 0x0F, 0x37, 0x24])       # 1: cabecas -- pele 0x37, laco 0x24
                                                   # (mesmo rosa de PALETA_SPRITE_CABECA)
    pal += bytes([0x0F, 0x0F, 0x0F, 0x0F])       # 2 (livre)
    pal += bytes([0x0F, 0x0F, 0x0F, 0x0F])       # 3 (livre)
    open("build/carro.pal", "wb").write(bytes(pal[:32]))

    sprites = bytearray()
    for col in range(0, 40, 8):
        for lin in range(0, 32, 8):
            tile = [[int(CARRO[lin + j][col + i]) if CARRO[lin + j][col + i] != '.' else 0
                     for i in range(8)] for j in range(8)]
            sprites += codificar(tile)
    sprites += cabeca_pequena(com_laco=False)     # Victor
    sprites += cabeca_pequena(com_laco=True)      # Amanda
    while len(sprites) < 16 * 32:                 # 2 paginas de 256 bytes
        sprites += BLANK
    open("build/chr_sprites_carro.bin", "wb").write(bytes(sprites))
    print(f"sprites do carro: build/chr_sprites_carro.bin ({len(sprites)} bytes)")

    from screenshot import NES_RGB
    from PIL import Image
    img = Image.new("RGB", (W, H))
    p = img.load()
    for y in range(H):
        for x in range(W):
            pal2 = PALETAS[attr[min(y // 16, H // 16 - 1)][min(x // 16, W // 16 - 1)]]
            p[x, y] = NES_RGB[pal2[px[y][x]] & 0x3F]
    img.resize((W * 2, H * 2), Image.NEAREST).save("build/carro-cena.png")
    print("build/carro-cena.png")

    linhas = ["; gerado por tools/make_carro.py -- nao edite a mao", "",
              f"PAGINAS_CARRO = {paginas}", ""]
    open("build/carro.inc", "w").write("\n".join(linhas))
    print("build/carro.inc")

if __name__ == "__main__":
    main()
