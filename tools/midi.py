#!/usr/bin/env python3
"""
Leitor de MIDI, o minimo pra extrair melodia: cabecalho, faixas, notas,
andamento e marcadores. Sem dependencia externa.
"""
import struct, sys

NOMES = ["C","C#","D","D#","E","F","F#","G","G#","A","A#","B"]

def nome_nota(n):
    return f"{NOMES[n % 12]}{n // 12 - 1}"     # 60 = C4

class Faixa:
    def __init__(self, i):
        self.i, self.nome, self.notas, self.marcas = i, "", [], []
        self.canais, self.instr = set(), set()

def varlen(d, p):
    v = 0
    while True:
        b = d[p]; p += 1
        v = (v << 7) | (b & 0x7F)
        if not b & 0x80:
            return v, p

def ler(caminho):
    d = open(caminho, "rb").read()
    assert d[:4] == b"MThd"
    fmt, n, div = struct.unpack(">HHH", d[8:14])
    p, faixas, tempos = 14, [], []

    for i in range(n):
        assert d[p:p+4] == b"MTrk", f"faixa {i} invalida"
        tam = struct.unpack(">I", d[p+4:p+8])[0]
        fim = p + 8 + tam
        p += 8
        f, t, rodando, abertas = Faixa(i), 0, None, {}

        while p < fim:
            dt, p = varlen(d, p)
            t += dt
            b = d[p]
            if b & 0x80:
                rodando = b; p += 1
            st = rodando
            if st == 0xFF:
                tipo = d[p]; p += 1
                tam2, p = varlen(d, p)
                dados = d[p:p+tam2]; p += tam2
                if tipo == 0x03:
                    f.nome = dados.decode("latin-1", "replace").strip()
                elif tipo in (0x01, 0x05, 0x06):        # texto, letra, marcador
                    f.marcas.append((t, dados.decode("latin-1","replace").strip()))
                elif tipo == 0x51:
                    tempos.append((t, struct.unpack(">I", b"\x00" + dados)[0]))
            elif st in (0xF0, 0xF7):
                tam2, p = varlen(d, p); p += tam2
            else:
                tipo, canal = st & 0xF0, st & 0x0F
                if tipo in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    a, b2 = d[p], d[p+1]; p += 2
                    if tipo == 0x90 and b2 > 0:
                        abertas.setdefault(a, []).append(t)
                        f.canais.add(canal)
                    elif tipo in (0x80,) or (tipo == 0x90 and b2 == 0):
                        if abertas.get(a):
                            ini = abertas[a].pop(0)
                            f.notas.append((ini, t - ini, a, canal))
                else:
                    if tipo == 0xC0:
                        f.instr.add(d[p])
                    p += 1
        f.notas.sort()
        faixas.append(f)
        p = fim
    return div, faixas, sorted(tempos)

if __name__ == "__main__":
    div, faixas, tempos = ler(sys.argv[1])
    bpm = 60_000_000 / tempos[0][1] if tempos else 120
    print(f"divisao: {div} ticks/seminima   andamento inicial: {bpm:.1f} BPM")
    if len(tempos) > 1:
        print(f"  ({len(tempos)} mudancas de andamento)")
    print()
    for f in faixas:
        if not f.notas:
            if f.marcas: print(f"faixa {f.i:2d} {f.nome!r}: {len(f.marcas)} marcadores")
            continue
        alt = [n[2] for n in f.notas]
        fim = max(n[0] + n[1] for n in f.notas)
        print(f"faixa {f.i:2d} {f.nome[:22]:22s} {len(f.notas):4d} notas  "
              f"canal {sorted(f.canais)}  instr {sorted(f.instr)}  "
              f"{nome_nota(min(alt))}-{nome_nota(max(alt))}  "
              f"ate {fim/div/ (bpm/60):.0f}s")
