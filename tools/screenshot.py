#!/usr/bin/env python3
"""
Desenha em PNG o que apareceria na TV: o fundo a partir da nametable
e os sprites a partir da OAM, com os tiles da CHR-RAM e as paletas que o
jogo carregou. Usado por ver_jogo.py.

Nao e uma PPU de verdade: desenha o fundo a partir da nametable, com os
tiles do CHR e as paletas que o codigo carregou. Da pra ver exatamente o
que apareceria na TV.
"""
import sys
sys.path.insert(0, "tools")
from nesemu import NES
from PIL import Image

# paleta de cores do NES (RGB), indexada pelos valores $00-$3F
NES_RGB = [
 (98,98,98),(0,31,178),(36,4,200),(82,0,178),(115,0,118),(128,0,36),(115,11,0),(82,40,0),
 (36,68,0),(0,87,0),(0,92,0),(0,83,36),(0,60,118),(0,0,0),(0,0,0),(0,0,0),
 (171,171,171),(13,87,255),(75,48,255),(138,19,255),(188,8,214),(206,9,104),(188,39,0),(138,88,0),
 (75,133,0),(13,167,0),(0,175,0),(0,164,104),(0,131,214),(0,0,0),(0,0,0),(0,0,0),
 (255,255,255),(83,174,255),(144,133,255),(211,101,255),(255,87,255),(255,93,207),(255,119,87),(226,164,0),
 (169,204,0),(96,232,0),(56,255,56),(56,255,162),(56,255,255),(61,61,61),(0,0,0),(0,0,0),
 (255,255,255),(190,229,255),(214,213,255),(238,204,255),(255,201,255),(255,203,238),(255,213,190),(240,232,163),
 (207,244,163),(180,255,163),(163,255,180),(163,255,220),(163,255,255),(190,190,190),(0,0,0),(0,0,0),
]

def tile_pixels(chr_data, table, index):
    """Devolve 8x8 indices de cor (0-3) de um tile."""
    base = table * 0x1000 + index * 16
    out = []
    for row in range(8):
        lo = chr_data[base + row]
        hi = chr_data[base + row + 8]
        out.append([((lo >> b) & 1) | (((hi >> b) & 1) << 1) for b in range(7, -1, -1)])
    return out

def render(nes, chr_data=None, scale=3):
    # com CHR-RAM os desenhos vivem na memoria de video, nao no arquivo
    if chr_data is None:
        chr_data = bytes(nes.bus.vram[:0x2000])
    pal = list(nes.bus.vram[0x3F00:0x3F20])
    img = Image.new("RGB", (256, 240))
    px = img.load()
    for ty in range(30):
        for tx in range(32):
            tile = nes.bus.vram[0x2000 + ty * 32 + tx]
            attr = nes.bus.vram[0x23C0 + (ty // 4) * 8 + (tx // 4)]
            shift = ((ty & 2) << 1) | (tx & 2)
            palnum = (attr >> shift) & 3
            bits = tile_pixels(chr_data, 1, tile)
            for y in range(8):
                for x in range(8):
                    c = bits[y][x]
                    entry = pal[0] if c == 0 else pal[palnum * 4 + c]
                    px[tx * 8 + x, ty * 8 + y] = NES_RGB[entry & 0x3F]

    # ---- sprites, por cima do fundo (ignorando prioridade) ----
    for i in range(0, 256, 4):
        y, tile, attr, x = nes.bus.oam[i:i + 4]
        if y >= 0xEF:                      # Y fora da tela = sprite escondido
            continue
        palnum = 4 + (attr & 3)            # sprites usam as paletas 4 a 7
        bits = tile_pixels(chr_data, 0, tile)
        for row in range(8):
            for col in range(8):
                c = bits[7 - row if attr & 0x80 else row][
                        7 - col if attr & 0x40 else col]
                if c == 0:
                    continue               # cor 0 e transparente em sprite
                sx, sy = x + col, y + row + 1
                if 0 <= sx < 256 and 0 <= sy < 240:
                    px[sx, sy] = NES_RGB[pal[palnum * 4 + c] & 0x3F]

    return img.resize((256 * scale, 240 * scale), Image.NEAREST)
