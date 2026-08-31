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

; ---- telas ----
TELA_MENU = 0
TELA_CENA = 1
TELA_JOGO = 2

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
VICTOR_X    = 176   ; atras da mesa, com a bandeja na frente dele
VICTOR_Y    = 152
PERTO_MIN   = 152   ; faixa de x em que o aviso aparece
PERTO_MAX   = 201
TILE_BOCA_E = 22    ; Victor de boca aberta
TILE_BOCA_D = 23
TILE_AVISO  = 24    ; a caixinha do "B"
TILE_AMA_BOCA_E = 28  ; Amanda de boca aberta (so na caixa dela)
TILE_AMA_BOCA_D = 29

; O balao de fala fica sempre nas colunas 8-23 (16 tiles), mas muda de
; LINHA conforme quem esta falando: caixa 0 (Victor) comeca na linha 8,
; caixa 1 (Amanda) comeca na 16 -- mais perto de onde ela fica parada.
; Os limites nao sao arbitrarios: toda linha de topo e multipla de 8
; tiles, entao os blocos de atributo (32x32px cada) caem inteiros dentro
; da caixa nos dois casos, e a paleta dela nao vaza pro cenario em volta.
;
; Como cada caixa ocupa exatamente 8 linhas de tiles (=1 pagina inteira
; de 256 bytes da nametable), o byte BAIXO de todo endereco dentro dela
; e igual nas duas -- so o byte ALTO muda (ver caixa_pag_tab). E por isso
; CAIXA_BAIXO/TEXTO_BAIXO continuam sendo uma constante so.
CAIXA_COL   = 8     ; colunas 8-23
CAIXA_BAIXO = $08   ; $..08 = coluna 8, linha 0 dentro da pagina da caixa
NOME_BAIXO  = $29   ; $..29 = coluna 9, linha 1: o nome de quem fala
TEXTO_BAIXO = $49   ; $..49 = coluna 9, linha 2: a mensagem, uma linha abaixo
ATRIB_PAL2  = $AA   ; os quatro quadrantes na paleta 2

; ---- minigame: pizzas caindo ----
; A faixa de captura e generosa de proposito (24px, quase a altura toda do
; sprite da Amanda) -- e um presente, nao um jogo de reflexo apertado.
TILE_PIZZA      = 26     ; ver tools/make_sprites.py
PONTOS_MIN      = 15     ; pontuacao que dispara a comemoracao
ERROS_MAX       = 5      ; erros que encerram a rodada
ESPERA_BASE     = 90     ; quadros entre pizzas, no comeco
ESPERA_MIN      = 30     ; nunca mais rapido que isso
SALTO_MAX       = 80     ; o x de uma pizza fica a no maximo isso do x da anterior
VEL_BASE        = 1      ; pixels por quadro, no comeco
VEL_MAX         = 3
DURACAO_COMEMORA = 90    ; quadros que a comemoracao fica na tela
CAPTURA_Y_MIN   = CHAO_Y - 4
CAPTURA_Y_MAX   = CHAO_Y + 24
PLACAR_PONTOS   = $2000 + 26        ; linha 0, coluna 26-27: dois digitos
PLACAR_ERROS    = $2000 + 32 + 26   ; linha 1, coluna 26: um digito

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
dlg_box:     .res 1         ; 0 = caixa do Victor, 1 = caixa da Amanda
perto:       .res 1         ; 1 = a Amanda esta ao alcance do Victor
oam_attr:    .res 1         ; proprio da OAM: 'tmp' e da musica, que roda no NMI
abre_jogo:   .res 1         ; 1 = o dialogo fechou; o laco principal troca de tela

; --- minigame: pizzas caindo ---
; 'jogo_tmp' e o scratch do laco principal (nao pode usar 'ptr'/'tmp':
; sao da musica, que roda no NMI a qualquer momento).
jogo_fase:   .res 1         ; 0 jogando, 1 comemorando, 2 fim de jogo
jogo_pontos: .res 1
jogo_erros:  .res 1
jogo_vel:    .res 1
jogo_espera: .res 1
jogo_temp:   .res 1
jogo_venceu: .res 1         ; 1 = ja disparou a comemoracao nesta rodada
jogo_tmp:    .res 1
placar_sujo: .res 1
rng_seed:    .res 1
ultimo_pz_x: .res 1         ; x da ultima pizza que nasceu, pra limitar o salto
pz_x:        .res 3
pz_y:        .res 3
pz_ativa:    .res 3

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
chr_jogo:         .incbin "chr_jogo.bin"      ; ceu, chao e digitos do placar
chr_sprites_jogo:  .incbin "chr_sprites.bin"   ; a mesma folha de sprites da cena
nam_jogo:         .incbin "jogo.nam"          ; tela + atributos (4 paginas)

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
    lda #$01                ; abre o balao
    sta dialogo
    lda #$00
    sta dlg_lin
    sta dlg_box              ; comeca sempre pela caixa do Victor
    sta player_frame          ; a boca aberta so existe no quadro 0 da cabeca

@sprites:
    jsr boca_victor
    jsr monta_oam
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
    lda dlg_box
    bne @fechada             ; caixa da Amanda: a boca dele fica parada
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

    PPU_ADDR $2000           ; a tela pronta, tiles e atributos
    lda #<nam_jogo
    sta ptr
    lda #>nam_jogo
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
    sta jogo_fase
    sta jogo_pontos
    sta jogo_erros
    sta jogo_venceu
    sta pz_ativa
    sta pz_ativa+1
    sta pz_ativa+2
    lda #120                 ; meio da tela: a primeira pizza pode ir pros dois lados
    sta ultimo_pz_x
    lda #ESPERA_BASE
    sta jogo_espera
    lda #VEL_BASE
    sta jogo_vel
    lda #$01
    sta placar_sujo

    jsr atualiza_oam_jogo

    lda #TELA_JOGO
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
    jsr desenha_nome         ; a etiqueta com o nome aparece de uma vez
    ldx dlg_box
    lda inicio_fala_tab, x   ; cada caixa comeca na sua propria linha de fala
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
    lda dlg_box
    bne @acabou_tudo         ; ja era a caixa da Amanda: acabou de verdade
    lda #$01                 ; era a do Victor: abre a dela agora
    sta dlg_box
    sta dialogo               ; volta pro estado 1 = abrindo
    lda #$00
    sta dlg_lin
    rts
@acabou_tudo:
    lda #$00
    sta dialogo
    sta dlg_box              ; deixa pronta pra proxima conversa
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
    ldx dlg_box
    lda dlg_txt
    cmp fim_fala_tab, x      ; cada caixa tem seu proprio fim
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
    lda dlg_txt
    sec
    sbc inicio_fala_tab, x   ; linha DENTRO da caixa atual, nao global
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
    lda #NOME_BAIXO
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
    adc #CAIXA_BAIXO
    sta PPUADDR

    ; ptr = nam_cena + (linha_do_topo_da_caixa + dlg_lin) * 32 + CAIXA_COL
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
    adc #<(nam_cena + CAIXA_COL)
    sta ptr
    lda tmp+1
    adc #>(nam_cena + CAIXA_COL)
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
;  E um arcade: depois de alcancar PONTOS_MIN ela ve uma comemoracao (o
;  "final" -- por enquanto um placeholder, o conteudo de verdade ainda nao
;  foi decidido), mas o jogo continua dali, tipo o foguete do Tetris. So
;  acaba quando ela erra ERROS_MAX pizzas.
; ==========================================================================
atualiza_jogo:
    lda jogo_fase
    cmp #$02                 ; fim de jogo: so espera o START
    bne @nao_fim
    lda botoes_novos
    and #BTN_START
    beq @so_desenha
    jmp carrega_menu
@so_desenha:
    jmp atualiza_oam_jogo

@nao_fim:
    cmp #$01                 ; comemorando: pizzas pausadas, so conta o tempo
    bne @jogando
    dec jogo_temp
    bne @so_desenha
    lda #$00
    sta jogo_fase
    jmp atualiza_oam_jogo

@jogando:
    jsr move_jogador
    jsr atualiza_pizzas
    jmp atualiza_oam_jogo

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
    ; saltarem de um extremo ao outro da tela. 'base' e o menor x possivel
    ; (ultimo_pz_x - SALTO_MAX, sem passar de ANDA_MIN); dai soma um
    ; deslocamento aleatorio de 0 a 2*SALTO_MAX e clampa no teto.
    lda ultimo_pz_x
    cmp #(SALTO_MAX + ANDA_MIN)
    bcc @usa_min
    sec
    sbc #SALTO_MAX
    jmp @tem_base
@usa_min:
    lda #ANDA_MIN
@tem_base:
    sta jogo_tmp                ; jogo_tmp = base

    jsr avanca_rng
    lda rng_seed
@mod:
    cmp #(2*SALTO_MAX+1)        ; reduz pro intervalo 0-(2*SALTO_MAX)
    bcc @tem_delta
    sbc #(2*SALTO_MAX+1)
    jmp @mod
@tem_delta:
    clc
    adc jogo_tmp
    bcs @estoura             ; passou de 255 -- estourou o teto com certeza
    cmp #(ANDA_MAX-16)
    bcc @tem_x
@estoura:
    lda #(ANDA_MAX-16)
@tem_x:
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
    lda #DURACAO_COMEMORA
    sta jogo_temp
@fim:
    rts

checa_derrota:
    lda jogo_erros
    cmp #ERROS_MAX
    bcc @fim
    lda #$02
    sta jogo_fase
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
;  pizzaria) e ate 3 pizzas (sprites 8-13, 2 tiles cada).
; --------------------------------------------------------------------------
atualiza_oam_jogo:
    jsr monta_oam
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
;  Placar: dois digitos de pontos e um de erros, escritos no fundo. So
;  redesenha quando 'placar_sujo' pede -- roda no NMI, pode usar ptr/tmp
;  (a musica toca depois, na mesma chamada, nunca ao mesmo tempo).
; --------------------------------------------------------------------------
desenha_placar:
    lda placar_sujo
    beq @fim
    lda #$00
    sta placar_sujo

    jsr converte_pontos       ; X = dezena, A = unidade
    pha
    txa
    clc
    adc #DIG_BASE
    tay
    bit PPUSTATUS
    PPU_ADDR PLACAR_PONTOS
    tya
    sta PPUDATA
    pla
    clc
    adc #DIG_BASE
    sta PPUDATA

    lda jogo_erros
    cmp #10
    bcc @erros_ok
    lda #9                    ; satura em 9 (nao deveria acontecer)
@erros_ok:
    clc
    adc #DIG_BASE
    tay                        ; PPU_ADDR usa A -- guarda o tile em Y antes
    bit PPUSTATUS
    PPU_ADDR PLACAR_ERROS
    tya
    sta PPUDATA
@fim:
    rts

; ---- jogo_pontos (0-255) -> dezena (X) e unidade (A), saturado em 99 ----
converte_pontos:
    ldx #$00
    lda jogo_pontos
@div10:
    cmp #10
    bcc @pronto
    sbc #10
    inx
    cpx #10
    bne @div10
@pronto:
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
    beq @menu
    cmp #TELA_CENA
    beq @cena
    jsr desenha_placar
    jmp @scroll
@menu:
    jsr pulsa_coracao
    jsr apaga_aviso_start
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
ama_pal:     .byte 0, 0, 1, 3,  0, 0, 1, 3
; Victor: 6 tiles
vic_dx:      .byte 0, 0, 0,  8, 8, 8
vic_dy:      .byte 0, 8, 16, 0, 8, 16

; pecas da moldura, por tipo de linha: topo, meio, base
borda_esq:   .byte TILE_BORDA+0, TILE_BORDA+3, TILE_BORDA+5
borda_meio:  .byte TILE_BORDA+1, TILE_BRANCO,  TILE_BORDA+6
borda_dir:   .byte TILE_BORDA+2, TILE_BORDA+4, TILE_BORDA+7

; ---- as duas caixas de fala: [0] = Victor, [1] = Amanda ----
; boxrow_tab e a unica coisa que realmente muda a posicao na tela; as
; outras tabelas sao so a mesma conta (ver comentario em CAIXA_COL) feita
; pra cada linha de topo.
boxrow_tab:      .byte 8, 16          ; linha do topo, em tiles
caixa_pag_tab:   .byte $21, $22       ; byte alto do endereco da caixa
atrib1_tab:      .byte $D2, $E2       ; endereco dos 4 bytes de atributo de cima
atrib2_tab:      .byte $DA, $EA       ; e os 4 de baixo
restoff1_tab:    .byte 18, 34         ; onde ler esses bytes de volta em nam_cena+960
restoff2_tab:    .byte 26, 42
inicio_fala_tab: .byte 0, N_FALA_VICTOR   ; dlg_txt em que cada caixa comeca
fim_fala_tab:    .byte N_FALA_VICTOR, N_FALAS ; e em que termina

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

.include "musica.inc"
.include "dialogo.inc"
.include "jogo.inc"

.segment "VECTORS"
    .word nmi, reset, irq
