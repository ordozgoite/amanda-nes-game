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
DLG_BASE = 204          # ver DLG_BASE em tools/make_scene.py -- nao e um label
# falante de cada uma das 13 partes do dialogo (0=Victor, 1=Amanda) --
# espelha FALANTE_GRUPO em tools/make_scene.py
FALANTE_TAB = [0, 0, 1, 0, 1, 1, 0, 0, 1, 0, 1, 0, 1]

def anda(nes, botao, n):
    for _ in range(n):
        nes.frame(botao)

def entra_no_minigame(nes, sym):
    """Boota, entra na pizzaria, passa por todas as partes do dialogo, cai no
    minigame (que comeca na tela de intro, jogo_fase==3) e aperta B pra
    dispensar a intro e jogar de vez."""
    for _ in range(12): nes.frame()
    nes.frame(BTN_START)
    for _ in range(70): nes.frame()    # o respiro pro plin, antes da cena carregar
    for _ in range(200):
        nes.frame(BTN_RIGHT)
        if nes.bus.ram[sym["perto"]]:
            break
    nes.frame(BTN_B)                    # abre a primeira caixa
    for _ in range(len(FALANTE_TAB)):
        for _ in range(400): nes.frame()   # digita a parte inteira e espera o B
        nes.frame(BTN_B)                    # fecha essa / abre a proxima (ou termina)
    for _ in range(20): nes.frame()    # carrega o minigame (tela de intro)
    nes.frame(BTN_B)                    # dispensa a intro
    for _ in range(10): nes.frame()    # troca pra nametable "jogando"

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
    check("16 sprites: Amanda (8) + Victor em pe (8)", len(spr) == 16, f"{len(spr)} sprites")
    amanda = [nes.bus.oam[i:i+4] for i in range(0, 32, 4)]
    victor = [nes.bus.oam[i:i+4] for i in range(32, 64, 4)]
    check("Amanda tem 16x32 (4 tiles de altura)",
          sorted({s[0] for s in amanda}) == [192, 200, 208, 216])
    # cabeca tem paleta propria (cabelo/laco); tronco e pernas dividem a
    # mesma (as pernas nao precisam de cor extra, e uma so ja da conta)
    check("paletas por linha de tile", [s[2] & 3 for s in amanda] == [0,0,1,1,0,0,1,1],
          str([s[2] & 3 for s in amanda]))
    # cabeca dele = paleta 2, torso = paleta 3 (logo), pernas reaproveitam a 2
    # (pretas, sem pele -- ver make_sprites.py); ele comeca em pe, deslocado
    # da cadeira (x=160), esperando ela chegar
    check("Victor em pe, deslocado da cadeira",
          [s[2] & 3 for s in victor] == [2,2,3,2,2,2,3,2] and {s[3] for s in victor} == {160, 168},
          f"paletas={[s[2] & 3 for s in victor]} xs={sorted({s[3] for s in victor})}")
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
    # longe dele: nada de aviso (sprite 16 = byte 64 da OAM)
    check("longe, sem aviso", d.bus.ram[sym["perto"]] == 0 and d.bus.oam[64] >= 0xEF)
    for _ in range(200):
        d.frame(BTN_RIGHT)
        if d.bus.ram[sym["perto"]]: break
    d.frame()
    check("chegando perto, o aviso B aparece",
          d.bus.oam[64] < 0xEF and d.bus.oam[65] == 24,
          f"y={d.bus.oam[64]} tile={d.bus.oam[65]}")
    check("o aviso fica sobre a cabeca dele, em pe (x=160, nao a cadeira)",
          d.bus.oam[67] == 160 and d.bus.oam[64] < 192)

    # B nao abre o balao na hora: ela so anda ate ficar alinhada com o
    # lugar dela (mesmo X de quando sentada), mas continua em pe -- o
    # dialogo comeca com os dois de pe. Ela so senta de verdade bem antes
    # do convite DELA pra ele sentar (PARTE_SENTAR, checado mais abaixo).
    d.frame(BTN_B)
    for _ in range(150):
        d.frame()
        if d.bus.ram[sym["dialogo"]] != 0: break
    check("ela se alinhou mas continua em pe quando o balao abre",
          d.bus.ram[sym["amanda_sentada"]] == 0
          and d.bus.ram[sym["player_x"]] == 200
          and d.bus.ram[sym["player_y"]] == 192,
          f"sentada={d.bus.ram[sym['amanda_sentada']]} x={d.bus.ram[sym['player_x']]} "
          f"y={d.bus.ram[sym['player_y']]}")
    # em pe: as pernas dela ainda aparecem (sprites 3 e 7) -- diferente de
    # quando ela senta de verdade, mais adiante nesta mesma conversa
    check("as pernas dela ainda aparecem, em pe",
          d.bus.oam[3*4] < 0xEF and d.bus.oam[7*4] < 0xEF,
          f"y3={d.bus.oam[12]} y7={d.bus.oam[28]}")
    check("so entao o balao abre", d.bus.ram[sym["dialogo"]] in (1, 2),
          f"estado {d.bus.ram[sym['dialogo']]}")
    check("o aviso some com o balao aberto", d.bus.oam[64] >= 0xEF)

    x_antes = d.bus.ram[sym["player_x"]]
    for _ in range(30): d.frame(BTN_RIGHT)
    check("ela nao anda enquanto ele fala",
          d.bus.ram[sym["player_x"]] == x_antes,
          f"{x_antes} -> {d.bus.ram[sym['player_x']]}")

    # a boca abre e fecha enquanto escreve -- nesta primeira parte ele ainda
    # esta em pe (16, 46) = tiles do "Victor em pe"; so senta depois do
    # convite dela, mais adiante nesta mesma conversa
    bocas = set()
    bocas_amanda = set()
    for _ in range(40):
        d.frame()
        bocas.add(d.bus.oam[37])
        bocas_amanda.add(d.bus.oam[5])
    check("a boca dele mexe enquanto fala, em pe", bocas == {31, 46}, str(sorted(bocas)))
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
    check("a boca para de mexer, em pe", d.bus.oam[37] == 31)
    # a etiqueta "VICTOR:" (fonte mini) fica na linha 9, uma acima da mensagem
    NOME_VICTOR = [255, 249, 247, 254, 252, 253, 245]
    NOME_AMANDA = [246, 250, 246, 251, 248, 246, 245]
    nome = [d.bus.vram[0x2000 + 9*32 + 5 + i] for i in range(7)]
    check("a etiqueta VICTOR: esta na tela", nome == NOME_VICTOR, f"tiles {nome}")
    # o texto foi mesmo escrito na tela: primeira linha comeca com N O S S A
    letras = [d.bus.vram[0x2000 + 10*32 + 5 + i] for i in range(5)]
    check("a primeira linha do balao esta na tela", letras == [217, 218, 222, 222, 204],
          f"tiles {letras}")
    check("essa e a caixa do Victor", d.bus.ram[sym["dlg_box"]] == 0)

    d.frame(BTN_B)
    for _ in range(14): d.frame()
    check("B fecha a parte 1 do Victor e abre a parte 2 (mesma caixa)",
          d.bus.ram[sym["dlg_box"]] == 0 and d.bus.ram[sym["dlg_parte"]] == 1
          and d.bus.ram[sym["dialogo"]] in (1, 2),
          f"dlg_box={d.bus.ram[sym['dlg_box']]} parte={d.bus.ram[sym['dlg_parte']]} "
          f"dialogo={d.bus.ram[sym['dialogo']]}")

    # da parte 2 em diante (o dialogo inteiro tem 13 partes agora, alternando
    # Victor/Amanda varias vezes -- ver FALANTE_TAB): percorre o resto de
    # forma generica, conferindo so que cada parte abre na caixa (posicao +
    # etiqueta) de quem realmente fala nela, sem transcrever cada frase.
    nome_por_falante = {0: NOME_VICTOR, 1: NOME_AMANDA}
    linha_nome = {0: 9, 1: 9}         # as duas caixas ficam na mesma linha agora
    col_nome = {0: 5, 1: 13}          # mas a coluna diferencia: Victor mais a
                                       # esquerda, Amanda mais a direita
    a_boca_mexeu = {0: False, 1: False}
    for parte in range(1, len(FALANTE_TAB)):
        for _ in range(400):
            d.frame()
            if d.bus.oam[5] == TILE_AMA_BOCA_E:
                a_boca_mexeu[1] = True
            if d.bus.oam[37] in (22, 46):   # 22 sentado, 46 em pe (ainda nao sentou)
                a_boca_mexeu[0] = True
        check(f"parte {parte}: o texto termina", d.bus.ram[sym["dialogo"]] == 3,
              f"dialogo={d.bus.ram[sym['dialogo']]}")
        falante = FALANTE_TAB[parte]
        check(f"parte {parte}: caixa do falante certo",
              d.bus.ram[sym["dlg_box"]] == falante,
              f"esperado {falante}, leu {d.bus.ram[sym['dlg_box']]}")
        linha = linha_nome[falante]
        col = col_nome[falante]
        nome_lido = [d.bus.vram[0x2000 + linha*32 + col + i] for i in range(7)]
        check(f"parte {parte}: etiqueta do falante certo",
              nome_lido == nome_por_falante[falante], f"tiles {nome_lido}")
        if parte == 8:   # a reacao da Amanda: so o coracaozinho, sem palavra
            coracao = d.bus.vram[0x2000 + (linha + 1)*32 + col + 6]
            check("parte 8: o coracaozinho aparece", coracao == 235, f"tile {coracao}")
        if parte == 2:   # PARTE_SENTAR: ela sentou ANTES desta fala (o convite)
            check("a animacao de sentar da Amanda terminou: ela esta sentada",
                  d.bus.ram[sym["amanda_sentada"]] == 1)
            check("ela esta na cadeira dela (x=200, y=152)",
                  d.bus.ram[sym["player_x"]] == 200 and d.bus.ram[sym["player_y"]] == 152,
                  f"x={d.bus.ram[sym['player_x']]} y={d.bus.ram[sym['player_y']]}")
            check("as pernas dela ficam escondidas, sentada",
                  d.bus.oam[3*4] >= 0xEF and d.bus.oam[7*4] >= 0xEF,
                  f"y3={d.bus.oam[12]} y7={d.bus.oam[28]}")
        if parte == 3:   # a primeira parte depois do convite pra ELE sentar
            check("a animacao de sentar do Victor terminou: ele esta sentado",
                  d.bus.ram[sym["victor_sentado"]] == 1)
            check("ele foi pra cadeira dele (x=176)",
                  d.bus.ram[sym["victor_x"]] == 176, f"x={d.bus.ram[sym['victor_x']]}")
            check("na mesma altura da mesa (y=152)",
                  d.bus.ram[sym["victor_y"]] == 152, f"y={d.bus.ram[sym['victor_y']]}")
            # sentado: volta a usar os 6 sprites de sempre (tiles 16-21); os
            # 2 extras que ele usava em pe (pernas, sprites 14-15) somem
            victor_oam = [d.bus.oam[i:i+4] for i in range(32, 64, 4)]
            check("Victor sentado usa os tiles 16-21",
                  [s[1] for s in victor_oam[:6]] == list(range(16, 22)),
                  str([s[1] for s in victor_oam[:6]]))
            check("os 2 sprites extras do 'em pe' ficam escondidos",
                  victor_oam[6][0] >= 0xEF and victor_oam[7][0] >= 0xEF,
                  f"y14={victor_oam[6][0]} y15={victor_oam[7][0]}")
        d.frame(BTN_B)
        for _ in range(14): d.frame()
    check("as bocas mexeram nas partes de cada um", all(a_boca_mexeu.values()),
          str(a_boca_mexeu))
    check("as 13 partes passaram, o dialogo fechou", d.bus.ram[sym["dialogo"]] == 0)

    print("\n== 6c. O dialogo acaba e o minigame comeca ==")
    for _ in range(10): d.frame()
    check("tela = jogo", d.bus.ram[sym["tela"]] == 2, f"tela={d.bus.ram[sym['tela']]}")
    check("banco 2 selecionado", d.bus.banco == 2, f"banco {d.bus.banco}")
    check("comeca na tela de intro, explicando o objetivo",
          d.bus.ram[sym["jogo_fase"]] == 3, f"fase={d.bus.ram[sym['jogo_fase']]}")
    d.frame(BTN_B)                       # dispensa a intro
    for _ in range(10): d.frame()        # troca de nametable (desliga/liga tela)
    check("B na intro comeca o jogo de verdade",
          d.bus.ram[sym["jogo_fase"]] == 0, f"fase={d.bus.ram[sym['jogo_fase']]}")
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
    # UI_BASE muda toda vez que a arte da tela do jogo cresce/encolhe (nao
    # e um label, so uma constante -- ver build/jogo.inc, gerado por
    # tools/make_jogo.py) -- le do arquivo em vez de hardcodar, pra nao
    # desalinhar de novo como aconteceu (211 -> 210 so nessa sessao)
    import re
    UI_BASE = int(re.search(r"UI_BASE\s*=\s*\$([0-9A-Fa-f]+)",
                             open("build/jogo.inc").read()).group(1), 16)
    UI_BARRA_VAZIA, UI_BARRA_CHEIA = UI_BASE, UI_BASE + 1
    UI_VIDA_CHEIA, UI_VIDA_VAZIA = UI_BASE + 2, UI_BASE + 3
    BARRA_ADDR = 0x2000 + 2*32 + 8
    VIDAS_ADDR = 0x2000 + 3*32 + 8
    check("o primeiro segmento da barra de pontos acendeu",
          d.bus.vram[BARRA_ADDR] == UI_BARRA_CHEIA,
          f"tile {d.bus.vram[BARRA_ADDR]}")
    check("o resto da barra continua vazio",
          all(d.bus.vram[BARRA_ADDR + i] == UI_BARRA_VAZIA for i in range(1, 15)),
          [d.bus.vram[BARRA_ADDR + i] for i in range(1, 15)])

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
    check("a primeira vida foi perdida (icone apagado)",
          d.bus.vram[VIDAS_ADDR] == UI_VIDA_VAZIA,
          f"tile {d.bus.vram[VIDAS_ADDR]}")
    check("o resto das vidas continua cheio",
          all(d.bus.vram[VIDAS_ADDR + i] == UI_VIDA_CHEIA for i in range(1, 5)),
          [d.bus.vram[VIDAS_ADDR + i] for i in range(1, 5)])

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
    for _ in range(60): v.frame()          # a fraseszinha feliz toca inteira
    check("o sprite dela continua visivel na vitoria (so a derrota esconde)",
          v.bus.oam[0] < 0xEF, f"y0={v.bus.oam[0]}")
    v.frame(BTN_B)                          # "APERTE B PRA CONTINUAR"
    for _ in range(20): v.frame()           # carrega a cena do carro
    check("B na vitoria leva pra cena do carro",
          v.bus.ram[sym["tela"]] == 3 and v.bus.banco == 3,
          f"tela={v.bus.ram[sym['tela']]} banco={v.bus.banco}")

    print("\n== 9b. A cena do carro: rolagem e sprites ==")
    # 20 sprites da lataria (0-19) + 2 cabecas (20, 21) -- todos visiveis,
    # nenhum escondido (y >= 0xEF)
    carro_oam = [v.bus.oam[i:i + 4] for i in range(0, 22 * 4, 4)]
    check("os 22 sprites do carro (lataria + 2 cabecas) estao visiveis",
          all(s[0] < 0xEF for s in carro_oam),
          [s[0] for s in carro_oam if s[0] >= 0xEF])
    scroll0 = v.bus.ram[sym["carro_scroll"]]
    for _ in range(30): v.frame()
    scroll1 = v.bus.ram[sym["carro_scroll"]]
    check("o scroll horizontal avanca sozinho (o carro 'anda')",
          scroll1 != scroll0, f"{scroll0} -> {scroll1}")
    check("mas o sprite do carro fica parado na tela (so o fundo rola)",
          v.bus.oam[3] == 100, f"x={v.bus.oam[3]}")   # CARRO_X, ver src/jogo.s
    v.frame(BTN_START)
    for _ in range(6): v.frame()
    check("START na cena do carro volta pro menu (escape hatch de sempre)",
          v.bus.ram[sym["tela"]] == 0 and v.bus.banco == 0,
          f"tela={v.bus.ram[sym['tela']]} banco={v.bus.banco}")

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

    print("\n== 10b. Derrota: B tenta de novo sem sair da tela ==")
    f.frame(BTN_B)
    for _ in range(10): f.frame()   # troca de nametable (desliga/liga tela)
    check("B na derrota reseta e volta a jogar, na mesma tela",
          f.bus.ram[sym["jogo_fase"]] == 0
          and f.bus.ram[sym["jogo_pontos"]] == 0
          and f.bus.ram[sym["jogo_erros"]] == 0
          and f.bus.ram[sym["tela"]] == 2,
          f"fase={f.bus.ram[sym['jogo_fase']]} pontos={f.bus.ram[sym['jogo_pontos']]} "
          f"erros={f.bus.ram[sym['jogo_erros']]} tela={f.bus.ram[sym['tela']]}")
    check("continua no banco do jogo, nao voltou pro menu",
          f.bus.banco == 2, f"banco {f.bus.banco}")

    print("\n== 10c. Derrota: START ainda desiste pro menu ==")
    g = NES(ROM)
    entra_no_minigame(g, sym)
    g.bus.ram[sym["player_x"]] = 8
    for _ in range(3000):
        g.frame()
        if g.bus.ram[sym["jogo_fase"]] == 2:
            break
    check("5 erros de novo, numa instancia separada", g.bus.ram[sym["jogo_fase"]] == 2)
    g.frame(BTN_START)
    for _ in range(6): g.frame()
    check("START no fim de jogo volta pro menu", g.bus.ram[sym["tela"]] == 0)
    check("banco 0 de volta (fim de jogo)", g.bus.banco == 0, f"banco {g.bus.banco}")

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
