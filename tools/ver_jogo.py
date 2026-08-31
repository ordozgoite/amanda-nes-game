#!/usr/bin/env python3
"""Roda o jogo e salva as telas por onde ele passa."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from screenshot import render

BTN_START, BTN_B, BTN_RIGHT = 0x08, 0x02, 0x80

nes = NES("jogo.nes")
for _ in range(12):
    nes.frame()
render(nes).save("build/jogo-1-menu.png")
print("build/jogo-1-menu.png   (banco", nes.bus.banco, ")")

nes.frame(BTN_START)
for _ in range(6):
    nes.frame()
render(nes).save("build/jogo-2-cena.png")
print("build/jogo-2-cena.png   (banco", nes.bus.banco, ")")

for _ in range(110):            # anda pra direita
    nes.frame(BTN_RIGHT)
render(nes).save("build/jogo-3-andando.png")
print("build/jogo-3-andando.png")

nes.frame(BTN_B)
for _ in range(6):
    nes.frame()
render(nes).save("build/jogo-4-voltou.png")
print("build/jogo-4-voltou.png (banco", nes.bus.banco, ")")
