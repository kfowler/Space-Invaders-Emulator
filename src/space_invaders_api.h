#ifndef SPACE_INVADERS_API_H
#define SPACE_INVADERS_API_H

/*
 * Space Invaders Emulator C API
 *
 * This is a C-compatible wrapper around the core emulator
 * for use with Python ctypes bindings and other languages.
 *
 * All functions use C linkage and simple types.
 */

#ifdef __cplusplus
extern "C" {
#endif

#include <stdint.h>
#include <stdbool.h>

// === Initialization ===

// Initialize emulator with ROM files
// Returns 0 on success, -1 on error
int si_api_init(const char *rom_h, const char *rom_g,
                const char *rom_f, const char *rom_e);

// Initialize with headless mode and DIP switch configuration
// dip_switches: array of 3 bytes for DIP switch settings
// Returns 0 on success, -1 on error
int si_api_init_headless(const char *rom_h, const char *rom_g,
                         const char *rom_f, const char *rom_e,
                         const uint8_t *dip_switches);

// Cleanup and free resources
void si_api_destroy(void);

// Reset to initial state
void si_api_reset(void);

// === Execution ===

// Execute one frame (returns cycles executed)
int si_api_step_frame(void);

// Execute N cycles (returns cycles actually executed)
int si_api_step_cycles(int cycles);

// === State Management ===

// Save complete state to file
int si_api_save_state(const char *filename);

// Load state from file
int si_api_load_state(const char *filename);

// === Input ===

// Set input buttons (bitfield)
// Bit 0: Coin
// Bit 1: P2 Start
// Bit 2: P1 Start
// Bit 4: P1 Fire
// Bit 5: Left
// Bit 6: Right
void si_api_set_input(uint8_t buttons);

// Get current input state
uint8_t si_api_get_input(void);

// === Display ===

// Update framebuffer from VRAM
void si_api_update_framebuffer(void);

// Get framebuffer pointer and dimensions
// buffer: receives pointer to ARGB8888 data
// width, height: receive dimensions
void si_api_get_framebuffer(const uint8_t **buffer, int *width, int *height);

// Get grayscale framebuffer
// buffer: caller-allocated buffer of size width*height
void si_api_get_framebuffer_gray(uint8_t *buffer);

// === Game State ===

// Get current score
uint32_t si_api_get_score(void);

// Get lives remaining
int si_api_get_lives(void);

// Check if game over
bool si_api_is_game_over(void);

// Get current level
int si_api_get_level(void);

// === Configuration ===

// Set speed multiplier (1.0 = normal, 0 = uncapped)
void si_api_set_speed(float multiplier);

// Enable/disable uncapped mode
void si_api_set_uncapped(bool uncapped);

// Set DIP switches
void si_api_set_dip_switches(uint8_t dip0, uint8_t dip1, uint8_t dip2);

// === Statistics ===

// Get total frames executed
uint32_t si_api_get_frame_count(void);

// Get total cycles executed
uint64_t si_api_get_cycle_count(void);

#ifdef __cplusplus
}
#endif

#endif // SPACE_INVADERS_API_H
