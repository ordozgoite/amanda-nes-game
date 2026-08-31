#!/usr/bin/env python3
"""
Os personagens.

  Amanda -- 16x32, dois quadros de caminhada. Personagem jogavel.
  Victor -- 16x24, sentado a mesa.

Cada tile de sprite tem 3 cores + transparente, e a paleta e escolhida por
tile. So existem 4 paletas de sprite no hardware inteiro, e a cena da
pizzaria ja usa as 4 (3 da Amanda + 1 do Victor) -- entao a paleta "3" faz
dupla funcao, escolhida por TILE, nao por personagem:

  paleta 0 (cabeca da Amanda): 1 = cabelo preto   2 = pele  3 = laco rosa
  paleta 1 (tronco e pernas
             da Amanda):       1 = vestido preto  2 = pele  3 = cabelo preto
  paleta 2 (cabeca do Victor): 1 = cabelo e barba 2 = pele  3 = cinza da camisa
  paleta 3 (torso do Victor):  1 = logo da Nike   2 = pele  3 = cinza da camisa

As pernas da Amanda nao tem paleta propria: como o vestido cobre a perna
inteira, todo pixel de pernas e indice 1 (preto) ou 3 (preto, a mecha de
cabelo) -- os dois iguais na paleta do tronco --, entao reaproveita essa
paleta em vez de gastar uma so pra si. Isso libera a paleta 3 pro torso do
Victor, que precisa de uma cor que a cabeca dele nao tem: o azul-ciano do
logo da Nike na camisa (a mesma camisa do primeiro encontro dos dois).
Cabeca e torso dele ja eram tiles diferentes, entao so trocar qual paleta
cada um usa (ver vic_pal em src/jogo.s) nao pede nenhum redesenho.

O cabelo dela e preto do topo ao quadril, escorrendo pelas costas por
cima do vestido -- por isso o indice 3 do tronco e das pernas e sempre a
mesma cor do cabelo, a mesma mecha atravessando a costura dos tiles em
y=16 e y=48. Ja na cabeca o indice 3 e outra coisa: um lacinho rosa (a
mesma cor do coracao de neon da parede) cravado no alto do cabelo, do
lado direito -- o detalhe que fecha a silhueta como feminina.
"""
import sys
from make_chr import encode_tile, BLANK

def linha(*segs):
    """linha(('.',3), ('1',10), ('.',3)) -> string de 16 chars."""
    s = "".join(c * n for c, n in segs)
    assert len(s) == 16, f"linha com {len(s)} chars: {s!r}"
    return s

# ====================================================== Amanda
# Cabeca: o cabelo desce pelos dois lados e vai clareando embaixo.
AMANDA_CABECA = [
    linha(('.',3), ('1',5), ('3',2), ('1',1), ('3',2), ('.',3)),  # topo do cabelo + lacinho
    linha(('.',2), ('1',7), ('3',3), ('1',2), ('.',2)),           # laco, no do meio
    linha(('.',2), ('1',6), ('3',2), ('1',1), ('3',2),
          ('1',1), ('.',2)),                                     # laco, pontas de baixo
    linha(('.',2), ('1',12), ('.',2)),
    linha(('.',2), ('1',3), ('2',6), ('1',3), ('.',2)),          # testa -- rosto estreito
    linha(('.',2), ('1',3), ('2',6), ('1',3), ('.',2)),
    linha(('.',2), ('1',2), ('2',8), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',1), ('1',1), ('2',4),
          ('1',1), ('2',1), ('1',2), ('.',2)),                   # olhos
    linha(('.',2), ('1',2), ('2',8), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',8), ('1',2), ('.',2)),
    linha(('.',2), ('1',2), ('2',3), ('1',2), ('2',3),
          ('1',2), ('.',2)),                                     # boca
    linha(('.',2), ('1',2), ('2',8), ('1',2), ('.',2)),
    linha(('.',2), ('1',3), ('2',6), ('1',3), ('.',2)),          # queixo
    linha(('.',2), ('1',4), ('2',4), ('1',4), ('.',2)),          # pescoco fino
    linha(('.',2), ('1',4), ('2',4), ('1',4), ('.',2)),
    linha(('.',2), ('1',4), ('2',4), ('1',4), ('.',2)),
]

# Amanda falando: so a linha da boca muda, alargando a marca escura --
# igual ideia do Victor, so que aqui a boca esta espalhada por dois tiles
# (a cabeca e 2 de largura), entao os dois precisam da versao aberta.
AMANDA_CABECA_FALANDO = list(AMANDA_CABECA)
AMANDA_CABECA_FALANDO[10] = linha(('.',2), ('1',2), ('2',2), ('1',4),
                                   ('2',2), ('1',2), ('.',2))

# O cabelo desce rente ao corpo, nao aberto pros lados.
AMANDA_TRONCO = [
    linha(('.',2), ('3',3), ('1',6), ('3',3), ('.',2)),           # ombros
    linha(('.',1), ('3',3), ('1',8), ('3',3), ('.',1)),
    linha(('2',1), ('3',2), ('1',10), ('3',2), ('2',1)),          # bracos
    linha(('2',1), ('3',2), ('1',10), ('3',2), ('2',1)),
    linha(('2',1), ('3',2), ('1',10), ('3',2), ('2',1)),
    linha(('2',1), ('3',2), ('1',10), ('3',2), ('2',1)),
    linha(('2',1), ('3',2), ('1',10), ('3',2), ('2',1)),
    linha(('.',1), ('2',1), ('3',2), ('1',8), ('3',2),
          ('2',1), ('.',1)),                                     # maos
]

# Vestido preto ate a canela, saia fechada (sem vao entre as pernas) --
# so a barra balanca um pouco entre os dois quadros de passo, e os
# sapatos aparecem por baixo.
AMANDA_PERNAS_A = [
    linha(('.',2), ('3',1), ('1',10), ('3',1), ('.',2)),          # cintura, cabelo ate o quadril
    linha(('.',2), ('3',1), ('1',10), ('3',1), ('.',2)),
    linha(('.',3), ('1',10), ('.',3)),                             # saia
    linha(('.',3), ('1',10), ('.',3)),
    linha(('.',2), ('1',12), ('.',2)),                             # barra
    linha(('.',2), ('1',12), ('.',2)),
    linha(('.',2), ('1',5), ('.',2), ('1',5), ('.',2)),           # sapatos
    linha(('.',16)),
]

AMANDA_PERNAS_B = [
    linha(('.',2), ('3',1), ('1',10), ('3',1), ('.',2)),
    linha(('.',2), ('3',1), ('1',10), ('3',1), ('.',2)),
    linha(('.',3), ('1',10), ('.',3)),
    linha(('.',3), ('1',10), ('.',3)),
    linha(('.',1), ('1',14), ('.',1)),                             # barra balanca no passo
    linha(('.',1), ('1',14), ('.',1)),
    linha(('.',1), ('1',5), ('.',4), ('1',5), ('.',1)),           # passada mais aberta
    linha(('.',16)),
]

# ====================================================== Victor sentado
# A barba cheia e o que o identifica nesse tamanho -- ocupa quase metade
# da cabeca, de proposito. O swoosh e pequeno e fica no peito esquerdo,
# como numa camisa de verdade.
VICTOR = [
    linha(('.',3), ('1',10), ('.',3)),                            # cabelo
    linha(('.',2), ('1',12), ('.',2)),
    linha(('.',2), ('1',12), ('.',2)),
    linha(('.',2), ('1',1), ('2',10), ('1',1), ('.',2)),           # testa -- rosto largo
    linha(('.',2), ('1',1), ('2',10), ('1',1), ('.',2)),
    linha(('.',2), ('1',1), ('2',1), ('1',2), ('2',4),
          ('1',2), ('2',1), ('1',1), ('.',2)),                     # sobrancelhas
    linha(('.',2), ('1',1), ('2',2), ('1',1), ('2',4),
          ('1',1), ('2',2), ('1',1), ('.',2)),                     # olhos
    linha(('.',2), ('1',1), ('2',10), ('1',1), ('.',2)),           # nariz
    linha(('.',2), ('1',1), ('2',10), ('1',1), ('.',2)),           # barba fina nas laterais
    linha(('.',2), ('1',1), ('2',10), ('1',1), ('.',2)),
    linha(('.',2), ('1',2), ('2',3), ('1',2), ('2',3),
          ('1',2), ('.',2)),                                       # bigode e boca
    linha(('.',2), ('1',3), ('2',6), ('1',3), ('.',2)),            # queixo aparecendo
    linha(('.',2), ('1',12), ('.',2)),                             # ponta da barba
    linha(('.',4), ('2',8), ('.',4)),                              # pescoco
    linha(('.',1), ('3',14), ('.',1)),                             # ombros
    linha(('3',16)),
    linha(('2',1), ('3',14), ('2',1)),
    linha(('2',1), ('3',14), ('2',1)),
    linha(('2',1), ('3',3), ('1',1), ('3',10), ('2',1)),           # swoosh: ponta
    linha(('2',1), ('3',2), ('1',3), ('3',9), ('2',1)),            # swoosh: risco
    linha(('2',1), ('3',14), ('2',1)),
    linha(('.',1), ('2',1), ('3',12), ('2',1), ('.',1)),
    linha(('.',1), ('2',2), ('3',10), ('2',2), ('.',1)),           # maos na mesa
    linha(('.',16)),
]

# Victor de boca aberta: nas duas linhas da boca a pele some e vira vao
# escuro. E a diferenca que da pra enxergar dentro de uma barba desse
# tamanho -- 6 pixels de pele que aparecem e somem.
VICTOR_FALANDO = list(VICTOR)
VICTOR_FALANDO[10] = linha(('.',2), ('1',12), ('.',2))
VICTOR_FALANDO[11] = linha(('.',2), ('1',12), ('.',2))

# ---- a pizza crek que cai no minigame: 16x8, retangular ----
PIZZA = [
    linha(('1',16)),                                              # crosta, borda de cima
    linha(('1',1), ('3',14), ('1',1)),
    linha(('1',1), ('3',3), ('2',2), ('3',5), ('2',2), ('3',2), ('1',1)),
    linha(('1',1), ('3',14), ('1',1)),
    linha(('1',1), ('3',2), ('2',2), ('3',6), ('2',2), ('3',2), ('1',1)),
    linha(('1',1), ('3',14), ('1',1)),
    linha(('1',1), ('3',14), ('1',1)),
    linha(('1',16)),                                              # crosta, borda de baixo
]

# ---- o aviso de "aperte B", que flutua sobre a cabeca dele ----
LETRA_B = ["111.", "1..1", "111.", "1..1", "111."]

def botao_b():
    """Caixinha de 16x8 com um B dentro."""
    g = [["."]*16 for _ in range(8)]
    for x in range(2, 14): g[0][x] = g[7][x] = "1"
    for y in range(1, 7):
        g[y][1] = g[y][14] = "1"
        for x in range(2, 14): g[y][x] = "2"
    for y in range(1, 7):
        g[y][2] = g[y][13] = "1" if y in (1, 6) else "2"
    for j, l in enumerate(LETRA_B):                 # o B no meio
        for i, c in enumerate(l):
            if c == "1": g[j + 2][i + 6] = "1"
    return ["".join(r) for r in g]

def fatiar(arte, largura=16):
    """Corta o desenho em tiles 8x8, coluna esquerda inteira e depois a direita."""
    alt = len(arte)
    assert alt % 8 == 0
    tiles = []
    for col in range(0, largura, 8):
        for lin in range(0, alt, 8):
            tiles.append([arte[lin + j][col:col + 8] for j in range(8)])
    return tiles

def build():
    amanda_a = AMANDA_CABECA + AMANDA_TRONCO + AMANDA_PERNAS_A
    amanda_b = AMANDA_CABECA + AMANDA_TRONCO + AMANDA_PERNAS_B
    assert len(amanda_a) == 32 and len(VICTOR) == 24

    saida = []
    for arte in (amanda_a, amanda_b):          # tiles 0-7 e 8-15
        for t in fatiar(arte):
            saida.append(encode_tile(t))
    for t in fatiar(VICTOR):                   # tiles 16-21
        saida.append(encode_tile(t))
    # so os dois tiles da boca mudam quando ele fala
    falando = fatiar(VICTOR_FALANDO)
    saida.append(encode_tile(falando[1]))      # tile 22: metade esquerda
    saida.append(encode_tile(falando[4]))      # tile 23: metade direita
    for t in fatiar(botao_b()):                # tiles 24-25: o aviso "B"
        saida.append(encode_tile(t))
    for t in fatiar(PIZZA):                    # tiles 26-27: a pizza do minigame
        saida.append(encode_tile(t))
    # a boca da Amanda: so as duas metades da cabeca onde ela cai (linha 8-15)
    amanda_falando = AMANDA_CABECA_FALANDO + AMANDA_TRONCO + AMANDA_PERNAS_A
    falando_a = fatiar(amanda_falando)
    saida.append(encode_tile(falando_a[1]))    # tile 28: metade esquerda
    saida.append(encode_tile(falando_a[5]))    # tile 29: metade direita
    while len(saida) < 32:                     # duas paginas de 256 bytes
        saida.append(BLANK)
    return b"".join(saida)

if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else "build/chr_sprites.bin"
    d = build()
    assert len(d) == 512, len(d)
    open(destino, "wb").write(d)
    print(f"sprites: {destino} ({len(d)} bytes) -- Amanda 0-15, "
          f"Victor 16-21, boca aberta 22-23, aviso B 24-25, pizza 26-27, "
          f"boca da Amanda aberta 28-29")
