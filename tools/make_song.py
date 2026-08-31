#!/usr/bin/env python3
"""
Compila a musica: tabelas de periodo + os fluxos de notas de cada canal.

O NES nao entende "sol"; ele entende um numero de 11 bits que divide o
clock da CPU. Este script converte nomes de nota em periodos e cospe um
arquivo .inc que o assembly inclui.

Formato do fluxo, por canal: pares (nota, duracao em quadros), $FF encerra
e o tocador volta pro comeco.
"""
import sys

CPU_HZ = 1789773.0
NOMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def indice(nome):
    """'G3' -> indice na tabela (1 = C2). 'P' e a pausa reservada (indice 0)."""
    if nome == "P":
        return 0
    n, oitava = nome[:-1], int(nome[-1])
    return (oitava - 2) * 12 + NOMES.index(n) + 1

def frequencia(idx):
    semitons = idx - 1 + (2 - 4) * 12 - 9      # distancia ate o la 440
    return 440.0 * (2.0 ** (semitons / 12.0))

N_NOTAS = 60          # do 2 ate si 6

# ------------------------------------------------------------------ musica
# Introducao de "Amanda" (Boston), a partir da tablatura.
#
# O que a tab revelou, e que a cifra sozinha nao dizia:
#
#   G   = G2  D3  G3  B3  G4      (6a casa 3, 4a/3a/2a soltas, 1a casa 3)
#   C/G = G2  E3  G3  C4  G4
#
# Ou seja: o sol do baixo NAO sai, e o sol agudo do topo TAMBEM nao --
# os dois ficam parados enquanto so as vozes de dentro se mexem (B3->C4,
# D3->E3). E isso que da o balanco da introducao, e e barato de tocar em
# tres canais.
#
# A versao anterior estava uma oitava acima e inventava um re agudo que
# nao existe no acorde.
#
# A MELODIA DO VOCAL CONTINUA FORA -- ela nao esta tabulada em lugar nenhum
# que eu tenha achado aberto.

# O andamento nao e mais chute: o MIDI da musica traz 61 BPM no cabecalho.
# Eu tinha posto ~80, rapido demais pra uma balada.
E  = 30               # colcheia a 60 BPM
CP = E * 8            # um compasso

ARPEJO_G  = ["D3", "G3", "B3", "G4", "D3", "G3", "B3", "G4"]
ARPEJO_CG = ["E3", "G3", "C4", "G4", "E3", "G3", "C4", "G4"]

COMPASSOS = [ARPEJO_G, ARPEJO_CG] * 4          # 8 compassos, ~32 s

# canal 0: o arpejo
canal0 = [(n, E) for compasso in COMPASSOS for n in compasso]

# canal 1: so a voz que se move. E ela que avisa o ouvido que o acorde
# mudou -- no violao e o hammer-on da segunda corda, B3 -> C4.
canal1 = [("B4" if c is ARPEJO_G else "C5", CP) for c in COMPASSOS]

# canal 2: pedal de sol, rearticulado a cada meio compasso pra nao virar orgao
canal2 = [("G2", CP // 2)] * (len(COMPASSOS) * 2)

# ------------------------------------------------------------------ refrao
# Depois do arpejo de intro vem o refrao, tirado do MIDI oficial da musica
# (tools/midi.py le-lo: 15 faixas, bateria + baixo + guitarras + uma faixa
# de sax alto que funciona como guia de melodia porque a musica nao tem
# vocal gravado). O refrao comeca em 1:38 (98.3s) -- confirmado de ouvido
# depois de eu sintetizar a faixa da melodia crua e comparar com o Victor.
# Uma passada inteira do refrao dura ~23.6s; ele se repete em seguida
# (faixa do violao em arpejo volta pro mesmo acorde de sol em 121.89s),
# entao uma passada so ja basta pro loop -- repetir de novo seria repetir
# o loop de um loop.
#
# canal 0 (melodia, faixa da sax): duracao de cada nota = tempo ate a
# proxima comecar, pra ficar legato; vao real (> 0.3s) virou pausa "P".
# canal 1 (acordes, tirados da faixa do violao em arpejo por baixo da
# melodia: sol, mi menor, si menor, do, sol/re, la menor, sol/re, re):
# um pad na fundamental de cada acorde, rearticulado na metade — mesma
# ideia do pedal do canal 2 acima, pra nao virar orgao.
# canal 2 (baixo, faixa do baixo): uma oitava acima do MIDI original —
# a oitava 1 fica fora da faixa de notas que este motor sabe tocar
# (comeca em C2, ver N_NOTAS).
#
# Duracao em quadros: arredondada pra grade de semicolcheia (15 quadros,
# metade do E do intro, o suficiente pra cobrir as notas mais curtas).
MELODIA_REFRAO = [
    ("A#3", 60), ("P", 45), ("G3", 15), ("D#4", 15), ("E4", 15), ("E4", 15),
    ("E4", 75), ("D4", 15), ("A#3", 45), ("P", 45), ("G3", 15), ("D#4", 15),
    ("E4", 15), ("E4", 15), ("E4", 45), ("D4", 15), ("C#4", 15), ("A#3", 120),
    ("P", 90), ("B3", 30), ("D#4", 15), ("E4", 15), ("E4", 15), ("D#4", 45),
    ("E4", 30), ("G4", 15), ("G#3", 15), ("G3", 15), ("F#3", 60), ("E3", 15),
    ("A3", 45), ("C4", 15), ("B3", 60), ("P", 45), ("B3", 15), ("B3", 45),
    ("B3", 15), ("A#3", 15), ("G#3", 105), ("P", 120),
]

CHORD_REFRAO = [
    ("G4", 180), ("G4", 180),
    ("E4", 60), ("E4", 60),
    ("B4", 120), ("B4", 120),
    ("C4", 60), ("C4", 60),
    ("G4", 60), ("G4", 60),
    ("A4", 60), ("A4", 60),
    ("G4", 60), ("G4", 60),
    ("D4", 120), ("D4", 120),
]

BAIXO_REFRAO = [
    ("G2", 225), ("D2", 15), ("G2", 105), ("D2", 15), ("E2", 120), ("B2", 105),
    ("F#2", 15), ("B2", 60), ("F#3", 15), ("E3", 15), ("D3", 15), ("B2", 15),
    ("C3", 105), ("C3", 15), ("B2", 30), ("B2", 75), ("B2", 15), ("A2", 120),
    ("G2", 90), ("D3", 15), ("E3", 15), ("D3", 105), ("D3", 15), ("D2", 120),
]

canal0 += MELODIA_REFRAO
canal1 += CHORD_REFRAO
canal2 += BAIXO_REFRAO

CANAIS = [canal0, canal1, canal2]

# confere que os tres canais tem a mesma duracao: cada um roda o proprio
# laco, entao qualquer diferenca faria eles se desencontrarem aos poucos
_durs = [sum(d for _, d in c) for c in CANAIS]
assert len(set(_durs)) == 1, f"canais desalinhados: {_durs}"

# ------------------------------------------------------------------ saida

def tabela(nome, valores, alto):
    linhas = [f"{nome}:"]
    for i in range(0, len(valores), 12):
        pedaco = valores[i:i + 12]
        b = [(v >> 8) & 0x07 if alto else v & 0xFF for v in pedaco]
        linhas.append("    .byte " + ", ".join(f"${v:02X}" for v in b))
    return "\n".join(linhas)

def main():
    saida = ["; gerado por tools/make_song.py -- nao edite a mao", ""]

    per = [0] * (N_NOTAS + 1)
    tri = [0] * (N_NOTAS + 1)
    for i in range(1, N_NOTAS + 1):
        f = frequencia(i)
        per[i] = max(8, min(2047, round(CPU_HZ / (16.0 * f)) - 1))
        tri[i] = max(2, min(2047, round(CPU_HZ / (32.0 * f)) - 1))

    saida += [tabela("per_lo", per, False), "", tabela("per_hi", per, True), "",
              tabela("tri_lo", tri, False), "", tabela("tri_hi", tri, True), ""]

    for c, notas in enumerate(CANAIS):
        total = sum(d for _, d in notas)
        saida.append(f"; canal {c}: {len(notas)} notas, {total} quadros "
                     f"({total/60:.1f} s)")
        saida.append(f"canal{c}:")
        for nome, dur in notas:
            assert 1 <= dur <= 255, dur
            saida.append(f"    .byte {indice(nome):3d}, {dur:3d}   ; {nome}")
        saida.append("    .byte $FF")
        saida.append("")

    saida += ["fluxo_lo:", "    .byte <canal0, <canal1, <canal2", "",
              "fluxo_hi:", "    .byte >canal0, >canal1, >canal2", ""]

    destino = sys.argv[1] if len(sys.argv) > 1 else "build/musica.inc"
    open(destino, "w").write("\n".join(saida))

    dur = sum(d for _, d in canal0) / 60.0
    print(f"musica compilada: {destino}  --  laco de {dur:.1f} s")
    for c, notas in enumerate(CANAIS):
        print(f"  canal {c}: {len(notas)} notas")

if __name__ == "__main__":
    main()
