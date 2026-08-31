#!/usr/bin/env python3
"""Roda o jogo e salva as telas por onde ele passa."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from screenshot import render

BTN_START, BTN_B, BTN_RIGHT = 0x08, 0x02, 0x80

sym = load_labels("build/jogo-labels.txt")

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

# --- fala com o Victor ate o fim, pra ver o dialogo dela e o minigame ---
for _ in range(60):
    nes.frame(BTN_RIGHT)
    if nes.bus.ram[sym["perto"]]:
        break
nes.frame(BTN_B)
for _ in range(6):
    nes.frame()
render(nes).save("build/jogo-5-fala-amanda.png")
print("build/jogo-5-fala-amanda.png")

for _ in range(400):             # digita o dialogo inteiro
    nes.frame()
render(nes).save("build/jogo-6-fala-fim.png")
print("build/jogo-6-fala-fim.png")

nes.frame(BTN_B)
for _ in range(20):
    nes.frame()
render(nes).save("build/jogo-7-minigame.png")
print("build/jogo-7-minigame.png (banco", nes.bus.banco, ")")

for _ in range(120):              # deixa uma pizza nascer e cair um pouco
    nes.frame()
render(nes).save("build/jogo-8-minigame-caindo.png")
print("build/jogo-8-minigame-caindo.png")

for _ in range(3000):             # pega pizzas ate ganhar
    nes.frame()
    if nes.bus.ram[sym["pz_ativa"]]:
        nes.bus.ram[sym["player_x"]] = nes.bus.ram[sym["pz_x"]]
    if nes.bus.ram[sym["jogo_fase"]] == 1:
        break
for _ in range(3):                # o placar leva 1 quadro pra alcancar o estado
    nes.frame()
render(nes).save("build/jogo-9-comemoracao.png")
print("build/jogo-9-comemoracao.png  pontos =", nes.bus.ram[sym["jogo_pontos"]])
