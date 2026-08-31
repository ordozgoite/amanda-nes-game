# CLAUDE.md

Jogo de NES em assembly 6502 (cc65). Presente de dois anos de namoro: a Amanda
anda pela pizzaria onde os dois se conheceram e conversa com o Victor.

## Comandos

```bash
make            # gera jogo.nes na raiz
make test       # test_jogo.py + test_musica.py -- rode SEMPRE apos mexer
make capturas   # telas em build/
make audio      # musica e fala em .wav, pra conferir de ouvido
make rodar      # abre no fceux
```

## A regra que organiza o projeto

**Nada de conteudo escrito a mao no assembly.** Graficos, musica e texto sao
gerados por scripts Python que cospem `.bin` e `.inc`; o `src/jogo.s` so
consome. Pra mudar um desenho, mexa no gerador, nunca em bytes soltos.

- graficos = arte ASCII em `tools/make_*.py`
- musica = nomes de nota em `tools/make_song.py`
- texto do balao = string em `tools/make_scene.py` (`FALA`), convertida em
  numeros de tile automaticamente

## Verificacao

Nao existe "compilou, entao funciona". `tools/nesemu.py` e um emulador 6502
com PPU/APU/mapper 2 que roda a ROM de verdade; os testes leem memoria de
video, OAM e registradores do APU. `tools/screenshot.py` desenha o quadro em
PNG — **olhe a imagem**, varios bugs so aparecem assim.

Ao mexer em qualquer coisa, rode `make test` e gere uma captura.

## Convencoes

- Comentarios e nomes em portugues, **sem acento** dentro de `.s` e `.py`
  (o ca65 e a fonte do jogo nao lidam com acentuacao). Texto pra pessoa —
  README, `.md` — vai acentuado normal.
- Comentario explica *por que*, nao *o que*. Varias armadilhas do NES so fazem
  sentido documentadas no ponto onde mordem.
- Constantes compartilhadas entre Python e assembly sao **emitidas** pelo
  gerador (ex.: `PAGINAS_CENA` em `build/dialogo.inc`), nunca duplicadas na
  mao — ja causou bug de tela preta.

## Armadilhas ja pagas (nao redescubra)

- **Atributo de cor cobre 16x16 pixels.** Qualquer coisa com paleta propria
  precisa cair em bloco alinhado, senao a cor vaza pro vizinho.
- **So escreva no PPU durante o vblank**, dentro do NMI, e um pedacinho por
  quadro. O balao desenha uma linha por vez; o texto, uma letra por vez.
- **UNROM tem conflito de barramento.** Troque de banco so por `troca_banco`,
  que grava numa tabela onde o conteudo ja e o numero do banco.
- **Depois de escrever paleta**, tire o PPUADDR de dentro dela, senao aquela
  cor vira o fundo da tela toda.
- **O DMA de OAM tem que acontecer antes de acender a tela** (`liga_tela`),
  senao o console real mostra um quadro de sprites aleatorios. Emulador nao
  denuncia isso.
- **Cada canal de musica roda o proprio laco.** Os tres precisam somar a mesma
  duracao total, ou vao se desencontrando. Ha um `assert` em `make_song.py`.
- **O tom de pele ($36) e igual ao chao da pizzaria.** Perna a mostra fica
  invisivel; por isso a Amanda usa vestido ate a canela, sem pele exposta
  abaixo do tronco.
- **A CHR da cena e enviada em paginas.** O numero vem de `PAGINAS_CENA`; se
  alguem escrever na mao e a cena crescer, os tiles do fim somem.

## Estado atual

Pronto: tela de titulo, musica em loop, cenario da pizzaria, Amanda jogavel,
Victor sentado, aviso de interacao, balao de fala letra a letra com tique e
boca mexendo.

Falta: a resposta dela, outras memorias (cenarios), a melodia do refrao (que
depende de fonte externa — veja a secao Musica do README) e o retrato final.
