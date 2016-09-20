OBJS = src/8080Core.c src/SpaceInvaders.c
#
all:
	clang $(OBJS) -arch x86_64 -g -O3 -Wall `sdl-config --cflags --libs` -o spaceinvaders
