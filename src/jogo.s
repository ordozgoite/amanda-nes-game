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

; ---- telas ----
TELA_MENU = 0
TELA_CENA = 1

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

; ---- personagens ----
; A Amanda tem 16x32 (2 tiles de largura por 4 de altura, 8 sprites).
; O Victor tem 16x24 e fica parado, sentado a mesa da frente.
ANDA_MIN    = 8
ANDA_MAX    = 232
CHAO_Y      = 192
TILE_VICTOR = 16
VICTOR_X    = 176   ; atras da mesa, com a bandeja na frente dele
VICTOR_Y    = 152
PERTO_MIN   = 152   ; faixa de x em que o aviso aparece
PERTO_MAX   = 201
TILE_BOCA_E = 22    ; Victor de boca aberta
TILE_BOCA_D = 23
TILE_AVISO  = 24    ; a caixinha do "B"

; O balao de fala ocupa colunas 4-19, linhas 8-15. Esses limites nao sao
; arbitrarios: alinhados assim, os blocos de atributo caem inteiros dentro
; da caixa, e a paleta dela nao vaza pro cenario em volta.
CAIXA_ALTO  = $21   ; byte alto de todos os enderecos da caixa
CAIXA_COL   = 8     ; colunas 8-23: fica bem acima da cabeca do Victor
CAIXA_BAIXO = $08   ; $2108 = linha 8, coluna 8
TEXTO_BAIXO = $29   ; $2129 = linha 9, coluna 9
ATRIB_1     = $D2   ; $23D2 e $23DA: os 8 bytes de atributo da caixa
ATRIB_2     = $DA
ATRIB_PAL2  = $AA   ; os quatro quadrantes na paleta 2

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
dlg_txt:     .res 1         ; qual linha de fala
dlg_col:     .res 1         ; coluna dentro da linha
dlg_wait:    .res 1
dlg_tipo:    .res 1
perto:       .res 1         ; 1 = a Amanda esta ao alcance do Victor
oam_attr:    .res 1         ; proprio da OAM: 'tmp' e da musica, que roda no NMI

; --- musica ---
ch_ptr_lo:   .res 3
ch_ptr_hi:   .res 3
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
    bne @cena
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
    lda botoes_novos
    and #BTN_START
    beq @fim
    jsr carrega_cena
@fim:
    rts

carrega_menu:
    lda #$01
    sta carregando
    jsr desliga_tela

    lda #BANCO_MENU
    jsr troca_banco

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
    jsr boca_victor
    jsr monta_oam
    jmp aviso_b

@livre:
    lda botoes_novos
    and #BTN_START
    beq @anda
    jmp carrega_menu        ; START volta pro titulo

@anda:
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
    bne @perto
    lda player_frame
    eor #$01
    sta player_frame
    jmp @perto
@parado:
    lda #$00
    sta player_frame
    sta player_anim

@perto:
    jsr calcula_perto
    lda perto
    beq @sprites
    lda botoes_novos
    and #BTN_B
    beq @sprites
    lda #$01                ; abre o balao
    sta dialogo
    lda #$00
    sta dlg_lin

@sprites:
    jsr boca_victor
    jsr monta_oam
    jmp aviso_b

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
;  O aviso "B" flutuando sobre a cabeca dele (sprites 14 e 15)
; --------------------------------------------------------------------------
aviso_b:
    ldy #$38                ; sprite 14 = byte 56 da OAM
    lda dialogo
    bne @esconde
    lda perto
    beq @esconde

    lda frame_count         ; sobe e desce 2 pixels, pra chamar atencao
    and #$10
    beq @baixo
    lda #(VICTOR_Y - 14)
    bne @poe
@baixo:
    lda #(VICTOR_Y - 12)
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
    lda #VICTOR_X
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
;  A boca dele abre e fecha enquanto o texto sai
; --------------------------------------------------------------------------
boca_victor:
    lda dialogo
    cmp #$02                ; so mexe a boca enquanto esta escrevendo
    bne @fechada
    lda frame_count
    and #$08
    beq @fechada
    lda #TILE_BOCA_E
    sta oam+37
    lda #TILE_BOCA_D
    sta oam+49
    rts
@fechada:
    lda #17
    sta oam+37
    lda #20
    sta oam+49
    rts

; --------------------------------------------------------------------------
carrega_cena:
    lda #$01
    sta carregando
    jsr desliga_tela

    lda #BANCO_CENA
    jsr troca_banco

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
    lda #2
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
    jsr oam_victor          ; ele ja esta la, sentado, esperando

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
    jsr monta_oam
    jsr aviso_b

    lda #TELA_CENA
    sta tela
    lda #$00
    sta carregando
    jmp liga_tela

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
;  O Victor sentado. Nao se move, entao a OAM dele e montada uma vez so,
;  na entrada da cena, a partir do sprite 8.
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

    lda #$02                ; paleta 2
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
    lda #$00
    sta dlg_txt
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
    lda #$00
    sta dialogo
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
    lda #CAIXA_ALTO
    sta PPUADDR
    lda dlg_lin
    asl
    asl
    asl
    asl
    asl                     ; linha * 32
    clc
    adc #CAIXA_BAIXO
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
    lda dlg_txt
    cmp #N_FALAS
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
    lda #CAIXA_ALTO
    sta PPUADDR
    lda dlg_txt
    asl
    asl
    asl
    asl
    asl                     ; linha do texto * 32
    clc
    adc #TEXTO_BAIXO
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

; ---- devolve uma linha do cenario, lida de volta da ROM ----
restaura_linha:
    bit PPUSTATUS
    lda #CAIXA_ALTO
    sta PPUADDR
    lda dlg_lin
    asl
    asl
    asl
    asl
    asl
    clc
    adc #CAIXA_BAIXO
    sta PPUADDR

    lda dlg_lin             ; nam_cena + (8+linha)*32 + 4
    asl
    asl
    asl
    asl
    asl
    clc
    adc #<(nam_cena + 8*32 + CAIXA_COL)
    sta ptr
    lda #>(nam_cena + 8*32 + CAIXA_COL)
    adc #$00
    sta ptr+1

    ldy #$00
:   lda (ptr), y
    sta PPUDATA
    iny
    cpy #16
    bne :-
    rts

poe_atributos:
    bit PPUSTATUS
    lda #$23
    sta PPUADDR
    lda #ATRIB_1
    sta PPUADDR
    lda #ATRIB_PAL2
    ldx #$04
:   sta PPUDATA
    dex
    bne :-
    lda #$23
    sta PPUADDR
    lda #ATRIB_2
    sta PPUADDR
    lda #ATRIB_PAL2
    ldx #$04
:   sta PPUDATA
    dex
    bne :-
    rts

restaura_atributos:
    bit PPUSTATUS
    lda #$23
    sta PPUADDR
    lda #ATRIB_1
    sta PPUADDR
    ldy #$00
:   lda nam_cena + 960 + 18, y
    sta PPUDATA
    iny
    cpy #$04
    bne :-
    lda #$23
    sta PPUADDR
    lda #ATRIB_2
    sta PPUADDR
    ldy #$00
:   lda nam_cena + 960 + 26, y
    sta PPUDATA
    iny
    cpy #$04
    bne :-
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
    bne @cena
    jsr pulsa_coracao
    jmp @scroll
@cena:
    jsr passo_dialogo

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
    ldx #$02
@canal:
    lda fluxo_lo, x
    sta ch_ptr_lo, x
    lda fluxo_hi, x
    sta ch_ptr_hi, x
    lda #$01
    sta ch_wait, x
    lda #$00
    sta ch_vol, x
    sta ch_atk, x
    dex
    bpl @canal

    lda #$00
    sta $4001
    sta $4005
    lda #$0F
    sta $4015
    rts

musica_tick:
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

    lda fluxo_lo, x         ; fim do fluxo: a musica volta pro comeco
    sta ptr
    sta ch_ptr_lo, x
    lda fluxo_hi, x
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
; Amanda: 8 tiles, coluna esquerda de cima a baixo e depois a direita
ama_dx:      .byte 0, 0, 0, 0,  8, 8, 8, 8
ama_dx_esp:  .byte 8, 8, 8, 8,  0, 0, 0, 0
ama_dy:      .byte 0, 8, 16, 24, 0, 8, 16, 24
ama_pal:     .byte 0, 0, 1, 3,  0, 0, 1, 3
; Victor: 6 tiles
vic_dx:      .byte 0, 0, 0,  8, 8, 8
vic_dy:      .byte 0, 8, 16, 0, 8, 16

; pecas da moldura, por tipo de linha: topo, meio, base
borda_esq:   .byte TILE_BORDA+0, TILE_BORDA+3, TILE_BORDA+5
borda_meio:  .byte TILE_BORDA+1, TILE_BRANCO,  TILE_BORDA+6
borda_dir:   .byte TILE_BORDA+2, TILE_BORDA+4, TILE_BORDA+7

txt_victor:  .byte "VICTOR", $00
txt_amanda:  .byte "AMANDA", $00

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

.include "musica.inc"
.include "dialogo.inc"

.segment "VECTORS"
    .word nmi, reset, irq
