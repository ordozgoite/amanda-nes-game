#!/usr/bin/env python3
"""Roda o jogo e salva as telas por onde ele passa."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from screenshot import render

BTN_START, BTN_B, BTN_RIGHT = 0x08, 0x02, 0x80
ESPERA_MENU = 70   # o respiro pro plin/eco, antes da cena carregar (ver jogo.s)

sym = load_labels("build/jogo-labels.txt")

nes = NES("jogo.nes")
for _ in range(12):
    nes.frame()
render(nes).save("build/jogo-1-menu.png")
print("build/jogo-1-menu.png   (banco", nes.bus.banco, ")")

nes.frame(BTN_START)
for _ in range(ESPERA_MENU):
    nes.frame()
render(nes).save("build/jogo-2-cena.png")
print("build/jogo-2-cena.png   (banco", nes.bus.banco, ")")

for _ in range(110):            # anda pra direita
    nes.frame(BTN_RIGHT)
render(nes).save("build/jogo-3-andando.png")
print("build/jogo-3-andando.png")

nes.frame(BTN_START)             # START de volta pro titulo, sem passar pelo dialogo
for _ in range(6):
    nes.frame()
render(nes).save("build/jogo-4-voltou.png")
print("build/jogo-4-voltou.png (banco", nes.bus.banco, ")")

# --- de novo, mas ate o fim: fala com o Victor (as duas partes), depois a
# Amanda, e cai no minigame ---
nes.frame(BTN_START)
for _ in range(ESPERA_MENU):
    nes.frame()
for _ in range(200):
    nes.frame(BTN_RIGHT)
    if nes.bus.ram[sym["perto"]]:
        break
nes.frame(BTN_B)               # ela vai sentar do lado dele antes do dialogo abrir
for _ in range(25):
    nes.frame()
render(nes).save("build/jogo-5-ela-senta.png")
print("build/jogo-5-ela-senta.png")

for _ in range(150):            # espera a sentada terminar e o balao abrir
    nes.frame()
    if nes.bus.ram[sym["dialogo"]]:
        break

# o dialogo inteiro tem 13 partes agora (ver FALANTE_GRUPO em
# tools/make_scene.py); so tira foto de algumas -- a primeira, a que abre
# logo depois dele sentar (parte 3, ver PARTE_SENTAR), a do coracaozinho
# (parte 8) e a ultima -- e passa pelas outras direto
CAPTURAS = {0: "build/jogo-6-fala-fim.png",
            3: "build/jogo-6a-victor-sentou.png",
            8: "build/jogo-6b-fala-coracao.png",
            12: "build/jogo-6c-fala-ultima.png"}
for parte in range(13):
    for _ in range(400):
        nes.frame()
    if parte in CAPTURAS:
        render(nes).save(CAPTURAS[parte])
        print(CAPTURAS[parte])
    nes.frame(BTN_B)

for _ in range(20):               # fecha a ultima caixa -> carrega a intro do minigame
    nes.frame()
render(nes).save("build/jogo-7-intro.png")
print("build/jogo-7-intro.png (banco", nes.bus.banco, ")")

nes.frame(BTN_B)                  # dispensa a intro -- so ai comeca a jogar
for _ in range(10):
    nes.frame()
render(nes).save("build/jogo-7b-minigame.png")
print("build/jogo-7b-minigame.png")

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
for _ in range(60):                # a fraseszinha feliz toca inteira
    nes.frame()
render(nes).save("build/jogo-9-vitoria.png")
print("build/jogo-9-vitoria.png  pontos =", nes.bus.ram[sym["jogo_pontos"]])

nes.frame(BTN_B)                  # "APERTE B PRA CONTINUAR" -> cena do carro
for _ in range(20):
    nes.frame()
render(nes).save("build/jogo-10-carro.png")
print("build/jogo-10-carro.png (banco", nes.bus.banco, ")")

for _ in range(150):               # deixa o cenario rolar um pouco
    nes.frame()
render(nes).save("build/jogo-11-carro-andando.png")
print("build/jogo-11-carro-andando.png  scroll =", nes.bus.ram[sym["carro_scroll"]])
