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
from make_sprites import VICTOR, AMANDA_CABECA

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
# Fica numa posicao FIXA na tela (sprite -- nao rola com o fundo), grande --
# perto da camera, com espaco de verdade pros dois respirarem na janela.
# Reaproveita o desenho de cabeca/ombro dos sprites do restaurante (VICTOR
# e AMANDA_CABECA, ver tools/make_sprites.py) em vez de redesenhar do zero
# -- mesma barba, mesmo cabelo, mesmo laco, so que 2x maior (ver _scale2x)
# e com uma paleta propria PRA CADA UM (nao uma paleta generica de "cabeca"
# igual antes), porque o cinza do colarinho do Victor e o rosa do laco da
# Amanda nao cabem juntos num unico slot de 3 cores.
#
# A LARGURA (8 colunas = 64px) ja esta no teto fisico do PPU: cada linha de
# varredura so desenha no maximo 8 sprites, e a janela/carroceria ja usam
# as 8 colunas inteiras -- nao da pra alargar mais sem estourar esse limite
# (sprite excedente simplesmente some da tela real, o emulador nao avisa).
#
# A silhueta nao e um retangulo -- tem celula vazia (canto do teto arredon-
# dado, vao embaixo do parachoque). O jogo so gasta 1 sprite de OAM por
# celula NAO vazia (ver main()), entao arredondar economiza orcamento, alem
# de ficar mais bonito.

CARRO_TILES_W = 8
CARRO_TILES_H = 8
CARRO_PX_W = CARRO_TILES_W * 8    # 64
CARRO_PX_H = CARRO_TILES_H * 8    # 64

_carro_px = [['.'] * CARRO_PX_W for _ in range(CARRO_PX_H)]
PAL_CEL = [[0] * CARRO_TILES_W for _ in range(CARRO_TILES_H)]   # 0=carro, 1=Victor, 2=Amanda

def _fill(x0, y0, w, h, ch):
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            _carro_px[y][x] = ch

def _stamp(x0, y0, linhas):
    for j, linha in enumerate(linhas):
        for i, ch in enumerate(linha):
            if ch != '.':
                _carro_px[y0 + j][x0 + i] = ch

def _scale2x(linhas):
    saida = []
    for linha in linhas:
        dobrada = "".join(c * 2 for c in linha)
        saida.append(dobrada)
        saida.append(dobrada)
    return saida

def _victor_retrato():
    """Cabeca+ombros do Victor sentado, direto do sprite do restaurante
    (VICTOR[0:16] -- cabelo, barba cheia, e as duas linhas de ombro/
    colarinho que ja fecham o desenho, ver make_sprites.py). Mesmo mapa de
    cor de sempre: '1'=cabelo, '2'=pele, '3'=cinza do colarinho -- so
    reaproveitado tal e qual, sem redesenhar."""
    return _scale2x(VICTOR[0:16])

def _amanda_retrato():
    """Cabeca da Amanda ate o queixo (AMANDA_CABECA[0:13], cabelo+laco+
    rosto -- pula o pescocinho fino original, curto demais pra esse
    tamanho) mais duas linhas de ombro NOVAS: vestido preto (mesma cor do
    cabelo, do jeito que o sprite dela ja trata as duas coisas -- ver
    docstring de make_sprites.py) com uma tira de pele nas pontas (braco).
    '1'=cabelo/vestido, '2'=pele, '3'=laco."""
    def l(*segs):
        s = "".join(c * n for c, n in segs)
        assert len(s) == 16, f"linha do ombro com {len(s)} chars: {s!r}"
        return s
    ombros = [
        l(('.',3), ('1',10), ('.',3)),
        l(('.',1), ('2',2), ('1',10), ('2',2), ('.',1)),
    ]
    return _scale2x(AMANDA_CABECA[0:13] + ombros)

def _desenhar_carro():
    # teto (tile-linha 0, y0-7): branco, a mesma cor da carroceria -- nao
    # da pra encaixar isso na propria celula do retrato (aquelas celulas
    # sao a paleta do Victor ou da Amanda, sem branco disponivel), entao e
    # uma fileira PROPRIA, gastando orcamento de OAM de verdade. Pra
    # sobrar (o teto do NES inteiro e 64 sprites NA TELA, nao por objeto),
    # a carroceria encolheu de 4 pra 3 linhas de tile (ver mais abaixo) --
    # os retratos ficam do jeito que estavam, ninguem mexeu neles.
    _fill(0, 0, 64, 8, '2')
    for i in range(3):                     # corta canto -- arredonda o teto
        for j in range(3 - i):
            _carro_px[i][j] = '.'
            _carro_px[i][63 - j] = '.'

    # janela (tile-linhas 1-4, y8-39): SEM preencher de azul primeiro -- o
    # respiro ao redor de cada retrato fica transparente (pixel 0, nao
    # pintado), entao o que aparece ali e o proprio fundo da cena (ceu/
    # predio) atras do carro, como se fosse o vidro de verdade refletindo
    # a rua -- nao uma cor solida flutuando por cima das cabecas feito na
    # versao anterior. (Nao da pra pintar de azul aqui de qualquer jeito:
    # essas celulas agora sao a paleta do Victor ou da Amanda, onde o
    # indice 3 e cinza/rosa, nao azul -- cada celula so tem UMA paleta.)
    victor = _victor_retrato()            # 32x32 (16x16 fonte, 2x)
    amanda = _amanda_retrato()             # 32x30 (15x15 fonte, 2x)
    # encostados exatamente na borda das 4 colunas de cada um (x0-31 e
    # x32-63) -- nao pode invadir a coluna vizinha, que e de uma paleta
    # DIFERENTE (ver PAL_CEL logo abaixo); um pixel a mais de qualquer
    # lado rendeia com a cor errada (ou, pra Amanda, sai fora da grade)
    _stamp(0, 8, victor)                   # metade esquerda da janela
    _stamp(32, 8, amanda)                  # metade direita
    for r in range(1, 5):
        for c in range(0, 4):
            PAL_CEL[r][c] = 1              # Victor
        for c in range(4, 8):
            PAL_CEL[r][c] = 2              # Amanda

    # carroceria (tile-linhas 5-7, y40-63, todas as 8 colunas) -- 3
    # linhas, nao 4: o teto acima tomou o lugar que uma 4a linha ocuparia
    _fill(0, 40, 64, 10, '2')              # branco
    _fill(31, 41, 2, 8, '1')               # friso da porta
    _fill(0, 50, 64, 3, '1')               # parachoque
    _fill(0, 53, 64, 11, '.')              # vao embaixo (chao) ate a base do sprite

    def _roda(x0, y0):
        _fill(x0, y0, 14, 14, '1')
        for i in range(2):                 # corta os 4 cantos -- arredonda o pneu
            for j in range(2 - i):
                for dy, dx in ((i, j), (i, 13 - j), (13 - i, j), (13 - i, 13 - j)):
                    _carro_px[y0 + dy][x0 + dx] = '.'
    _roda(8, 44)                           # roda esquerda -- topo (y44) fica sob o
    _roda(42, 44)                          # parachoque, so o pneu "aparece" embaixo

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
    # paletas de sprite: 0 = carro (cinza-escuro/branco/vidro azul); 1 =
    # Victor (cabelo preto/pele/cinza do colarinho -- mesmo mapa de
    # PALETA_SPRITE_VICTOR); 2 = Amanda (cabelo preto/pele/laco rosa --
    # mesmo mapa de PALETA_SPRITE_CABECA). Precisam ser DUAS paletas
    # separadas (nao uma "cabeca" generica como antes): o cinza do
    # colarinho dele e o rosa do laco dela nao cabem no mesmo slot de 3
    # cores. O trim do carro (roda, parachoque, friso) usa 0x00 (cinza bem
    # escuro), NAO 0x0F (preto puro) -- a rua tambem e 0x0F, e roda/
    # parachoque cai bem em cima dela; com a mesma cor eles ficam
    # invisiveis (mesma armadilha da calcada vs. rua, ver CLAUDE.md).
    pal += bytes([0x0F, 0x00, 0x30, 0x21])       # 0: carro branco
    pal += bytes([0x0F, 0x0F, 0x37, 0x10])       # 1: Victor -- pele 0x37, colarinho 0x10
    pal += bytes([0x0F, 0x0F, 0x37, 0x24])       # 2: Amanda -- pele 0x37, laco 0x24
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
