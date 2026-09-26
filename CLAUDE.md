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
- **Limitar so um lado de uma faixa nao limita a faixa.** O salto da pizza
  (`SALTO_MAX`) so limitava a base (o minimo) e somava um deslocamento fixo
  por cima; perto da borda a base ficava presa em `ANDA_MIN`, mas o
  deslocamento continuava indo ate o mesmo teto de sempre -- o salto real
  passava longe do prometido. Precisa calcular base E topo (os dois
  clampados na tela) antes de sortear, e sortear dentro do tamanho real
  dessa faixa (`topo - base`), nao um deslocamento fixo.
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
- **Sair de um estado do NMI pra outro sistema precisa zerar a variavel de
  estado, nao so setar a do sistema novo.** A animacao de sentar (depois de
  `PARTE_SENTAR`) saia de `@fechando` pra ligar `senta_fase` sem zerar
  `dialogo` (que ainda valia 4). Resultado: `passo_dialogo` reentrava em
  `@fechando` TODO NMI, e essa reentrada forcava `senta_fase` de volta pra 1
  a cada quadro -- a animacao nunca passava do primeiro passo (andar ate o
  x), porque o proprio NMI desfazia o progresso do quadro anterior antes do
  laco principal conseguir avancar pra fase seguinte. Sintoma enganoso: o
  valor lido entre quadros parecia estavel (sempre a mesma fase), porque a
  leitura via teste so via o resultado JA sobrescrito pelo NMI seguinte --
  so apareceu de verdade imprimindo o estado quadro a quadro.
- **Um personagem com duas poses que usam numeros diferentes de sprites da
  OAM precisa esconder a sobra na mao ao trocar pra pose menor.** O Victor
  em pe usa 8 sprites (cabeca+torso+pernas, ver `monta_oam_victor_empe`);
  sentado usa so 6 (a mesa esconde as pernas, ver `oam_victor`). Quando ele
  senta, `oam_victor` passa a rodar no lugar da rotina de 8 sprites -- mas
  se ninguem mexer explicitamente nos 2 sprites que sobraram (14 e 15), eles
  ficam presos pra sempre com o ultimo quadro da perna "em pe", porque
  nenhuma rotina volta a escrever ali. `oam_victor` esconde os dois (Y=$FF)
  no fim, mesmo sem usa-los.
- **Uma flag calculada so em UM caminho do laco fica com o valor antigo
  quando esse caminho e pulado por uma maquina de estado.** `calcula_perto`
  (e portanto `perto`) so roda dentro do ramo "andando livre" de
  `atualiza_cena`; enquanto uma animacao de sentar esta em andamento, esse
  ramo nem executa. Resultado: `perto` continuava valendo 1 (do instante em
  que o B foi apertado) durante toda a caminhada dela ate a cadeira, e o
  aviso "B" ficava flutuando bobo sobre a cena. Precisou zerar `perto` na
  mao no momento de disparar a animacao, ja que ninguem mais ia recalcula-lo
  ate ela terminar.
- **Uma rotina que escreve num endereco FIXO da nametable (HUD, placar)
  nao sabe qual "tela logica" esta ativa.** O minigame passou a ter quatro
  nametables diferentes (jogando/intro/vitoria/derrota), todas carregadas
  na mesma janela de memoria -- mas `desenha_hud` continuava rodando toda
  vez que `placar_sujo` pedia, sem checar `jogo_fase`, e escrevia a barra/
  vidas por cima da tela de intro (que nao tem esse layout ali). Rotinas
  assim precisam checar explicitamente se a tela onde elas escrevem e a
  que esta ativa.
- **Estado de gameplay (pizzas caindo, sprite do personagem) nao se limpa
  sozinho quando a "tela logica" muda por baixo dele.** `atualiza_oam_jogo`
  desenhava `pz_ativa`/pizzas incondicionalmente; ao vencer ou perder, uma
  pizza que ainda estivesse caindo continuava sendo desenhada, congelada,
  por cima da tela de vitoria/derrota -- um sprite fantasma flutuando onde
  nao devia. `checa_vitoria`/`checa_derrota` agora zeram `pz_ativa`
  explicitamente ao trocar de fase.
- **`paleta()` (em `make_scene.py`/`make_jogo.py`) espera coordenadas em
  TILES, nao em pixels.** Chamar `paleta(x0, y0, ...)` com x0/y0 em pixel
  (ex.: a posicao de um retrato desenhado com `px[y][x]=`) marca o bloco de
  atributo errado -- a paleta acaba caindo numa regiao qualquer da tela, e
  o desenho pega a cor de fundo errada (virou tudo roxo/azul do ceu, nao a
  cor de pele/cabelo pretendida). Sempre dividir por 8 antes de chamar.
- **Sorriso e choro nao sao so "cantos pra cima/baixo" -- e o CENTRO da boca
  que inverte em relacao aos cantos.** Sorriso: cantos mais pra cima (indice
  de linha menor) que o centro. Choro/frown: o oposto, cantos mais pra baixo
  (indice maior) que o centro. `RETRATO_TRISTE` nasceu com as duas linhas
  trocadas -- lia como sorriso, nao choro -- e so foi pego numa re-derivacao
  visual cuidadosa, nao por teste (nenhum teste automatizado confere
  "expressao facial"). `RETRATO_FELIZ` reaproveita o padrao ORIGINAL
  (pre-troca) de `RETRATO_TRISTE`, que ja era um sorriso por acidente.
- **Rolagem horizontal de hardware precisa de espelhamento vertical no
  cartucho** (`$2000`/`$2400` viram duas telas DIFERENTES, lado a lado --
  exatamente o que a rolagem horizontal precisa). O fundo tem que ser
  desenhado como UMA imagem continua e periodica (521px = duas nametables
  coladas); todo elemento que se repete precisa ter um periodo que divida
  512 certinho (ver `make_carro.py`: predios a cada 64px, tracejado da rua
  a cada 32px), senao a costura entre o fim e o comeco do loop fica visivel.
- **O emulador (`tools/nesemu.py`) e o `tools/screenshot.py` nao sabiam nada
  sobre `PPUSCROLL`** (a escrita em `$2005` so alternava o latch, o valor
  em si era descartado, e o render sempre lia a partir de `$2000` fixo) --
  porque nenhuma cena anterior tinha usado rolagem. Qualquer cena nova que
  use um recurso de PPU inedito no projeto pode esbarrar num buraco assim
  na ferramentagem, nao so no jogo; "olhe a imagem" so funciona se a
  ferramenta que desenha a imagem souber renderizar o recurso novo.
- **Um personagem sentado dentro de outro sprite maior (o carro) ainda
  esbarra no limite de 8 sprites por linha de varredura.** O carro (5 tiles
  x 4 tiles = 20 sprites de lataria + 2 cabecas) foi desenhado com esse
  limite em mente desde o inicio -- nao da pra simplesmente aumentar a
  escala de uma arte ja pronta (o mockup em PIL) sem recontar quantos
  sprites caem em cada linha.
- **O limite de 8 sprites por linha de varredura e sobre LARGURA, nao
  altura.** Cada linha de varredura so conta os tiles cuja COLUNA passa por
  ali -- um sprite empilhado bem alto nao soma nada a mais nas linhas onde
  nenhum outro sprite daquela coluna esta. Foi assim que o carro pode ficar
  bem mais alto (8 linhas de tile) sem estourar o limite: a grade inteira
  ja nasce com no maximo 8 colunas de largura, entao QUALQUER linha
  individual automaticamente respeita o teto, nao importa quantas linhas
  de tile existam no total (so o total geral de sprites em tela, 64, e que
  limita a altura).
- **Silhueta que nao e um retangulo preenchido precisa de uma tabela de
  posicao, nao de um loop fixo `col*ALTURA+linha`.** O carro tem canto
  arredondado (teto) e celula vazia (vao embaixo do parachoque) -- um loop
  uniforme desenharia sprite em cima de pixel transparente do mesmo jeito,
  gastando OAM a toa. `make_carro.py` varre a grade inteira, PULA celula
  100% transparente, e emite tres tabelas paralelas (offset x, offset y,
  indice do tile, paleta) que `monta_oam_carro` so percorre -- e tambem
  como retrato (paleta 1 ou 2, uma pra cada personagem) e lataria (paleta
  0) convivem na MESMA tabela: a paleta e so mais uma coluna por entrada,
  nao uma camada extra de sprite por cima.
- **O orcamento de OAM (64 sprites) e da TELA INTEIRA, nao por objeto --
  e estourar nao avisa, so faz sprite sumir no hardware real.** Ao
  aumentar os retratos do carro pra mostrar mais detalhe (cabelo, barba,
  ombro), a grade foi de ~50 pra 68 celulas sem nenhum aviso do
  `ca65`/`ld65` -- so os testes e a inspecao visual pegariam isso, e olhando
  so a imagem (que nao simula o limite) nem isso. Baixar de 68 pra <64
  exigiu cortar uma fileira inteira (o "teto" dedicado, redundante com o
  cabelo dos dois que ja fecha aquela borda), nao so aparar canto.
- **Colar dois desenhos de personagem que usam PALETAS ORIGINAIS
  diferentes (cabeca vs. torso, ou um personagem vs. outro) numa unica
  celula/paleta nova exige reconferir o que cada indice de cor significava
  em cada um.** `VICTOR` (paleta cabeca: 1=cabelo,2=pele,3=cinza) e
  `AMANDA_CABECA` (paleta cabeca: 1=cabelo,2=pele,3=laco-rosa) coincidem
  nos indices 1/2 mas NAO no 3 -- por isso viraram DUAS paletas novas no
  carro (uma pra cada), nao uma paleta "de cabeca" generica reaproveitada
  pros dois como na primeira versao. Tambem por isso o vidro da janela nao
  pode ser pintado de azul preenchendo a celula antes de carimbar o
  retrato: aquela celula agora e a paleta do Victor ou da Amanda, sem slot
  de azul nenhum -- o respiro em volta do retrato fica transparente (o
  fundo da cena aparece), nao pintado.
- **Carimbar duas artes lado a lado numa grade onde CADA METADE tem uma
  paleta diferente exige alinhar o carimbo EXATAMENTE na borda da coluna,
  nao "por perto".** Um recuo de 2px (achando que ia sobrar um respiro
  bonito entre os dois retratos) fez o retrato do Victor vazar 2px pra
  dentro das colunas da paleta da Amanda (saindo com a cor errada ali) e
  empurrou o retrato dela pra fora da borda direita da grade inteira --
  index out of range na hora de gerar. Sem sobra: harmonizar arte alinhada
  a pixel exato quando ela precisa caber num numero fixo de colunas.
- **Cor "preta" de sprite (`$0F`) sobre fundo TAMBEM preto ($0F) some --
  mas cinza-escuro ($00) sobre um cinza-claro DIFERENTE tambem some, so que
  ao contrario.** O trim do carro (roda, parachoque) e preto ($0F) igual a
  rua, entao ficava invisivel ali -- trocado pra $00 (cinza-escuro) resol-
  veu contra a rua, mas $00 e EXATAMENTE a cor que a calcada ja usava,
  entao o teto/pilar do carro (que fica bem na faixa de y da calcada)
  sumiu ali por sua vez. A calcada teve que subir pra um cinza mais claro
  ($10) pra abrir distancia dos DOIS lados -- nao basta checar contra um
  unico vizinho, checar contra TODOS os fundos que aquele elemento pode
  sobrepor.

- **`copy.deepcopy` num `NES` do emulador gera um console zumbi.** A
  tabela de opcodes da CPU sao closures presas a CPU original, entao a
  copia executa instrucoes no console antigo e trava com "opcode nao
  implementado". Pra testar dois caminhos a partir do mesmo ponto (ex.:
  B e START no carro), use `nes.copia()`, que recria a CPU por cima de uma
  copia do barramento.
- **Foto colorida de verdade nao cabe no NES.** O atributo de 16x16 quebra
  a pele do rosto em blocos, e nenhuma escolha de paleta salvou (testado).
  As fotos sao sepia pontilhadas, com UMA paleta so, e os tiles ainda
  precisam ser agrupados (k-medoides em `make_foto.py`), porque o
  pontilhado quase nunca repete e a foto sozinha passa de 256 tiles.

- **Caixa de fala numa tela que rola precisa de tela dividida.** O balao
  e escrito na nametable, entao rolaria junto com os predios. No carro, o
  topo (ceu) fica parado e so o resto rola: o NMI deixa a rolagem em (0,0)
  e `divide_tela_carro` espera o "sprite 0 hit" -- o sprite 0 e um pixel
  branco em cima de uma estrela fixa (`SPR0_X/SPR0_Y`, `make_carro.py`) --
  pra trocar a rolagem no meio do quadro. As duas esperas tem limite de
  tempo: sem sprite 0 encostando em nada, o NMI travaria pra sempre. O
  carro, por isso, comeca no sprite 1 da OAM.
- **O emulador nao tinha "sprite 0 hit" nem rolagem por linha** (mesma
  licao do `PPUSCROLL`): `nesemu.py` agora calcula o ciclo do hit no comeco
  de cada quadro e anota em `linhas_scroll` cada troca de rolagem feita no
  meio dele; `screenshot.py` desenha linha a linha a partir disso. O tempo
  e aproximado (240 linhas em 20000 ciclos, nao 113,67 por linha como no
  console) -- serve pra ordem das coisas, nao pra contar ciclo.
- **A CHR da pizzaria esta cheia (256), a do carro nao.** Os acentos da
  conversa do carro (Ã, É) so existem la, logo abaixo de `DLG_BASE`
  (`ACENTOS_CARRO` em `make_scene.py`); o resto da fonte e da moldura usa
  os MESMOS numeros de tile nas duas cenas, entao o texto gerado serve pras
  duas sem traducao.

## Estado atual

Pronto: tela de titulo (em silencio -- START toca um "plin" e leva pra
pizzaria, que so ai comeca a musica), cenario da pizzaria, dialogo completo
(incluindo a resposta dela, caixa do Victor mais a esquerda e da Amanda mais
a direita, mesma altura pros dois -- acima dos sprites, sem colidir).

Sentar reversal: a Amanda que chega andando e convida ELE a sentar do lado
dela -- ela se alinha em pe primeiro, o dialogo comeca com os dois de pe,
ela senta sozinha bem antes de falar "vem, senta aqui do meu lado"
(`PARTE_SENTAR`), e so depois disso o Victor anda ate a cadeira e senta
tambem (`atualiza_senta`/`atualiza_senta_victor` em `src/jogo.s`). A faixa
de aproximacao pro aviso "B" comeca na borda da mesa (`PERTO_MIN`), nao
precisa mais chegar coladinho nele.

Minigame das pizzas caindo, com fluxo completo:
- **intro** (`jogo_fase = 3`): "PEGUE N PIZZAS!" antes da primeira pizza cair,
  ate apertar B.
- **jogando** (`fase = 0`): HUD visual, nao numerico -- barra de `PONTOS_MIN`
  segmentos e `ERROS_MAX` coracoezinhos, nas linhas 2-3 (fora da faixa que
  overscan de TV de tubo corta).
- **vitoria** (`fase = 1`): retrato grande e feliz (mesma tecnica de "zoom"
  da derrota, sorriso em vez de choro -- ver `RETRATO_FELIZ`) com uma
  fraseszinha feliz de 4 notas (G3-B3-D4-G4, uma vez so; ver
  `FELIZ`/`toca_feliz1..4`), pausando o refrao do minigame do mesmo jeito
  que a derrota pausa. "PARABENS! APERTE B PRA CONTINUAR" -- B leva pra
  cena do carro (`carrega_carro`), nao volta mais a jogar.
- **derrota** (`fase = 2`): sprite dela some da tela, so fica um retrato
  grande e triste (fundo, nao sprite -- "zoom" que o sprite normal nao
  comporta) com uma fraseszinha triste de 4 notas (B3-G3-E3-D3, uma vez so;
  ver `TRISTE`/`toca_triste1..4`). B reseta e tenta de novo NA HORA, sem
  voltar pro menu (perderia o progresso da conversa); START ainda desiste
  pro menu se ela quiser.

**Cena do carro** (`tela = TELA_CARRO`, banco `BANCO_CARRO`, ver
`tools/make_carro.py`/`carrega_carro` em `src/jogo.s`): os dois indo pra
casa depois do encontro. Por enquanto so o visual -- o Fiat Argo branco
do Victor DE VERDADE (foto de referencia dele), de PERFIL lateral (nao
mais de frente com os dois visiveis pelo vidro -- pedido dele: vidro
fechado/fume, sem gente aparecendo). Isso simplificou bastante: uma unica
paleta de sprite agora (trim escuro/branco/ambar), sem precisar de uma
paleta por personagem. 64x48px (a largura, 8 sprites = 8 colunas, ainda
esbarra no MESMO teto fisico do PPU de sempre -- 8 e o maximo que uma
linha de varredura do NES desenha -- mas agora ela representa o
COMPRIMENTO do carro, nao a largura de uma carroceria vista de frente,
entao rende muito mais sensacao de "carro comprido" pro mesmo orcamento
de pixels). Parado na tela (sprite), na faixa de baixo da pista -- a mais
perto da camera --, ceu de meia-noite estrelado e predios/calcada/rua
deslizando atras dele em rolagem de hardware continua (loop de 512px sem
costura visivel). A silhueta nao e um retangulo uniforme -- os sprites
vem de uma tabela de posicao/tile/paleta gerada por `make_carro.py` e
consumida por `monta_oam_carro`, nao de um loop fixo (ver armadilha da
silhueta irregular abaixo). START volta pro menu. Toca o refrao de
"Amanda" (que segue pelas fotos).

**Conversa no carro:** depois de `CARRO_ESPERA_FALA` quadros a Amanda
puxa assunto sozinha (caixa da direita, no ceu parado), B fecha, o Victor
responde (caixa da esquerda). O texto fica em `GRUPOS_FALA_CARRO`
(`make_scene.py`), no maximo `CARRO_TEXTO_MAX` linhas por caixa. So depois
da conversa o B segue pras fotos (antes, um B apressado pularia tudo).

**Fotos** (`tela = TELA_FOTO`, ver `tools/make_foto.py`/`carrega_foto`):
B no carro abre a primeira; cada foto em `fotos/` vira uma polaroide
sepia pontilhada com legenda (`FOTOS` no gerador: arquivo, recorte,
legenda). O gerador escolhe o banco (4-6) e emite as tabelas em
`build/fotos.inc`. B passa pra proxima; depois da ultima, volta pro menu
(provisorio, ate existir a cena final). A musica do carro em diante e o
refrao de "Amanda", que continua tocando sem reiniciar entre as fotos; por
enquanto o minigame ainda usa o mesmo refrao.

## Falta

- **Mais fotos, se quiserem.** Hoje sao tres, nesta ordem: a casa dela a
  noite ("GOSTEI MUITO DE TE CONHECER / *SMACK*"), "NOSSO PRIMEIRO ANO
  NOVO" e "MINHA COMPANHEIRA DE LOJA". Opcoes por foto em `FOTOS`
  (`make_foto.py`): legenda em 2 linhas com "\n", `equaliza` pra foto sem
  contraste, `ceu_noite` pra trocar ceu de dia por ceu estrelado.
- **Cena final:** Victor, Amanda e o Hulk (cachorro dela, sprite andando)
  com "FELIZ 2 ANOS DE NAMORO".
- **Musica nova pro minigame** (o refrao passa a ser so da parte final).
- Transicao (fade) entre carro e fotos, se ficar seco.
