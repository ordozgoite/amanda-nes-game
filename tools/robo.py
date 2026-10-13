#!/usr/bin/env python3
"""
Um jogador de mentira pro minigame, pros testes e capturas.

Joga com o CONTROLE, andando 1 pixel por quadro como a Amanda de verdade --
nao teleporta o player_x pra baixo da pizza. E isso que prova que a curva de
dificuldade (make_jogo.py) e ganhavel: se alguma pizza nascesse longe demais
pra alcancar a pe, ou uma pimenta caisse em cima dela, o robo erraria.

Estrategia: vai pra baixo da pizza mais baixa (a proxima a chegar); se uma
pimenta estiver perto de cair e o proximo passo entraria na faixa dela,
espera parado (ou sai de baixo, se ja estiver la). Como a pimenta cai na
coluna da proxima pizza, entre esta e a proxima, na pratica o robo pega
esta, chega perto da proxima, espera do lado a pimenta passar e so entao
entra.
"""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from make_jogo import PZ_N, PIMENTA_Y_MIN

BTN_LEFT, BTN_RIGHT = 0x40, 0x80

# tem que bater com testa_pimenta em src/jogo.s: doi se
#   player_x < pz_x + 4  e  pz_x < player_x + 12
# (uma folga de 2px de cada lado, pro robo nao jogar no limite)
FOLGA = 2
# a partir daqui a pimenta ja e perigo iminente: a pimenta cai no maximo
# ~2 px/quadro e atravessar a coluna dela leva ~16 quadros. Mais alta que
# isso, passar por baixo e seguro -- e precisa ser, porque a pimenta que
# nasce junto com uma pizza pode estar no caminho ate ela.
ALERTA_Y = PIMENTA_Y_MIN - 36

def objetos(nes, sym):
    ram = nes.bus.ram
    for i in range(PZ_N):
        if ram[sym["pz_ativa"] + i]:
            yield (ram[sym["pz_tipo"] + i], ram[sym["pz_x"] + i], ram[sym["pz_y"] + i])

def perigoso(px, pimentas):
    return any(x - 12 - FOLGA < px < x + 4 + FOLGA for x in pimentas)

def botao(nes, sym, desvia=True):
    """O botao a apertar neste quadro. Com desvia=False ele finge que as
    pimentas nao existem -- serve pra provar que elas atrapalham de verdade."""
    px = nes.bus.ram[sym["player_x"]]
    objs = list(objetos(nes, sym))
    pimentas = [x for t, x, y in objs if t == 1 and y >= ALERTA_Y and desvia]
    pizzas = [(y, x) for t, x, y in objs if t == 0]

    if perigoso(px, pimentas):
        # ja esta embaixo de uma: sai pelo lado mais perto
        for d in range(1, 40):
            if not perigoso(px - d, pimentas) and px - d >= 8:
                return BTN_LEFT
            if not perigoso(px + d, pimentas) and px + d <= 232:
                return BTN_RIGHT
        return 0

    if not pizzas:
        return 0
    alvo = max(pizzas)[1]
    if alvo < px and not perigoso(px - 1, pimentas):
        return BTN_LEFT
    if alvo > px and not perigoso(px + 1, pimentas):
        return BTN_RIGHT
    return 0

def joga(nes, sym, quadros, ate=None, desvia=True):
    """Joga ate `ate(nes)` ficar verdadeiro (ou acabar os quadros). Devolve
    quantos quadros levou, e quantas vidas se perderam pra pimenta."""
    pimentadas = 0
    for q in range(quadros):
        antes = {i for i in range(PZ_N) if nes.bus.ram[sym["pz_ativa"] + i]
                 and nes.bus.ram[sym["pz_tipo"] + i] == 1}
        erros0 = nes.bus.ram[sym["jogo_erros"]]
        nes.frame(botao(nes, sym, desvia))
        # uma pimenta que sumiu ACIMA do chao e uma que acertou
        if nes.bus.ram[sym["jogo_erros"]] > erros0:
            for i in antes:
                if not nes.bus.ram[sym["pz_ativa"] + i] and nes.bus.ram[sym["pz_y"] + i] < 208:
                    pimentadas += 1
        if ate and ate(nes):
            return q + 1, pimentadas
    return quadros, pimentadas
