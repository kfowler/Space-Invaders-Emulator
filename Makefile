# Space Invaders Emulator - Build Configuration
# Optimized for macOS Apple Silicon (M2 Max)

# Source files
CORE_OBJS = src/8080Core.c src/8080Memory.c src/space_invaders_core.c
API_OBJS = src/space_invaders_api.c

# Compiler and flags
CC = gcc
CFLAGS_BASE = -Wall -Wextra -std=c11
CFLAGS_OPT = -O3 -march=native -flto
CFLAGS_DEBUG = -g -DDEBUG

# SDL2 configuration
SDL2_CFLAGS = $(shell sdl2-config --cflags)
SDL2_LIBS = $(shell sdl2-config --libs) -lSDL2_mixer

# Build targets
all: sinv testr

# Playable Space Invaders (with SDL2 graphics/sound)
sinv: $(CORE_OBJS) src/SpaceInvaders.c
	$(CC) $(CFLAGS_BASE) $(CFLAGS_OPT) $(CFLAGS_DEBUG) \
		$(CORE_OBJS) src/SpaceInvaders.c \
		$(SDL2_CFLAGS) $(SDL2_LIBS) \
		-o spaceinvaders

# Test ROM runner (no SDL2)
testr: $(CORE_OBJS) src/testrom.c
	$(CC) $(CFLAGS_BASE) $(CFLAGS_OPT) $(CFLAGS_DEBUG) \
		$(CORE_OBJS) src/testrom.c \
		-o testrom

# Headless emulator (no SDL2, for RL training)
headless: $(CORE_OBJS) $(API_OBJS) src/SpaceInvaders.c
	$(CC) $(CFLAGS_BASE) $(CFLAGS_OPT) $(CFLAGS_DEBUG) -DHEADLESS \
		$(CORE_OBJS) $(API_OBJS) src/SpaceInvaders.c \
		-o spaceinvaders_headless

# Shared library for Python bindings (macOS .dylib)
libspaceinvaders.dylib: $(CORE_OBJS) $(API_OBJS)
	$(CC) $(CFLAGS_BASE) $(CFLAGS_OPT) -DHEADLESS -shared -fPIC \
		$(CORE_OBJS) $(API_OBJS) \
		-o libspaceinvaders.dylib

# Clean build artifacts
clean:
	rm -f spaceinvaders testrom spaceinvaders_headless libspaceinvaders.dylib
	rm -rf *.dSYM

# Install library to system location (optional)
install: libspaceinvaders.dylib
	mkdir -p /usr/local/lib
	cp libspaceinvaders.dylib /usr/local/lib/
	mkdir -p /usr/local/include
	cp src/space_invaders_api.h /usr/local/include/

.PHONY: all sinv testr headless clean install
