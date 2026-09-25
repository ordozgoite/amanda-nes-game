#!/usr/bin/env python3
"""
As fotos da parte final: uma foto de verdade (fotos/*.jpg) vira uma
"polaroide" sepia pontilhada, com legenda embaixo.

Por que monocromatica: foto colorida convertida direto fica cheia de
blocos, porque o atributo de cor so muda a cada 16x16 e o tom de pele
"quebra" no meio do rosto (testado -- ficou feio). Com UMA paleta so de 4
tons (preto, marrom, ambar, creme) nao existe fronteira de atributo
nenhuma, e o pontilhado ordenado (Bayer 4x4) faz os 4 tons parecerem
muitos, tipo a camera do Game Boy.

O limite que sobra e o de 256 tiles por tela: a foto sozinha tem ~350
tiles diferentes (o pontilhado quase nunca repete). Entao os tiles da foto
sao agrupados (k-medoides) ate caber no que sobra depois da moldura e da
legenda: cada tile e trocado pelo "parente" mais parecido VISTO DE LONGE
(compara a media 2x2, que e como o olho le pontilhado), e o representante
de cada grupo e um tile real da foto, entao o pontilhado continua nitido.

Emite build/fotos.inc com os .incbin nos bancos livres e as tabelas que o
assembly percorre (ver carrega_foto) -- o numero de fotos, o banco de cada
uma e quantas paginas de CHR copiar vem daqui, nunca escritos a mao.
"""
import random
import sys
sys.path.insert(0, "tools")
from make_chr import FONT
from PIL import Image, ImageEnhance, ImageOps

# ------------------------------------------------------------- as fotos
# recorte = (x0, y0, x1, y1) em pixels da foto original; a proporcao deve
# ser perto de FOTO_W:FOTO_H (176:128), senao a imagem estica.
# legenda: so letras sem acento, numeros e pontuacao da fonte do jogo.
FOTOS = [
    dict(arquivo="fotos/01-mesa.jpg", recorte=(60, 430, 1080, 1172),
         legenda="NOSSO PRIMEIRO ANO NOVO"),
]

# sepia: 0 preto (fundo da tela e sombra da foto), 1 marrom, 2 ambar, 3 creme
PALETA = [0x0F, 0x17, 0x27, 0x37]

# a polaroide: moldura creme, foto 22x16 tiles, faixa larga embaixo pra
# legenda. Tudo alinhado em tile -- borda cortando um tile no meio so
# criaria tiles "meio moldura, meio foto" a toa.
W, H = 256, 240
FOTO_W, FOTO_H = 176, 128
FOTO_X, FOTO_Y = 40, 40
MOLDURA = (32, 32, 192, 176)          # x, y, larg, alt (em pixels)
LEGENDA_Y = FOTO_Y + FOTO_H + 18

BANCOS_LIVRES = [4, 5, 6]
BANCO_BYTES = 0x4000

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

def converte(foto):
    """Devolve (indices 0-3 pontilhados, alvo continuo 0.0-3.0) da foto."""
    img = Image.open(foto["arquivo"]).convert("RGB").crop(foto["recorte"])
    g = img.convert("L").resize((FOTO_W, FOTO_H), Image.LANCZOS)
    g = ImageOps.autocontrast(g, cutoff=1)
    alvo = [g.getpixel((x, y)) / 255 * 3 for y in range(FOTO_H) for x in range(FOTO_W)]
    idx = []
    for y in range(FOTO_H):
        for x in range(FOTO_W):
            v = alvo[y * FOTO_W + x] + (BAYER[y % 4][x % 4] + .5) / 16 - .5
            idx.append(max(0, min(3, round(v))))
    return idx, alvo

def celula(arr, larg, tx, ty):
    return tuple(arr[(ty * 8 + y) * larg + tx * 8 + x] for y in range(8) for x in range(8))

def borra(t):
    """Media 2x2 -- o pontilhado visto de longe."""
    return [sum(t[(y + dy) * 8 + x + dx] for dy in (0, 1) for dx in (0, 1)) / 4
            for y in range(7) for x in range(7)]

def reduz(pads, alvos, limite):
    """k-medoides: no maximo `limite` padroes diferentes."""
    cands = sorted(set(pads))
    if len(cands) <= limite:
        return pads
    ba = [borra(a) for a in alvos]
    bc = {p: borra(p) for p in cands}
    def custo(i, p):
        return sum((u - v) ** 2 for u, v in zip(ba[i], bc[p]))
    random.seed(20260925)
    cent = random.sample(cands, limite)
    for _ in range(10):
        atrib = [min(range(limite), key=lambda k: custo(i, cent[k])) for i in range(len(pads))]
        novo = []
        for k in range(limite):
            m = [i for i in range(len(pads)) if atrib[i] == k]
            if not m:
                novo.append(cent[k])
                continue
            opcoes = {pads[i] for i in m} | {cent[k]}
            novo.append(min(opcoes, key=lambda p: sum(custo(i, p) for i in m)))
        if novo == cent:
            break
        cent = novo
    return [cent[a] for a in atrib]

def monta_tela(foto):
    """Canvas 256x240 de indices 0-3 + a lista de celulas da foto."""
    px = [[0] * W for _ in range(H)]
    mx, my, mw, mh = MOLDURA
    for y in range(my, my + mh):
        for x in range(mx, mx + mw):
            px[y][x] = 3
    s = foto["legenda"].upper()
    assert all(ch == ' ' or ch in FONT for ch in s), f"letra fora da fonte: {s!r}"
    lx = (W - len(s) * 6) // 2
    assert mx < lx and lx + len(s) * 6 < mx + mw, f"legenda larga demais: {s!r}"
    for n, ch in enumerate(s):
        for j, linha in enumerate(FONT.get(ch, [])):
            for i, p in enumerate(linha):
                if p == 'X':
                    px[LEGENDA_Y + j][lx + n * 6 + i] = 0
    idx, alvo = converte(foto)
    for y in range(FOTO_H):
        for x in range(FOTO_W):
            px[FOTO_Y + y][FOTO_X + x] = idx[y * FOTO_W + x]
    return px, idx, alvo

def codificar(t):
    lo, hi = [], []
    for y in range(8):
        b0 = b1 = 0
        for x in range(8):
            c = t[y * 8 + x]
            if c & 1: b0 |= 1 << (7 - x)
            if c & 2: b1 |= 1 << (7 - x)
        lo.append(b0); hi.append(b1)
    return bytes(lo + hi)

def gera(n, foto):
    px, idx, alvo = monta_tela(foto)
    flat = [v for linha in px for v in linha]
    TW, TH = FOTO_W // 8, FOTO_H // 8
    fx, fy = FOTO_X // 8, FOTO_Y // 8
    # tiles fixos (fora da foto) primeiro: moldura, legenda, fundo
    fixos = {celula(flat, W, tx, ty) for ty in range(30) for tx in range(32)
             if not (fx <= tx < fx + TW and fy <= ty < fy + TH)}
    pads = [celula(idx, FOTO_W, tx, ty) for ty in range(TH) for tx in range(TW)]
    alvos = [celula(alvo, FOTO_W, tx, ty) for ty in range(TH) for tx in range(TW)]
    antes = len(set(pads))
    pads = reduz(pads, alvos, 256 - len(fixos))
    for k, p in enumerate(pads):
        tx, ty = k % TW, k // TW
        for j in range(8):
            for i in range(8):
                px[FOTO_Y + ty * 8 + j][FOTO_X + tx * 8 + i] = p[j * 8 + i]
    flat = [v for linha in px for v in linha]

    tiles, indice, nt = [], {}, []
    for ty in range(30):
        for tx in range(32):
            t = celula(flat, W, tx, ty)
            if t not in indice:
                indice[t] = len(tiles)
                tiles.append(t)
            nt.append(indice[t])
    assert len(tiles) <= 256, f"foto {n}: {len(tiles)} tiles"
    print(f"foto {n} ({foto['arquivo']}): {antes} tiles na foto -> "
          f"{len(set(pads))}, {len(tiles)}/256 na tela")

    chr_ = b"".join(codificar(t) for t in tiles)
    paginas = (len(chr_) + 255) // 256
    chr_ += bytes(paginas * 256 - len(chr_))
    open(f"build/chr_foto{n}.bin", "wb").write(chr_)
    # uma paleta so -> atributos todos zero
    open(f"build/foto{n}.nam", "wb").write(bytes(nt) + bytes(64))

    from screenshot import NES_RGB
    img = Image.new("RGB", (W, H))
    img.putdata([NES_RGB[PALETA[v]] for v in flat])
    img.resize((W * 2, H * 2), Image.NEAREST).save(f"build/foto{n}.png")
    return paginas, len(chr_) + 1024

def main():
    blocos = []
    banco, usado = 0, 0
    for n, foto in enumerate(FOTOS, 1):
        paginas, tam = gera(n, foto)
        if usado + tam > BANCO_BYTES:
            banco, usado = banco + 1, 0
        assert banco < len(BANCOS_LIVRES), "fotos demais pros bancos livres"
        usado += tam
        blocos.append((n, BANCOS_LIVRES[banco], paginas))

    pal = bytes(PALETA * 4) + bytes([0x0F] * 16)
    open("build/foto.pal", "wb").write(pal)

    L = ["; gerado por tools/make_foto.py -- nao edite a mao", "",
         f"FOTOS_N = {len(FOTOS)}", ""]
    for n, b, _ in blocos:
        L += [f'.segment "BANK{b}"',
              f'chr_foto{n}: .incbin "chr_foto{n}.bin"',
              f'nam_foto{n}: .incbin "foto{n}.nam"']
    L += ['', '.segment "RODATA"',
          "foto_banco_tab: .byte " + ", ".join(str(b) for _, b, _ in blocos),
          "foto_pag_tab:   .byte " + ", ".join(str(p) for _, _, p in blocos),
          "foto_chr_lo:    .byte " + ", ".join(f"<chr_foto{n}" for n, _, _ in blocos),
          "foto_chr_hi:    .byte " + ", ".join(f">chr_foto{n}" for n, _, _ in blocos),
          "foto_nam_lo:    .byte " + ", ".join(f"<nam_foto{n}" for n, _, _ in blocos),
          "foto_nam_hi:    .byte " + ", ".join(f">nam_foto{n}" for n, _, _ in blocos),
          "paletas_foto:   .incbin \"foto.pal\"",
          '.segment "CODE"', ""]
    open("build/fotos.inc", "w").write("\n".join(L))
    print("build/fotos.inc")

if __name__ == "__main__":
    main()
