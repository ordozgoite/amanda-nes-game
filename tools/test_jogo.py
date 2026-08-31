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
TILE_AMA_BOCA_E = 28   # ver TILE_AMA_BOCA_E em src/jogo.s -- nao e um label

def anda(nes, botao, n):
    for _ in range(n):
        nes.frame(botao)

def entra_no_minigame(nes, sym):
    """Boota, entra na pizzaria, passa pelas tres partes do dialogo e cai no minigame."""
    for _ in range(12): nes.frame()
    nes.frame(BTN_START)
    for _ in range(70): nes.frame()    # o respiro pro plin, antes da cena carregar
    for _ in range(200):
        nes.frame(BTN_RIGHT)
        if nes.bus.ram[sym["perto"]]:
            break
    nes.frame(BTN_B)
    for _ in range(150): nes.frame()   # Victor, parte 1 ("...bonita!")
    nes.frame(BTN_B)                    # fecha, abre a parte 2 (ainda o Victor)
    for _ in range(150): nes.frame()   # Victor, parte 2 ("crocs rsrs")
    nes.frame(BTN_B)                    # fecha a dele, abre a da Amanda
    for _ in range(200): nes.frame()   # a fala dela inteira
    nes.frame(BTN_B)
    for _ in range(20): nes.frame()    # fecha a caixa dela e carrega o minigame

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
    POS_AVISO_START = 0x2000 + 24 * 32 + 3
    check("aviso de START na tela",
          nes.nt_text(POS_AVISO_START, 25) == "APERTE START PARA COMECAR")
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

    print("\n== 3. START leva pra pizzaria (com um respiro pro plin) ==")
    POS_AVISO_START = 0x2000 + 24 * 32 + 3
    nes.frame(BTN_START)
    check("o plin toca na hora", nes.bus.apu[0x06] | nes.bus.apu[0x07],
          f"${nes.bus.apu[0x06]:02X} ${nes.bus.apu[0x07]:02X}")
    check("ainda no menu, so contando", nes.bus.ram[sym["tela"]] == 0
          and nes.bus.ram[sym["menu_saindo"]] == 1)
    for _ in range(3): nes.frame()
    check("o aviso de START some", nes.nt_text(POS_AVISO_START, 25) == " " * 25)
    for _ in range(5): nes.frame()          # ~130ms depois do plin
    check("o eco 1 toca no pulso 1, mais baixo", nes.bus.apu[0x00] == 0x59,
          f"${nes.bus.apu[0x00]:02X}")
    for _ in range(8): nes.frame()          # ~130ms depois do eco 1
    check("o eco 2 toca no pulso 1, mais baixo ainda", nes.bus.apu[0x00] == 0x55,
          f"${nes.bus.apu[0x00]:02X}")
    for _ in range(17): nes.frame()
    check("ainda esperando, nao pulou direto pra cena", nes.bus.ram[sym["tela"]] == 0)
    for _ in range(40): nes.frame()    # os ~60 quadros de espera, com folga
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
    # cabeca tem paleta propria (cabelo/laco); tronco e pernas dividem a
    # mesma (as pernas nao precisam de cor extra, e uma so ja da conta)
    check("paletas por linha de tile", [s[2] & 3 for s in amanda] == [0,0,1,1,0,0,1,1],
          str([s[2] & 3 for s in amanda]))
    # cabeca dele = paleta 2, torso = paleta 3 (onde mora o logo da camisa)
    check("Victor sentado, parado a mesa",
          [s[2] & 3 for s in victor] == [2,2,3,2,2,3] and {s[3] for s in victor} == {176, 184})
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
    for _ in range(70): d.frame()      # o respiro pro plin, antes da cena carregar
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
    bocas_amanda = set()
    for _ in range(40):
        d.frame()
        bocas.add(d.bus.oam[37])
        bocas_amanda.add(d.bus.oam[5])
    check("a boca dele mexe enquanto fala", bocas == {17, 22}, str(sorted(bocas)))
    check("a boca DELA fica parada na fala do Victor", bocas_amanda == {1},
          str(sorted(bocas_amanda)))
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
    # a etiqueta "VICTOR:" (fonte mini) fica na linha 9, uma acima da mensagem
    nome = [d.bus.vram[0x2000 + 9*32 + 9 + i] for i in range(7)]
    check("a etiqueta VICTOR: esta na tela", nome == [255, 249, 247, 254, 252, 253, 245],
          f"tiles {nome}")
    # o texto foi mesmo escrito na tela: primeira linha comeca com N O S S A
    letras = [d.bus.vram[0x2000 + 10*32 + 9 + i] for i in range(5)]
    check("a primeira linha do balao esta na tela", letras == [219, 220, 224, 224, 206],
          f"tiles {letras}")
    check("essa e a caixa do Victor", d.bus.ram[sym["dlg_box"]] == 0)

    d.frame(BTN_B)
    for _ in range(14): d.frame()
    check("B fecha a parte 1 do Victor e abre a parte 2 (mesma caixa)",
          d.bus.ram[sym["dlg_box"]] == 0 and d.bus.ram[sym["dlg_parte"]] == 1
          and d.bus.ram[sym["dialogo"]] in (1, 2),
          f"dlg_box={d.bus.ram[sym['dlg_box']]} parte={d.bus.ram[sym['dlg_parte']]} "
          f"dialogo={d.bus.ram[sym['dialogo']]}")

    for _ in range(150): d.frame()
    check("a parte 2 do Victor termina", d.bus.ram[sym["dialogo"]] == 3)
    nome_p2 = [d.bus.vram[0x2000 + 9*32 + 9 + i] for i in range(7)]
    check("ainda e a etiqueta VICTOR: (mesma caixa)",
          nome_p2 == [255, 249, 247, 254, 252, 253, 245], f"tiles {nome_p2}")
    letras_p2 = [d.bus.vram[0x2000 + 10*32 + 9 + i] for i in range(9)]
    check("a parte 2 esta na tela: EU VIM DE",
          letras_p2 == [210, 226, 232, 227, 214, 218, 232, 209, 210],
          f"tiles {letras_p2}")

    d.frame(BTN_B)
    for _ in range(14): d.frame()
    check("B fecha a parte 2 do Victor e abre a da Amanda",
          d.bus.ram[sym["dlg_box"]] == 1 and d.bus.ram[sym["dialogo"]] in (1, 2),
          f"dlg_box={d.bus.ram[sym['dlg_box']]} dialogo={d.bus.ram[sym['dialogo']]}")

    # a boca dele nao pode mexer: agora quem fala e a Amanda
    bocas2 = set()
    bocas2_amanda = set()
    for _ in range(60):
        d.frame()
        bocas2.add(d.bus.oam[37])
        bocas2_amanda.add(d.bus.oam[5])
    check("a boca dele NAO mexe na fala da Amanda", bocas2 == {17}, str(sorted(bocas2)))
    check("a boca DELA mexe na propria fala", bocas2_amanda == {1, TILE_AMA_BOCA_E},
          str(sorted(bocas2_amanda)))

    for _ in range(150): d.frame()
    check("a fala da Amanda termina", d.bus.ram[sym["dialogo"]] == 3)
    # a caixa dela fica na linha 16 (uma pagina abaixo da do Victor)
    nome2 = [d.bus.vram[0x2000 + 17*32 + 9 + i] for i in range(7)]
    check("a etiqueta AMANDA: esta na tela", nome2 == [246, 250, 246, 251, 248, 246, 245],
          f"tiles {nome2}")
    letras2 = [d.bus.vram[0x2000 + 18*32 + 9 + i] for i in range(5)]
    check("a fala da Amanda esta na tela: S E N T A",
          letras2 == [224, 210, 219, 225, 206], f"tiles {letras2}")

    d.frame(BTN_B)
    for _ in range(14): d.frame()
    check("B fecha a caixa da Amanda", d.bus.ram[sym["dialogo"]] == 0)

    print("\n== 6c. O dialogo acaba e o minigame comeca ==")
    for _ in range(10): d.frame()
    check("tela = jogo", d.bus.ram[sym["tela"]] == 2, f"tela={d.bus.ram[sym['tela']]}")
    check("banco 2 selecionado", d.bus.banco == 2, f"banco {d.bus.banco}")
    check("fase = jogando", d.bus.ram[sym["jogo_fase"]] == 0)
    check("placar comeca zerado",
          d.bus.ram[sym["jogo_pontos"]] == 0 and d.bus.ram[sym["jogo_erros"]] == 0)

    print("\n== 7. O minigame: pegar pizza ==")
    for _ in range(200):
        d.frame()
        if d.bus.ram[sym["pz_ativa"]]:
            break
    check("uma pizza nasceu", d.bus.ram[sym["pz_ativa"]] == 1)
    alvo_x = d.bus.ram[sym["pz_x"]]
    d.bus.ram[sym["player_x"]] = alvo_x            # poe a Amanda embaixo dela
    pontos0 = d.bus.ram[sym["jogo_pontos"]]
    for _ in range(250):
        d.frame()
        if d.bus.ram[sym["jogo_pontos"]] > pontos0 or d.bus.ram[sym["pz_ativa"]] == 0:
            break
    check("pegar a pizza soma ponto", d.bus.ram[sym["jogo_pontos"]] > pontos0,
          f"{pontos0} -> {d.bus.ram[sym['jogo_pontos']]}")
    check("som de comer no canal de ruido",
          (d.bus.apu[0x0C], d.bus.apu[0x0E], d.bus.apu[0x0F]) == (0x0C, 0x03, 0x48),
          f"${d.bus.apu[0x0C]:02X} ${d.bus.apu[0x0E]:02X} ${d.bus.apu[0x0F]:02X}")
    for _ in range(4): d.frame()
    DIG_BASE = 96   # ver DIG_BASE em tools/make_jogo.py -- nao e um label, so uma constante
    dez = d.bus.vram[0x2000 + 26] - DIG_BASE
    check("o digito do placar foi escrito", 0 <= dez <= 9, f"tile {d.bus.vram[0x2000+26]}")

    print("\n== 8. O minigame: errar pizza ==")
    erros0 = d.bus.ram[sym["jogo_erros"]]
    d.bus.ram[sym["player_x"]] = 8                  # bem longe de onde a proxima nasce
    for _ in range(250):
        d.frame()
        if d.bus.ram[sym["jogo_erros"]] > erros0:
            break
    check("deixar cair soma erro", d.bus.ram[sym["jogo_erros"]] > erros0,
          f"{erros0} -> {d.bus.ram[sym['jogo_erros']]}")
    check("som de queda no canal de ruido",
          (d.bus.apu[0x0C], d.bus.apu[0x0E], d.bus.apu[0x0F]) == (0x09, 0x0A, 0x68),
          f"${d.bus.apu[0x0C]:02X} ${d.bus.apu[0x0E]:02X} ${d.bus.apu[0x0F]:02X}")
    for _ in range(4): d.frame()
    erro_tile = d.bus.vram[0x2000 + 32 + 26] - DIG_BASE
    check("o digito de erros foi escrito", 0 <= erro_tile <= 9,
          f"tile {d.bus.vram[0x2000+32+26]}")

    print("\n== 8b. O minigame: pizzas nao saltam de extremo a extremo ==")
    s = NES(ROM)
    entra_no_minigame(s, sym)
    SALTO_MAX = 80   # ver SALTO_MAX em src/jogo.s -- nao e um label, so uma constante
    ativa_antes = [0, 0, 0]
    nascimentos = []
    for quadro in range(6000):
        # pega tudo que aparece, pra rodada nunca acabar por erro demais
        for i in range(3):
            if s.bus.ram[sym["pz_ativa"] + i]:
                s.bus.ram[sym["player_x"]] = s.bus.ram[sym["pz_x"] + i]
        s.frame()
        for i in range(3):
            ativa = s.bus.ram[sym["pz_ativa"] + i]
            if ativa and not ativa_antes[i]:
                nascimentos.append((quadro, s.bus.ram[sym["pz_x"] + i]))
            ativa_antes[i] = ativa
        if len(nascimentos) >= 25:
            break
    saltos = [abs(nascimentos[i][1] - nascimentos[i-1][1]) for i in range(1, len(nascimentos))]
    check("pizzas suficientes nasceram pro teste valer", len(nascimentos) >= 15,
          f"{len(nascimentos)} nascimentos")
    check(f"nenhum salto passou de {SALTO_MAX}px", saltos and max(saltos) <= SALTO_MAX,
          f"maior salto: {max(saltos) if saltos else '?'}px, x's: "
          f"{[x for _, x in nascimentos]}")

    print("\n== 9. O minigame: vitoria ao alcancar PONTOS_MIN ==")
    v = NES(ROM)
    entra_no_minigame(v, sym)
    check("entrou no minigame", v.bus.ram[sym["tela"]] == 2)
    for _ in range(3000):
        v.frame()
        if v.bus.ram[sym["pz_ativa"]]:
            v.bus.ram[sym["player_x"]] = v.bus.ram[sym["pz_x"]]
        if v.bus.ram[sym["jogo_fase"]] == 1:
            break
    check("15 pontos disparam a comemoracao", v.bus.ram[sym["jogo_fase"]] == 1,
          f"pontos={v.bus.ram[sym['jogo_pontos']]} fase={v.bus.ram[sym['jogo_fase']]}")
    for _ in range(150): v.frame()
    check("a comemoracao acaba e o jogo continua",
          v.bus.ram[sym["jogo_fase"]] == 0, f"fase={v.bus.ram[sym['jogo_fase']]}")

    print("\n== 10. O minigame: derrota ao acumular ERROS_MAX ==")
    f = NES(ROM)
    entra_no_minigame(f, sym)
    f.bus.ram[sym["player_x"]] = 8                   # nunca sai daqui: erra tudo
    for _ in range(3000):
        f.frame()
        if f.bus.ram[sym["jogo_fase"]] == 2:
            break
    check("5 erros encerram a rodada", f.bus.ram[sym["jogo_fase"]] == 2,
          f"erros={f.bus.ram[sym['jogo_erros']]} fase={f.bus.ram[sym['jogo_fase']]}")
    f.frame(BTN_START)
    for _ in range(6): f.frame()
    check("START no fim de jogo volta pro menu", f.bus.ram[sym["tela"]] == 0)
    check("banco 0 de volta (fim de jogo)", f.bus.banco == 0, f"banco {f.bus.banco}")

    print("\n== 11. A musica troca de estado junto com a tela ==")
    # a essa altura 'nes' esta de volta ao menu (secao 6) -- e o menu agora
    # fica em silencio (so a pizzaria e o minigame tocam musica)
    check("menu em silencio", nes.bus.apu[0x00] & 0x0F == 0 and
          nes.bus.apu[0x04] & 0x0F == 0)
    nes.frame(BTN_START)                    # entra na pizzaria: a musica comeca
    for _ in range(70):                     # o respiro pro plin, antes da cena carregar
        nes.frame()
    p1 = nes.bus.apu[0x02] | ((nes.bus.apu[0x03] & 7) << 8)
    mudou = False
    for _ in range(40):
        nes.frame()
        p = nes.bus.apu[0x02] | ((nes.bus.apu[0x03] & 7) << 8)
        if p != p1:
            mudou = True
    check("canais ainda ligados", nes.bus.apu[0x15] & 0x0F == 0x0F)
    check("as notas continuam mudando na pizzaria", mudou)
    nes.frame(BTN_START)                    # volta pro menu, deixa o estado como antes
    for _ in range(6):
        nes.frame()
    check("silencia de novo ao voltar pro menu",
          nes.bus.ram[sym["tela"]] == 0 and nes.bus.apu[0x00] & 0x0F == 0)

    print("\n== 12. Estabilidade ==")
    for _ in range(3):
        nes.frame(BTN_START)
        for _ in range(70):            # o respiro pro plin, antes da cena carregar
            nes.frame()
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
