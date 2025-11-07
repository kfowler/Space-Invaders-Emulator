#ifndef SPACE_INVADERS_CORE_H
#define SPACE_INVADERS_CORE_H

#include <stdint.h>
#include <stdbool.h>

// Input button flags
#define SI_BTN_COIN      (1 << 0)  // Insert coin
#define SI_BTN_P2_START  (1 << 1)  // Player 2 start
#define SI_BTN_P1_START  (1 << 2)  // Player 1 start
#define SI_BTN_P1_FIRE   (1 << 4)  // Player 1 fire
#define SI_BTN_LEFT      (1 << 5)  // Move left
#define SI_BTN_RIGHT     (1 << 6)  // Move right
#define SI_BTN_P2_FIRE   (1 << 4)  // Player 2 fire (same bit, different port)

// Screen dimensions
#define SI_SCREEN_WIDTH  256
#define SI_SCREEN_HEIGHT 224

// Memory addresses
#define SI_VRAM_START    0x2400
#define SI_VRAM_END      0x4000
#define SI_RAM_START     0x2000
#define SI_RAM_SIZE      0x2000

// Emulator configuration
typedef struct {
    bool headless;           // Run without rendering
    float speed_multiplier;  // Speed multiplier (1.0 = normal, 0 = uncapped)
    bool uncapped;           // Run as fast as possible
    uint8_t dip_switches[3]; // DIP switch settings
} si_config_t;

// Emulator state
typedef struct {
    uint8_t screen_buf[SI_SCREEN_WIDTH * SI_SCREEN_HEIGHT * 4];  // ARGB framebuffer
    uint16_t shift_reg;      // Hardware shift register
    int shift_offset;        // Shift register offset
    uint8_t input_state;     // Current input button state
    uint32_t frame_count;    // Total frames executed
    uint64_t cycle_count;    // Total cycles executed
    bool initialized;        // Emulator initialized flag
    si_config_t config;      // Configuration
} si_state_t;

// Global emulator state
extern si_state_t si_state;

// === Core Functions ===

// Initialize the emulator with ROM files
// Returns 0 on success, -1 on error
int si_init(const char *rom_h, const char *rom_g, const char *rom_f, const char *rom_e);

// Initialize with custom configuration
int si_init_with_config(const char *rom_h, const char *rom_g,
                        const char *rom_f, const char *rom_e,
                        const si_config_t *config);

// Cleanup emulator resources
void si_destroy(void);

// Reset emulator to initial state
void si_reset(void);

// Step emulator by one frame (returns number of cycles executed)
int si_step_frame(void);

// Step emulator by N cycles
int si_step_cycles(int cycles);

// === State Management ===

// Save complete emulator state to file
// Returns 0 on success, -1 on error
int si_save_state(const char *filename);

// Load emulator state from file
// Returns 0 on success, -1 on error
int si_load_state(const char *filename);

// === Input Control ===

// Set input state (bitfield of SI_BTN_* flags)
void si_set_input(uint8_t buttons);

// Get current input state
uint8_t si_get_input(void);

// === Display Access ===

// Update framebuffer from VRAM (call after si_step_frame)
void si_update_framebuffer(void);

// Get pointer to framebuffer (ARGB8888 format)
// Returns pointer to screen_buf and dimensions
const uint8_t* si_get_framebuffer(int *width, int *height);

// Get grayscale framebuffer (single channel, 0-255)
// Caller must provide buffer of size width * height
void si_get_framebuffer_grayscale(uint8_t *buffer);

// === Game State Queries ===

// Get current score (returns 0 if not available)
uint32_t si_get_score(void);

// Get number of lives remaining (returns 0 if not available)
int si_get_lives(void);

// Check if game is over
bool si_is_game_over(void);

// Get current level/wave
int si_get_level(void);

// === Configuration ===

// Set speed multiplier (1.0 = normal, 2.0 = 2x speed, 0 = uncapped)
void si_set_speed(float multiplier);

// Enable/disable uncapped mode (run as fast as possible)
void si_set_uncapped(bool uncapped);

// Set DIP switches (lives, difficulty, etc.)
void si_set_dip_switches(uint8_t dip0, uint8_t dip1, uint8_t dip2);

// === Statistics ===

// Get total frame count
uint32_t si_get_frame_count(void);

// Get total cycle count
uint64_t si_get_cycle_count(void);

// === Port I/O Handlers (internal) ===
uint8_t si_port_in(int port);
void si_port_out(int port, uint8_t value);

#endif // SPACE_INVADERS_CORE_H
