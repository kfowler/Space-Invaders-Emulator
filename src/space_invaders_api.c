#include "space_invaders_api.h"
#include "space_invaders_core.h"
#include "8080Memory.h"

// === Initialization ===

int si_api_init(const char *rom_h, const char *rom_g,
                const char *rom_f, const char *rom_e) {
    return si_init(rom_h, rom_g, rom_f, rom_e);
}

int si_api_init_headless(const char *rom_h, const char *rom_g,
                         const char *rom_f, const char *rom_e,
                         const uint8_t *dip_switches) {
    si_config_t config = {
        .headless = true,
        .speed_multiplier = 0.0f,  // Uncapped by default for RL
        .uncapped = true,
        .dip_switches = {
            dip_switches ? dip_switches[0] : 0x0E,
            dip_switches ? dip_switches[1] : 0x08,
            dip_switches ? dip_switches[2] : 0x00
        }
    };
    return si_init_with_config(rom_h, rom_g, rom_f, rom_e, &config);
}

void si_api_destroy(void) {
    si_destroy();
}

void si_api_reset(void) {
    si_reset();
}

// === Execution ===

int si_api_step_frame(void) {
    return si_step_frame();
}

int si_api_step_cycles(int cycles) {
    return si_step_cycles(cycles);
}

// === State Management ===

int si_api_save_state(const char *filename) {
    return si_save_state(filename);
}

int si_api_load_state(const char *filename) {
    return si_load_state(filename);
}

// === Input ===

void si_api_set_input(uint8_t buttons) {
    si_set_input(buttons);
}

uint8_t si_api_get_input(void) {
    return si_get_input();
}

// === Display ===

void si_api_update_framebuffer(void) {
    si_update_framebuffer();
}

void si_api_get_framebuffer(const uint8_t **buffer, int *width, int *height) {
    *buffer = si_get_framebuffer(width, height);
}

void si_api_get_framebuffer_gray(uint8_t *buffer) {
    si_get_framebuffer_grayscale(buffer);
}

// === Game State ===

uint32_t si_api_get_score(void) {
    return si_get_score();
}

int si_api_get_lives(void) {
    return si_get_lives();
}

bool si_api_is_game_over(void) {
    return si_is_game_over();
}

int si_api_get_level(void) {
    return si_get_level();
}

// === Configuration ===

void si_api_set_speed(float multiplier) {
    si_set_speed(multiplier);
}

void si_api_set_uncapped(bool uncapped) {
    si_set_uncapped(uncapped);
}

void si_api_set_dip_switches(uint8_t dip0, uint8_t dip1, uint8_t dip2) {
    si_set_dip_switches(dip0, dip1, dip2);
}

// === Statistics ===

uint32_t si_api_get_frame_count(void) {
    return si_get_frame_count();
}

uint64_t si_api_get_cycle_count(void) {
    return si_get_cycle_count();
}

// === Debug ===

uint8_t si_api_read_ram(uint16_t address) {
    return readByte(address);
}

// === Structured State Observations ===

uint8_t si_api_get_player_x(void) { return si_get_player_x(); }
uint8_t si_api_get_player_y(void) { return si_get_player_y(); }
bool si_api_get_player_alive(void) { return si_get_player_alive(); }
void si_api_get_alien_grid(uint8_t *grid) { si_get_alien_grid(grid); }
uint8_t si_api_get_alien_count(void) { return si_get_alien_count(); }
uint8_t si_api_get_player_shot(uint8_t *x, uint8_t *y) { return si_get_player_shot(x, y); }
uint8_t si_api_get_rolling_shot(uint8_t *x, uint8_t *y) { return si_get_rolling_shot(x, y); }
uint8_t si_api_get_plunger_shot(uint8_t *x, uint8_t *y) { return si_get_plunger_shot(x, y); }
uint8_t si_api_get_squiggly_shot(uint8_t *x, uint8_t *y) { return si_get_squiggly_shot(x, y); }
bool si_api_get_ufo_active(uint8_t *x, uint8_t *y) { return si_get_ufo_active(x, y); }
