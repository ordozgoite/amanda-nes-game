#!/usr/bin/env python3
"""Grava o audio do minigame: a musica do refrao mais os dois efeitos --
pegar a pizza e deixar ela cair no chao."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels
from apu import APU, gravar_wav

sym = load_labels("build/jogo-labels.txt")
B, START, RIGHT = 0x02, 0x08, 0x80
nes, apu, som = NES("jogo.nes"), APU(), []

def anda(botao=0, n=1, gravando=False):
    for _ in range(n):
        nes.frame(botao)
        if gravando:
            som.extend(apu.quadro(nes.bus.apu))

anda(n=12); anda(START, 1); anda(n=6)
for _ in range(200):
    anda(RIGHT, 1)
    if nes.bus.ram[sym["perto"]]:
        break
anda(B, 1)
anda(n=300)                          # a fala do Victor inteira
anda(B, 1)                           # fecha a caixa dele, abre a da Amanda
anda(n=200)                          # a fala dela inteira
anda(B, 1)
anda(n=20)                           # fecha a caixa dela -- carrega o minigame

anda(n=60, gravando=True)            # um instante do refrao, sem efeito

for _ in range(200):                 # pega a primeira pizza que nascer
    nes.frame()
    som.extend(apu.quadro(nes.bus.apu))
    if nes.bus.ram[sym["pz_ativa"]]:
        break
nes.bus.ram[sym["player_x"]] = nes.bus.ram[sym["pz_x"]]
anda(n=200, gravando=True)           # ate ela pegar -- grava o som_come

nes.bus.ram[sym["player_x"]] = 8     # bem longe -- a proxima pizza cai no chao
anda(n=200, gravando=True)           # ate errar -- grava o som_cai

dur, pico = gravar_wav("build/minigame.wav", som)
print(f"build/minigame.wav  --  {dur:.1f} s, pico {pico:.3f}")
