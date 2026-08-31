#!/usr/bin/env python3
"""
Sintetiza o som do APU do NES a partir do estado dos registradores.

A engine de musica escreve nos registradores uma vez por quadro, entao
nao e preciso emular o APU ciclo a ciclo: basta olhar o estado ao fim de
cada quadro e gerar 1/60 de segundo de audio com ele. As fases das ondas
sao mantidas entre quadros, senao estalaria a cada 16 ms.

Saida: WAV de 44,1 kHz, pra voce ouvir antes de qualquer coisa ir pro
cartucho.
"""
import struct

CPU_HZ = 1789773.0          # clock do 6502 no NES americano (NTSC)
TAXA   = 44100
POR_QUADRO = TAXA / 60.0

# as quatro larguras de pulso da onda quadrada, como fracao do ciclo
DUTY = (0.125, 0.25, 0.50, 0.75)


class APU:
    def __init__(self):
        self.fase = [0.0, 0.0, 0.0]     # quadrada 1, quadrada 2, triangulo
        self.fase_ruido = 0.0
        self.lfsr = 1
        self.resto = 0.0
        self.filtro = 0.0

    # ---------------------------------------------------------- canais
    @staticmethod
    def _periodo(reg, lo, hi):
        return (reg[lo] | ((reg[hi] & 0x07) << 8))

    def _quadrada(self, reg, base, canal, n):
        p = self._periodo(reg, base + 2, base + 3)
        vol = reg[base] & 0x0F
        duty = DUTY[(reg[base] >> 6) & 3]
        if p < 8 or vol == 0:
            return [0.0] * n
        freq = CPU_HZ / (16.0 * (p + 1))
        passo = freq / TAXA
        saida = []
        f = self.fase[canal]
        for _ in range(n):
            saida.append(vol if (f % 1.0) < duty else 0.0)
            f += passo
        self.fase[canal] = f % 1.0
        return saida

    def _triangulo(self, reg, n):
        p = self._periodo(reg, 0x0A, 0x0B)
        # o contador linear em $4008 e o que liga e desliga a nota
        if p < 2 or (reg[0x08] & 0x7F) == 0:
            return [0.0] * n
        freq = CPU_HZ / (32.0 * (p + 1))
        passo = freq / TAXA
        saida = []
        f = self.fase[2]
        for _ in range(n):
            x = (f % 1.0) * 2.0
            v = x if x < 1.0 else 2.0 - x        # onda triangular 0..1
            saida.append(round(v * 15.0))        # o NES quantiza em 16 degraus
            f += passo
        self.fase[2] = f % 1.0
        return saida

    def _ruido(self, reg, n):
        vol = reg[0x0C] & 0x0F
        if vol == 0:
            return [0.0] * n
        tabela = (4, 8, 16, 32, 64, 96, 128, 160, 202, 254, 380, 508, 762,
                  1016, 2034, 4068)
        p = tabela[reg[0x0E] & 0x0F]
        passo = (CPU_HZ / p) / TAXA
        curto = bool(reg[0x0E] & 0x80)
        saida = []
        f = self.fase_ruido
        for _ in range(n):
            f += passo
            while f >= 1.0:
                f -= 1.0
                bit = 6 if curto else 1
                novo = ((self.lfsr ^ (self.lfsr >> bit)) & 1) << 14
                self.lfsr = (self.lfsr >> 1) | novo
            saida.append(0.0 if (self.lfsr & 1) else vol)
        self.fase_ruido = f
        return saida

    # ---------------------------------------------------------- mistura
    def quadro(self, reg):
        """Um quadro de audio a partir do estado atual dos registradores."""
        self.resto += POR_QUADRO
        n = int(self.resto)
        self.resto -= n

        habilita = reg[0x15]
        q1 = self._quadrada(reg, 0x00, 0, n) if habilita & 1 else [0.0] * n
        q2 = self._quadrada(reg, 0x04, 1, n) if habilita & 2 else [0.0] * n
        tr = self._triangulo(reg, n)         if habilita & 4 else [0.0] * n
        ru = self._ruido(reg, n)             if habilita & 8 else [0.0] * n

        saida = []
        for i in range(n):
            # aproximacao linear do misturador do NES
            pulso = 0.00752 * (q1[i] + q2[i])
            tnd = 0.00851 * tr[i] + 0.00494 * ru[i]
            v = pulso + tnd
            self.filtro += (v - self.filtro) * 0.55    # tira o brilho aspero
            saida.append(self.filtro)
        return saida


def gravar_wav(caminho, amostras, pico_alvo=0.85):
    """Tira o nivel DC e normaliza. O misturador do NES so produz valores
    positivos; mandar isso direto pro WAV daria um sinal todo deslocado."""
    limpo = []
    ax = ay = 0.0
    for x in amostras:
        y = x - ax + 0.995 * ay          # passa-alta de 1a ordem
        ax, ay = x, y
        limpo.append(y)

    pico = max((abs(v) for v in limpo), default=0.0) or 1.0
    escala = pico_alvo / pico

    quadros = bytearray()
    for v in limpo:
        quadros += struct.pack("<h", int(max(-1.0, min(1.0, v * escala)) * 32000))
    with open(caminho, "wb") as f:
        f.write(b"RIFF" + struct.pack("<I", 36 + len(quadros)) + b"WAVE")
        f.write(b"fmt " + struct.pack("<IHHIIHH", 16, 1, 1, TAXA, TAXA * 2, 2, 16))
        f.write(b"data" + struct.pack("<I", len(quadros)) + bytes(quadros))
    return len(amostras) / TAXA, pico
