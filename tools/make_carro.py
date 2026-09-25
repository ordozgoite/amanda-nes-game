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

W, H = 512, 240
NT_TILES_W = 32           # tiles por nametable (256px / 8)
N_NT = W // (NT_TILES_W * 8)   # 2 nametables

PALETAS = [
    [0x0F, 0x0F, 0x0F, 0x30],   # 0 ceu preto de meia-noite + estrelas brancas
    [0x0F, 0x04, 0x05, 0x27],   # 1 predios: 2 tons de roxo escuro + janela acesa (ambar)
    [0x0F, 0x10, 0x0F, 0x27],   # 2 calcada cinza-claro / rua preta / faixa amarela --
                                 # cinza-claro (nao 0x00) pra nao se confundir com o
                                 # cinza-escuro do trim do carro (mesma faixa de y)
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
# O Fiat Argo branco do Victor de verdade, de PERFIL (nao mais de frente
# com os dois no vidro) -- pedido dele, foto em mao: vidro fechado/fume,
# sem gente aparecendo. Isso muda o problema todo pro melhor: nao precisa
# mais reservar metade da largura pra cada personagem (e cada um com a
# PROPRIA paleta, ver historico no CLAUDE.md) -- e um perfil lateral usa a
# largura pra mostrar o COMPRIMENTO do carro (capo+cabine+porta-malas lado
# a lado), que e exatamente a dimensao que "carro comprido" pedia, em vez
# de duas cabecas lado a lado. Fica numa posicao FIXA na tela (sprite --
# nao rola com o fundo).
#
# A LARGURA (8 colunas = 64px) continua no MESMO teto fisico do PPU de
# sempre (8 sprites por linha de varredura, o maximo que o hardware
# desenha) -- so que agora ela representa comprimento, nao largura de
# carroceria, entao rende muito mais "carro comprido" pro mesmo orcamento.
#
# So uma paleta agora (vidro fechado tira a paleta extra por personagem):
# 1 = trim escuro (vidro fume, pneu, para-choque, friso) -- 0x00, NAO 0x0F
# puro, pra nao sumir em cima da rua (mesma armadilha de sempre, ver
# CLAUDE.md); 2 = branco (carroceria); 3 = ambar (farol/retrovisor -- o
# mesmo tom das janelas acesas dos predios atras, ver PALETAS acima).

CARRO_TILES_W = 8
CARRO_TILES_H = 6
CARRO_PX_W = CARRO_TILES_W * 8    # 64
CARRO_PX_H = CARRO_TILES_H * 8    # 48

_carro_px = [['.'] * CARRO_PX_W for _ in range(CARRO_PX_H)]
PAL_CEL = [[0] * CARRO_TILES_W for _ in range(CARRO_TILES_H)]   # so a paleta 0 por enquanto

def _fill(x0, y0, w, h, ch):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            _carro_px[y][x] = ch

def _desenhar_carro():
    # nariz do carro em x=63 (anda "pra direita"); traseira em x=0.
    # teto: uma aba de spoiler na traseira (o Argo tem um bem sutil, ver
    # foto de referencia), depois plano ate perto do para-brisa
    _fill(14, 2, 5, 2, '2')                # aba do spoiler
    _fill(14, 4, 34, 4, '2')                # teto

    # vidro fume -- trapezio (mais estreito em cima, perto do teto, mais
    # largo embaixo, perto da linha de cintura), sugerindo o angulo do
    # para-brisa (frente) e do vidro traseiro (atras) num pixel art bem
    # simples, em "escada" em vez de diagonal de verdade
    _fill(17, 8, 28, 3, '1')
    _fill(14, 11, 35, 3, '1')
    _fill(11, 14, 41, 6, '1')

    # carroceria principal -- do pe do vidro (y20, logo abaixo do trapezio
    # de cima) ate a soleira, LARGURA TODA (nao so capo/porta-malas nas
    # pontas): o vidro so descia ate y19, entao parar o branco em y24
    # deixava um vao sem preencher entre y20-23 no meio (nem vidro, nem
    # carroceria, nem capo/porta-malas -- eles so cobrem as pontas) --
    # o fundo da cena aparecia ali, uma fatia horizontal faltando no
    # meio do carro.
    _fill(4, 20, 58, 12, '2')
    _fill(0, 22, 4, 10, '1')                # para-choque traseiro
    _fill(60, 22, 4, 10, '1')               # para-choque dianteiro
    _fill(4, 32, 58, 2, '1')                # soleira

    # farol (frente) e lanterna (atras) -- so um aceno de cor pra marcar
    # as pontas, e o retrovisor, perto da base do para-brisa
    _fill(59, 23, 3, 3, '3')
    _fill(2, 23, 3, 3, '3')
    _fill(45, 10, 3, 3, '1')

    def _roda(x0, y0, tam):
        c = (tam - 1) / 2
        for y in range(tam):
            for x in range(tam):
                if (x - c) ** 2 + (y - c) ** 2 <= c * c:
                    _carro_px[y0 + y][x0 + x] = '1'
        aro = tam // 3
        _fill(x0 + aro, y0 + aro, tam - 2 * aro, tam - 2 * aro, '3')
    _roda(6, 30, 14)                        # roda traseira
    _roda(44, 30, 14)                       # roda dianteira

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
    # paleta de sprite: so uma agora (vidro fechado/fume, sem gente
    # aparecendo, tira a exigencia de uma paleta por personagem que a
    # versao anterior precisava). 1 = trim escuro (vidro, pneu, para-
    # choque, friso) -- 0x00, NAO 0x0F puro: a rua tambem e 0x0F, e o
    # trim cai bem em cima dela; com a mesma cor ele fica invisivel
    # (mesma armadilha da calcada vs. rua, ver CLAUDE.md). 2 = branco
    # (carroceria). 3 = ambar (farol/retrovisor -- mesmo tom das janelas
    # acesas dos predios atras, PALETAS[1]).
    pal += bytes([0x0F, 0x00, 0x30, 0x27])       # 0: o carro
    pal += bytes([0x0F, 0x0F, 0x0F, 0x0F])       # 1 (livre)
    pal += bytes([0x0F, 0x0F, 0x0F, 0x0F])       # 2 (livre)
    pal += bytes([0x0F, 0x0F, 0x0F, 0x0F])       # 3 (livre)
    open("build/carro.pal", "wb").write(bytes(pal[:32]))

    _desenhar_carro()
    NUM = {'.': 0, '1': 1, '2': 2, '3': 3}
    sprite_tiles, sprite_indice = [], {}
    carro_ofs_x, carro_ofs_y, carro_tile, carro_pal = [], [], [], []
    for r in range(CARRO_TILES_H):
        for c in range(CARRO_TILES_W):
            tile = tuple(tuple(NUM[_carro_px[r * 8 + j][c * 8 + i]] for i in range(8))
                         for j in range(8))
            if all(v == 0 for linha in tile for v in linha):
                continue                          # celula vazia -- economiza OAM
            if tile not in sprite_indice:
                sprite_indice[tile] = len(sprite_tiles)
                sprite_tiles.append(tile)
            carro_ofs_x.append(c * 8)
            carro_ofs_y.append(r * 8)
            carro_tile.append(sprite_indice[tile])
            carro_pal.append(PAL_CEL[r][c])

    n_sprites = len(carro_ofs_x)
    print(f"sprites do carro: {n_sprites} celulas, {len(sprite_tiles)} tiles unicos")

    sprites = bytearray()
    for t in sprite_tiles:
        sprites += codificar(t)
    pag_sprites = (len(sprites) + 255) // 256
    sprites += bytes(pag_sprites * 256 - len(sprites))
    open("build/chr_sprites_carro.bin", "wb").write(bytes(sprites))
    print(f"CHR dos sprites: build/chr_sprites_carro.bin ({len(sprites)} bytes, {pag_sprites} paginas)")

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

    # usa as paletas DE VERDADE (pal[16:32], as 4 de sprite) em vez de uma
    # cor chutada a mao -- assim a preview nunca desalinha do que o jogo
    # de verdade vai mostrar (foi exatamente isso que escondeu o cinza do
    # colarinho do Victor atras de rosa numa versao anterior desta preview)
    zoom = Image.new("RGB", (CARRO_PX_W, CARRO_PX_H))
    zp = zoom.load()
    for r in range(CARRO_TILES_H):
        for c in range(CARRO_TILES_W):
            base = 16 + PAL_CEL[r][c] * 4
            cores = [NES_RGB[pal[base + v] & 0x3F] for v in range(4)]
            for j in range(8):
                for i in range(8):
                    v = NUM[_carro_px[r * 8 + j][c * 8 + i]]
                    zp[c * 8 + i, r * 8 + j] = cores[v] if v else (60, 10, 80)
    zoom.resize((CARRO_PX_W * 6, CARRO_PX_H * 6), Image.NEAREST).save("build/carro-sprite-zoom.png")
    print("build/carro-sprite-zoom.png")

    def tab(nome, valores):
        return f"{nome}: .byte " + ", ".join(str(v) for v in valores)

    linhas = ["; gerado por tools/make_carro.py -- nao edite a mao", "",
              f"PAGINAS_CARRO = {paginas}",
              f"PAGINAS_SPRITES_CARRO = {pag_sprites}",
              f"CARRO_N_SPRITES = {n_sprites}",
              f"CARRO_PX_W = {CARRO_PX_W}",
              f"CARRO_PX_H = {CARRO_PX_H}",
              "",
              tab("carro_ofs_x_tab", carro_ofs_x),
              tab("carro_ofs_y_tab", carro_ofs_y),
              tab("carro_tile_tab", carro_tile),
              tab("carro_pal_tab", carro_pal),
              ""]
    open("build/carro.inc", "w").write("\n".join(linhas))
    print("build/carro.inc")

if __name__ == "__main__":
    main()
