#!/usr/bin/env python3
"""
Emulador 6502 minimo + PPU/controle suficientes pra rodar a ROM de verdade.

Nao e um emulador de NES completo: ele executa a CPU, guarda o que o codigo
escreve na VRAM/OAM/paletas e entrega os botoes do controle. Isso ja basta
pra checar, em teste automatizado, que a tela foi montada como deveria.

Usado por test_menu.py (verificacao) e screenshot.py (desenha o PNG).
"""
import sys

# ====================================================================== CPU

class CPU:
    def __init__(self, bus):
        self.bus = bus
        self.a = self.x = self.y = 0
        self.sp = 0xFD
        self.pc = 0
        self.c = self.z = self.i = self.d = self.v = self.n = 0
        self.cycles = 0
        self.table = build_table(self)

    # ---- flags ----
    def get_p(self, brk=0):
        return (self.n << 7) | (self.v << 6) | 0x20 | (brk << 4) | \
               (self.d << 3) | (self.i << 2) | (self.z << 1) | self.c

    def set_p(self, v):
        self.n = (v >> 7) & 1; self.v = (v >> 6) & 1; self.d = (v >> 3) & 1
        self.i = (v >> 2) & 1; self.z = (v >> 1) & 1; self.c = v & 1

    def setzn(self, v):
        self.z = 1 if v == 0 else 0
        self.n = (v >> 7) & 1

    # ---- memoria ----
    def rd(self, a):  return self.bus.read(a & 0xFFFF)
    def wr(self, a, v): self.bus.write(a & 0xFFFF, v & 0xFF)
    def rd16(self, a): return self.rd(a) | (self.rd(a + 1) << 8)

    def push(self, v):
        self.wr(0x100 + self.sp, v)
        self.sp = (self.sp - 1) & 0xFF

    def pop(self):
        self.sp = (self.sp + 1) & 0xFF
        return self.rd(0x100 + self.sp)

    # ---- controle ----
    def reset(self):
        self.pc = self.rd16(0xFFFC)
        self.sp = 0xFD
        self.i = 1

    def nmi(self):
        self.push((self.pc >> 8) & 0xFF)
        self.push(self.pc & 0xFF)
        self.push(self.get_p(0))
        self.i = 1
        self.pc = self.rd16(0xFFFA)
        self.cycles += 7

    def step(self):
        op = self.rd(self.pc)
        self.pc = (self.pc + 1) & 0xFFFF
        entry = self.table[op]
        if entry is None:
            raise RuntimeError(f"opcode nao implementado ${op:02X} em ${self.pc-1:04X}")
        fn, cyc = entry
        fn()
        self.cycles += cyc


def build_table(c):
    """Monta a tabela de opcodes. Devolve {op: (funcao, ciclos)}."""
    t = [None] * 256

    # ---------- modos de enderecamento (devolvem endereco efetivo) ----------
    def imm():
        a = c.pc; c.pc = (c.pc + 1) & 0xFFFF; return a
    def zp():
        a = c.rd(c.pc); c.pc = (c.pc + 1) & 0xFFFF; return a
    def zpx():
        a = (c.rd(c.pc) + c.x) & 0xFF; c.pc = (c.pc + 1) & 0xFFFF; return a
    def zpy():
        a = (c.rd(c.pc) + c.y) & 0xFF; c.pc = (c.pc + 1) & 0xFFFF; return a
    def ab():
        a = c.rd16(c.pc); c.pc = (c.pc + 2) & 0xFFFF; return a
    def abx():
        a = (c.rd16(c.pc) + c.x) & 0xFFFF; c.pc = (c.pc + 2) & 0xFFFF; return a
    def aby():
        a = (c.rd16(c.pc) + c.y) & 0xFFFF; c.pc = (c.pc + 2) & 0xFFFF; return a
    def indx():
        p = (c.rd(c.pc) + c.x) & 0xFF; c.pc = (c.pc + 1) & 0xFFFF
        return c.rd(p) | (c.rd((p + 1) & 0xFF) << 8)
    def indy():
        p = c.rd(c.pc); c.pc = (c.pc + 1) & 0xFFFF
        base = c.rd(p) | (c.rd((p + 1) & 0xFF) << 8)
        return (base + c.y) & 0xFFFF

    # ---------- operacoes ----------
    def op_lda(m): v = c.rd(m()); c.a = v; c.setzn(v)
    def op_ldx(m): v = c.rd(m()); c.x = v; c.setzn(v)
    def op_ldy(m): v = c.rd(m()); c.y = v; c.setzn(v)
    def op_sta(m): c.wr(m(), c.a)
    def op_stx(m): c.wr(m(), c.x)
    def op_sty(m): c.wr(m(), c.y)
    def op_and(m): c.a &= c.rd(m()); c.setzn(c.a)
    def op_ora(m): c.a |= c.rd(m()); c.setzn(c.a)
    def op_eor(m): c.a ^= c.rd(m()); c.setzn(c.a)
    def op_bit(m):
        v = c.rd(m())
        c.z = 1 if (c.a & v) == 0 else 0
        c.n = (v >> 7) & 1
        c.v = (v >> 6) & 1
    def op_adc(m):
        v = c.rd(m()); s = c.a + v + c.c
        c.v = 1 if (~(c.a ^ v) & (c.a ^ s) & 0x80) else 0
        c.c = 1 if s > 0xFF else 0
        c.a = s & 0xFF; c.setzn(c.a)
    def op_sbc(m):
        v = c.rd(m()) ^ 0xFF; s = c.a + v + c.c
        c.v = 1 if (~(c.a ^ v) & (c.a ^ s) & 0x80) else 0
        c.c = 1 if s > 0xFF else 0
        c.a = s & 0xFF; c.setzn(c.a)
    def op_cmp(m):
        v = c.rd(m()); r = (c.a - v) & 0xFF
        c.c = 1 if c.a >= v else 0; c.setzn(r)
    def op_cpx(m):
        v = c.rd(m()); r = (c.x - v) & 0xFF
        c.c = 1 if c.x >= v else 0; c.setzn(r)
    def op_cpy(m):
        v = c.rd(m()); r = (c.y - v) & 0xFF
        c.c = 1 if c.y >= v else 0; c.setzn(r)
    def op_inc(m):
        a = m(); v = (c.rd(a) + 1) & 0xFF; c.wr(a, v); c.setzn(v)
    def op_dec(m):
        a = m(); v = (c.rd(a) - 1) & 0xFF; c.wr(a, v); c.setzn(v)
    def op_asl(m):
        a = m(); v = c.rd(a); c.c = (v >> 7) & 1
        v = (v << 1) & 0xFF; c.wr(a, v); c.setzn(v)
    def op_lsr(m):
        a = m(); v = c.rd(a); c.c = v & 1
        v >>= 1; c.wr(a, v); c.setzn(v)
    def op_rol(m):
        a = m(); v = c.rd(a); nc = (v >> 7) & 1
        v = ((v << 1) | c.c) & 0xFF; c.c = nc; c.wr(a, v); c.setzn(v)
    def op_ror(m):
        a = m(); v = c.rd(a); nc = v & 1
        v = (v >> 1) | (c.c << 7); c.c = nc; c.wr(a, v); c.setzn(v)

    def branch(cond):
        off = c.rd(c.pc); c.pc = (c.pc + 1) & 0xFFFF
        if cond:
            if off & 0x80: off -= 256
            c.pc = (c.pc + off) & 0xFFFF

    def bind(m, f):   # amarra modo + operacao numa funcao sem argumentos
        return lambda: f(m)

    # carga / armazenamento
    for op, m, cy in ((0xA9, imm, 2), (0xA5, zp, 3), (0xB5, zpx, 4), (0xAD, ab, 4),
                      (0xBD, abx, 4), (0xB9, aby, 4), (0xA1, indx, 6), (0xB1, indy, 5)):
        t[op] = (bind(m, op_lda), cy)
    for op, m, cy in ((0xA2, imm, 2), (0xA6, zp, 3), (0xB6, zpy, 4), (0xAE, ab, 4), (0xBE, aby, 4)):
        t[op] = (bind(m, op_ldx), cy)
    for op, m, cy in ((0xA0, imm, 2), (0xA4, zp, 3), (0xB4, zpx, 4), (0xAC, ab, 4), (0xBC, abx, 4)):
        t[op] = (bind(m, op_ldy), cy)
    for op, m, cy in ((0x85, zp, 3), (0x95, zpx, 4), (0x8D, ab, 4), (0x9D, abx, 5),
                      (0x99, aby, 5), (0x81, indx, 6), (0x91, indy, 6)):
        t[op] = (bind(m, op_sta), cy)
    for op, m, cy in ((0x86, zp, 3), (0x96, zpy, 4), (0x8E, ab, 4)):
        t[op] = (bind(m, op_stx), cy)
    for op, m, cy in ((0x84, zp, 3), (0x94, zpx, 4), (0x8C, ab, 4)):
        t[op] = (bind(m, op_sty), cy)

    # aritmetica / logica
    for op, m, cy in ((0x29, imm, 2), (0x25, zp, 3), (0x35, zpx, 4), (0x2D, ab, 4),
                      (0x3D, abx, 4), (0x39, aby, 4), (0x21, indx, 6), (0x31, indy, 5)):
        t[op] = (bind(m, op_and), cy)
    for op, m, cy in ((0x09, imm, 2), (0x05, zp, 3), (0x15, zpx, 4), (0x0D, ab, 4),
                      (0x1D, abx, 4), (0x19, aby, 4), (0x01, indx, 6), (0x11, indy, 5)):
        t[op] = (bind(m, op_ora), cy)
    for op, m, cy in ((0x49, imm, 2), (0x45, zp, 3), (0x55, zpx, 4), (0x4D, ab, 4),
                      (0x5D, abx, 4), (0x59, aby, 4), (0x41, indx, 6), (0x51, indy, 5)):
        t[op] = (bind(m, op_eor), cy)
    for op, m, cy in ((0x24, zp, 3), (0x2C, ab, 4)):
        t[op] = (bind(m, op_bit), cy)
    for op, m, cy in ((0x69, imm, 2), (0x65, zp, 3), (0x75, zpx, 4), (0x6D, ab, 4),
                      (0x7D, abx, 4), (0x79, aby, 4), (0x61, indx, 6), (0x71, indy, 5)):
        t[op] = (bind(m, op_adc), cy)
    for op, m, cy in ((0xE9, imm, 2), (0xE5, zp, 3), (0xF5, zpx, 4), (0xED, ab, 4),
                      (0xFD, abx, 4), (0xF9, aby, 4), (0xE1, indx, 6), (0xF1, indy, 5)):
        t[op] = (bind(m, op_sbc), cy)
    for op, m, cy in ((0xC9, imm, 2), (0xC5, zp, 3), (0xD5, zpx, 4), (0xCD, ab, 4),
                      (0xDD, abx, 4), (0xD9, aby, 4), (0xC1, indx, 6), (0xD1, indy, 5)):
        t[op] = (bind(m, op_cmp), cy)
    for op, m, cy in ((0xE0, imm, 2), (0xE4, zp, 3), (0xEC, ab, 4)):
        t[op] = (bind(m, op_cpx), cy)
    for op, m, cy in ((0xC0, imm, 2), (0xC4, zp, 3), (0xCC, ab, 4)):
        t[op] = (bind(m, op_cpy), cy)
    for op, m, cy in ((0xE6, zp, 5), (0xF6, zpx, 6), (0xEE, ab, 6), (0xFE, abx, 7)):
        t[op] = (bind(m, op_inc), cy)
    for op, m, cy in ((0xC6, zp, 5), (0xD6, zpx, 6), (0xCE, ab, 6), (0xDE, abx, 7)):
        t[op] = (bind(m, op_dec), cy)
    for op, m, cy in ((0x06, zp, 5), (0x16, zpx, 6), (0x0E, ab, 6), (0x1E, abx, 7)):
        t[op] = (bind(m, op_asl), cy)
    for op, m, cy in ((0x46, zp, 5), (0x56, zpx, 6), (0x4E, ab, 6), (0x5E, abx, 7)):
        t[op] = (bind(m, op_lsr), cy)
    for op, m, cy in ((0x26, zp, 5), (0x36, zpx, 6), (0x2E, ab, 6), (0x3E, abx, 7)):
        t[op] = (bind(m, op_rol), cy)
    for op, m, cy in ((0x66, zp, 5), (0x76, zpx, 6), (0x6E, ab, 6), (0x7E, abx, 7)):
        t[op] = (bind(m, op_ror), cy)

    # acumulador
    def asl_a():
        c.c = (c.a >> 7) & 1; c.a = (c.a << 1) & 0xFF; c.setzn(c.a)
    def lsr_a():
        c.c = c.a & 1; c.a >>= 1; c.setzn(c.a)
    def rol_a():
        nc = (c.a >> 7) & 1; c.a = ((c.a << 1) | c.c) & 0xFF; c.c = nc; c.setzn(c.a)
    def ror_a():
        nc = c.a & 1; c.a = (c.a >> 1) | (c.c << 7); c.c = nc; c.setzn(c.a)
    t[0x0A] = (asl_a, 2); t[0x4A] = (lsr_a, 2)
    t[0x2A] = (rol_a, 2); t[0x6A] = (ror_a, 2)

    # transferencias / pilha
    def tax(): c.x = c.a; c.setzn(c.x)
    def tay(): c.y = c.a; c.setzn(c.y)
    def txa(): c.a = c.x; c.setzn(c.a)
    def tya(): c.a = c.y; c.setzn(c.a)
    def tsx(): c.x = c.sp; c.setzn(c.x)
    def txs(): c.sp = c.x
    def pha(): c.push(c.a)
    def php(): c.push(c.get_p(1))
    def pla(): c.a = c.pop(); c.setzn(c.a)
    def plp(): c.set_p(c.pop())
    for op, f in ((0xAA, tax), (0xA8, tay), (0x8A, txa), (0x98, tya),
                  (0xBA, tsx), (0x9A, txs)):
        t[op] = (f, 2)
    t[0x48] = (pha, 3); t[0x08] = (php, 3); t[0x68] = (pla, 4); t[0x28] = (plp, 4)

    # inc/dec de registrador
    def inx(): c.x = (c.x + 1) & 0xFF; c.setzn(c.x)
    def dex(): c.x = (c.x - 1) & 0xFF; c.setzn(c.x)
    def iny(): c.y = (c.y + 1) & 0xFF; c.setzn(c.y)
    def dey(): c.y = (c.y - 1) & 0xFF; c.setzn(c.y)
    t[0xE8] = (inx, 2); t[0xCA] = (dex, 2); t[0xC8] = (iny, 2); t[0x88] = (dey, 2)

    # saltos
    def jmp_abs(): c.pc = c.rd16(c.pc)
    def jmp_ind():
        p = c.rd16(c.pc)
        # bug real do 6502: nao atravessa a fronteira de pagina
        hi = (p & 0xFF00) | ((p + 1) & 0xFF)
        c.pc = c.rd(p) | (c.rd(hi) << 8)
    def jsr():
        target = c.rd16(c.pc)
        ret = (c.pc + 1) & 0xFFFF
        c.push((ret >> 8) & 0xFF); c.push(ret & 0xFF)
        c.pc = target
    def rts():
        lo = c.pop(); hi = c.pop()
        c.pc = ((hi << 8) | lo) + 1 & 0xFFFF
    def rti():
        c.set_p(c.pop())
        lo = c.pop(); hi = c.pop()
        c.pc = (hi << 8) | lo
    t[0x4C] = (jmp_abs, 3); t[0x6C] = (jmp_ind, 5)
    t[0x20] = (jsr, 6); t[0x60] = (rts, 6); t[0x40] = (rti, 6)

    # desvios condicionais
    t[0x90] = (lambda: branch(c.c == 0), 2)
    t[0xB0] = (lambda: branch(c.c == 1), 2)
    t[0xD0] = (lambda: branch(c.z == 0), 2)
    t[0xF0] = (lambda: branch(c.z == 1), 2)
    t[0x10] = (lambda: branch(c.n == 0), 2)
    t[0x30] = (lambda: branch(c.n == 1), 2)
    t[0x50] = (lambda: branch(c.v == 0), 2)
    t[0x70] = (lambda: branch(c.v == 1), 2)

    # flags
    def clc(): c.c = 0
    def sec(): c.c = 1
    def cli(): c.i = 0
    def sei(): c.i = 1
    def clv(): c.v = 0
    def cld(): c.d = 0
    def sed(): c.d = 1
    for op, f in ((0x18, clc), (0x38, sec), (0x58, cli), (0x78, sei),
                  (0xB8, clv), (0xD8, cld), (0xF8, sed)):
        t[op] = (f, 2)

    t[0xEA] = (lambda: None, 2)   # NOP
    return t


# ====================================================================== BUS

class Bus:
    def __init__(self, rom):
        assert rom[:4] == b"NES\x1a", "nao e um arquivo iNES"
        prg_banks = rom[4]
        self.prg = rom[16:16 + 16384 * prg_banks]
        self.mapper = (rom[6] >> 4) | (rom[7] & 0xF0)
        self.n_bancos = prg_banks
        self.banco = 0
        self.ram = bytearray(0x800)
        self.vram = bytearray(0x4000)
        self.oam = bytearray(256)

        self.ppu_ctrl = 0
        self.ppu_mask = 0
        self.vblank = False
        self.latch = 0          # alterna entre byte alto e baixo de $2006/$2005
        self.vaddr = 0

        self.buttons = 0
        self.strobe = False
        self.shift = 0

        # tudo que o codigo escreve no APU, pra sintetizar o som depois
        self.apu = bytearray(0x18)

        self.dma_cycles = 0

    # ---- CPU <-> memoria ----
    def read(self, a):
        if a < 0x2000:
            return self.ram[a & 0x7FF]
        if a < 0x4000:
            reg = a & 7
            if reg == 2:
                v = 0x80 if self.vblank else 0x00
                self.vblank = False
                self.latch = 0
                return v
            return 0
        if a == 0x4016:
            if self.strobe:
                return self.buttons & 1
            v = self.shift & 1
            self.shift = (self.shift >> 1) | 0x80
            return v
        if a < 0x8000:
            return 0
        if self.mapper == 2:
            # UNROM: $8000 e o banco escolhido, $C000 e sempre o ultimo
            if a < 0xC000:
                return self.prg[self.banco * 0x4000 + (a - 0x8000)]
            return self.prg[(self.n_bancos - 1) * 0x4000 + (a - 0xC000)]
        # NROM-128: os 16 KB aparecem em $8000 e de novo em $C000
        return self.prg[(a - 0x8000) % len(self.prg)]

    def write(self, a, v):
        if a < 0x2000:
            self.ram[a & 0x7FF] = v
            return
        if a < 0x4000:
            reg = a & 7
            if reg == 0:
                self.ppu_ctrl = v
            elif reg == 1:
                self.ppu_mask = v
            elif reg == 5:
                self.latch ^= 1
            elif reg == 6:
                if self.latch == 0:
                    self.vaddr = (v << 8) | (self.vaddr & 0xFF)
                    self.latch = 1
                else:
                    self.vaddr = (self.vaddr & 0xFF00) | v
                    self.latch = 0
            elif reg == 7:
                self.vram[self.vaddr & 0x3FFF] = v
                self.vaddr += 32 if (self.ppu_ctrl & 0x04) else 1
            return
        if a == 0x4014:
            base = v << 8
            for i in range(256):
                self.oam[i] = self.read(base + i)
            self.dma_cycles += 513
            return
        if 0x4000 <= a <= 0x4017 and a not in (0x4014, 0x4016):
            self.apu[a - 0x4000] = v
            return
        if a == 0x4016:
            if v & 1:
                self.strobe = True
                self.shift = self.buttons
            else:
                self.strobe = False
            return
        if a >= 0x8000:
            if self.mapper == 2:
                # conflito de barramento: o cartucho ve o AND entre o que a
                # CPU escreve e o que a ROM esta devolvendo no mesmo endereco
                efetivo = v & self.read(a)
                self.banco = efetivo & (self.n_bancos - 1)
            return


# ====================================================================== NES

class NES:
    def __init__(self, path):
        self.bus = Bus(open(path, "rb").read())
        self.cpu = CPU(self.bus)
        self.cpu.reset()
        self.frames = 0

    def run_cycles(self, n):
        target = self.cpu.cycles + n
        while self.cpu.cycles < target:
            self.cpu.step()
            if self.bus.dma_cycles:
                self.cpu.cycles += self.bus.dma_cycles
                self.bus.dma_cycles = 0

    def frame(self, buttons=0):
        self.bus.buttons = buttons
        if self.bus.strobe:
            self.bus.shift = buttons
        self.run_cycles(20000)          # parte visivel
        self.bus.vblank = True
        if self.bus.ppu_ctrl & 0x80:
            self.cpu.nmi()
        self.run_cycles(2200)           # vblank
        self.bus.vblank = False
        self.frames += 1

    # ---- ajudantes de leitura ----
    def nt_text(self, addr, length):
        """Le 'length' tiles da nametable e converte de volta pra texto."""
        out = []
        for i in range(length):
            out.append(chr(self.bus.vram[addr + i] + 0x20))
        return "".join(out)

    def sprites(self):
        """Devolve as entradas visiveis da OAM como (y, tile, attr, x)."""
        out = []
        for i in range(0, 256, 4):
            y = self.bus.oam[i]
            if y < 0xEF:
                out.append((y, self.bus.oam[i + 1], self.bus.oam[i + 2], self.bus.oam[i + 3]))
        return out


# ============================================================ apoio aos testes

BTN_A, BTN_B, BTN_SEL, BTN_START = 0x01, 0x02, 0x04, 0x08
BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT = 0x10, 0x20, 0x40, 0x80

def load_labels(path):
    sym = {}
    for line in open(path):
        parts = line.split()
        if len(parts) == 3 and parts[0] == "al":
            sym[parts[2].lstrip(".")] = int(parts[1], 16)
    return sym

FAILS = []

def check(name, cond, detail=""):
    status = "OK  " if cond else "FALHA"
    print(f"  [{status}] {name}" + (f"   {detail}" if detail else ""))
    if not cond:
        FAILS.append(name)
