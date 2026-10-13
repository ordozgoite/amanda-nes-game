#!/usr/bin/env python3
"""Roda o jogo e salva as telas por onde ele passa."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from screenshot import render
import robo
from make_jogo import PZ_N

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

nes.frame(BTN_START)             # START nao faz mais nada depois do titulo
for _ in range(6):
    nes.frame()
render(nes).save("build/jogo-4-start-nada.png")
print("build/jogo-4-start-nada.png (tela", nes.bus.ram[sym["tela"]], ")")

# --- ate o fim: fala com o Victor (as duas partes), depois a Amanda, e
# cai no minigame ---
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

# o robo joga ate a primeira pimenta aparecer (captura dela caindo) e
# depois ate ganhar
robo.joga(nes, sym, 6000, ate=lambda n: any(
    n.bus.ram[sym["pz_ativa"] + i] and n.bus.ram[sym["pz_tipo"] + i]
    and n.bus.ram[sym["pz_y"] + i] > 110 for i in range(PZ_N)))
render(nes).save("build/jogo-8b-minigame-pimenta.png")
print("build/jogo-8b-minigame-pimenta.png  pontos =", nes.bus.ram[sym["jogo_pontos"]])
robo.joga(nes, sym, 12000, ate=lambda n: n.bus.ram[sym["jogo_fase"]] == 1)
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

def ate_ler(nes):
    """Espera a caixa terminar de escrever (dialogo == 3)."""
    for _ in range(300):
        nes.frame()
        if nes.bus.ram[sym["dialogo"]] == 3:
            break
    nes.frame()

ate_ler(nes)                      # a Amanda puxa assunto sozinha
render(nes).save("build/jogo-11b-carro-amanda.png")
print("build/jogo-11b-carro-amanda.png")
nes.frame(BTN_B)
ate_ler(nes)                      # e o Victor responde
render(nes).save("build/jogo-11c-carro-victor.png")
print("build/jogo-11c-carro-victor.png")
nes.frame(BTN_B)
for _ in range(12):
    nes.frame()

def ate_tela(nes, tela, limite=200):
    """B ja apertado: espera o fade escurecer, a tela trocar e clarear."""
    for _ in range(limite):
        nes.frame()
        if nes.bus.ram[sym["tela"]] == tela and nes.bus.ram[sym["fade_nivel"]] == 0:
            break
    nes.frame()                   # a paleta clara so chega no PPU no NMI seguinte

nes.frame(BTN_B)                  # conversa acabou: B escurece -> primeira foto
for _ in range(12):
    nes.frame()
render(nes).save("build/jogo-11d-carro-escurecendo.png")
print("build/jogo-11d-carro-escurecendo.png  fade =", nes.bus.ram[sym["fade_nivel"]])
ate_tela(nes, 4)
from make_foto import FOTOS
for n in range(1, len(FOTOS) + 1):
    if n > 1:
        nes.frame(BTN_B)
        for _ in range(10):
            nes.frame()
        ate_tela(nes, 4)
    nome = f"build/jogo-12-foto{n}.png"
    render(nes).save(nome)
    print(nome, "(banco", nes.bus.banco, ")")

nes.frame(BTN_B)                  # depois da ultima: a cena final
for _ in range(30):
    nes.frame()
ate_tela(nes, 5)
render(nes).save("build/jogo-15-fim-chegando.png")
print("build/jogo-15-fim-chegando.png (banco", nes.bus.banco, ")")
for _ in range(200):
    nes.frame()
    if nes.bus.ram[sym["hulk_pulo"]] >= 5:   # no alto do pulinho, latindo
        break
nes.frame()
render(nes).save("build/jogo-15b-fim-hulk-latindo.png")
print("build/jogo-15b-fim-hulk-latindo.png")
for _ in range(400):
    nes.frame()
    if nes.bus.ram[sym["fim_fase"]] == 2:
        break
render(nes).save("build/jogo-16-fim.png")
print("build/jogo-16-fim.png")
for _ in range(400):
    nes.frame()
    if nes.bus.ram[sym["cor_y"]] and nes.bus.ram[sym["cor_y"]] < 150:
        break
render(nes).save("build/jogo-17-fim-coracao.png")
print("build/jogo-17-fim-coracao.png")
for _ in range(600):
    nes.frame()
    if nes.bus.ram[sym["lati_t"]] == 5:       # boca aberta, ela no alto do pulo
        break
nes.frame()                       # a OAM chega no PPU no quadro seguinte
render(nes).save("build/jogo-18-fim-latido.png")
print("build/jogo-18-fim-latido.png")
