JOGO  = jogo.nes
DADOS = build/chr_menu.bin build/chr_cena.bin build/chr_sprites.bin \
        build/cena.nam build/cena.pal build/dialogo.inc build/musica.inc \
        build/chr_jogo.bin build/jogo.nam build/jogo.pal build/jogo.inc

all: $(JOGO)

# ---- graficos e musica, gerados por scripts Python ----
build/chr_menu.bin: tools/make_chr.py
	@mkdir -p build
	python3 tools/make_chr.py

build/chr_sprites.bin: tools/make_sprites.py tools/make_chr.py
	@mkdir -p build
	python3 tools/make_sprites.py build/chr_sprites.bin

build/chr_cena.bin build/cena.nam build/cena.pal build/dialogo.inc: tools/make_scene.py tools/make_chr.py
	@mkdir -p build
	python3 tools/make_scene.py

build/chr_jogo.bin build/jogo.nam build/jogo.pal build/jogo.inc: tools/make_jogo.py tools/make_chr.py tools/make_scene.py
	@mkdir -p build
	python3 tools/make_jogo.py

build/musica.inc: tools/make_song.py
	@mkdir -p build
	python3 tools/make_song.py build/musica.inc

# ---- o cartucho ----
$(JOGO): src/jogo.s $(DADOS) unrom.cfg
	ca65 -g --include-dir build --bin-include-dir build -o build/jogo.o src/jogo.s
	ld65 -C unrom.cfg -o $(JOGO) build/jogo.o -m build/jogo.map -Ln build/jogo-labels.txt
	@echo "ROM pronta: $(JOGO)"

# ---- verificacao ----
test: $(JOGO)
	python3 tools/test_jogo.py
	python3 tools/test_musica.py

capturas: $(JOGO)
	python3 tools/ver_jogo.py

audio: $(JOGO)
	python3 tools/render_audio.py $(JOGO) build/musica.wav 2100
	python3 tools/audio_menu.py
	python3 tools/audio_dialogo.py
	python3 tools/audio_minigame.py

rodar: $(JOGO)
	fceux --sound 1 --volume 150 --xscale 3 --yscale 3 $(JOGO)

clean:
	rm -rf build

.PHONY: all test capturas audio rodar clean
