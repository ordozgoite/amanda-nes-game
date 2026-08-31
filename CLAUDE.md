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
- **A macro `PPU_ADDR` usa o registrador A.** Se voce calcula um valor em A
  (ex.: o tile de um digito) e so DEPOIS chama `PPU_ADDR`, ela reescreve A
  com o endereco e o valor calculado se perde. Guarde em Y ou na pilha antes
  de chamar `PPU_ADDR`, e restaure depois -- foi assim que o digito de erros
  do placar saiu errado da primeira vez.
- **O placar (ou qualquer escrita da NMI) leva um quadro pra aparecer.** O
  laco principal muda o estado (pontos, fase) num quadro; so a NMI seguinte
  desenha. Testes que leem a tela logo depois de detectar a mudanca no RAM
  precisam esperar mais um `frame()`, senao veem o valor antigo.
- **`ADC` pode estourar 255 e o `CMP` seguinte nao percebe.** No clamp do x
  da pizza, `base + delta` as vezes passava de 255, o acumulador dava a
  volta, e o `cmp` de teto comparava o valor ja embrulhado -- que parecia
  pequeno, entao passava no teste. Depois de somar, cheque o carry (`bcs`)
  antes do `cmp`: se estourou 255, ja passou de qualquer teto menor.
- **Trocar de musica no meio do jogo (`troca_musica`) mexe em `ch_ptr_lo/hi`
  em duas escritas separadas.** Se o NMI disparar entre elas, a musica le um
  ponteiro Frankenstein (byte baixo de uma nota, alto de outra) e ou trava
  ou toca lixo. So chame `troca_musica` entre `desliga_tela`/`liga_tela`:
  com a tela apagada o NMI nem dispara (`desliga_tela` zera `PPUCTRL`), entao
  a troca fica atomica de graca.
- **Testar a troca de musica pelo valor do periodo e enganoso.** Uma nota
  pode segurar o mesmo periodo por dezenas de quadros (a primeira do refrao
  aguenta 60), entao "os proximos 2 quadros batem" pode travar no MEIO da
  nota, nao no comeco dela -- e a partir dali tudo desalinha. So vale
  comparar o laco inteiro contra o esperado (ver `test_musica.py`).

## Estado atual

Pronto: tela de titulo, musica em loop, cenario da pizzaria, dialogo completo
(incluindo a resposta dela), minigame das pizzas caindo (arcade rejogavel,
com placar, derrota em `ERROS_MAX` erros e uma comemoracao ao alcancar
`PONTOS_MIN` pontos).

Falta: o conteudo de verdade da comemoracao -- hoje e so um placeholder (o
jogo congela um instante e volta a jogar, sem imagem nem texto; ver
`atualiza_jogo` em `src/jogo.s`, estado `jogo_fase = 1`). Tambem faltam
outras memorias (cenarios) e o retrato final -- que pode virar o conteudo
real dessa comemoracao quando estiver decidido.
