#!/usr/bin/env python3
"""
Confere a engine de musica no nivel dos registradores.

Em vez de tentar ouvir, o teste le o periodo que o codigo escreveu no APU
a cada quadro e compara com a nota que deveria estar tocando segundo a
partitura. Se a engine errar uma nota ou a duracao, aparece aqui.
"""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, check, FAILS
from make_song import CANAIS, indice, frequencia, CPU_HZ

ROM = "jogo.nes"

def periodos_esperados():
    """A sequencia de periodos que cada canal deveria produzir, quadro a quadro.

    Numa pausa (indice 0) a engine so zera o volume -- @pausa em jogo.s nao
    escreve $4002/$4003 (nem tri_lo/tri_hi), entao o periodo continua sendo
    o da ultima nota tocada."""
    trilhas = []
    for c, notas in enumerate(CANAIS):
        linha = []
        p_atual = 0
        for nome, dur in notas:
            i = indice(nome)
            if i != 0:
                f = frequencia(i)
                div = 32.0 if c == 2 else 16.0
                p_atual = max(2, min(2047, round(CPU_HZ / (div * f)) - 1))
            linha += [p_atual] * dur
        trilhas.append(linha)
    return trilhas

def lidos(bus):
    p1 = bus.apu[0x02] | ((bus.apu[0x03] & 7) << 8)
    p2 = bus.apu[0x06] | ((bus.apu[0x07] & 7) << 8)
    tr = bus.apu[0x0A] | ((bus.apu[0x0B] & 7) << 8)
    return [p1, p2, tr]

def main():
    esperado = periodos_esperados()
    laco = len(esperado[0])

    nes = NES(ROM)
    obs = [[], [], []]
    for _ in range(laco * 2 + 8):
        nes.frame()
        v = lidos(nes.bus)
        for c in range(3):
            obs[c].append(v[c])

    print("== 1. O APU foi ligado ==")
    check("canais habilitados em $4015", nes.bus.apu[0x15] & 0x0F == 0x0F,
          f"${nes.bus.apu[0x15]:02X}")
    check("sweep desligado nas duas quadradas",
          nes.bus.apu[0x01] == 0 and nes.bus.apu[0x05] == 0)

    print("\n== 2. As notas batem com a partitura ==")
    # o tocador comeca no primeiro NMI; acha o deslocamento e usa pra todos
    desloc = next(d for d in range(8)
                  if obs[0][d] == esperado[0][0] and obs[0][d + 1] == esperado[0][0])
    check("engine comeca a tocar", desloc < 8, f"no quadro {desloc}")

    nomes = ("arpejo (quadrada 1)", "harmonia (quadrada 2)", "baixo (triangulo)")
    for c in range(3):
        erros = 0
        primeiro = None
        for i in range(laco):
            if obs[c][desloc + i] != esperado[c][i]:
                erros += 1
                if primeiro is None:
                    primeiro = (i, obs[c][desloc + i], esperado[c][i])
        det = "" if not erros else f"1o erro no quadro {primeiro[0]}: " \
                                   f"leu {primeiro[1]}, esperava {primeiro[2]}"
        check(f"{nomes[c]}: {laco} quadros conferem", erros == 0, det)

    print("\n== 3. O laco fecha e repete ==")
    volta = obs[0][desloc + laco:desloc + laco + laco]
    check("segunda passada igual a primeira", volta == esperado[0],
          f"{sum(1 for a, b in zip(volta, esperado[0]) if a != b)} diferencas")

    print("\n== 4. Envelope de volume ==")
    dur1 = CANAIS[0][0][1]                  # duracao da 1a nota, tirada da partitura
    nes2 = NES(ROM)
    vols = []
    for _ in range(desloc + dur1 * 2 + 5):
        nes2.frame()
        vols.append(nes2.bus.apu[0x00] & 0x0F)
    vols = vols[desloc:]                    # os primeiros quadros sao antes do 1o NMI
    nota = vols[:dur1]
    check("volume cai dentro da nota", nota[0] > nota[-1],
          " ".join(str(v) for v in nota))
    # a engine para de decair em 4 (o 'cmp #$05' do aplica_volume): a nota
    # perde forca mas nao some, que e o que faz soar tocada e nao percutida
    check("volume nao chega a zero (sustenta)", min(nota) >= 4, f"minimo {min(nota)}")
    check("nota seguinte reataca no volume cheio", vols[dur1] == 0x0F,
          f"quadro {dur1}: volume {vols[dur1]}")
    check("bit de volume constante ligado", nes2.bus.apu[0x00] & 0x10 != 0)
    check("contador de duracao segurado", nes2.bus.apu[0x00] & 0x20 != 0)

    print("\n== 5. A tela continua viva junto com a musica ==")
    check("nomes ainda na tela",
          nes.nt_text(0x2000 + 12 * 32 + 13, 6) == "VICTOR" and
          nes.nt_text(0x2000 + 17 * 32 + 13, 6) == "AMANDA")
    check("coracao ainda pulsa", nes.bus.vram[0x3F06] in (0x06, 0x16, 0x26, 0x36),
          f"${nes.bus.vram[0x3F06]:02X}")
    check("pilha nao vazou com o NMI mais pesado",
          0xF0 <= nes.cpu.sp <= 0xFF, f"SP=${nes.cpu.sp:02X}")

    print()
    if FAILS:
        print(f"### {len(FAILS)} FALHA(S): " + ", ".join(FAILS))
        return 1
    print("### tudo passou")
    return 0

if __name__ == "__main__":
    sys.exit(main())
