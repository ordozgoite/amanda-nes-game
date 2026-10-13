#!/usr/bin/env python3
"""
Testa o jogo inteiro, do menu ate a cena final -- e que dela nao se volta.
"""
import re
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels, check, FAILS
import robo

ROM = "jogo.nes"
BTN_A, BTN_B, BTN_SEL, BTN_START = 0x01, 0x02, 0x04, 0x08
BTN_UP, BTN_DOWN, BTN_LEFT, BTN_RIGHT = 0x10, 0x20, 0x40, 0x80
TODOS = 0xFF
TELA_CARRO, TELA_FOTO, TELA_FIM, TELA_LETREIRO = 3, 4, 5, 6
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

    print("\n== 6. Depois do titulo, START nao volta mais pro menu ==")
    nes.frame(BTN_START)
    for _ in range(6):
        nes.frame()
    check("continua na pizzaria", nes.bus.ram[sym["tela"]] == 1 and nes.bus.banco == 1,
          f"tela={nes.bus.ram[sym['tela']]} banco={nes.bus.banco}")
    check("os dois continuam na tela", len(nes.sprites()) == 16)

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
        if parte == 8:   # "...INTELIGENTE! <3": o coracaozinho fecha a 3a linha
            coracao = d.bus.vram[0x2000 + (linha + 3)*32 + col + 13]
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
    sprites_inc = open("build/sprites.inc").read()
    TILE_PIMENTA = int(re.search(r"TILE_PIMENTA\s*=\s*(\d+)", sprites_inc).group(1))
    PAGINAS_SPRITES = int(re.search(r"PAGINAS_SPRITES\s*=\s*(\d+)", sprites_inc).group(1))
    folha = open("build/chr_sprites.bin", "rb").read()
    check("a folha de sprites inteira foi pra CHR, com a pimenta junto",
          bytes(d.bus.vram[0:PAGINAS_SPRITES * 256]) == folha
          and any(folha[TILE_PIMENTA * 16:(TILE_PIMENTA + 2) * 16]))

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
    UI_BASE = int(re.search(r"UI_BASE\s*=\s*\$([0-9A-Fa-f]+)",
                             open("build/jogo.inc").read()).group(1), 16)
    UI_BARRA_VAZIA, UI_BARRA_CHEIA = UI_BASE, UI_BASE + 1
    UI_VIDA_CHEIA, UI_VIDA_VAZIA = UI_BASE + 2, UI_BASE + 3
    UI_BARRA_MEIA = UI_BASE + 4
    BARRA_ADDR = 0x2000 + 2*32 + 8
    VIDAS_ADDR = 0x2000 + 3*32 + 8
    from make_jogo import (BARRA_TILES, PONTOS_MIN, ERROS_MAX, SALTO_MAX, PIMENTA_DESDE,
                           PIMENTA_LONGE, PZ_N)
    check("uma pizza acende MEIO segmento (cada um vale duas)",
          d.bus.vram[BARRA_ADDR] == UI_BARRA_MEIA,
          f"tile {d.bus.vram[BARRA_ADDR]}")
    check("o resto da barra continua vazio",
          all(d.bus.vram[BARRA_ADDR + i] == UI_BARRA_VAZIA for i in range(1, BARRA_TILES)),
          [d.bus.vram[BARRA_ADDR + i] for i in range(1, BARRA_TILES)])
    # a barra em todos os estados: pontos -> tiles esperados
    b = d.copia()
    for pontos in (2, 3, 17, PONTOS_MIN - 1):
        b.bus.ram[sym["jogo_pontos"]] = pontos
        b.bus.ram[sym["placar_sujo"]] = 1
        b.frame()
        esperado = [UI_BARRA_CHEIA] * (pontos // 2) + [UI_BARRA_MEIA] * (pontos % 2)
        esperado += [UI_BARRA_VAZIA] * (BARRA_TILES - len(esperado))
        lido = list(b.bus.vram[BARRA_ADDR:BARRA_ADDR + BARRA_TILES])
        check(f"barra com {pontos} pizzas: {pontos // 2} cheios + {pontos % 2} meio",
              lido == esperado, lido)
    check("e nada foi escrito depois do fim da barra",
          b.bus.vram[BARRA_ADDR + BARRA_TILES] == d.bus.vram[BARRA_ADDR + BARRA_TILES])

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
          all(d.bus.vram[VIDAS_ADDR + i] == UI_VIDA_CHEIA for i in range(1, ERROS_MAX)) and
          d.bus.vram[VIDAS_ADDR + ERROS_MAX] == 0,      # e nenhum coracao a mais depois
          [d.bus.vram[VIDAS_ADDR + i] for i in range(1, ERROS_MAX + 1)])

    print("\n== 8b. O minigame: pizzas nao saltam de extremo a extremo ==")
    s = NES(ROM)
    entra_no_minigame(s, sym)
    ativa_antes = [0] * PZ_N
    nascimentos = []            # (quadro, tipo, x, pontos na hora)
    max_ativos = 0
    for quadro in range(6000):
        # o robo pega tudo que aparece, pra rodada nunca acabar por erro demais
        s.frame(robo.botao(s, sym))
        for i in range(PZ_N):
            ativa = s.bus.ram[sym["pz_ativa"] + i]
            if ativa and not ativa_antes[i]:
                nascimentos.append((quadro, s.bus.ram[sym["pz_tipo"] + i],
                                    s.bus.ram[sym["pz_x"] + i],
                                    s.bus.ram[sym["jogo_pontos"]]))
            ativa_antes[i] = ativa
        max_ativos = max(max_ativos, sum(ativa_antes))
        if s.bus.ram[sym["jogo_fase"]] != 0:
            break
    pizzas = [x for _, t, x, _ in nascimentos if t == 0]
    saltos = [abs(pizzas[i] - pizzas[i-1]) for i in range(1, len(pizzas))]
    check("pizzas suficientes nasceram pro teste valer", len(pizzas) >= 25,
          f"{len(pizzas)} pizzas")
    check(f"nenhum salto passou de {SALTO_MAX}px", saltos and max(saltos) <= SALTO_MAX,
          f"maior salto: {max(saltos) if saltos else '?'}px, x's: {pizzas}")

    print("\n== 8c. O minigame: as pimentas ==")
    pimentas = [(q, x, p) for q, t, x, p in nascimentos if t == 1]
    check("pimentas cairam durante a rodada", len(pimentas) >= 3, len(pimentas))
    check(f"nenhuma antes de {PIMENTA_DESDE} pizzas (primeiro ela aprende a pegar)",
          all(p >= PIMENTA_DESDE for _, _, p in pimentas), pimentas)
    # as duas nascem na mesma passada do laco principal, mas o NMI pode cair
    # bem no meio dela (entre nasce_pizza e nasce_pimenta) -- ai o teste,
    # que le a RAM entre quadros, ve a pizza um quadro antes
    pizza_de = {q: x for q, t, x, _ in nascimentos if t == 0}
    def junto(q):
        return pizza_de.get(q, pizza_de.get(q - 1))
    check("toda pimenta nasce junto com uma pizza (em paralelo)",
          all(junto(q) is not None for q, _, _ in pimentas),
          [q for q, _, _ in pimentas if junto(q) is None])
    longe = [abs((x + 4) - (junto(q) + 8)) for q, x, _ in pimentas if junto(q) is not None]
    check(f"e nunca grudada nela (centros a {PIMENTA_LONGE}px ou mais)",
          longe and min(longe) >= PIMENTA_LONGE, longe)
    def pizza_depois(q):
        return next((x for q2, t, x, _ in nascimentos if t == 0 and q2 > q), None)
    desvio = [(x + 4) - (pizza_depois(q) + 8) for q, x, _ in pimentas
              if pizza_depois(q) is not None]
    check("toda pimenta cai na coluna da proxima pizza (centro a -8..+7px)",
          desvio and all(-8 <= d <= 7 for d in desvio), desvio)
    check("toda pimenta nasce dentro da tela", all(8 <= x <= 240 for _, x, _ in pimentas),
          [x for _, x, _ in pimentas])
    print(f"  (no maximo {max_ativos} de {PZ_N} objetos caindo ao mesmo tempo)")
    # quem ignora a pimenta e vai direto pra baixo da pizza leva na cabeca --
    # senao a pimenta seria so enfeite (a primeira versao era: caia longe de
    # onde a Amanda ia estar, e nem um robo desatento se machucava)
    ing = NES(ROM)
    entra_no_minigame(ing, sym)
    _, pimentadas = robo.joga(ing, sym, 6000, desvia=False,
                              ate=lambda n: n.bus.ram[sym["jogo_fase"]] != 0
                              or n.bus.ram[sym["jogo_erros"]] > 0)
    check("ignorar as pimentas custa vida (elas atrapalham de verdade)",
          pimentadas > 0, f"erros={ing.bus.ram[sym['jogo_erros']]}")

    # uma pimenta caindo em cima dela, montada na mao
    def so_uma_pimenta(nes, x, y):
        for i in range(PZ_N):
            nes.bus.ram[sym["pz_ativa"] + i] = 0
        nes.bus.ram[sym["pz_ativa"]] = 1
        nes.bus.ram[sym["pz_tipo"]] = 1
        nes.bus.ram[sym["pz_x"]] = x
        nes.bus.ram[sym["pz_y"]] = y
        nes.bus.ram[sym["jogo_espera"]] = 250     # nada mais nasce enquanto isso
    p = d.copia()
    p.bus.ram[sym["jogo_pontos"]] = 10
    so_uma_pimenta(p, p.bus.ram[sym["player_x"]] + 4, 120)
    p.frame()
    p.frame()                 # a OAM montada num quadro so vai pro PPU no NMI seguinte
    y0 = p.bus.oam[32]
    check("a pimenta e desenhada em pe: dois tiles, um embaixo do outro",
          p.bus.oam[33] == TILE_PIMENTA and p.bus.oam[37] == TILE_PIMENTA + 1
          and p.bus.oam[36] == y0 + 8 and p.bus.oam[35] == p.bus.oam[39],
          list(p.bus.oam[32:40]))
    erros0 = p.bus.ram[sym["jogo_erros"]]
    for _ in range(120):
        p.frame()
        if p.bus.ram[sym["jogo_erros"]] > erros0:
            break
    check("encostar na pimenta custa uma vida", p.bus.ram[sym["jogo_erros"]] == erros0 + 1,
          f"{erros0} -> {p.bus.ram[sym['jogo_erros']]}")
    check("a pimenta some na hora", p.bus.ram[sym["pz_ativa"]] == 0)
    check("o som da pimenta e diferente do da pizza caindo (ruido metalico)",
          (p.bus.apu[0x0C], p.bus.apu[0x0E], p.bus.apu[0x0F]) == (0x0A, 0x86, 0x88),
          f"${p.bus.apu[0x0C]:02X} ${p.bus.apu[0x0E]:02X} ${p.bus.apu[0x0F]:02X}")
    check("os pontos nao mudam", p.bus.ram[sym["jogo_pontos"]] == 10)

    p = d.copia()
    p.bus.ram[sym["jogo_pontos"]] = 10
    px = p.bus.ram[sym["player_x"]]
    so_uma_pimenta(p, px + 60 if px < 120 else px - 60, 120)
    erros0 = p.bus.ram[sym["jogo_erros"]]
    for _ in range(120):
        p.frame()
        if not p.bus.ram[sym["pz_ativa"]]:
            break
    check("desviar: a pimenta chega no chao e some sem custar nada",
          p.bus.ram[sym["pz_ativa"]] == 0 and p.bus.ram[sym["jogo_erros"]] == erros0,
          f"ativa={p.bus.ram[sym['pz_ativa']]} erros={p.bus.ram[sym['jogo_erros']]}")
    # raspao: a caixa da pimenta e apertada de proposito
    p = d.copia()
    p.bus.ram[sym["jogo_pontos"]] = 10
    px = p.bus.ram[sym["player_x"]]
    so_uma_pimenta(p, px + 13, 120)            # so o cabelo solto encostaria
    erros0 = p.bus.ram[sym["jogo_erros"]]
    for _ in range(120):
        p.frame()
        if not p.bus.ram[sym["pz_ativa"]]:
            break
    check("de raspao (na borda do sprite dela) nao doi",
          p.bus.ram[sym["jogo_erros"]] == erros0)

    print("\n== 9. O minigame: vitoria ao alcancar PONTOS_MIN ==")
    v = NES(ROM)
    entra_no_minigame(v, sym)
    check("entrou no minigame", v.bus.ram[sym["tela"]] == 2)
    # o robo anda com o controle, 1px por quadro -- ganhar sem perder vida
    # prova que nenhuma pizza nasce longe demais e nenhuma pimenta cai
    # num lugar impossivel de desviar
    quadros, pimentadas = robo.joga(v, sym, 12000,
                                    ate=lambda n: n.bus.ram[sym["jogo_fase"]] != 0)
    check(f"{PONTOS_MIN} pontos disparam a comemoracao", v.bus.ram[sym["jogo_fase"]] == 1,
          f"pontos={v.bus.ram[sym['jogo_pontos']]} fase={v.bus.ram[sym['jogo_fase']]}")
    check("da pra ganhar andando, sem perder nenhuma vida",
          v.bus.ram[sym["jogo_erros"]] == 0 and pimentadas == 0,
          f"erros={v.bus.ram[sym['jogo_erros']]} pimentadas={pimentadas}")
    check(f"a rodada demora mais (uns 45s): {quadros / 60:.0f}s",
          40 * 60 <= quadros <= 70 * 60, quadros)
    for _ in range(60): v.frame()          # a fraseszinha feliz toca inteira
    check("o sprite dela continua visivel na vitoria (so a derrota esconde)",
          v.bus.oam[0] < 0xEF, f"y0={v.bus.oam[0]}")
    v.frame(BTN_B)                          # "APERTE B PRA CONTINUAR"
    for _ in range(20): v.frame()           # carrega a cena do carro
    check("B na vitoria leva pra cena do carro",
          v.bus.ram[sym["tela"]] == 3 and v.bus.banco == 3,
          f"tela={v.bus.ram[sym['tela']]} banco={v.bus.banco}")

    print("\n== 9b. A cena do carro: rolagem e sprites ==")
    # numero de celulas (a silhueta inteira do carro, ver monta_oam_carro)
    # vem do proprio gerador, pra nao travar um valor que muda toda vez
    # que a arte do carro mexe
    n_carro = int(re.search(r"CARRO_N_SPRITES\s*=\s*(\d+)",
                             open("build/carro.inc").read()).group(1))
    # o carro comeca no sprite 1: o 0 e o marcador da divisao de tela
    carro_oam = [v.bus.oam[i:i + 4] for i in range(4, 4 + n_carro * 4, 4)]
    check(f"as {n_carro} celulas do carro estao visiveis",
          all(s[0] < 0xEF for s in carro_oam),
          [s[0] for s in carro_oam if s[0] >= 0xEF])
    scroll0 = v.bus.ram[sym["carro_scroll"]]
    x0 = v.bus.oam[7]                        # x da 1a celula da tabela
    for _ in range(30): v.frame()
    scroll1 = v.bus.ram[sym["carro_scroll"]]
    check("o scroll horizontal avanca sozinho (o carro 'anda')",
          scroll1 != scroll0, f"{scroll0} -> {scroll1}")
    check("mas o sprite do carro fica parado na tela (so o fundo rola)",
          v.bus.oam[7] == x0, f"{x0} -> {v.bus.oam[7]}")
    check("no carro nao tem musica (ela estreia na primeira foto)",
          v.bus.ram[sym["musica_liga"]] == 0)
    check("os pulsos ficam calados (a fraseszinha da vitoria nao vaza)",
          v.bus.apu[0x00] & 0x0F == 0 and v.bus.apu[0x04] & 0x0F == 0)
    amb_motor = int(re.search(r"AMB_MOTOR\s*=\s*(\d+)", car_inc_txt := open("build/carro.inc").read()).group(1))
    amb_vol = int(re.search(r"AMB_RUIDO_VOL\s*=\s*(\d+)", car_inc_txt).group(1))
    tri = v.bus.apu[0x0A] | ((v.bus.apu[0x0B] & 7) << 8)
    check("o motor: triangulo ligado, bem grave",
          v.bus.apu[0x08] & 0x7F and amb_motor <= tri <= amb_motor + 10, f"periodo {tri}")
    periodos, volumes = set(), []
    rua = v.copia()                          # 'v' segue sem a conversa ter comecado
    for _ in range(400):
        rua.frame()
        periodos.add(rua.bus.apu[0x0A])
        volumes.append(rua.bus.apu[0x0C] & 0x0F)
    check("o motor oscila um pouco (nao e uma nota parada)", len(periodos) > 2, sorted(periodos))
    check("a rua: ruido baixinho o tempo todo", min(volumes) >= 1 and volumes.count(amb_vol) > 100,
          f"min={min(volumes)}")
    check("de vez em quando um carro passa (o ruido sobe e desce)",
          max(volumes) > amb_vol + 3, f"max={max(volumes)}")

    print("\n== 9c. O carro: ceu parado em cima, rua rolando embaixo ==")
    car_inc = open("build/carro.inc").read()
    spr0_y = int(re.search(r"SPR0_Y\s*=\s*(\d+)", car_inc).group(1))
    check("o sprite 0 fica em cima da estrela da divisao",
          v.bus.oam[0] == spr0_y - 1, f"y={v.bus.oam[0]}")
    trocas = v.bus.linhas_scroll
    check("o topo do quadro comeca sem rolagem (ceu parado, nametable 0)",
          trocas[0][1:] == (0, 0), trocas[:2])
    meio = [t for t in trocas[1:] if t[1] == (v.bus.ram[sym["carro_scroll"]] - 1) & 0xFF]
    check("a rolagem troca no meio do quadro, logo abaixo da estrela",
          meio and spr0_y < meio[0][0] < 118, trocas)

    print("\n== 9d. O carro: a conversa ==")
    # copia do console parado no carro: o 9b continua dali com o START
    fo = v.copia()
    dlg = open("build/dialogo.inc").read()
    carro_ini = int(re.search(r"PARTE_CARRO_INI\s*=\s*(\d+)", dlg).group(1))
    falas = {int(n): [int(b, 16) for b in re.findall(r"\$([0-9A-F]{2})", bs)][:-1]
             for n, bs in re.findall(r"^fala(\d+):\s*\.byte ([^;]*)", dlg, re.M)}
    inicios = [int(x) for x in re.search(r"inicio_fala_tab:\s*\.byte ([\d, ]+)", dlg).group(1).split(",")]
    fo.frame(BTN_B)                          # B apressado, antes da conversa
    for _ in range(6): fo.frame()
    check("B antes da conversa nao pula o carro", fo.bus.ram[sym["tela"]] == 3)
    for _ in range(200):
        fo.frame()
        if fo.bus.ram[sym["dialogo"]] == 3:
            break
    fo.frame()
    # Amanda fala primeiro: caixa da direita (coluna 12), linha 2, texto na 4
    linha1 = list(fo.bus.vram[0x2000 + 4 * 32 + 13: 0x2000 + 4 * 32 + 13 + len(falas[inicios[carro_ini]])])
    check("a caixa da Amanda abre sozinha, a direita, no ceu parado",
          fo.bus.ram[sym["dlg_box"]] == 3 and linha1 == falas[inicios[carro_ini]],
          f"box={fo.bus.ram[sym['dlg_box']]}")
    fo.frame(BTN_B)
    for _ in range(200):
        fo.frame()
        if fo.bus.ram[sym["dialogo"]] == 3:
            break
    fo.frame()
    resp = falas[inicios[carro_ini + 1]]
    check("depois do B, o Victor responde na caixa da esquerda (coluna 4)",
          fo.bus.ram[sym["dlg_box"]] == 2 and
          list(fo.bus.vram[0x2000 + 4 * 32 + 5: 0x2000 + 4 * 32 + 5 + len(resp)]) == resp)
    fo.frame(BTN_B)
    for _ in range(12): fo.frame()
    nt0 = open("build/carro_nt0.nam", "rb").read()
    check("a conversa acabou e o ceu voltou ao que era (linhas 2-7)",
          fo.bus.ram[sym["carro_fase"]] == 2 and fo.bus.ram[sym["dialogo"]] == 0 and
          bytes(fo.bus.vram[0x2040:0x2100]) == nt0[0x40:0x100])

    print("\n== 9e. B no carro escurece pro letreiro ==")
    inc = open("build/fotos.inc").read()
    n_fotos = int(re.search(r"FOTOS_N\s*=\s*(\d+)", inc).group(1))
    banco1 = int(re.search(r"foto_banco_tab:\s*\.byte\s*(\d+)", inc).group(1))
    pal_carro = bytes(fo.bus.vram[0x3F00:0x3F20])
    fo.frame(BTN_START)
    for _ in range(6): fo.frame()
    check("START no carro nao faz nada", fo.bus.ram[sym["tela"]] == TELA_CARRO)
    fo.frame(BTN_B)
    for _ in range(14): fo.frame()
    meio = bytes(fo.bus.vram[0x3F00:0x3F20])
    check("a tela do carro escurece antes de trocar",
          fo.bus.ram[sym["tela"]] == TELA_CARRO and meio != pal_carro and
          all(m == 0x0F or (m >> 4) < (c >> 4) for m, c in zip(meio, pal_carro) if c != 0x0F),
          f"{pal_carro.hex()} -> {meio.hex()}")
    check("o som da rua abaixa junto", fo.bus.apu[0x0C] & 0x0F < amb_vol,
          fo.bus.apu[0x0C] & 0x0F)

    def ate_trocar(n, tela):
        """Espera a tela nova aparecer E clarear inteira (+1 quadro pro NMI)."""
        for _ in range(200):
            n.frame()
            if n.bus.ram[sym["tela"]] == tela and n.bus.ram[sym["fade_nivel"]] == 0:
                break
        n.frame()

    print("\n== 9e. O letreiro: \"DEPOIS DISSO, O RESTO E HISTORIA.\" ==")
    let_inc = open("build/letreiro.inc").read()
    let_n = int(re.search(r"LETREIRO_N\s*=\s*(\d+)", let_inc).group(1))
    let_som = [int(v) for v in re.search(r"^let_som: .byte (.*)$", let_inc, re.M).group(1).split(", ")]
    for _ in range(200):
        fo.frame()
        if fo.bus.ram[sym["tela"]] == TELA_LETREIRO:
            break
    check("depois do carro vem o letreiro (banco 0)",
          fo.bus.ram[sym["tela"]] == TELA_LETREIRO and fo.bus.banco == 0,
          f"tela={fo.bus.ram[sym['tela']]} banco={fo.bus.banco}")
    fo.frame()
    check("tela preta, nenhuma letra ainda", not any(fo.bus.vram[0x2000:0x23C0]))
    check("sem musica e sem a rua: silencio",
          fo.bus.ram[sym["musica_liga"]] == 0 and fo.bus.apu[0x08] == 0 and
          fo.bus.apu[0x0C] & 0x1F == 0x10)
    tecs, letras, cursor_xs = 0, [], set()
    for _ in range(1200):
        antes = fo.bus.ram[sym["let_pos"]]
        fo.bus.apu[0x0F] = 0                 # marca: so um "tec" NESTE quadro reescreve
        fo.frame(BTN_B if fo.frames % 7 == 0 else 0)   # B apressado nao pula nada
        if fo.bus.ram[sym["let_pos"]] != antes:
            letras.append(fo.bus.ram[sym["let_pos"]])
            tecs += fo.bus.apu[0x0C] == 0x01 and fo.bus.apu[0x0F] == 0x18
        if fo.bus.oam[0] < 0xEF:
            cursor_xs.add(fo.bus.oam[3])
        if fo.bus.ram[sym["let_fase"]] == 1:
            break
    fo.frame()
    check("as letras saem uma por uma, nessa ordem", letras == list(range(1, let_n + 1)),
          letras[:5])
    check("cada letra (menos espaco) faz o \"tec\" da maquina",
          tecs == sum(let_som), f"{tecs} de {sum(let_som)}")
    check("B no meio nao pulou pra foto (o texto sai inteiro)",
          fo.bus.ram[sym["tela"]] == TELA_LETREIRO and fo.bus.ram[sym["let_fase"]] == 1)
    check("no fim, a frase inteira na tela, tile por tile",
          bytes(fo.bus.vram[0x2000:0x23C0]) == open("build/letreiro.nam", "rb").read()[:960])
    check("o \"plim\" do fim (sino nos dois pulsos)",
          fo.bus.apu[0x00] == 0x84 and fo.bus.apu[0x04] == 0x83)
    check("o cursor anda junto com a frase", len(cursor_xs) > 8, len(cursor_xs))
    aceso = set()
    for _ in range(80):
        fo.frame()
        aceso.add(fo.bus.oam[0] < 0xEF)
    check("pronto, o cursor pisca", aceso == {True, False})
    check("e continua em silencio ate o B", fo.bus.ram[sym["musica_liga"]] == 0)
    fo.frame(BTN_START)
    for _ in range(6): fo.frame()
    check("START no letreiro nao faz nada", fo.bus.ram[sym["tela"]] == TELA_LETREIRO and
          fo.bus.ram[sym["let_fase"]] == 1)

    fo.frame(BTN_B)
    for _ in range(200):
        fo.frame()
        if fo.bus.ram[sym["tela"]] == TELA_FOTO:
            break
    check("B no letreiro leva pra primeira foto",
          fo.bus.ram[sym["tela"]] == TELA_FOTO and fo.bus.banco == banco1,
          f"tela={fo.bus.ram[sym['tela']]} banco={fo.bus.banco}")
    check("ela chega escura e vai clareando", fo.bus.ram[sym["fade_nivel"]] > 0)
    check("a musica estreia aqui: o refrao de \"Amanda\"",
          fo.bus.ram[sym["musica_liga"]] == 1 and
          (fo.bus.ram[sym["ch_base_lo"]] | (fo.bus.ram[sym["ch_base_hi"]] << 8)) == sym["musica1_canal0"])
    check("no andamento escrito (o minigame acelerado nao vaza)",
          fo.bus.ram[sym["musica_vel"]] == 16, fo.bus.ram[sym["musica_vel"]])
    fo.frame(BTN_B)                          # B no meio do fade nao pula a foto
    ate_trocar(fo, TELA_FOTO)
    check("B enquanto clareia nao pula a foto",
          fo.bus.ram[sym["foto_atual"]] == 0 and fo.bus.ram[sym["foto_saindo"]] == 0)
    nam = open("build/foto1.nam", "rb").read()
    check("a nametable e a da foto 1, tile por tile (atributos inclusos)",
          bytes(fo.bus.vram[0x2000:0x2400]) == nam)
    chr1 = open("build/chr_foto1.bin", "rb").read()
    check("os tiles da foto foram todos pra pattern table 1",
          bytes(fo.bus.vram[0x1000:0x1000 + len(chr1)]) == chr1)
    pal = open("build/foto.pal", "rb").read()
    check("depois de clarear, a paleta sepia e a de verdade",
          bytes(fo.bus.vram[0x3F00:0x3F20]) == pal[:32],
          bytes(fo.bus.vram[0x3F00:0x3F04]).hex())
    check("PPUADDR nao fica parado dentro da paleta",
          not (0x3F00 <= fo.bus.vaddr <= 0x3F1F), f"${fo.bus.vaddr:04X}")
    check("nenhum sprite do carro sobrou por cima da foto",
          all(fo.bus.oam[i] >= 0xEF for i in range(0, 256, 4)))
    fo.frame(BTN_START)
    for _ in range(6): fo.frame()
    check("START na foto nao faz nada", fo.bus.ram[sym["tela"]] == TELA_FOTO and
          fo.bus.ram[sym["foto_atual"]] == 0)
    for n in range(2, n_fotos + 1):
        fo.frame(BTN_B)
        for _ in range(10): fo.frame()
        ate_trocar(fo, TELA_FOTO)
        check(f"B leva pra foto {n}, com a nametable dela",
              fo.bus.ram[sym["tela"]] == TELA_FOTO and
              bytes(fo.bus.vram[0x2000:0x2400]) == open(f"build/foto{n}.nam", "rb").read())
    check("a musica nao reinicia entre as fotos (segue o refrao)",
          fo.bus.ram[sym["musica_liga"]] == 1)

    print("\n== 9f. A cena final ==")
    fim_inc = open("build/fim.inc").read()
    def const(nome):
        return int(re.search(rf"^{nome}\s*=\s*(\d+)", fim_inc, re.M).group(1))
    fo.frame(BTN_B)
    for _ in range(40):
        fo.frame()
        if fo.bus.ram[sym["tela"]] == TELA_FIM:
            break
    check(f"B depois da ultima foto ({n_fotos}) leva pra cena final",
          fo.bus.ram[sym["tela"]] == TELA_FIM and fo.bus.banco == 0,
          f"tela={fo.bus.ram[sym['tela']]} banco={fo.bus.banco}")
    fo.frame()
    check("o fundo e o da cena final, tile por tile",
          bytes(fo.bus.vram[0x2000:0x2400]) == open("build/fim.nam", "rb").read())
    def casal_visivel(n):
        return [n.bus.oam[k:k + 4] for k in range(0, 64, 4) if n.bus.oam[k] < 0xEF]
    check("no comeco so o Hulk esta na tela (o casal vem depois)",
          len(fo.sprites()) == 6 and not casal_visivel(fo), f"{len(fo.sprites())} sprites")
    hulk = [fo.bus.oam[i:i + 4] for i in range(64, 88, 4)]
    check("o Hulk usa a paleta 2 (preto, bege, cinza)", all(s[2] & 3 == 2 for s in hulk))
    check("e entra pela borda esquerda", fo.bus.ram[sym["hulk_x"]] < 8, fo.bus.ram[sym["hulk_x"]])
    check("o texto comeca apagado", fo.bus.vram[0x3F05] == 0x0F and fo.bus.vram[0x3F06] == 0x0F)
    FASE_HULK_ANDA, FASE_HULK_PARA, FASE_CASAL_ANDA, FASE_ACENDENDO, FASE_PARADOS = range(5)
    quadros, pulos, aus, tons, casal_antes = set(), set(), 0, set(), 0
    devolvido = []
    au_antes = 0
    while fo.bus.ram[sym["fim_fase"]] < FASE_CASAL_ANDA:
        fo.frame()
        if fo.bus.ram[sym["fim_fase"]] == FASE_HULK_ANDA:
            quadros.add(fo.bus.ram[sym["hulk_quadro"]])
        pulos.add(fo.bus.ram[sym["hulk_pulo"]])
        casal_antes += len(casal_visivel(fo))
        au = fo.bus.ram[sym["au_pulso"]]
        if au:
            tons.add(fo.bus.apu[0x06] | ((fo.bus.apu[0x07] & 7) << 8))
        elif au_antes:
            # o "au" acabou neste quadro: o pulso 2 tem que estar de volta
            # no periodo da nota que a musica esta tocando agora
            nota = fo.bus.ram[sym["ch_note"] + 1]
            esperado = fo.bus.read(sym["per_lo"] + nota) | ((fo.bus.read(sym["per_hi"] + nota) & 7) << 8)
            devolvido.append(nota == 0 or
                             (fo.bus.apu[0x06] | ((fo.bus.apu[0x07] & 7) << 8)) == esperado)
        aus += au and not au_antes
        au_antes = au
    check("o Hulk anda sozinho ate perto do meio e para",
          fo.bus.ram[sym["hulk_x"]] == const("FIM_HULK_X"), fo.bus.ram[sym["hulk_x"]])
    check("e o casal nem apareceu enquanto isso", casal_antes == 0, casal_antes)
    check("ele troca as patinhas andando", {0, 1} <= quadros, sorted(quadros))
    check("e chega latindo, de boca aberta andando (quadros 3 e 5)",
          {3, 5} <= quadros, sorted(quadros))
    check("varios latidos antes do casal chegar", aus >= 4, aus)
    check("ele pula a cada latido", max(pulos) >= 4, sorted(pulos))
    check("o \"au\" tem tom: o pulso 2 cai de agudo pra grave",
          tons and min(tons) < 130 and max(tons) > 200, sorted(tons))
    check("depois de cada \"au\", o pulso 2 volta pra nota da musica",
          devolvido and all(devolvido), devolvido)

    ys_casal, xs_casal, colunas = set(), set(), set()
    while fo.bus.ram[sym["fim_fase"]] == FASE_CASAL_ANDA:
        fo.frame()
        ys_casal.add((fo.bus.ram[sym["player_y"]], fo.bus.ram[sym["victor_y"]]))
        vis = casal_visivel(fo)
        xs_casal |= {c[3] for c in vis}
        colunas.add(len(vis) // 4)
    fo.frame()
    check("o casal entra pela direita, sem nenhuma coluna dando a volta pra esquerda",
          min(xs_casal) >= const("FIM_AMANDA_X"), sorted(xs_casal)[:4])
    check("uma coluna de cada vez vai entrando", colunas >= {0, 1, 2, 3, 4}, sorted(colunas))
    check("andando, os dois nao pulam",
          ys_casal == {(const("FIM_CHAO") - 32, const("FIM_CHAO") - 32)}, ys_casal)
    for _ in range(600):
        fo.frame()
        if fo.bus.ram[sym["fim_fase"]] == FASE_PARADOS:
            break
    fo.frame()
    check("Victor (8) + Amanda (8) + Hulk (6) na tela", len(fo.sprites()) == 22,
          f"{len(fo.sprites())} sprites")
    check("param do lado dele, cada um no seu lugar",
          (fo.bus.ram[sym["hulk_x"]], fo.bus.ram[sym["player_x"]], fo.bus.ram[sym["victor_x"]]) ==
          (const("FIM_HULK_X"), const("FIM_AMANDA_X"), const("FIM_VICTOR_X")))
    rampa = [re.search(rf"^fim_rampa{k}: .byte (.*)$", fim_inc, re.M).group(1).split(", ")[-1]
             for k in (1, 2)]
    check("\"FELIZ 2 ANOS DE NAMORO\" acende (as cores finais do texto)",
          bytes(fo.bus.vram[0x3F05:0x3F07]) == bytes(int(c[1:], 16) for c in rampa),
          bytes(fo.bus.vram[0x3F05:0x3F07]).hex())
    rabo, coracao, au, ys_ama, ys_vic = set(), False, False, set(), set()
    for _ in range(600):
        fo.frame()
        rabo.add(fo.bus.ram[sym["hulk_quadro"]])
        coracao |= fo.bus.oam[88] < 0xEF
        # o latido: ruido no modo curto, com envelope (sem volume constante)
        au |= fo.bus.apu[0x0E] & 0x80 and not fo.bus.apu[0x0C] & 0x10
        ys_ama.add(fo.bus.ram[sym["player_y"]])
        ys_vic.add(fo.bus.ram[sym["victor_y"]])
    check("parado, o Hulk abana o rabo", {0, 2} <= rabo, sorted(rabo))
    check("e late de boca aberta (quadros 3 e 4)", {3, 4} & rabo, sorted(rabo))
    check("o latido toca no ruido", au)
    chao = const("FIM_CHAO") - 32
    check("os dois dao um pulinho quando ele late",
          min(ys_ama) < chao and min(ys_vic) < chao and max(ys_ama) == max(ys_vic) == chao,
          f"{sorted(ys_ama)} {sorted(ys_vic)}")
    check("um coracaozinho sobe dos dois", coracao)
    check("a musica continua: o refrao", fo.bus.ram[sym["musica_liga"]] == 1 and
          (fo.bus.ram[sym["ch_base_lo"]] | (fo.bus.ram[sym["ch_base_hi"]] << 8)) == sym["musica1_canal0"])
    fim_oam = bytes(fo.bus.oam[0:88])
    for k in range(600):
        fo.frame([BTN_START, BTN_B, BTN_A, BTN_SEL, TODOS, 0][k % 6])
    check("o fim e pra sempre: nenhum botao sai da cena final",
          fo.bus.ram[sym["tela"]] == TELA_FIM and fo.bus.banco == 0)
    check("e ninguem sai do lugar (x dos 16 sprites dos dois)",
          bytes(fo.bus.oam[3:64:4]) == fim_oam[3:64:4])
    check("pilha inteira depois de tudo", 0xF0 <= fo.cpu.sp <= 0xFF, f"SP=${fo.cpu.sp:02X}")

    print("\n== 10. O minigame: derrota ao acumular ERROS_MAX ==")
    f = NES(ROM)
    entra_no_minigame(f, sym)
    f.bus.ram[sym["player_x"]] = 8                   # nunca sai daqui: erra tudo
    for _ in range(3000):
        f.frame()
        if f.bus.ram[sym["jogo_fase"]] == 2:
            break
    check(f"{ERROS_MAX} erros encerram a rodada", f.bus.ram[sym["jogo_fase"]] == 2,
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

    print("\n== 10c. Derrota: START nao desiste (nao ha volta pro menu) ==")
    g = NES(ROM)
    entra_no_minigame(g, sym)
    g.bus.ram[sym["player_x"]] = 8
    for _ in range(3000):
        g.frame()
        if g.bus.ram[sym["jogo_fase"]] == 2:
            break
    check(f"{ERROS_MAX} erros de novo, numa instancia separada", g.bus.ram[sym["jogo_fase"]] == 2)
    g.frame(BTN_START)
    for _ in range(6): g.frame()
    check("START na derrota nao faz nada",
          g.bus.ram[sym["tela"]] == 2 and g.bus.ram[sym["jogo_fase"]] == 2 and g.bus.banco == 2)

    print("\n== 11. A musica troca de estado junto com a tela ==")
    m = NES(ROM)
    for _ in range(12): m.frame()
    check("menu em silencio", m.bus.apu[0x00] & 0x0F == 0 and
          m.bus.apu[0x04] & 0x0F == 0)
    m.frame(BTN_START)                      # entra na pizzaria: a musica comeca
    for _ in range(70):                     # o respiro pro plin, antes da cena carregar
        m.frame()
    p1 = m.bus.apu[0x02] | ((m.bus.apu[0x03] & 7) << 8)
    mudou = False
    for _ in range(40):
        m.frame()
        p = m.bus.apu[0x02] | ((m.bus.apu[0x03] & 7) << 8)
        if p != p1:
            mudou = True
    check("canais ainda ligados", m.bus.apu[0x15] & 0x0F == 0x0F)
    check("as notas continuam mudando na pizzaria", mudou)

    print("\n== 12. Estabilidade ==")
    # 'nes' esta na pizzaria desde a secao 3: aperta de tudo por um tempo
    for k in range(600):
        nes.frame([BTN_START, BTN_RIGHT, BTN_SEL, BTN_LEFT, BTN_A, 0][k % 6])
    check("nenhum botao tira da pizzaria", nes.bus.ram[sym["tela"]] == 1)
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
