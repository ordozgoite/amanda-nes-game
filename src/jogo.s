; ==========================================================================
;  Victor & Amanda -- dois anos
;
;  Cartucho UNROM (mapper 2): 128 KB de codigo em 8 bancos, e CHR-RAM.
;  Nao havendo CHR-ROM, cada tela manda os proprios graficos pra memoria
;  de video antes de aparecer -- e por isso que cada cena pode ter os seus
;  256 desenhos, em vez de todas dividirem um conjunto so.
; ==========================================================================

PPUCTRL   = $2000
PPUMASK   = $2001
PPUSTATUS = $2002
OAMADDR   = $2003
PPUSCROLL = $2005
PPUADDR   = $2006
PPUDATA   = $2007
OAMDMA    = $4014
JOY1      = $4016

; ---- bancos ----
BANCO_MENU = 0
BANCO_CENA = 1
BANCO_JOGO = 2
BANCO_CARRO = 3

; ---- telas ----
TELA_MENU = 0
TELA_CENA = 1
TELA_JOGO = 2
TELA_CARRO = 3

; ---- botoes, na ordem em que o controle os entrega ----
BTN_A     = $80
BTN_B     = $40
BTN_SEL   = $20
BTN_START = $10
BTN_UP    = $08
BTN_DOWN  = $04
BTN_LEFT  = $02
BTN_RIGHT = $01

; ---- tiles do coracao do menu ----
HEART_TL  = $70
HEART_TR  = $71
HEART_BL  = $72
HEART_BR  = $73

POS_VICTOR    = $2000 + 12*32 + 13
POS_HEART_TOP = $2000 + 14*32 + 15
POS_HEART_BOT = $2000 + 15*32 + 15
POS_AMANDA    = $2000 + 17*32 + 13
POS_ATTR      = $23C0 + 3*8 + 3
POS_AVISO_START = $2000 + 24*32 + 3   ; "APERTE START..." la embaixo, centralizado

; ---- espera entre o START e a pizzaria, com o eco do plin no meio ----
MENU_ESPERA_INICIAL = 60   ; ~1s a 60 quadros/s
MENU_ESPERA_ECO1     = MENU_ESPERA_INICIAL - 8    ; ~130ms depois do plin
MENU_ESPERA_ECO2     = MENU_ESPERA_INICIAL - 16   ; ~130ms depois do eco 1

; ---- personagens ----
; A Amanda tem 16x32 (2 tiles de largura por 4 de altura, 8 sprites).
; O Victor tem 16x24 e fica parado, sentado a mesa da frente.
ANDA_MIN    = 8
ANDA_MAX    = 232
CHAO_Y      = 192
TILE_VICTOR = 16
VICTOR_X    = 176   ; atras da mesa, com a bandeja na frente dele -- e onde ele senta
VICTOR_Y    = 152
AMANDA_SENTADA_X = 200   ; do lado direito dele, no mesmo banco da mesa
PERTO_MIN   = 128   ; faixa de x em que o aviso aparece -- comeca na borda
                     ; esquerda da mesa da frente (16*8, ver make_scene.py),
                     ; bem antes dela chegar exatamente do lado dele
PERTO_MAX   = 201
TILE_BOCA_E = 22    ; Victor sentado de boca aberta
TILE_BOCA_D = 23
TILE_AVISO  = 24    ; a caixinha do "B"
TILE_AMA_BOCA_E = 28  ; Amanda de boca aberta (so na caixa dela)
TILE_AMA_BOCA_D = 29

; Victor comeca em pe, um pouco deslocado da cadeira -- so senta quando ela
; pede, na parte PARTE_SENTAR do dialogo (ver passo_dialogo).
VICTOR_EMPE_X   = 160
VICTOR_EMPE_Y   = CHAO_Y
TILE_VICTOR_EMPE = 30    ; ver tools/make_sprites.py -- "Victor em pe 30-45"
TILE_BOCA_EMPE_E = 46
TILE_BOCA_EMPE_D = 47

; O balao de fala fica sempre na mesma LINHA pros dois (CAIXA_ROW; ver
; boxrow_tab), acima de onde os dois personagens ficam o tempo todo,
; andando ou sentados. A COLUNA e o que diferencia quem fala: a caixa do
; Victor cai um pouco mais pra esquerda, a da Amanda mais pra direita --
; alem do nome dentro da caixa, a posicao tambem ajuda a saber quem fala
; num relance. O deslocamento e de exatamente 1 bloco de atributo (4
; tiles = 32px): assim os blocos de 32x32 da nametable (ver atrib1_tab
; mais abaixo) continuam caindo inteiros dentro da caixa nos dois casos,
; sem vazar paleta pro cenario em volta.
;
; Como cada caixa ocupa exatamente 8 linhas de tiles (=1 pagina inteira
; de 256 bytes da nametable), o byte ALTO do endereco e o mesmo pros dois
; falantes (ver caixa_pag_tab) -- so o BAIXO muda com a coluna (ver
; caixa_baixo_tab/nome_baixo_tab/texto_baixo_tab).
CAIXA_ROW        = 8    ; linha 8, em tiles -- a mesma pros dois
CAIXA_COL_VICTOR = 4    ; colunas 4-19
CAIXA_COL_AMANDA = 12   ; colunas 12-27
ATRIB_PAL2  = $AA   ; os quatro quadrantes na paleta 2

; ---- minigame: pizzas caindo ----
; A faixa de captura e generosa de proposito (24px, quase a altura toda do
; sprite da Amanda) -- e um presente, nao um jogo de reflexo apertado.
TILE_PIZZA      = 26     ; ver tools/make_sprites.py
; PONTOS_MIN e ERROS_MAX vem de build/jogo.inc (tools/make_jogo.py) -- o
; texto da intro/vitoria precisa do mesmo numero ("PEGUE 15 PIZZAS!"), entao
; o Python e quem manda nisso agora, nao o assembly.
ESPERA_BASE     = 90     ; quadros entre pizzas, no comeco
ESPERA_MIN      = 30     ; nunca mais rapido que isso
SALTO_MAX       = 80     ; o x de uma pizza fica a no maximo isso do x da anterior
VEL_BASE        = 1      ; pixels por quadro, no comeco
VEL_MAX         = 3
; a fraseszinha triste da derrota: nota 1 toca na hora (checa_derrota),
; as outras tres a cada DERROTA_PASSO quadros -- ver derrota_espera
DERROTA_ESPERA_INICIAL = 75
DERROTA_PASSO          = 25
DERROTA_NOTA2 = DERROTA_ESPERA_INICIAL - DERROTA_PASSO
DERROTA_NOTA3 = DERROTA_ESPERA_INICIAL - DERROTA_PASSO*2
DERROTA_NOTA4 = DERROTA_ESPERA_INICIAL - DERROTA_PASSO*3
; a fraseszinha feliz da vitoria -- mesma ideia, mais rapida (notas mais
; curtas, ver toca_feliz1..4). Prefixo VITORIA_ (nao FELIZ_) de proposito:
; FELIZ_NOTA1..4 ja e o nome das notas musicais (ver musica.inc/
; make_song.py) -- mesma pegadinha que separou TRISTE_NOTAn de DERROTA_NOTAn.
VITORIA_ESPERA_INICIAL = 45
VITORIA_PASSO          = 15
VITORIA_NOTA2 = VITORIA_ESPERA_INICIAL - VITORIA_PASSO
VITORIA_NOTA3 = VITORIA_ESPERA_INICIAL - VITORIA_PASSO*2
VITORIA_NOTA4 = VITORIA_ESPERA_INICIAL - VITORIA_PASSO*3
CAPTURA_Y_MIN   = CHAO_Y - 4
CAPTURA_Y_MAX   = CHAO_Y + 24
; HUD: barra de pontos (PONTOS_MIN segmentos, linha 2) e vidas (ERROS_MAX
; iconezinhos, linha 3) -- ver desenha_barra/desenha_vidas. Comecam na
; coluna 8, depois do rotulo "PONTOS"/"VIDAS" (ver make_jogo.py).
BARRA_ADDR      = $2000 + 2*32 + 8
VIDAS_ADDR      = $2000 + 3*32 + 8
; UI_BASE vem de build/jogo.inc (tools/make_jogo.py) -- indice do primeiro
; dos 4 tiles de HUD, na ordem em que o Python escreveu (ver ui_ordem).
UI_BARRA_VAZIA  = UI_BASE + 0
UI_BARRA_CHEIA  = UI_BASE + 1
UI_VIDA_CHEIA   = UI_BASE + 2
UI_VIDA_VAZIA   = UI_BASE + 3

; --------------------------------------------------------------------------
.segment "HEADER"
    .byte "NES", $1A
    .byte 8                 ; 8 x 16 KB de PRG
    .byte 0                 ; sem CHR-ROM: o cartucho tem CHR-RAM
    .byte $21               ; mapper 2, espelhamento vertical
    .byte $00
    .res 8, $00

; --------------------------------------------------------------------------
.segment "ZEROPAGE"
frame_count: .res 1
pulse_step:  .res 1
ptr:         .res 2         ; ponteiro de trabalho
tmp:         .res 2
paginas:     .res 1         ; quantas paginas de 256 bytes copiar
nmi_flag:    .res 1         ; muda a cada quadro; o laco principal espera nela
carregando:  .res 1         ; 1 = montando tela, o NMI nao deve mexer no video
tela:        .res 1         ; qual tela esta no ar

botoes:      .res 1
botoes_ant:  .res 1
botoes_novos:.res 1         ; so os que acabaram de ser apertados

; --- menu: pausa entre o START e a pizzaria, pra dar tempo de ouvir o plin ---
menu_saindo: .res 1         ; 1 = START ja foi apertado, contando pra sair
menu_espera: .res 1
apaga_aviso: .res 1         ; 1 = o NMI precisa apagar "APERTE START..."

player_x:    .res 1
player_y:    .res 1
player_dir:  .res 1         ; 0 = olhando pra direita, 1 = pra esquerda
player_frame:.res 1         ; 0 ou 1, os dois passos
player_anim: .res 1
andando:     .res 1
tile_base:   .res 1

; --- dialogo ---
dialogo:     .res 1         ; 0=fora 1=abrindo 2=escrevendo 3=lendo 4=fechando
dlg_lin:     .res 1         ; linha da caixa sendo desenhada ou restaurada
dlg_txt:     .res 1         ; qual linha de fala (indice global em FALA)
dlg_col:     .res 1         ; coluna dentro da linha
dlg_wait:    .res 1
dlg_tipo:    .res 1
dlg_box:     .res 1         ; quem fala agora: 0 = Victor, 1 = Amanda (posicao/nome)
dlg_parte:   .res 1         ; qual parte do dialogo (0, 1, 2...), indexa fala/falante
perto:       .res 1         ; 1 = a Amanda esta ao alcance do Victor
oam_attr:    .res 1         ; proprio da OAM: 'tmp' e da musica, que roda no NMI
abre_jogo:   .res 1         ; 1 = o dialogo fechou; o laco principal troca de tela

; --- animacao de sentar da Amanda, disparada ao apertar B perto dele ---
senta_fase:    .res 1       ; 0 fora, 1 andando ate o x do banco, 2 subindo ate a mesa
amanda_sentada:.res 1       ; 1 = desenha ela sentada (cabeca+tronco, sem pernas)

; --- o Victor: comeca em pe e anda ate a cadeira quando o dialogo pede
; (PARTE_SENTAR, ver passo_dialogo). Mesma ideia da animacao da Amanda, so
; que sem espelhar -- ele so anda pra direita, da posicao em pe ate a mesa.
victor_x:      .res 1
victor_y:      .res 1
victor_frame:  .res 1       ; 0 ou 1, os dois passos (em pe/andando)
victor_anim:   .res 1
victor_senta_fase: .res 1   ; 0 fora, 1 andando, 2 subindo, 3 pronto
victor_sentado:.res 1       ; 0 = desenha em pe (andando), 1 = desenha sentado

; --- minigame: pizzas caindo ---
; 'jogo_tmp' e o scratch do laco principal (nao pode usar 'ptr'/'tmp':
; sao da musica, que roda no NMI a qualquer momento).
jogo_fase:   .res 1         ; 0 jogando, 1 vitoria, 2 derrota, 3 aguardando o 1o B
jogo_pontos: .res 1
jogo_erros:  .res 1
jogo_vel:    .res 1
jogo_espera: .res 1
jogo_venceu: .res 1         ; 1 = ja disparou a comemoracao nesta rodada
; checa_vitoria/checa_derrota rodam de dentro do laco de pizzas
; (atualiza_pizzas) -- trocar de nametable ali no meio clobber ia o X do
; laco. Em vez disso so avisam com essa flag; quem troca de verdade e
; atualiza_jogo, no topo do laco principal, onde e seguro.
jogo_troca:  .res 1
; a fraseszinha triste da derrota (ver checa_derrota/toca_triste1..4): toca
; uma nota na hora e mais tres com atraso, contadas por derrota_espera --
; mesma ideia do menu_espera/MENU_ESPERA_ECO1/2 pro "plin" e o eco dele.
derrota_tocando: .res 1
derrota_espera:  .res 1
vitoria_tocando: .res 1        ; o mesmo esquema, pra fraseszinha feliz
vitoria_espera:  .res 1
jogo_tmp:    .res 1
jogo_tmp2:   .res 1
placar_sujo: .res 1
rng_seed:    .res 1
ultimo_pz_x: .res 1         ; x da ultima pizza que nasceu, pra limitar o salto
pz_x:        .res 3
pz_y:        .res 3
pz_ativa:    .res 3

; --- cena do carro ---
; scroll horizontal em 9 bits (0-511, as duas telas coladas -- ver
; make_carro.py): carro_scroll e o byte baixo (val de PPUSCROLL), carro_nt
; e o bit de qual nametable ($2000 ou $2400) esta na base -- os dois
; incrementados a cada NMI (ver nmi/atualiza_scroll_carro), pra rolagem
; ficar suave mesmo sem nada rodando no laco principal.
carro_scroll: .res 1
carro_nt:     .res 1

; --- musica ---
musica_liga: .res 1         ; 0 = motor desligado (menu, em silencio)
ch_ptr_lo:   .res 3
ch_ptr_hi:   .res 3
ch_base_lo:  .res 3         ; onde cada canal reinicia ao bater $FF -- muda
ch_base_hi:  .res 3         ; com a musica ativa (ver troca_musica)
ch_wait:     .res 3
ch_note:     .res 3
ch_vol:      .res 3
ch_atk:      .res 3

.segment "OAM"
oam:         .res 256

; --------------------------------------------------------------------------
;  Dados das telas, nos bancos que entram e saem
; --------------------------------------------------------------------------
.segment "BANK0"
chr_menu:   .incbin "chr_menu.bin"       ; fonte + coracao (8 paginas)

.segment "BANK1"
chr_cena:    .incbin "chr_cena.bin"      ; a Pizza Crek (13 paginas)
chr_sprites: .incbin "chr_sprites.bin"   ; Amanda e Victor (2 paginas)
nam_cena:   .incbin "cena.nam"           ; tela + atributos (4 paginas)

.segment "BANK2"
chr_jogo:         .incbin "chr_jogo.bin"      ; ceu, chao, retrato triste, HUD
chr_sprites_jogo:  .incbin "chr_sprites.bin"   ; a mesma folha de sprites da cena
nam_jogo:         .incbin "jogo.nam"          ; tela jogando (4 paginas)
nam_jogo_intro:   .incbin "jogo_intro.nam"    ; "PEGUE N PIZZAS!" -- antes de comecar
nam_jogo_vitoria: .incbin "jogo_vitoria.nam"  ; "PARABENS!" -- ao alcancar PONTOS_MIN
nam_jogo_derrota: .incbin "jogo_derrota.nam"  ; retrato triste -- ao alcancar ERROS_MAX

.segment "BANK3"
chr_carro:         .incbin "chr_carro.bin"         ; ceu, predios, rua (4 paginas)
chr_sprites_carro:  .incbin "chr_sprites_carro.bin"  ; carro + as duas cabecas
nam_carro0:        .incbin "carro_nt0.nam"         ; metade esquerda (vai em $2000)
nam_carro1:        .incbin "carro_nt1.nam"         ; metade direita (vai em $2400)

; ==========================================================================
.segment "CODE"

.macro PPU_ADDR endereco
    lda #>endereco
    sta PPUADDR
    lda #<endereco
    sta PPUADDR
.endmacro

; --------------------------------------------------------------------------
;  Troca o banco visivel em $8000.
;
;  Na UNROM o cartucho nao tem porta separada: o valor vai pelo barramento
;  de dados junto com a leitura da propria ROM. Se os dois discordarem, o
;  chip recebe lixo. Por isso grava-se num endereco cujo conteudo ja e o
;  numero do banco -- a tabela abaixo.
; --------------------------------------------------------------------------
troca_banco:
    tax
    sta tabela_bancos, x
    rts

tabela_bancos:
    .byte 0, 1, 2, 3, 4, 5, 6, 7

; ==========================================================================
reset:
    sei
    cld
    ldx #$40
    stx $4017
    ldx #$FF
    txs
    inx
    stx PPUCTRL
    stx PPUMASK
    stx $4010

    bit PPUSTATUS
:   bit PPUSTATUS
    bpl :-

    lda #$00
    ldx #$00
@limpa_ram:
    sta $0000, x
    sta $0300, x
    sta $0400, x
    sta $0500, x
    sta $0600, x
    sta $0700, x
    inx
    bne @limpa_ram

:   bit PPUSTATUS
    bpl :-

    jsr musica_init
    jsr carrega_menu

; --------------------------------------------------------------------------
;  Laco principal: um passo por quadro, em cima do NMI
; --------------------------------------------------------------------------
principal:
    lda nmi_flag
:   cmp nmi_flag
    beq :-                  ; espera virar o quadro

    jsr le_controle

    lda tela
    beq @menu
    cmp #TELA_CENA
    beq @cena
    cmp #TELA_JOGO
    beq @jogo
    jsr atualiza_carro
    jmp principal
@jogo:
    jsr atualiza_jogo
    jmp principal
@menu:
    jsr atualiza_menu
    jmp principal
@cena:
    jsr atualiza_cena
    jmp principal

; ==========================================================================
;  Controle
; ==========================================================================
le_controle:
    lda botoes
    sta botoes_ant

    lda #$01                ; trava e destrava: o controle carrega o estado
    sta JOY1
    lda #$00
    sta JOY1

    ldx #$08
:   lda JOY1                ; sai um botao por leitura, do A ao direita
    lsr                     ; bit 0 -> carry
    rol botoes              ; carry entra pela direita
    dex
    bne :-

    lda botoes_ant          ; o que mudou de solto pra apertado agora
    eor #$FF
    and botoes
    sta botoes_novos
    rts

; ==========================================================================
;  Tela: menu
; ==========================================================================
atualiza_menu:
    lda menu_saindo           ; ja apertou START? so espera a contagem zerar
    bne @contando
    lda botoes_novos
    and #BTN_START
    beq @fim
    jsr toca_plin
    lda #$01
    sta apaga_aviso           ; o NMI apaga o texto no proximo quadro
    sta menu_saindo
    lda #MENU_ESPERA_INICIAL
    sta menu_espera
@fim:
    rts
@contando:
    dec menu_espera

    lda menu_espera            ; o "eco" e so o mesmo plin de novo, mais
    cmp #MENU_ESPERA_ECO1      ; baixo, no outro pulso (livre nesse instante
    bne @nao_eco1               ; que o motor de 3 canais ainda esta desligado)
    jsr toca_eco1
@nao_eco1:
    lda menu_espera
    cmp #MENU_ESPERA_ECO2
    bne @nao_eco2
    jsr toca_eco2
@nao_eco2:
    lda menu_espera
    bne @fim
    jsr carrega_cena
    rts

; ---- some com "APERTE START..." -- roda no NMI, so escreve durante o vblank ----
apaga_aviso_start:
    lda apaga_aviso
    beq @fim
    lda #$00
    sta apaga_aviso
    bit PPUSTATUS
    PPU_ADDR POS_AVISO_START
    lda #$00                  ; tile 0 = espaco em branco
    ldy #25
:   sta PPUDATA
    dey
    bne :-
@fim:
    rts

carrega_menu:
    lda #$01
    sta carregando
    jsr desliga_tela

    lda #BANCO_MENU
    jsr troca_banco

    lda #$00
    sta menu_saindo            ; comeca sempre livre pra um novo START
    sta apaga_aviso

    jsr musica_para          ; o menu fica em silencio

    bit PPUSTATUS           ; graficos do fundo -> pattern table 1
    PPU_ADDR $1000
    lda #<chr_menu
    sta ptr
    lda #>chr_menu
    sta ptr+1
    lda #8
    sta paginas
    jsr copia_ppu

    lda #<paletas_menu
    sta ptr
    lda #>paletas_menu
    sta ptr+1
    jsr carrega_paletas

    jsr limpa_nametable
    jsr desenha_menu
    jsr esconde_sprites

    lda #TELA_MENU
    sta tela
    lda #$00
    sta carregando
    jmp liga_tela

; --------------------------------------------------------------------------
limpa_nametable:
    bit PPUSTATUS
    PPU_ADDR $2000
    lda #$00
    ldx #$00
    ldy #$00
@volta:
    sta PPUDATA
    inx
    bne @volta
    iny
    cpy #4                  ; 960 tiles + 64 bytes de atributo
    bne @volta
    rts

desenha_menu:
    bit PPUSTATUS

    PPU_ADDR POS_VICTOR
    ldx #$00
@victor:
    lda txt_victor, x
    beq @amanda
    sec
    sbc #$20                ; ascii -> numero do tile
    sta PPUDATA
    inx
    bne @victor

@amanda:
    PPU_ADDR POS_AMANDA
    ldx #$00
@le_amanda:
    lda txt_amanda, x
    beq @coracao
    sec
    sbc #$20
    sta PPUDATA
    inx
    bne @le_amanda

@coracao:
    PPU_ADDR POS_HEART_TOP
    lda #HEART_TL
    sta PPUDATA
    lda #HEART_TR
    sta PPUDATA
    PPU_ADDR POS_HEART_BOT
    lda #HEART_BL
    sta PPUDATA
    lda #HEART_BR
    sta PPUDATA

    PPU_ADDR POS_ATTR       ; os dois blocos que cobrem o coracao
    lda #%01000000
    sta PPUDATA
    lda #%00010000
    sta PPUDATA

    PPU_ADDR POS_AVISO_START
    ldx #$00
@aviso:
    lda txt_aviso_start, x
    beq @fim
    sec
    sbc #$20
    sta PPUDATA
    inx
    bne @aviso
@fim:
    rts

; --------------------------------------------------------------------------
;  O pulso do coracao, so no menu
; --------------------------------------------------------------------------
pulsa_coracao:
    lda frame_count
    and #$07
    bne @fim

    inc pulse_step
    lda pulse_step
    and #$07
    tax
    bit PPUSTATUS
    PPU_ADDR $3F06          ; cor 2 da paleta 1 = preenchimento do coracao
    lda pulso, x
    sta PPUDATA
    PPU_ADDR $0000          ; tira o endereco de dentro da paleta
@fim:
    rts

; ==========================================================================
;  Tela: a pizzaria
; ==========================================================================
atualiza_cena:
    lda abre_jogo            ; o dialogo acabou de fechar nesta rodada?
    beq @sem_transicao
    lda #$00
    sta abre_jogo
    jmp carrega_jogo
@sem_transicao:

    lda senta_fase            ; ela animando ate o banco? nao le botao nenhum
    beq @sem_animacao
    jmp atualiza_senta
@sem_animacao:

    lda victor_senta_fase     ; ele animando ate o banco? idem
    beq @sem_animacao_victor
    jmp atualiza_senta_victor
@sem_animacao_victor:

    lda dialogo
    beq @livre

    ; --- com o balao aberto a Amanda nao anda; B fecha quando terminou ---
    lda dialogo
    cmp #$03
    bne @so_sprites
    lda botoes_novos
    and #BTN_B
    beq @so_sprites
    lda #$04                ; comeca a fechar
    sta dialogo
    lda #$00
    sta dlg_lin
@so_sprites:
    jsr desenha_victor
    jsr boca_victor
    jsr desenha_amanda
    jsr boca_amanda
    jmp aviso_b

@livre:
    lda botoes_novos
    and #BTN_START
    beq @anda
    jmp carrega_menu        ; START volta pro titulo

@anda:
    jsr move_jogador

    jsr calcula_perto
    lda perto
    beq @sprites
    lda botoes_novos
    and #BTN_B
    beq @sprites
    lda #$01                ; ela senta primeiro -- o dialogo so abre quando
    sta senta_fase           ; a animacao terminar (ver atualiza_senta)
    lda #$00
    sta perto                ; senao o aviso "B" fica flutuando sobre ele
                              ; enquanto ela anda ate a cadeira (calcula_perto
                              ; nao roda mais durante a animacao, pra reler)
@sprites:
    jsr desenha_victor
    jsr boca_victor
    jsr desenha_amanda
    jsr boca_amanda
    jmp aviso_b

; --------------------------------------------------------------------------
;  Anda pra esquerda/direita e alterna o passo -- usado pela cena da
;  pizzaria e pelo minigame, os dois lugares em que a Amanda caminha.
; --------------------------------------------------------------------------
move_jogador:
    lda #$00
    sta andando

    lda botoes
    and #BTN_LEFT
    beq @direita
    lda player_x
    cmp #ANDA_MIN
    bcc @direita
    dec player_x
    lda #$01
    sta player_dir
    sta andando

@direita:
    lda botoes
    and #BTN_RIGHT
    beq @anima
    lda player_x
    cmp #ANDA_MAX
    bcs @anima
    inc player_x
    lda #$00
    sta player_dir
    lda #$01
    sta andando

@anima:
    lda andando
    beq @parado
    inc player_anim
    lda player_anim
    and #$07                ; troca de passo a cada 8 quadros
    bne @fim
    lda player_frame
    eor #$01
    sta player_frame
    rts
@parado:
    lda #$00
    sta player_frame
    sta player_anim
@fim:
    rts

; --------------------------------------------------------------------------
;  A Amanda esta perto o bastante da mesa?
; --------------------------------------------------------------------------
calcula_perto:
    lda #$00
    sta perto
    lda player_x
    cmp #PERTO_MIN
    bcc @fim
    cmp #PERTO_MAX
    bcs @fim
    lda #$01
    sta perto
@fim:
    rts

; --------------------------------------------------------------------------
;  O aviso "B" flutuando sobre a cabeca dele (sprite 16, longe da faixa
;  8-15 que o Victor usa -- em pe ele precisa de 8 sprites, nao so 6).
;  A posicao segue victor_x/victor_y, que mudam quando ele anda ate sentar.
; --------------------------------------------------------------------------
aviso_b:
    ldy #$40                ; sprite 16 = byte 64 da OAM
    lda dialogo
    bne @esconde
    lda perto
    beq @esconde

    lda frame_count         ; sobe e desce 2 pixels, pra chamar atencao
    and #$10
    beq @baixo
    lda victor_y
    sec
    sbc #14
    jmp @poe
@baixo:
    lda victor_y
    sec
    sbc #12
@poe:
    sta oam, y
    sta oam+4, y
    lda #TILE_AVISO
    sta oam+1, y
    lda #(TILE_AVISO+1)
    sta oam+5, y
    lda #$02                ; paleta 2
    sta oam+2, y
    sta oam+6, y
    lda victor_x
    sta oam+3, y
    clc
    adc #$08
    sta oam+7, y
    rts
@esconde:
    lda #$FF
    sta oam, y
    sta oam+4, y
    rts

; --------------------------------------------------------------------------
;  A boca dele abre e fecha enquanto o texto sai. desenha_victor ja redesenha
;  a boca fechada todo quadro (em pe ou sentado), entao aqui so precisa
;  sobrescrever com o tile aberto -- sem @fechada pra restaurar na mao.
; --------------------------------------------------------------------------
boca_victor:
    lda dialogo
    cmp #$02                ; so mexe a boca enquanto esta escrevendo
    bne @fim
    lda dlg_box
    bne @fim                 ; caixa da Amanda: a boca dele fica parada
    lda frame_count
    and #$08
    beq @fim
    lda victor_sentado
    bne @sentado
    lda #TILE_BOCA_EMPE_E    ; em pe: cabeca ocupa sprites 8-15 (4 tiles por
    sta oam+37               ; coluna) -- metade esquerda no byte 37, direita
    lda #TILE_BOCA_EMPE_D    ; no 53 (ver monta_oam_victor_empe)
    sta oam+53
    rts
@sentado:
    lda #TILE_BOCA_E
    sta oam+37
    lda #TILE_BOCA_D
    sta oam+49
    rts
@fim:
    rts

; --------------------------------------------------------------------------
;  A boca da Amanda abre e fecha na caixa DELA -- ao contrario do Victor,
;  a cabeca dela e montada de novo todo quadro (monta_oam, porque ela anda),
;  entao so precisa sobrescrever o tile quando esta falando; o resto do
;  tempo o proprio monta_oam ja poe o tile fechado certo.
; --------------------------------------------------------------------------
boca_amanda:
    lda dialogo
    cmp #$02                ; so mexe a boca enquanto esta escrevendo
    bne @fim
    lda dlg_box
    beq @fim                 ; caixa do Victor: a boca dela fica parada
    lda frame_count
    and #$08
    beq @fim
    lda #TILE_AMA_BOCA_E     ; sprite 1 = byte 5 (cabeca, metade esquerda)
    sta oam+5
    lda #TILE_AMA_BOCA_D     ; sprite 5 = byte 21 (metade direita)
    sta oam+21
@fim:
    rts

; --------------------------------------------------------------------------
;  A animacao de sentar: anda ate o x do banco do lado do Victor, sobe ate
;  a altura da mesa, e so entao devolve o dialogo pra proxima parte. Sem
;  isso, so trocar de sprite deixaria ela flutuando no meio do salao ou do
;  tamanho errado -- ela precisa MESMO se mover ate a mesa antes de sentar.
;  Nao le botao nenhum: e uma cutscene curta, nao um trecho jogavel.
; --------------------------------------------------------------------------
; --------------------------------------------------------------------------
;  A animacao de sentar da Amanda agora e disparada em DOIS momentos
;  separados, nao mais um so: primeiro ela so ANDA ate ficar alinhada com
;  o lugar dela (fase 1, disparada no B perto dele -- ver atualiza_cena),
;  e o dialogo comeca com os dois em pe. So mais tarde, bem antes da fala
;  "vem, senta aqui do meu lado" (PARTE_SENTAR), e que ela SOBE de verdade
;  pra cadeira (fase 2, disparada em passo_dialogo -- ver @fechando). As
;  duas fases nunca se seguem automaticamente uma da outra, entao o
;  despachante so precisa saber qual das duas esta ativa.
; --------------------------------------------------------------------------
atualiza_senta:
    lda senta_fase
    cmp #$01
    beq @andando
    jmp @subindo              ; so sobra a fase 2 -- nunca chega aqui com
                               ; outro valor (ver atualiza_cena)

@andando:
    lda player_x
    cmp #AMANDA_SENTADA_X
    beq @chegou_x
    bcc @anda_direita
    dec player_x
    lda #$01
    sta player_dir
    jmp @passo
@anda_direita:
    inc player_x
    lda #$00
    sta player_dir
@passo:
    inc player_anim
    lda player_anim
    and #$07                 ; troca de passo a cada 8 quadros, igual andar normal
    bne @desenha
    lda player_frame
    eor #$01
    sta player_frame
    jmp @desenha
@chegou_x:
    lda #$00                 ; so alinhou -- ainda em pe. O dialogo comeca
    sta senta_fase             ; do zero, os dois de pe (ver PARTE_SENTAR
    lda #$00                   ; mais adiante, que dispara a fase 2 quando
    sta player_frame            ; for a vez dela se sentar de verdade).
    sta player_anim
    jmp abre_dialogo_de_pe

@subindo:
    lda player_y
    cmp #VICTOR_Y
    beq @chegou_y
    dec player_y
    lda player_y
    cmp #(MESA_Y+1)           ; ainda na frente da mesa (y > MESA_Y)?
    bcs @desenha              ; sim: continua desenhando com pernas
    lda #$01                  ; nao: ja passou da borda da mesa -- esconde
    sta amanda_sentada        ; as pernas AGORA, nao so quando a subida
    jmp @desenha              ; terminar, senao ela atravessa o tampo
@chegou_y:
    lda #$00
    sta senta_fase
    lda #$01
    sta amanda_sentada        ; a partir de agora ela desenha sentada
    jmp avanca_apos_sentar    ; abre a caixa de PARTE_SENTAR, ja sentada

@desenha:
    jsr desenha_victor
    jsr boca_victor
    jsr desenha_amanda
    jsr boca_amanda
    rts

; ---- ela terminou de andar (ainda em pe): abre o dialogo do zero ----
abre_dialogo_de_pe:
    lda #$00
    sta senta_fase
    sta dlg_parte             ; primeira parte do dialogo inteiro
    sta dlg_box               ; comeca sempre pela caixa do Victor
    sta dlg_lin
    lda #$01
    sta dialogo
    lda #$00
    sta player_frame          ; a boca aberta so existe no quadro 0 da cabeca
    rts

; --------------------------------------------------------------------------
;  Ele anda da posicao em pe ate a cadeira e senta -- mesma logica da
;  atualiza_senta, so que so anda pra direita (nunca precisa espelhar) e o
;  alvo e a cadeira dele (VICTOR_X/VICTOR_Y). Disparada em PARTE_SENTAR
;  (ver passo_dialogo), quando a fala dela ("vem senta aqui do meu lado")
;  termina de fechar.
; --------------------------------------------------------------------------
atualiza_senta_victor:
    lda victor_senta_fase
    cmp #$01
    beq @andando
    cmp #$02
    beq @subindo
    jmp avanca_apos_sentar    ; fase 3: ele sentou, volta pro resto do dialogo

@andando:
    lda victor_x
    cmp #VICTOR_X
    beq @chegou_x
    inc victor_x              ; a cadeira dele fica sempre a direita da posicao em pe
    inc victor_anim
    lda victor_anim
    and #$07                  ; troca de passo a cada 8 quadros, igual a Amanda
    bne @desenha
    lda victor_frame
    eor #$01
    sta victor_frame
    jmp @desenha
@chegou_x:
    lda #$02                  ; parou de andar: agora sobe ate a mesa
    sta victor_senta_fase
    lda #$00
    sta victor_frame
    sta victor_anim
    jmp @desenha

@subindo:
    lda victor_y
    cmp #VICTOR_Y
    beq @chegou_y
    dec victor_y
    lda victor_y
    cmp #(MESA_Y+1)           ; ainda na frente da mesa (y > MESA_Y)?
    bcs @desenha              ; sim: continua desenhando com pernas
    lda #$01                  ; nao: ja passou da borda da mesa -- esconde
    sta victor_sentado         ; as pernas AGORA, nao so quando a subida
    jmp @desenha               ; terminar, senao ele atravessa o tampo
@chegou_y:
    lda #$01
    sta victor_sentado         ; a partir de agora ele desenha sentado
    lda #$03
    sta victor_senta_fase

@desenha:
    jsr desenha_victor
    jsr boca_victor
    jsr desenha_amanda
    jsr boca_amanda
    rts

; ---- volta pro dialogo na parte seguinte a PARTE_SENTAR ----
avanca_apos_sentar:
    lda #$00
    sta victor_senta_fase
    inc dlg_parte
    ldx dlg_parte
    lda falante_tab, x
    sta dlg_box
    lda #$01
    sta dialogo
    lda #$00
    sta dlg_lin
    rts

; ---- desenha a Amanda andando ou sentada, conforme a fase atual ----
desenha_amanda:
    lda amanda_sentada
    bne @sentada
    jmp monta_oam
@sentada:
    jmp monta_oam_sentada

; --------------------------------------------------------------------------
;  Amanda sentada: cabeca + tronco, sem pernas -- exatamente como o Victor
;  (a mesa esconde o resto). Nao precisou de nenhum desenho novo: sao os
;  MESMOS tiles 0,1,2,4,5,6 do sprite de andar (fatiar em make_sprites.py
;  ja corta cabeca e tronco em tiles separados das pernas), so que sem
;  nunca trocar de quadro nem espelhar -- ela fica de frente pra mesa.
; --------------------------------------------------------------------------
monta_oam_sentada:
    ldx #$00
    ldy #$00
@loop:
    cpx #$03                 ; tiles 3 e 7 sao as pernas -- escondidos
    beq @esconde
    cpx #$07
    beq @esconde

    lda player_y
    clc
    adc ama_dy, x
    sta oam, y

    txa                      ; tile_base sempre 0: sentada nao tem passo
    sta oam+1, y

    lda ama_pal, x
    sta oam+2, y             ; nunca espelha -- sentada de frente pra mesa

    lda ama_dx, x
    clc
    adc player_x
    sta oam+3, y
    jmp @prox
@esconde:
    lda #$FF
    sta oam, y
@prox:
    iny
    iny
    iny
    iny
    inx
    cpx #$08
    bne @loop
    rts

; --------------------------------------------------------------------------
carrega_cena:
    lda #$01
    sta carregando
    jsr desliga_tela

    lda #BANCO_CENA
    jsr troca_banco

    lda #$00                ; a pizzaria comeca a tocar a introducao
    jsr troca_musica

    bit PPUSTATUS           ; cenario -> pattern table 1 (fundo)
    PPU_ADDR $1000
    lda #<chr_cena
    sta ptr
    lda #>chr_cena
    sta ptr+1
    lda #PAGINAS_CENA
    sta paginas
    jsr copia_ppu

    PPU_ADDR $0000          ; personagens -> pattern table 0 (sprites)
    lda #<chr_sprites
    sta ptr
    lda #>chr_sprites
    sta ptr+1
    lda #3                  ; 3 paginas: Amanda + Victor sentado + Victor em pe
    sta paginas
    jsr copia_ppu

    PPU_ADDR $2000          ; a tela pronta, tiles e atributos
    lda #<nam_cena
    sta ptr
    lda #>nam_cena
    sta ptr+1
    lda #4
    sta paginas
    jsr copia_ppu

    lda #<paletas_cena
    sta ptr
    lda #>paletas_cena
    sta ptr+1
    jsr carrega_paletas

    jsr esconde_sprites

    lda #VICTOR_EMPE_X       ; ele comeca em pe, deslocado da cadeira
    sta victor_x
    lda #VICTOR_EMPE_Y
    sta victor_y
    lda #$00
    sta victor_frame
    sta victor_anim
    sta victor_senta_fase
    sta victor_sentado

    lda #40                 ; a Amanda entra pela esquerda
    sta player_x
    lda #CHAO_Y
    sta player_y
    lda #$00
    sta player_dir
    sta player_frame
    sta player_anim
    sta dialogo
    sta perto
    sta senta_fase
    sta amanda_sentada
    jsr desenha_victor
    jsr monta_oam
    jsr aviso_b

    lda #TELA_CENA
    sta tela
    lda #$00
    sta carregando
    jmp liga_tela

; --------------------------------------------------------------------------
carrega_jogo:
    lda #$01
    sta carregando
    jsr desliga_tela

    lda #BANCO_JOGO
    jsr troca_banco

    lda #$01                ; o minigame toca o refrao de "Amanda"
    jsr troca_musica

    bit PPUSTATUS            ; ceu e chao -> pattern table 1 (fundo)
    PPU_ADDR $1000
    lda #<chr_jogo
    sta ptr
    lda #>chr_jogo
    sta ptr+1
    lda #PAGINAS_JOGO
    sta paginas
    jsr copia_ppu

    PPU_ADDR $0000           ; Amanda e a pizza -> pattern table 0 (sprites)
    lda #<chr_sprites_jogo
    sta ptr
    lda #>chr_sprites_jogo
    sta ptr+1
    lda #2
    sta paginas
    jsr copia_ppu

    PPU_ADDR $2000           ; a tela pronta, tiles e atributos -- comeca na
    lda #<nam_jogo_intro     ; intro ("PEGUE N PIZZAS!"), nao direto jogando
    sta ptr
    lda #>nam_jogo_intro
    sta ptr+1
    lda #4
    sta paginas
    jsr copia_ppu

    lda #<paletas_jogo
    sta ptr
    lda #>paletas_jogo
    sta ptr+1
    jsr carrega_paletas

    jsr esconde_sprites

    lda #40                  ; a Amanda comeca no mesmo lugar da pizzaria
    sta player_x
    lda #CHAO_Y
    sta player_y
    lda #$00
    sta player_dir
    sta player_frame
    sta player_anim
    sta jogo_pontos
    sta jogo_erros
    sta jogo_venceu
    sta pz_ativa
    sta pz_ativa+1
    sta pz_ativa+2
    lda #$03                 ; aguardando o primeiro B -- ver atualiza_jogo
    sta jogo_fase
    lda #120                 ; meio da tela: a primeira pizza pode ir pros dois lados
    sta ultimo_pz_x
    lda #ESPERA_BASE
    sta jogo_espera
    lda #VEL_BASE
    sta jogo_vel             ; placar_sujo fica pra quando mostra_jogando
                              ; trocar da intro pra tela de jogo de verdade
    jsr atualiza_oam_jogo

    lda #TELA_JOGO
    sta tela
    lda #$00
    sta carregando
    jmp liga_tela

; --------------------------------------------------------------------------
;  Troca so a nametable da tela do jogo -- ptr/ptr+1 ja apontando pra ela
;  (CHR e paleta ja estao carregadas, nao precisam mexer de novo). Usada
;  nas quatro transicoes de estado do minigame (intro/jogando/vitoria/
;  derrota, ver checa_vitoria/checa_derrota/atualiza_jogo).
; --------------------------------------------------------------------------
troca_nametable_jogo:
    jsr desliga_tela
    PPU_ADDR $2000
    lda #4
    sta paginas
    jsr copia_ppu
    jmp liga_tela

; ==========================================================================
;  Tela: o carro -- por enquanto so o visual (o carro parado, os predios e
;  a rua deslizando atras). A conversa entra num passo futuro; por hora a
;  cena so fica em loop ate START (volta pro menu, ver atualiza_carro).
; ==========================================================================
; posicao fixa na tela (o carro e sprite, nao rola com o fundo -- e assim
; que ele parece "parado" enquanto anda). CARRO_X centraliza os 64px de
; largura (256-64)/2; CARRO_Y poe a roda (base do sprite, perto do fim dos
; 64px de altura, ver CARRO_PX_H em tools/make_carro.py) na faixa de baixo
; da pista -- a mais perto da camera.
CARRO_X = 96
CARRO_Y = 172

carrega_carro:
    lda #$01
    sta carregando
    jsr desliga_tela

    lda #BANCO_CARRO
    jsr troca_banco

    jsr musica_para          ; sem musica nessa cena por enquanto (so o visual)

    bit PPUSTATUS            ; ceu/predios/rua -> pattern table 1 (fundo)
    PPU_ADDR $1000
    lda #<chr_carro
    sta ptr
    lda #>chr_carro
    sta ptr+1
    lda #PAGINAS_CARRO
    sta paginas
    jsr copia_ppu

    PPU_ADDR $0000            ; o carro + as duas cabecas -> pattern table 0
    lda #<chr_sprites_carro
    sta ptr
    lda #>chr_sprites_carro
    sta ptr+1
    lda #PAGINAS_SPRITES_CARRO
    sta paginas
    jsr copia_ppu

    PPU_ADDR $2000             ; metade esquerda do loop de 512px
    lda #<nam_carro0
    sta ptr
    lda #>nam_carro0
    sta ptr+1
    lda #4
    sta paginas
    jsr copia_ppu

    PPU_ADDR $2400             ; metade direita -- $2400 e uma tela DIFERENTE
    lda #<nam_carro1           ; de $2000 porque o cartucho usa espelhamento
    sta ptr                     ; vertical (ver HEADER); e assim que a rolagem
    lda #>nam_carro1            ; horizontal de hardware funciona
    sta ptr+1
    lda #4
    sta paginas
    jsr copia_ppu

    lda #<paletas_carro
    sta ptr
    lda #>paletas_carro
    sta ptr+1
    jsr carrega_paletas

    jsr esconde_sprites
    jsr monta_oam_carro

    lda #$00
    sta carro_scroll
    sta carro_nt

    lda #TELA_CARRO
    sta tela
    lda #$00
    sta carregando
    jmp liga_tela

; --------------------------------------------------------------------------
;  Monta a OAM do carro a partir da tabela gerada por tools/make_carro.py
;  (carro_ofs_x/y_tab, carro_tile_tab, carro_pal_tab, CARRO_N_SPRITES): a
;  silhueta tem canto arredondado e celula vazia (teto, vao embaixo), entao
;  nao e uma grade retangular uniforme -- cada entrada da tabela ja diz
;  onde (offset x/y) e com qual tile/paleta desenhar aquela celula, tanto
;  faz se e lataria (paleta 0) ou cabeca (paleta 1). So roda uma vez, na
;  carga da cena: nada aqui muda quadro a quadro, entao nao precisa
;  redesenhar no laco principal (o NMI manda a mesma OAM de novo sozinho,
;  todo quadro).
; --------------------------------------------------------------------------
monta_oam_carro:
    ldx #$00
    ldy #$00
@loop:
    lda carro_ofs_y_tab, x
    clc
    adc #CARRO_Y
    sta oam, y

    lda carro_tile_tab, x
    sta oam+1, y

    lda carro_pal_tab, x
    sta oam+2, y

    lda carro_ofs_x_tab, x
    clc
    adc #CARRO_X
    sta oam+3, y

    iny
    iny
    iny
    iny
    inx
    cpx #CARRO_N_SPRITES
    bne @loop
    rts

; ---- laco principal da cena do carro: por enquanto so espera START ----
atualiza_carro:
    lda botoes_novos
    and #BTN_START
    beq @fim
    jmp carrega_menu
@fim:
    rts

; ==========================================================================
;  Sprites: o personagem sao 6 tiles, 2 de largura por 3 de altura
; ==========================================================================
monta_oam:
    lda player_frame        ; quadro 2 comeca no tile 8
    beq @base0
    lda #$08
    bne @guarda
@base0:
    lda #$00
@guarda:
    sta tile_base

    ldx #$00                ; qual dos 8 tiles
    ldy #$00                ; posicao na OAM (4 bytes por sprite)
@loop:
    lda player_y
    clc
    adc ama_dy, x
    sta oam, y

    txa
    clc
    adc tile_base
    sta oam+1, y

    ; a paleta muda por linha de tile: cabeca, tronco e pernas usam
    ; paletas diferentes, e e assim que o cabelo vai escurecendo
    lda ama_pal, x
    sta oam_attr
    lda player_dir
    beq @sem_espelho
    lda #$40                ; espelhado na horizontal
    ora oam_attr
    bne @poe_attr
@sem_espelho:
    lda oam_attr
@poe_attr:
    sta oam+2, y

    lda player_dir
    beq @x_normal
    lda ama_dx_esp, x       ; espelhado: as colunas trocam de lado
    jmp @soma_x
@x_normal:
    lda ama_dx, x
@soma_x:
    clc
    adc player_x
    sta oam+3, y

    iny
    iny
    iny
    iny
    inx
    cpx #$08
    bne @loop
    rts

; --------------------------------------------------------------------------
;  Desenha o Victor, sentado ou em pe, conforme a fase atual.
; --------------------------------------------------------------------------
desenha_victor:
    lda victor_sentado
    bne @sentado
    jmp monta_oam_victor_empe
@sentado:
    jmp oam_victor

; --------------------------------------------------------------------------
;  O Victor sentado: 6 sprites (sem pernas, a mesa esconde) a partir do
;  sprite 8. So sobra estatico depois que ele senta, mas redesenha todo
;  quadro assim mesmo -- e o mesmo custo de sempre e evita ter que lembrar
;  de chamar isso so uma vez em cada lugar que ele pode passar a sentado.
;  Tambem esconde os sprites 14-15: quando ele estava em pe (8 sprites,
;  ver monta_oam_victor_empe) essas duas pernas ficavam la; sentado, ninguem
;  mais escreve nelas, entao sem isso o ultimo quadro em pe ficaria preso.
; --------------------------------------------------------------------------
oam_victor:
    ldx #$00
    ldy #$20                ; sprite 8 = byte 32 da OAM
@loop:
    lda #VICTOR_Y
    clc
    adc vic_dy, x
    sta oam, y

    txa
    clc
    adc #TILE_VICTOR
    sta oam+1, y

    lda vic_pal, x           ; cabeca = paleta 2, torso = paleta 3 (logo)
    sta oam+2, y

    lda #VICTOR_X
    clc
    adc vic_dx, x
    sta oam+3, y

    iny
    iny
    iny
    iny
    inx
    cpx #$06
    bne @loop

    lda #$FF                 ; esconde a sobra dos sprites 14-15 (pernas
    sta oam+56               ; do "Victor em pe", nao usadas sentado)
    sta oam+60
    rts

; --------------------------------------------------------------------------
;  O Victor em pe/andando: 8 sprites (cabeca+torso+pernas, 2 colunas) a
;  partir do sprite 8 -- mesma ideia da monta_oam da Amanda, so que sem
;  espelhar (ele nunca anda pra esquerda nesta cena).
; --------------------------------------------------------------------------
monta_oam_victor_empe:
    lda victor_frame
    beq @base0
    lda #$08
    bne @guarda
@base0:
    lda #$00
@guarda:
    sta tile_base

    ldx #$00
    ldy #$20                ; sprite 8 = byte 32 da OAM
@loop:
    lda victor_y
    clc
    adc vic_empe_dy, x
    sta oam, y

    txa
    clc
    adc tile_base
    clc
    adc #TILE_VICTOR_EMPE
    sta oam+1, y

    lda vic_empe_pal, x
    sta oam+2, y

    lda victor_x
    clc
    adc vic_empe_dx, x
    sta oam+3, y

    iny
    iny
    iny
    iny
    inx
    cpx #$08
    bne @loop
    rts

esconde_sprites:
    lda #$FF                ; Y fora da tela = sprite invisivel
    ldx #$00
:   sta oam, x
    inx
    bne :-
    rts

; ==========================================================================
;  O balao de fala
;
;  Ele e desenhado no FUNDO, tile a tile, e por isso todo o trabalho mora
;  no NMI: so durante o vblank da pra escrever na memoria de video sem
;  sujar a imagem. Cada quadro faz um pedacinho -- uma linha da moldura,
;  ou uma letra -- e nunca estoura o tempo disponivel.
; ==========================================================================
passo_dialogo:
    lda dialogo
    beq @fim
    cmp #$01
    beq @abrindo
    cmp #$02
    beq @escrevendo
    cmp #$04
    beq @fechando
@fim:
    rts

@abrindo:
    lda dlg_lin
    bne :+
    jsr poe_atributos       ; na primeira linha, ajusta as paletas do bloco
:   jsr desenha_linha
    inc dlg_lin
    lda dlg_lin
    cmp #$08
    bcc @fim
    lda #$02                ; moldura pronta, comeca a escrever
    sta dialogo
    jsr desenha_nome         ; a etiqueta com o nome aparece de uma vez
    ldx dlg_parte
    lda inicio_fala_tab, x   ; cada parte comeca na sua propria linha de fala
    sta dlg_txt
    lda #$00
    sta dlg_col
    sta dlg_wait
    rts

@escrevendo:
    dec dlg_wait
    bpl @cala               ; nos quadros entre as letras, corta o tique
    lda #$02                ; uma letra a cada 3 quadros
    sta dlg_wait
    jmp escreve_letra
@cala:
    lda #$10                ; volume constante zero
    sta $400C
    rts

@fechando:
    jsr restaura_linha
    inc dlg_lin
    lda dlg_lin
    cmp #$08
    bcc @fim
    jsr restaura_atributos
    lda dlg_parte
    cmp #PARTE_SENTAR
    bne @nao_e_convite
    lda #$00                  ; era o convite pra ele sentar: anima em vez de
    sta dialogo                ; abrir a proxima caixa direto. Zerar 'dialogo'
    lda #$01                   ; e essencial -- sem isso o passo_dialogo reentra
    sta victor_senta_fase      ; em @fechando todo NMI (dialogo ainda seria 4) e
    rts                        ; forca victor_senta_fase de volta pra 1 pra sempre.
@nao_e_convite:
    cmp #(PARTE_SENTAR-1)      ; a PROXIMA parte e o convite pra sentar?
    bne @sem_sentar
    lda #$00                  ; entao e a vez DELA sentar antes de falar --
    sta dialogo                ; mesmo motivo do zerar 'dialogo' acima.
    lda #$02                   ; pula direto pra fase 2 (subir): ela ja esta
    sta senta_fase              ; alinhada em x desde o inicio do dialogo.
    rts
@sem_sentar:
    inc dlg_parte
    lda dlg_parte
    cmp #N_PARTES
    bcs @acabou_tudo         ; nao ha proxima parte: a conversa acabou
    ldx dlg_parte
    lda falante_tab, x       ; quem fala na proxima parte -- pode ser o
    sta dlg_box              ; mesmo de novo (Victor 1 -> Victor 2)
    lda #$01
    sta dialogo               ; volta pro estado 1 = abrindo
    lda #$00
    sta dlg_lin
    rts
@acabou_tudo:
    lda #$00
    sta dialogo
    sta dlg_box              ; deixa pronto pra proxima conversa
    sta dlg_parte
    lda #$01                 ; o laco principal troca de tela no proximo quadro
    sta abre_jogo
    rts

; ---- uma linha da moldura (dlg_lin = 0 topo, 7 base, resto meio) ----
desenha_linha:
    ldx #$01
    lda dlg_lin
    bne :+
    ldx #$00                ; linha de cima
    beq :++
:   cmp #$07
    bne :+
    ldx #$02                ; linha de baixo
:   stx dlg_tipo

    bit PPUSTATUS
    ldx dlg_box
    lda caixa_pag_tab, x
    sta PPUADDR
    lda dlg_lin
    asl
    asl
    asl
    asl
    asl                     ; linha * 32
    clc
    adc caixa_baixo_tab, x
    sta PPUADDR

    ldx dlg_tipo
    lda borda_esq, x
    sta PPUDATA
    lda borda_meio, x
    ldy #14
:   sta PPUDATA
    dey
    bne :-
    ldx dlg_tipo
    lda borda_dir, x
    sta PPUDATA
    rts

; ---- escreve a proxima letra ----
escreve_letra:
    ldx dlg_txt
    lda fala_lo, x
    sta ptr
    lda fala_hi, x
    sta ptr+1
    ldy dlg_col
    lda (ptr), y
    bne @tem

    inc dlg_txt             ; $00 termina a linha
    lda #$00
    sta dlg_col
    ldx dlg_parte
    lda dlg_txt
    cmp fim_fala_tab, x      ; cada parte tem seu proprio fim
    bcc @fim
    lda #$03                ; acabou o texto: espera o B
    sta dialogo
    lda #$10                ; e cala o tique da fala
    sta $400C
@fim:
    rts

@tem:
    sta dlg_tipo
    bit PPUSTATUS
    ldx dlg_box
    lda caixa_pag_tab, x
    sta PPUADDR
    ldy dlg_parte            ; Y aqui, pra nao perder dlg_box em X
    lda dlg_txt
    sec
    sbc inicio_fala_tab, y   ; linha DENTRO da parte atual, nao global
    asl
    asl
    asl
    asl
    asl                     ; linha do texto * 32
    clc
    adc texto_baixo_tab, x
    adc dlg_col
    sta PPUADDR
    lda dlg_tipo
    sta PPUDATA
    inc dlg_col

    ; O tique da fala vai no canal de ruido: as duas quadradas e o
    ; triangulo estao ocupados com a musica. O volume e ligado aqui e
    ; desligado no quadro seguinte -- assim o tique dura um quadro exato,
    ; sem depender do contador de duracao do APU.
    lda #$14                ; volume constante 4
    sta $400C
    lda #$0C
    sta $400E
    lda #$18                ; duracao curtissima
    sta $400F
    rts

; ---- escreve o nome de quem fala, de uma vez (nao letra a letra) ----
desenha_nome:
    lda dlg_box
    bne @amanda
    lda #<nome_victor
    sta ptr
    lda #>nome_victor
    sta ptr+1
    jmp @tem_ptr
@amanda:
    lda #<nome_amanda
    sta ptr
    lda #>nome_amanda
    sta ptr+1
@tem_ptr:
    ldx dlg_box
    bit PPUSTATUS
    lda caixa_pag_tab, x
    sta PPUADDR
    lda nome_baixo_tab, x
    sta PPUADDR

    ldy #$00
@loop:
    lda (ptr), y
    sta PPUDATA
    iny
    cpy #7
    bne @loop
    rts

; ---- devolve uma linha do cenario, lida de volta da ROM ----
restaura_linha:
    ldx dlg_box
    bit PPUSTATUS
    lda caixa_pag_tab, x
    sta PPUADDR
    lda dlg_lin
    asl
    asl
    asl
    asl
    asl
    clc
    adc caixa_baixo_tab, x
    sta PPUADDR

    ; ptr = nam_cena + (linha_do_topo_da_caixa + dlg_lin) * 32 + coluna_da_caixa
    lda boxrow_tab, x
    clc
    adc dlg_lin
    sta tmp                 ; linha absoluta (0-29), depois *32 em 16 bits
    lda #$00
    sta tmp+1
    asl tmp
    rol tmp+1
    asl tmp
    rol tmp+1
    asl tmp
    rol tmp+1
    asl tmp
    rol tmp+1
    asl tmp
    rol tmp+1
    lda tmp
    clc
    adc caixacol_lo_tab, x
    sta ptr
    lda tmp+1
    adc caixacol_hi_tab, x
    sta ptr+1

    ldy #$00
:   lda (ptr), y
    sta PPUDATA
    iny
    cpy #16
    bne :-
    rts

poe_atributos:
    ldx dlg_box
    bit PPUSTATUS
    lda #$23
    sta PPUADDR
    lda atrib1_tab, x
    sta PPUADDR
    lda #ATRIB_PAL2
    ldy #$04
:   sta PPUDATA
    dey
    bne :-

    bit PPUSTATUS
    lda #$23
    sta PPUADDR
    lda atrib2_tab, x        ; X ainda e dlg_box
    sta PPUADDR
    lda #ATRIB_PAL2
    ldy #$04
:   sta PPUDATA
    dey
    bne :-
    rts

restaura_atributos:
    ldx dlg_box
    lda restoff1_tab, x
    clc
    adc #<(nam_cena + 960)
    sta ptr
    lda #>(nam_cena + 960)
    adc #$00
    sta ptr+1

    bit PPUSTATUS
    lda #$23
    sta PPUADDR
    lda atrib1_tab, x
    sta PPUADDR
    ldy #$00
:   lda (ptr), y
    sta PPUDATA
    iny
    cpy #$04
    bne :-

    lda restoff2_tab, x
    clc
    adc #<(nam_cena + 960)
    sta ptr
    lda #>(nam_cena + 960)
    adc #$00
    sta ptr+1

    bit PPUSTATUS
    lda #$23
    sta PPUADDR
    lda atrib2_tab, x
    sta PPUADDR
    ldy #$00
:   lda (ptr), y
    sta PPUDATA
    iny
    cpy #$04
    bne :-
    rts

; ==========================================================================
;  Tela: o minigame -- pizzas caem, a Amanda anda embaixo pra pegar.
;
;  E um arcade: depois de alcancar PONTOS_MIN ela ve uma tela de vitoria,
;  mas o jogo continua dali, tipo o foguete do Tetris (jogo_venceu trava
;  a comemoracao pra nao repetir). Se erra ERROS_MAX pizzas, ve uma tela
;  de derrota e pode tentar de novo na hora (B), sem sair pro menu -- ou
;  desistir com START. Antes da primeira pizza cair, uma tela de intro
;  explica o objetivo (fase 3), senao quem joga pela primeira vez nao
;  entende que e um minigame.
; ==========================================================================
atualiza_jogo:
    lda jogo_troca            ; checa_vitoria/checa_derrota so avisam --
    beq @sem_troca             ; trocar de nametable e feito aqui, no topo
    lda #$00                   ; do laco principal, nunca de dentro do laco
    sta jogo_troca              ; de pizzas (ver o comentario em jogo_troca)
    jsr troca_tela_do_estado
@sem_troca:

    lda jogo_fase
    cmp #$03                 ; aguardando o primeiro B: intro na tela
    bne @nao_intro
    lda botoes_novos
    and #BTN_B
    beq @so_desenha
    jsr mostra_jogando
    jmp @so_desenha
@nao_intro:

    cmp #$02                 ; derrota: B tenta de novo, START desiste
    bne @nao_derrota
    jsr toca_triste_tick      ; avanca a fraseszinha triste, se ainda tocando
    lda botoes_novos
    and #BTN_START
    beq @checa_b_derrota
    jmp carrega_menu
@checa_b_derrota:
    lda botoes_novos
    and #BTN_B
    beq @so_desenha
    jsr reinicia_jogo
    jmp @so_desenha
@nao_derrota:

    cmp #$01                 ; vitoria: espera B pra ir pra cena do carro
    bne @jogando
    jsr toca_feliz_tick        ; avanca a fraseszinha feliz, se ainda tocando
    lda botoes_novos
    and #BTN_B
    beq @so_desenha
    jmp carrega_carro

@jogando:
    jsr move_jogador
    jsr atualiza_pizzas
@so_desenha:
    jmp atualiza_oam_jogo

; ---- escolhe a nametable certa pro jogo_fase atual (so vitoria/derrota
; -- a intro e carregada direto por carrega_jogo, fora do laco de pizzas,
; entao nao precisa passar por aqui) ----
troca_tela_do_estado:
    lda jogo_fase
    cmp #$01
    bne @derrota
    lda #<nam_jogo_vitoria
    sta ptr
    lda #>nam_jogo_vitoria
    sta ptr+1
    jmp troca_nametable_jogo
@derrota:
    lda #<nam_jogo_derrota
    sta ptr
    lda #>nam_jogo_derrota
    sta ptr+1
    jmp troca_nametable_jogo

; ---- volta (ou comeca) a jogar: nametable "jogando", fase 0. Usada pra
; sair da intro e (via reinicia_jogo) pra tentar de novo apos a derrota --
; a vitoria agora vai direto pra cena do carro, nao volta mais aqui. ----
mostra_jogando:
    lda #<nam_jogo
    sta ptr
    lda #>nam_jogo
    sta ptr+1
    jsr troca_nametable_jogo
    lda #$00
    sta jogo_fase
    lda #$01
    sta placar_sujo
    rts

; ---- ela perdeu e apertou B: reseta os numeros e comeca de novo, sem
; sair da tela (ver checa_derrota) ----
reinicia_jogo:
    lda #$00
    sta jogo_pontos
    sta jogo_erros
    sta jogo_venceu
    sta pz_ativa
    sta pz_ativa+1
    sta pz_ativa+2
    sta derrota_tocando        ; corta a fraseszinha triste se ainda
    lda #120                    ; estivesse tocando
    sta ultimo_pz_x
    lda #ESPERA_BASE
    sta jogo_espera
    lda #VEL_BASE
    sta jogo_vel
    lda #$01                   ; retoma o refrao de onde musica_para deixou
    sta musica_liga             ; (so 1 byte -- musica_para nao tocou em
    jmp mostra_jogando          ; ch_ptr/ch_wait/ch_vol, nao precisa reiniciar)

; --------------------------------------------------------------------------
;  Move as pizzas ativas, spawna novas e detecta captura ou erro.
;  So roda no laco principal -- nao pode tocar em 'ptr'/'tmp' (da musica).
; --------------------------------------------------------------------------
atualiza_pizzas:
    lda jogo_espera
    beq @tenta_spawn
    dec jogo_espera
    jmp @move
@tenta_spawn:
    jsr spawna_pizza

@move:
    ldx #$00
@loop:
    lda pz_ativa, x
    beq @prox
    lda pz_y, x
    clc
    adc jogo_vel
    sta pz_y, x
    cmp #CAPTURA_Y_MIN
    bcc @prox                ; ainda caindo, nem chegou na faixa
    cmp #CAPTURA_Y_MAX
    bcs @sumiu                ; passou da faixa sem ser pega -- erro

    jsr testa_pega
    bcc @prox                 ; carry limpo = ainda nao encostou nela
    lda #$00
    sta pz_ativa, x
    inc jogo_pontos
    lda #$01
    sta placar_sujo
    jsr som_come
    jsr checa_vitoria
    jmp @prox
@sumiu:
    lda #$00
    sta pz_ativa, x
    inc jogo_erros
    lda #$01
    sta placar_sujo
    jsr som_cai
    jsr checa_derrota
@prox:
    inx
    cpx #$03
    bne @loop
    rts

; ---- a pizza x (indice em X) esta sobre a Amanda? carry = 1 se sim ----
testa_pega:
    lda player_x
    clc
    adc #16
    sta jogo_tmp
    lda pz_x, x
    cmp jogo_tmp
    bcs @nao                  ; pizza inteira a direita da Amanda
    lda pz_x, x
    clc
    adc #16
    sta jogo_tmp
    lda player_x
    cmp jogo_tmp
    bcs @nao                  ; Amanda inteira a direita da pizza
    sec
    rts
@nao:
    clc
    rts

; ---- acha uma pizza livre e a poe caindo no topo, num x aleatorio ----
spawna_pizza:
    ldx #$00
@procura:
    lda pz_ativa, x
    beq @achou
    inx
    cpx #$03
    bne @procura
    rts                        ; as tres estao ocupadas, tenta de novo depois
@achou:
    ; o x fica dentro de +-SALTO_MAX do x da pizza anterior, pra elas nao
    ; saltarem de um extremo ao outro da tela. Calcula base..topo (a faixa
    ; toda, ja dentro da tela) e sorteia um valor DENTRO dela -- nao da pra
    ; so limitar a base e somar um deslocamento fixo: perto de uma borda
    ; isso deixava o topo escapar bem alem de SALTO_MAX pro outro lado.
    lda ultimo_pz_x             ; topo = min(ultimo_pz_x + SALTO_MAX, ANDA_MAX-16)
    clc
    adc #SALTO_MAX
    bcs @topo_estourou          ; passou de 255 -- estourou o teto com certeza
    cmp #(ANDA_MAX-16)
    bcc @tem_topo
@topo_estourou:
    lda #(ANDA_MAX-16)
@tem_topo:
    sta jogo_tmp2                ; jogo_tmp2 = topo

    lda ultimo_pz_x             ; base = max(ultimo_pz_x - SALTO_MAX, ANDA_MIN)
    cmp #(SALTO_MAX + ANDA_MIN)
    bcc @usa_min
    sec
    sbc #SALTO_MAX
    jmp @tem_base
@usa_min:
    lda #ANDA_MIN
@tem_base:
    sta jogo_tmp                ; jogo_tmp = base

    lda jogo_tmp2                ; jogo_tmp2 = (topo - base) + 1 = tamanho da faixa
    sec
    sbc jogo_tmp
    clc
    adc #$01
    sta jogo_tmp2

    jsr avanca_rng
    lda rng_seed
@mod:
    cmp jogo_tmp2                ; reduz pro tamanho da faixa
    bcc @tem_delta
    sbc jogo_tmp2
    jmp @mod
@tem_delta:
    clc
    adc jogo_tmp                 ; x = base + deslocamento, sempre dentro da faixa
    sta pz_x, x
    sta ultimo_pz_x
    lda #26                    ; nasce logo abaixo da faixa vermelha do topo
    sta pz_y, x
    lda #$01
    sta pz_ativa, x

    ; a dificuldade sobe aos poucos com a pontuacao
    lda jogo_pontos
    lsr
    lsr
    sta jogo_tmp                ; pontos/4

    lda #ESPERA_BASE
    sec
    sbc jogo_tmp
    cmp #ESPERA_MIN
    bcs @espera_ok
    lda #ESPERA_MIN
@espera_ok:
    sta jogo_espera

    lda #VEL_BASE
    clc
    adc jogo_tmp
    cmp #VEL_MAX
    bcc @vel_ok
    lda #VEL_MAX
@vel_ok:
    sta jogo_vel
    rts

; ---- LFSR de 8 bits; mistura o frame_count pra nunca travar em zero ----
avanca_rng:
    lda rng_seed
    asl
    bcc @sem_eor
    eor #$1D
@sem_eor:
    eor frame_count
    sta rng_seed
    rts

checa_vitoria:
    lda jogo_venceu
    bne @fim
    lda jogo_pontos
    cmp #PONTOS_MIN
    bcc @fim
    lda #$01
    sta jogo_venceu
    sta jogo_fase
    sta jogo_troca             ; atualiza_jogo troca a tela no topo do
                                 ; laco principal (nao daqui -- checa_vitoria
                                 ; roda dentro do laco de pizzas)
    lda #$00                   ; esconde qualquer pizza que ainda estivesse
    sta pz_ativa                ; caindo -- senao ela fica flutuando parada
    sta pz_ativa+1               ; por cima da tela de vitoria/derrota
    sta pz_ativa+2

    jsr musica_para              ; pausa o refrao, mesmo esquema da derrota
    lda #$01
    sta vitoria_tocando
    lda #VITORIA_ESPERA_INICIAL
    sta vitoria_espera
    jsr toca_feliz1               ; a primeira nota toca na hora
@fim:
    rts

; ---- avanca a fraseszinha feliz (notas 2-4) -- chamada todo quadro
; enquanto jogo_fase==1, do laco principal (ver atualiza_jogo) ----
toca_feliz_tick:
    lda vitoria_tocando
    beq @fim
    dec vitoria_espera
    lda vitoria_espera
    cmp #VITORIA_NOTA2
    bne @nao_nota2
    jsr toca_feliz2
@nao_nota2:
    lda vitoria_espera
    cmp #VITORIA_NOTA3
    bne @nao_nota3
    jsr toca_feliz3
@nao_nota3:
    lda vitoria_espera
    cmp #VITORIA_NOTA4
    bne @fim
    jsr toca_feliz4
    lda #$00
    sta vitoria_tocando          ; acabou -- para de contar
@fim:
    rts

checa_derrota:
    lda jogo_erros
    cmp #ERROS_MAX
    bcc @fim
    lda #$02
    sta jogo_fase
    lda #$01
    sta jogo_troca
    lda #$00                   ; esconde qualquer pizza que ainda estivesse
    sta pz_ativa                ; caindo (mesmo motivo do checa_vitoria)
    sta pz_ativa+1
    sta pz_ativa+2

    jsr musica_para             ; pausa o refrao -- so registrador/A, seguro
    lda #$01                    ; chamar daqui de dentro do laco de pizzas
    sta derrota_tocando
    lda #DERROTA_ESPERA_INICIAL
    sta derrota_espera
    jsr toca_triste1             ; a primeira nota toca na hora
@fim:
    rts

; ---- avanca a fraseszinha triste (notas 2-4) -- chamada todo quadro
; enquanto jogo_fase==2, do laco principal (ver atualiza_jogo) ----
toca_triste_tick:
    lda derrota_tocando
    beq @fim
    dec derrota_espera
    lda derrota_espera
    cmp #DERROTA_NOTA2
    bne @nao_nota2
    jsr toca_triste2
@nao_nota2:
    lda derrota_espera
    cmp #DERROTA_NOTA3
    bne @nao_nota3
    jsr toca_triste3
@nao_nota3:
    lda derrota_espera
    cmp #DERROTA_NOTA4
    bne @fim
    jsr toca_triste4
    lda #$00
    sta derrota_tocando         ; acabou -- para de contar
@fim:
    rts

; --------------------------------------------------------------------------
;  Efeitos sonoros no canal de ruido. A musica so usa os dois pulsos e o
;  triangulo -- o ruido fica livre o jogo inteiro -- e o contador de
;  duracao do proprio APU desliga o som sozinho, sem precisar de um quadro
;  de "desligar" depois (diferente do tique da fala, que e so 1 quadro e
;  por isso e desligado a mao). Por isso da pra chamar do laco principal
;  sem tocar em nada que o NMI/musica usem.
; --------------------------------------------------------------------------
som_come:
    lda #$0C                ; volume com decaimento, velocidade media
    sta $400C
    lda #$03                ; ruido branco, periodo curto -- som agudo e seco
    sta $400E
    lda #$48                ; duracao curta (~streaming de umas poucas notas)
    sta $400F
    rts

som_cai:
    lda #$09                ; decaimento um pouco mais rapido
    sta $400C
    lda #$0A                ; periodo mais longo -- som mais grave, de baque
    sta $400E
    lda #$68                ; duracao um pouco maior que o som_come
    sta $400F
    rts

; --------------------------------------------------------------------------
;  Monta a OAM do minigame: a Amanda (sprites 0-7, o mesmo monta_oam da
;  pizzaria) e ate 3 pizzas (sprites 8-13, 2 tiles cada). Na derrota
;  (fase 2), o bonequinho dela some da tela -- so o retrato grande e
;  triste fica, ate ela apertar B pra tentar de novo (ver reinicia_jogo).
; --------------------------------------------------------------------------
atualiza_oam_jogo:
    lda jogo_fase
    cmp #$02
    bne @com_amanda
    ldx #$00
@esconde_amanda:
    lda #$FF
    sta oam, x
    inx
    inx
    inx
    inx
    cpx #$20                 ; sprites 0-7 = bytes 0-31
    bne @esconde_amanda
    jmp @pizzas
@com_amanda:
    jsr monta_oam
@pizzas:
    ldx #$00
    ldy #$20                 ; sprite 8 = byte 32
@loop:
    lda pz_ativa, x
    beq @esconde
    lda pz_y, x
    sta oam, y
    sta oam+4, y
    lda #TILE_PIZZA
    sta oam+1, y
    lda #(TILE_PIZZA+1)
    sta oam+5, y
    lda #$02                 ; paleta 2 (so a pizza usa, nesta tela)
    sta oam+2, y
    sta oam+6, y
    lda pz_x, x
    sta oam+3, y
    clc
    adc #$08
    sta oam+7, y
    jmp @prox
@esconde:
    lda #$FF
    sta oam, y
    sta oam+4, y
@prox:
    tya
    clc
    adc #$08
    tay
    inx
    cpx #$03
    bne @loop
    rts

; --------------------------------------------------------------------------
;  HUD: a barra de pontos (PONTOS_MIN segmentos) e as vidas (ERROS_MAX
;  iconezinhos), escritas no fundo. So redesenha quando 'placar_sujo'
;  pede -- roda no NMI, pode usar ptr/tmp (a musica toca depois, na mesma
;  chamada, nunca ao mesmo tempo). BARRA_ADDR/VIDAS_ADDR nunca cruzam uma
;  pagina de 256 bytes (15 e 5 tiles, respectivamente), entao da pra somar
;  o indice direto no byte baixo sem se preocupar com o carry.
; --------------------------------------------------------------------------
desenha_hud:
    lda jogo_fase             ; so faz sentido jogando -- nas telas de
    bne @fim                   ; intro/vitoria/derrota, BARRA_ADDR/VIDAS_ADDR
    lda placar_sujo             ; caem em cima do desenho delas, nao do HUD
    beq @fim
    lda #$00
    sta placar_sujo

    ldx #$00
@loop_barra:
    txa
    cmp jogo_pontos
    lda #UI_BARRA_VAZIA
    bcs @poe_barra           ; X >= jogo_pontos: esse segmento ainda nao foi
    lda #UI_BARRA_CHEIA
@poe_barra:
    pha
    bit PPUSTATUS
    lda #>BARRA_ADDR
    sta PPUADDR
    txa
    clc
    adc #<BARRA_ADDR
    sta PPUADDR
    pla
    sta PPUDATA
    inx
    cpx #PONTOS_MIN
    bne @loop_barra

    ldx #$00
@loop_vidas:
    txa
    cmp jogo_erros
    lda #UI_VIDA_VAZIA
    bcc @poe_vida             ; X < jogo_erros: essa vida ja foi perdida
    lda #UI_VIDA_CHEIA
@poe_vida:
    pha
    bit PPUSTATUS
    lda #>VIDAS_ADDR
    sta PPUADDR
    txa
    clc
    adc #<VIDAS_ADDR
    sta PPUADDR
    pla
    sta PPUDATA
    inx
    cpx #ERROS_MAX
    bne @loop_vidas
@fim:
    rts

; ==========================================================================
;  Video: ligar, desligar, copiar
; ==========================================================================
desliga_tela:
    lda #$00
    sta PPUMASK             ; a tela apaga; so assim da pra escrever a vontade
    sta PPUCTRL             ; e sem NMI mexendo no meio
    rts

liga_tela:
    ; Manda a OAM pro PPU ANTES de acender a tela. A tabela de sprites de
    ; dentro do PPU nasce com lixo, e so o DMA a limpa -- sem isso, o console
    ; real mostra um quadro de sprites aleatorios ate o primeiro NMI. Em
    ; emulador ela costuma nascer zerada, entao o defeito nao aparece.
    lda #$00
    sta OAMADDR
    lda #>oam
    sta OAMDMA

    lda #$00
    sta PPUSCROLL
    sta PPUSCROLL
    lda #%10010000          ; NMI ligado, fundo na pattern table 1
    sta PPUCTRL
    lda #%00011110          ; mostra fundo e sprites, inclusive na borda
    sta PPUMASK
    rts

; --------------------------------------------------------------------------
;  Rolagem horizontal da cena do carro -- roda todo NMI (ver nmi). Escreve
;  o proprio PPUSCROLL/PPUCTRL (por isso pula o @scroll generico de 0,0) e
;  incrementa carro_scroll: quando ele da a volta em 256, alterna
;  carro_nt -- e assim que os 512px das duas nametables coladas (ver
;  make_carro.py) viram um scroll continuo de 0 a 511 que da a volta
;  sozinho, sem custura, porque o desenho e periodico nesse tamanho.
; --------------------------------------------------------------------------
atualiza_scroll_carro:
    lda carro_scroll
    sta PPUSCROLL
    lda #$00
    sta PPUSCROLL             ; sem scroll vertical

    lda #%10010000            ; os mesmos bits fixos de liga_tela...
    ora carro_nt                ; ...mais qual nametable esta na base
    sta PPUCTRL

    inc carro_scroll           ; anda 1px por quadro -- de proposito devagar,
    bne @fim                    ; um passeio, nao uma corrida
    lda carro_nt
    eor #$01
    sta carro_nt
@fim:
    rts

; ---- copia 'paginas' x 256 bytes de (ptr) pra onde PPUADDR aponta ----
copia_ppu:
    ldy #$00
@loop:
    lda (ptr), y
    sta PPUDATA
    iny
    bne @loop
    inc ptr+1
    dec paginas
    bne @loop
    rts

; ---- 32 bytes de paleta a partir de (ptr) ----
carrega_paletas:
    bit PPUSTATUS
    PPU_ADDR $3F00
    ldy #$00
:   lda (ptr), y
    sta PPUDATA
    iny
    cpy #32
    bne :-
    rts

; ==========================================================================
;  NMI -- uma vez por quadro, na unica janela segura pra mexer no video
; ==========================================================================
nmi:
    pha
    txa
    pha
    tya
    pha

    inc frame_count

    lda carregando          ; montando tela? entao o video e do carregador
    bne @so_musica

    lda #$00                ; manda os sprites pro PPU
    sta OAMADDR
    lda #>oam
    sta OAMDMA

    lda tela
    beq @menu
    cmp #TELA_CENA
    beq @cena
    cmp #TELA_CARRO
    beq @carro
    jsr desenha_hud          ; so sobra TELA_JOGO aqui
    jmp @scroll
@menu:
    jsr pulsa_coracao
    jsr apaga_aviso_start
    jmp @scroll
@cena:
    jsr passo_dialogo
    jmp @scroll
@carro:
    jsr atualiza_scroll_carro   ; escreve o proprio PPUSCROLL/PPUCTRL --
    jmp @so_musica               ; pula o @scroll generico (0,0) abaixo

@scroll:
    lda #$00
    sta PPUSCROLL
    sta PPUSCROLL

@so_musica:
    jsr musica_tick
    inc nmi_flag

    pla
    tay
    pla
    tax
    pla
    rti

irq:
    rti

; ==========================================================================
;  Engine de musica -- tres canais, um passo por quadro
; ==========================================================================
musica_init:
    lda #$00
    sta $4001
    sta $4005
    lda #$0F
    sta $4015
    jmp musica_para

; --------------------------------------------------------------------------
;  Troca a musica ativa (A = indice, ver musica_offset/MUSICAS). So chame
;  entre desliga_tela/liga_tela: com o NMI desligado da pra escrever
;  ch_ptr_lo/hi em duas passadas sem risco da musica ler o par pela metade.
; --------------------------------------------------------------------------
troca_musica:
    tax
    lda musica_offset, x
    tay                      ; y = indice inicial dessa musica em fluxo_lo/hi
    ldx #$00                 ; x = canal (0..2)
@canal:
    lda fluxo_lo, y
    sta ch_ptr_lo, x
    sta ch_base_lo, x
    lda fluxo_hi, y
    sta ch_ptr_hi, x
    sta ch_base_hi, x
    lda #$01
    sta ch_wait, x
    lda #$00
    sta ch_vol, x
    sta ch_atk, x
    iny
    inx
    cpx #$03
    bne @canal
    lda #$01
    sta musica_liga
    rts

; --------------------------------------------------------------------------
;  Silencia as 3 vozes e desliga o motor -- o menu fica sem musica. Tambem
;  so chame entre desliga_tela/liga_tela, pelo mesmo motivo de troca_musica.
; --------------------------------------------------------------------------
musica_para:
    lda #$00
    sta musica_liga
    sta $4000                ; quadrada 1: volume 0
    sta $4004                ; quadrada 2: volume 0
    sta $4008                ; triangulo: contador linear 0
    rts

; --------------------------------------------------------------------------
;  O "plin" do menu, tocado no START antes de entrar na pizzaria. Uma nota
;  so, pulso 2 -- livre nesse instante porque o motor de 3 canais ainda
;  esta desligado (musica_liga=0). Usa o proprio decaimento de hardware do
;  APU (contador de duracao) em vez do motor manual: mais simples pra um
;  efeito instantaneo que a musica nem vai acompanhar.
; --------------------------------------------------------------------------
toca_plin:
    lda #%10011111           ; duty 50%, volume constante 15, sem "halt" (bit5=0)
    sta $4004                ; (sem halt = o contador de duracao decai sozinho)
    lda per_lo + PLIN_NOTA
    sta $4006
    lda per_hi + PLIN_NOTA
    ora #(9 << 3)             ; contador de duracao curto (indice 9 = 8 quadros)
    sta $4007
    rts

; --------------------------------------------------------------------------
;  O "eco" do plin: a mesma nota de novo, mais baixa a cada vez, no pulso 1
;  (o outro canal livre nesse instante). Nao existe eco de verdade no APU
;  do NES -- sem linha de atraso --, entao a imitacao e essa: repetir o som
;  mais fraco e um pouco depois, tocado por MENU_ESPERA_ECO1/2 em cima do
;  contador que ja existia pra dar tempo do plin original tocar sozinho.
;  Duty 25% (mais fino que os 50% do plin) ajuda a diferenciar do original.
; --------------------------------------------------------------------------
toca_eco1:
    lda #%01011001           ; duty 25%, volume constante 9
    sta $4000
    lda per_lo + PLIN_NOTA
    sta $4002
    lda per_hi + PLIN_NOTA
    ora #(9 << 3)
    sta $4003
    rts

toca_eco2:
    lda #%01010101           ; duty 25%, volume constante 5 -- o mais fraco
    sta $4000
    lda per_lo + PLIN_NOTA
    sta $4002
    lda per_hi + PLIN_NOTA
    ora #(9 << 3)
    sta $4003
    rts

; --------------------------------------------------------------------------
;  A fraseszinha triste da derrota (B3-G3-E3-D3, ver TRISTE em
;  tools/make_song.py), disparada por checa_derrota + o contador
;  derrota_espera (ver atualiza_jogo). Toca no pulso 2 -- livre porque
;  musica_para ja pausou o motor de 3 canais nesse instante -- com duty
;  12.5% (mais fino, pra nao confundir com o "plin" nem o eco, que usam
;  50%/25%) e um diminuendo leve de uma nota pra outra. Indice 14 no
;  contador de duracao = 26 quadros, quase encostando na proxima nota
;  (DERROTA_PASSO=25): mais sustentado que o "plin" (indice 9 = 8
;  quadros), pra soar mais choroso que staccato.
; --------------------------------------------------------------------------
toca_triste1:
    lda #%00011100           ; duty 12.5%, volume constante 12
    sta $4004
    lda per_lo + TRISTE_NOTA1
    sta $4006
    lda per_hi + TRISTE_NOTA1
    ora #(14 << 3)
    sta $4007
    rts

toca_triste2:
    lda #%00011011           ; volume 11
    sta $4004
    lda per_lo + TRISTE_NOTA2
    sta $4006
    lda per_hi + TRISTE_NOTA2
    ora #(14 << 3)
    sta $4007
    rts

toca_triste3:
    lda #%00011010           ; volume 10
    sta $4004
    lda per_lo + TRISTE_NOTA3
    sta $4006
    lda per_hi + TRISTE_NOTA3
    ora #(14 << 3)
    sta $4007
    rts

toca_triste4:
    lda #%00011000           ; volume 8 -- a mais fraca, o suspiro final
    sta $4004
    lda per_lo + TRISTE_NOTA4
    sta $4006
    lda per_hi + TRISTE_NOTA4
    ora #(14 << 3)
    sta $4007
    rts

; --------------------------------------------------------------------------
;  O espelho do toca_triste: a fraseszinha feliz da vitoria (G3-B3-D4-G4,
;  ver FELIZ em tools/make_song.py), disparada por checa_vitoria + o
;  contador feliz_espera (ver atualiza_jogo). Duty 50% e crescendo de
;  volume (ao contrario do diminuendo triste) pra soar animado, tipo um
;  "ta-da" -- e o mesmo pulso 2 (o refrao ja pausou nesse instante, ver
;  musica_para). Indice 9 no contador de duracao = 8 quadros: mais curta
;  e seca que a triste (indice 14), pra soar alegre/pontuada em vez de
;  choroza.
; --------------------------------------------------------------------------
toca_feliz1:
    lda #%10011010            ; duty 50%, volume constante 10
    sta $4004
    lda per_lo + FELIZ_NOTA1
    sta $4006
    lda per_hi + FELIZ_NOTA1
    ora #(9 << 3)
    sta $4007
    rts

toca_feliz2:
    lda #%10011100            ; volume 12
    sta $4004
    lda per_lo + FELIZ_NOTA2
    sta $4006
    lda per_hi + FELIZ_NOTA2
    ora #(9 << 3)
    sta $4007
    rts

toca_feliz3:
    lda #%10011101            ; volume 13
    sta $4004
    lda per_lo + FELIZ_NOTA3
    sta $4006
    lda per_hi + FELIZ_NOTA3
    ora #(9 << 3)
    sta $4007
    rts

toca_feliz4:
    lda #%10011111            ; volume 15 -- o "ta-da" final, no maximo
    sta $4004
    lda per_lo + FELIZ_NOTA4
    sta $4006
    lda per_hi + FELIZ_NOTA4
    ora #(10 << 3)             ; indice 10 = 60 quadros -- segura o "ta-da" final
    sta $4007
    rts

musica_tick:
    lda musica_liga
    beq @fim
    ldx #$00
@canal:
    dec ch_wait, x
    bne @volume
    jsr proxima_nota
@volume:
    jsr aplica_volume
    inx
    cpx #$03
    bne @canal
@fim:
    rts

proxima_nota:
    lda ch_ptr_lo, x
    sta ptr
    lda ch_ptr_hi, x
    sta ptr+1
    ldy #$00
    lda (ptr), y
    cmp #$FF
    bne @tem_nota

    lda ch_base_lo, x       ; fim do fluxo: a musica volta pro comeco (da musica ativa)
    sta ptr
    sta ch_ptr_lo, x
    lda ch_base_hi, x
    sta ptr+1
    sta ch_ptr_hi, x
    lda (ptr), y

@tem_nota:
    sta ch_note, x
    iny
    lda (ptr), y
    sta ch_wait, x

    lda ch_ptr_lo, x
    clc
    adc #$02
    sta ch_ptr_lo, x
    bcc @sem_vira
    inc ch_ptr_hi, x
@sem_vira:
    lda #$0F
    sta ch_vol, x
    lda #$01
    sta ch_atk, x

escreve_periodo:
    ldy ch_note, x
    beq @pausa
    cpx #$02
    beq @triangulo

    lda per_lo, y
    sta tmp
    lda per_hi, y
    sta tmp+1
    txa
    asl
    asl
    tay
    lda tmp
    sta $4002, y
    lda tmp+1
    sta $4003, y            ; reinicia a onda: e o ataque da nota
    rts

@triangulo:
    lda tri_lo, y
    sta $400A
    lda tri_hi, y
    sta $400B
    lda #$FF
    sta $4008
    rts

@pausa:
    cpx #$02
    beq @cala_triangulo
    lda #$00
    sta ch_vol, x
    rts
@cala_triangulo:
    lda #$00
    sta $4008
    rts

aplica_volume:
    cpx #$02
    beq @fim                ; o triangulo nao tem controle de volume

    lda ch_atk, x
    beq @talvez_decai
    lda #$00
    sta ch_atk, x
    beq @escreve

@talvez_decai:
    lda frame_count
    and #$01
    bne @escreve
    lda ch_vol, x
    cmp #$05
    bcc @escreve
    dec ch_vol, x

@escreve:
    txa
    asl
    asl
    tay
    lda ch_vol, x
    ora #$30
    ora duty_canal, x
    sta $4000, y
@fim:
    rts

; ==========================================================================
;  Dados
; ==========================================================================
duty_canal:  .byte $40, $80, $00
musica_offset: .byte 0, 3     ; onde cada musica comeca em fluxo_lo/hi (3 canais cada)
; Amanda: 8 tiles, coluna esquerda de cima a baixo e depois a direita
ama_dx:      .byte 0, 0, 0, 0,  8, 8, 8, 8
ama_dx_esp:  .byte 8, 8, 8, 8,  0, 0, 0, 0
ama_dy:      .byte 0, 8, 16, 24, 0, 8, 16, 24
; pernas reaproveitam a paleta do tronco (1) -- ver make_sprites.py sobre
; por que elas nao precisam mais de paleta propria
ama_pal:     .byte 0, 0, 1, 1,  0, 0, 1, 1
; Victor: 6 tiles (cabeca, cabeca, TORSO, cabeca, cabeca, TORSO -- ver fatiar
; em make_sprites.py). O torso usa a paleta 3, com o logo da Nike ciano.
vic_dx:      .byte 0, 0, 0,  8, 8, 8
vic_dy:      .byte 0, 8, 16, 0, 8, 16
vic_pal:     .byte 2, 2, 3, 2, 2, 3
; Victor em pe: 8 tiles, coluna esquerda de cima a baixo (cabeca, cabeca,
; torso, pernas) e depois a direita -- mesmo padrao da Amanda. As pernas
; reaproveitam a paleta 2 (cabeca): sao pretas, sem pele exposta, entao nao
; colidem com o tom de pele nela (ver make_sprites.py sobre o chao/pele).
vic_empe_dx: .byte 0, 0, 0, 0,  8, 8, 8, 8
vic_empe_dy: .byte 0, 8, 16, 24, 0, 8, 16, 24
vic_empe_pal:.byte 2, 2, 3, 2,  2, 2, 3, 2

; pecas da moldura, por tipo de linha: topo, meio, base
borda_esq:   .byte TILE_BORDA+0, TILE_BORDA+3, TILE_BORDA+5
borda_meio:  .byte TILE_BORDA+1, TILE_BRANCO,  TILE_BORDA+6
borda_dir:   .byte TILE_BORDA+2, TILE_BORDA+4, TILE_BORDA+7

; ---- as duas caixas de fala (por QUEM fala): [0] = Victor, [1] = Amanda ----
; mesma LINHA pros dois (CAIXA_ROW), acima dos sprites -- so a COLUNA
; diferencia (CAIXA_COL_VICTOR/CAIXA_COL_AMANDA, ver comentario mais
; acima). Cada tabela e so essa mesma conta (endereco = pagina + linha*32
; + coluna, ou o bloco de atributo correspondente) feita pra cada coluna.
; inicio_fala_tab/fim_fala_tab/falante_tab (por PARTE do dialogo, nao por
; caixa) vem geradas em dialogo.inc.
boxrow_tab:      .byte CAIXA_ROW, CAIXA_ROW
caixa_pag_tab:   .byte $21, $21                          ; byte alto -- so a LINHA muda
                                                           ; a pagina, e ela e igual pros dois
caixa_baixo_tab: .byte CAIXA_COL_VICTOR, CAIXA_COL_AMANDA          ; linha 0 da caixa
nome_baixo_tab:  .byte 32+CAIXA_COL_VICTOR+1, 32+CAIXA_COL_AMANDA+1 ; linha 1 (nome)
texto_baixo_tab: .byte 64+CAIXA_COL_VICTOR+1, 64+CAIXA_COL_AMANDA+1 ; linha 2 (texto)
caixacol_lo_tab: .byte <(nam_cena+CAIXA_COL_VICTOR), <(nam_cena+CAIXA_COL_AMANDA)
caixacol_hi_tab: .byte >(nam_cena+CAIXA_COL_VICTOR), >(nam_cena+CAIXA_COL_AMANDA)
; endereco de atributo = $23C0 + (linha//4)*8 + (coluna//4) -- CAIXA_ROW=8
; cai certinho no limite de um bloco (linha//4 = 2 no topo da caixa, 3 na
; base, 4 linhas depois)
atrib1_tab:      .byte $C0+(CAIXA_ROW/4)*8+CAIXA_COL_VICTOR/4, $C0+(CAIXA_ROW/4)*8+CAIXA_COL_AMANDA/4
atrib2_tab:      .byte $C0+(CAIXA_ROW/4+1)*8+CAIXA_COL_VICTOR/4, $C0+(CAIXA_ROW/4+1)*8+CAIXA_COL_AMANDA/4
restoff1_tab:    .byte (CAIXA_ROW/4)*8+CAIXA_COL_VICTOR/4, (CAIXA_ROW/4)*8+CAIXA_COL_AMANDA/4
restoff2_tab:    .byte (CAIXA_ROW/4+1)*8+CAIXA_COL_VICTOR/4, (CAIXA_ROW/4+1)*8+CAIXA_COL_AMANDA/4

txt_victor:  .byte "VICTOR", $00
txt_amanda:  .byte "AMANDA", $00
txt_aviso_start: .byte "APERTE START PARA COMECAR", $00

pulso:       .byte $16, $26, $36, $26, $16, $06, $06, $06

paletas_menu:
    .byte $0F, $30, $10, $00
    .byte $0F, $06, $16, $36
    .byte $0F, $00, $00, $00
    .byte $0F, $00, $00, $00
    .byte $0F, $30, $16, $27
    .byte $0F, $30, $21, $11
    .byte $0F, $30, $30, $30
    .byte $0F, $30, $30, $30

paletas_cena:
    .incbin "cena.pal"

paletas_jogo:
    .incbin "jogo.pal"

paletas_carro:
    .incbin "carro.pal"

.include "musica.inc"
.include "dialogo.inc"
.include "jogo.inc"
.include "carro.inc"

.segment "VECTORS"
    .word nmi, reset, irq
