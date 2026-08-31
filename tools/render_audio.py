#!/usr/bin/env python3
"""Roda a ROM e grava o que sairia pela TV como .wav, pra voce ouvir."""
import sys
sys.path.insert(0, "tools")
from nesemu import NES
from apu import APU, gravar_wav

rom = sys.argv[1] if len(sys.argv) > 1 else "build/jogo.nes"
saida = sys.argv[2] if len(sys.argv) > 2 else "build/musica.wav"
quadros = int(sys.argv[3]) if len(sys.argv) > 3 else 60 * 17

nes = NES(rom)
apu = APU()
amostras = []
for _ in range(quadros):
    nes.frame()
    amostras += apu.quadro(nes.bus.apu)

dur, pico = gravar_wav(saida, amostras)
print(f"{saida}  --  {dur:.1f} s, {len(amostras)} amostras, "
      f"pico bruto {pico:.3f} (normalizado)")
