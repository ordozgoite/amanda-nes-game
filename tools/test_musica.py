#!/usr/bin/env python3
"""
Confere a engine de musica no nivel dos registradores.

Em vez de tentar ouvir, o teste le o periodo que o codigo escreveu no APU
a cada quadro e compara com a nota que deveria estar tocando segundo a
partitura. Se a engine errar uma nota ou a duracao, aparece aqui.
"""
import sys
sys.path.insert(0, "tools")
from nesemu import NES, load_labels, check, FAILS
from make_song import MUSICAS, indice, frequencia, CPU_HZ, PLIN
from test_jogo import entra_no_minigame, BTN_START

ROM = "jogo.nes"

def periodos_esperados(canais):
    """A sequencia de periodos que cada canal dessa musica deveria produzir,
    quadro a quadro.

    Numa pausa (indice 0) a engine so zera o volume -- @pausa em jogo.s nao
    escreve $4002/$4003 (nem tri_lo/tri_hi), entao o periodo continua sendo
    o da ultima nota tocada."""
    trilhas = []
    for c, notas in enumerate(canais):
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

def periodo_nota(nome):
    f = frequencia(indice(nome))
    return max(2, min(2047, round(CPU_HZ / (16.0 * f)) - 1))

def lidos(bus):
    p1 = bus.apu[0x02] | ((bus.apu[0x03] & 7) << 8)
    p2 = bus.apu[0x06] | ((bus.apu[0x07] & 7) << 8)
    tr = bus.apu[0x0A] | ((bus.apu[0x0B] & 7) << 8)
    return [p1, p2, tr]

def acha_desloc(obs0, esperado0, janela):
    """Deslocamento em que obs0[d : d+len(esperado0)] bate com o laco
    INTEIRO esperado -- nao basta comparar so os 2 primeiros quadros: uma
    nota pode segurar o mesmo periodo por dezenas de quadros (a 1a do
    refrao aguenta 60), entao um casamento de 2 quadros pode estar no MEIO
    dela, nao no comeco. O filtro pelo 1o valor so evita comparar o laco
    inteiro em toda posicao -- e so um atalho, a prova real e a fatia
    inteira batendo."""
    laco = len(esperado0)
    alvo = esperado0[0]
    for d in range(janela):
        if obs0[d] == alvo and obs0[d:d + laco] == esperado0:
            return d
    return None

def main():
    sym = load_labels("build/jogo-labels.txt")

    print("== 1. Nasce em silencio -- o menu nao toca musica ==")
    nes = NES(ROM)
    for _ in range(30):
        nes.frame()
    check("canais habilitados em $4015", nes.bus.apu[0x15] & 0x0F == 0x0F,
          f"${nes.bus.apu[0x15]:02X}")
    check("sweep desligado nas duas quadradas",
          nes.bus.apu[0x01] == 0 and nes.bus.apu[0x05] == 0)
    check("quadrada 1 muda", nes.bus.apu[0x00] & 0x0F == 0,
          f"volume ${nes.bus.apu[0x00] & 0x0F:X}")
    check("quadrada 2 muda", nes.bus.apu[0x04] & 0x0F == 0,
          f"volume ${nes.bus.apu[0x04] & 0x0F:X}")
    check("triangulo mudo", nes.bus.apu[0x08] == 0, f"${nes.bus.apu[0x08]:02X}")

    print("\n== 2. START toca o \"plin\" ==")
    nes.frame(BTN_START)
    reg4004 = nes.bus.apu[0x04]
    check("pulso 2 com volume constante no maximo", reg4004 & 0x1F == 0x1F,
          f"${reg4004:02X}")
    check("sem halt (o contador de duracao decai sozinho)",
          reg4004 & 0x20 == 0, f"${reg4004:02X}")
    lido = nes.bus.apu[0x06] | ((nes.bus.apu[0x07] & 7) << 8)
    esperado_plin = periodo_nota(PLIN)
    check("toca a nota certa", lido == esperado_plin,
          f"leu {lido}, esperava {esperado_plin} ({PLIN})")

    print("\n== 3. A pizzaria bate com a partitura ==")
    # a partir daqui a musica troca em algum ponto dentro do carregamento da
    # cena, sem hora certa -- por isso a busca cobre o laco inteiro (ver
    # acha_desloc) em vez de assumir que ja comeca no 1o quadro capturado.
    esperado_cena = periodos_esperados(MUSICAS[0])
    laco_cena = len(esperado_cena[0])
    JANELA_CENA = laco_cena

    obs = [[], [], []]
    for _ in range(JANELA_CENA + laco_cena * 2):
        nes.frame()
        v = lidos(nes.bus)
        for c in range(3):
            obs[c].append(v[c])

    desloc = acha_desloc(obs[0], esperado_cena[0], JANELA_CENA)
    check("a musica comeca a tocar", desloc is not None,
          "" if desloc is not None else
          "nenhum deslocamento faz a introducao bater")

    if desloc is not None:
        nomes = ("arpejo (quadrada 1)", "harmonia (quadrada 2)", "baixo (triangulo)")
        for c in range(3):
            erros = 0
            primeiro = None
            for i in range(laco_cena):
                if obs[c][desloc + i] != esperado_cena[c][i]:
                    erros += 1
                    if primeiro is None:
                        primeiro = (i, obs[c][desloc + i], esperado_cena[c][i])
            det = "" if not erros else f"1o erro no quadro {primeiro[0]}: " \
                                       f"leu {primeiro[1]}, esperava {primeiro[2]}"
            check(f"{nomes[c]}: {laco_cena} quadros conferem", erros == 0, det)

        print("\n== 4. O laco fecha e repete ==")
        volta = obs[0][desloc + laco_cena:desloc + laco_cena * 2]
        check("segunda passada igual a primeira", volta == esperado_cena[0],
              f"{sum(1 for a, b in zip(volta, esperado_cena[0]) if a != b)} diferencas")

    print("\n== 5. Envelope de volume ==")
    dur1 = MUSICAS[0][0][0][1]              # duracao da 1a nota, tirada da partitura
    prox_nome = MUSICAS[0][0][1][0]         # o que vem depois -- nota ou pausa "P"
    nes2 = NES(ROM)
    for _ in range(30):                     # a mesma folga da secao 1 antes do 1o botao
        nes2.frame()
    nes2.frame(BTN_START)
    esperado_1a_nota = periodos_esperados(MUSICAS[0])[0][0]
    JANELA_ENV = laco_cena
    vols, periodos = [], []
    for _ in range(JANELA_ENV + dur1 * 2 + 5):
        nes2.frame()
        vols.append(nes2.bus.apu[0x00] & 0x0F)
        periodos.append(lidos(nes2.bus)[0])
    desloc2 = next((d for d in range(JANELA_ENV) if periodos[d] == esperado_1a_nota and
                    periodos[d:d + dur1] == [esperado_1a_nota] * dur1), None)
    check("achou o comeco da 1a nota pra medir o envelope", desloc2 is not None)

    if desloc2 is not None:
        vols_nota = vols[desloc2:desloc2 + dur1]
        check("volume cai dentro da nota", vols_nota[0] > vols_nota[-1],
              " ".join(str(v) for v in vols_nota))
        # a engine para de decair em 4 (o 'cmp #$05' do aplica_volume): a
        # nota perde forca mas nao some, que e o que faz soar tocada e nao
        # percutida
        check("volume nao chega a zero (sustenta)", min(vols_nota) >= 4,
              f"minimo {min(vols_nota)}")
        prox_vol = vols[desloc2 + dur1]
        if prox_nome == "P":
            check("nota seguinte silencia (pausa)", prox_vol == 0x00,
                  f"volume {prox_vol}")
        else:
            check("nota seguinte reataca no volume cheio", prox_vol == 0x0F,
                  f"volume {prox_vol}")
        check("bit de volume constante ligado", nes2.bus.apu[0x00] & 0x10 != 0)
        check("contador de duracao segurado", nes2.bus.apu[0x00] & 0x20 != 0)

    print("\n== 6. O minigame troca pra musica de \"Amanda\" ==")
    # carrega_jogo chama troca_musica(1); carrega_menu chama musica_para e
    # carrega_cena chama troca_musica(0) com o mesmo mecanismo, entao testar
    # uma direcao (aqui) cobre a troca em si.
    esperado_jogo = periodos_esperados(MUSICAS[1])
    laco_jogo = len(esperado_jogo[0])
    JANELA_JOGO = laco_jogo

    nes3 = NES(ROM)
    entra_no_minigame(nes3, sym)
    obs_jogo = [[], [], []]
    for _ in range(JANELA_JOGO + laco_jogo + 8):
        nes3.frame()
        v = lidos(nes3.bus)
        for c in range(3):
            obs_jogo[c].append(v[c])

    desloc_jogo = acha_desloc(obs_jogo[0], esperado_jogo[0], JANELA_JOGO)
    check("a musica troca ao entrar no minigame", desloc_jogo is not None,
          "" if desloc_jogo is not None else
          "nenhum deslocamento faz o refrao bater")

    if desloc_jogo is not None:
        for c in range(3):
            erros = 0
            primeiro = None
            for i in range(laco_jogo):
                if obs_jogo[c][desloc_jogo + i] != esperado_jogo[c][i]:
                    erros += 1
                    if primeiro is None:
                        primeiro = (i, obs_jogo[c][desloc_jogo + i], esperado_jogo[c][i])
            det = "" if not erros else f"1o erro no quadro {primeiro[0]}: " \
                                       f"leu {primeiro[1]}, esperava {primeiro[2]}"
            check(f"canal {c} (refrao): {laco_jogo} quadros conferem", erros == 0, det)

    print("\n== 7. A tela continua viva junto com a musica ==")
    # 'nes' ja saiu do menu (ficou parado na pizzaria desde a secao 3, com a
    # introducao tocando ha centenas de quadros) -- o que interessa aqui e
    # que a tela sobrevive ao motor de musica rodando pesado no NMI, entao
    # confere a cena, nao mais o menu.
    check("continua na pizzaria", nes.bus.ram[sym["tela"]] == 1,
          f"tela={nes.bus.ram[sym['tela']]}")
    check("Amanda e o Victor ainda na tela", len(nes.sprites()) >= 8,
          f"{len(nes.sprites())} sprites")
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
