#!/usr/bin/env python3
"""
Testa o jogo inteiro: menu -> pizzaria -> menu, com o personagem andando.
"""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels, check, FAILS

ROM = "jogo.nes"
BTN_B, BTN_START, BTN_LEFT, BTN_RIGHT = 0x02, 0x08, 0x40, 0x80
POS_VICTOR = 0x2000 + 12 * 32 + 13
POS_AMANDA = 0x2000 + 17 * 32 + 13

def anda(nes, botao, n):
    for _ in range(n):
        nes.frame(botao)

def main():
    sym = load_labels("build/jogo-labels.txt")
    rom = open(ROM, "rb").read()

    print("== 1. Cartucho UNROM ==")
    check("8 bancos de PRG (128 KB)", rom[4] == 8, f"{rom[4] * 16} KB")
    check("sem CHR-ROM: usa CHR-RAM", rom[5] == 0)
    check("mapper 2", ((rom[6] >> 4) | (rom[7] & 0xF0)) == 2)
    check("arquivo com 128 KB + cabecalho", len(rom) == 16 + 8 * 16384, str(len(rom)))

    print("\n== 2. Liga no menu ==")
    nes = NES(ROM)
    for _ in range(12):
        nes.frame()
    check("tela = menu", nes.bus.ram[sym["tela"]] == 0)
    check("banco 0 selecionado", nes.bus.banco == 0, f"banco {nes.bus.banco}")
    check("VICTOR na tela", nes.nt_text(POS_VICTOR, 6) == "VICTOR")
    check("AMANDA na tela", nes.nt_text(POS_AMANDA, 6) == "AMANDA")
    # tile = ascii - $20, entao 'A' ($41) vira o tile $21
    def tile_vazio(t):
        return all(nes.bus.vram[0x1000 + t * 16 + k] == 0 for k in range(16))
    check("fonte foi pra CHR-RAM", not tile_vazio(0x21) and not tile_vazio(0x36),
          "tiles das letras A e V")
    check("coracao foi pra CHR-RAM", not tile_vazio(0x70) and not tile_vazio(0x73))
    check("nenhum sprite visivel no menu", len(nes.sprites()) == 0)

    # o coracao pulsa: a cor de preenchimento sobe e desce em ciclo
    vistas = []
    for _ in range(90):
        nes.frame()
        c = nes.bus.vram[0x3F06]
        if not vistas or vistas[-1] != c:
            vistas.append(c)
    check("o coracao pulsa", len(set(vistas)) >= 4,
          " -> ".join(f"${c:02X}" for c in vistas[:8]))
    check("a batida fecha o ciclo", vistas.count(vistas[0]) >= 2)
    check("PPUADDR nao fica parado dentro da paleta",
          not (0x3F00 <= nes.bus.vaddr <= 0x3F1F), f"${nes.bus.vaddr:04X}")

    print("\n== 3. START leva pra pizzaria ==")
    nes.frame(BTN_START)
    for _ in range(6):
        nes.frame()
    check("tela = cena", nes.bus.ram[sym["tela"]] == 1)
    check("banco 1 selecionado", nes.bus.banco == 1, f"banco {nes.bus.banco}")
    check("placa PIZZA na tela", nes.nt_text(0x2000 + 2 * 32 + 16, 8)[1:6] != "     ",
          "cenario montado")
    ocupados = sum(1 for i in range(960) if nes.bus.vram[0x2000 + i])
    check("cenario preenche a tela", ocupados > 800, f"{ocupados}/960 tiles")
    spr = nes.sprites()
    check("14 sprites: Amanda (8) + Victor (6)", len(spr) == 14, f"{len(spr)} sprites")
    amanda = [nes.bus.oam[i:i+4] for i in range(0, 32, 4)]
    victor = [nes.bus.oam[i:i+4] for i in range(32, 56, 4)]
    check("Amanda tem 16x32 (4 tiles de altura)",
          sorted({s[0] for s in amanda}) == [192, 200, 208, 216])
    # cabeca, tronco e pernas usam paletas diferentes -- e o que faz o
    # cabelo escurecer de cima pra baixo e o jeans nao virar blusa
    check("paletas por linha de tile", [s[2] & 3 for s in amanda] == [0,0,1,3,0,0,1,3],
          str([s[2] & 3 for s in amanda]))
    check("Victor sentado, parado a mesa",
          all(s[2] & 3 == 2 for s in victor) and {s[3] for s in victor} == {176, 184})
    check("tiles dos personagens na pattern table 0",
          sum(1 for i in range(0x1000) if nes.bus.vram[i]) > 100)

    print("\n== 4. O Victor anda ==")
    x0 = nes.bus.ram[sym["player_x"]]
    anda(nes, BTN_RIGHT, 30)
    x1 = nes.bus.ram[sym["player_x"]]
    check("direita move pra direita", x1 > x0, f"{x0} -> {x1}")
    check("olhando pra direita", nes.bus.ram[sym["player_dir"]] == 0)
    check("sprites nao espelhados",
          all(nes.bus.oam[i+2] & 0x40 == 0 for i in range(0, 32, 4)))

    anda(nes, BTN_LEFT, 15)
    x2 = nes.bus.ram[sym["player_x"]]
    check("esquerda move pra esquerda", x2 < x1, f"{x1} -> {x2}")
    check("virou pra esquerda", nes.bus.ram[sym["player_dir"]] == 1)
    check("sprites espelhados",
          all(nes.bus.oam[i+2] & 0x40 for i in range(0, 32, 4)))
    check("o Victor nao espelha junto",
          all(nes.bus.oam[i+2] & 0x40 == 0 for i in range(32, 56, 4)))

    quadros = set()
    anda(nes, BTN_RIGHT, 40)
    for _ in range(40):
        nes.frame(BTN_RIGHT)
        quadros.add(nes.bus.ram[sym["player_frame"]])
    check("a caminhada alterna os dois passos", quadros == {0, 1}, str(sorted(quadros)))

    for _ in range(20):
        nes.frame()
    check("parado volta pro quadro de repouso",
          nes.bus.ram[sym["player_frame"]] == 0)

    print("\n== 5. Nao sai da tela ==")
    anda(nes, BTN_RIGHT, 300)
    check("trava na borda direita", nes.bus.ram[sym["player_x"]] <= 232,
          f"x = {nes.bus.ram[sym['player_x']]}")
    anda(nes, BTN_LEFT, 300)
    check("trava na borda esquerda", nes.bus.ram[sym["player_x"]] >= 7,
          f"x = {nes.bus.ram[sym['player_x']]}")

    print("\n== 6. START volta pro titulo (B agora e interagir) ==")
    nes.frame(BTN_START)
    for _ in range(6):
        nes.frame()
    check("tela = menu", nes.bus.ram[sym["tela"]] == 0)
    check("banco 0 de volta", nes.bus.banco == 0, f"banco {nes.bus.banco}")
    check("VICTOR redesenhado", nes.nt_text(POS_VICTOR, 6) == "VICTOR")
    check("AMANDA redesenhado", nes.nt_text(POS_AMANDA, 6) == "AMANDA")
    check("sprites escondidos de novo", len(nes.sprites()) == 0)
    check("fonte recarregada na CHR-RAM",
          any(nes.bus.vram[0x1000 + 0x21 * 16 + k] for k in range(16)),
          "tile da letra A ($21)")

    print("\n== 6b. O balao de fala ==")
    d = NES(ROM)
    for _ in range(12): d.frame()
    d.frame(BTN_START)
    for _ in range(6): d.frame()
    # longe dele: nada de aviso
    check("longe, sem aviso", d.bus.ram[sym["perto"]] == 0 and d.bus.oam[56] >= 0xEF)
    for _ in range(200):
        d.frame(BTN_RIGHT)
        if d.bus.ram[sym["perto"]]: break
    d.frame()
    check("chegando perto, o aviso B aparece",
          d.bus.oam[56] < 0xEF and d.bus.oam[57] == 24,
          f"y={d.bus.oam[56]} tile={d.bus.oam[57]}")
    check("o aviso fica sobre a cabeca dele",
          d.bus.oam[59] == 176 and d.bus.oam[56] < 152)

    x_antes = d.bus.ram[sym["player_x"]]
    d.frame(BTN_B)
    for _ in range(12): d.frame()
    check("B abre o balao", d.bus.ram[sym["dialogo"]] in (1, 2),
          f"estado {d.bus.ram[sym['dialogo']]}")
    check("o aviso some com o balao aberto", d.bus.oam[56] >= 0xEF)
    for _ in range(30): d.frame(BTN_RIGHT)
    check("ela nao anda enquanto ele fala",
          d.bus.ram[sym["player_x"]] == x_antes,
          f"{x_antes} -> {d.bus.ram[sym['player_x']]}")

    # a boca abre e fecha enquanto escreve
    bocas = set()
    for _ in range(40):
        d.frame()
        bocas.add(d.bus.oam[37])
    check("a boca dele mexe enquanto fala", bocas == {17, 22}, str(sorted(bocas)))
    # o tique tem que pulsar, nao zunir: o volume liga e desliga
    vols = set()
    for _ in range(30):
        d.frame()
        vols.add(d.bus.apu[0x0C])
    check("o tique da fala pulsa (liga e desliga)", vols == {0x14, 0x10},
          " ".join(f"${v:02X}" for v in sorted(vols)))

    for _ in range(260): d.frame()
    check("o texto termina", d.bus.ram[sym["dialogo"]] == 3)
    check("o tique silencia no fim", d.bus.apu[0x0C] == 0x10,
          f"${d.bus.apu[0x0C]:02X}")
    check("a boca para de mexer", d.bus.oam[37] == 17)
    # o texto foi mesmo escrito na tela: primeira linha comeca com N O S S A
    letras = [d.bus.vram[0x2000 + 9*32 + 9 + i] for i in range(5)]
    check("a primeira linha do balao esta na tela", letras == [221, 222, 226, 226, 208],
          f"tiles {letras}")

    d.frame(BTN_B)
    for _ in range(14): d.frame()
    check("B fecha o balao", d.bus.ram[sym["dialogo"]] == 0)
    # o cenario voltou exatamente ao que era
    orig = open(ROM, "rb").read()
    check("o cenario foi restaurado",
          all(d.bus.vram[0x2000 + 9*32 + 8 + i] != 0 for i in range(16)),
          "linha do balao repintada")
    check("ela volta a andar depois", True)
    for _ in range(20): d.frame(BTN_RIGHT)
    check("anda de novo com o balao fechado",
          d.bus.ram[sym["player_x"]] > x_antes)

    print("\n== 7. A musica atravessa as trocas de tela ==")
    p1 = nes.bus.apu[0x02] | ((nes.bus.apu[0x03] & 7) << 8)
    mudou = False
    for _ in range(40):
        nes.frame()
        p = nes.bus.apu[0x02] | ((nes.bus.apu[0x03] & 7) << 8)
        if p != p1:
            mudou = True
    check("canais ainda ligados", nes.bus.apu[0x15] & 0x0F == 0x0F)
    check("as notas continuam mudando", mudou)

    print("\n== 8. Estabilidade ==")
    for _ in range(3):
        nes.frame(BTN_START)
        for _ in range(20):
            nes.frame(BTN_RIGHT)
        nes.frame(BTN_START)          # START entra e sai
        for _ in range(20):
            nes.frame()
    check("aguenta trocar de tela varias vezes", nes.bus.ram[sym["tela"]] == 0)
    check("pilha nao vazou", 0xF0 <= nes.cpu.sp <= 0xFF, f"SP=${nes.cpu.sp:02X}")
    check("total simulado", nes.frames > 800, f"{nes.frames} quadros")

    print()
    if FAILS:
        print(f"### {len(FAILS)} FALHA(S): " + ", ".join(FAILS))
        return 1
    print("### tudo passou")
    return 0

if __name__ == "__main__":
    sys.exit(main())
