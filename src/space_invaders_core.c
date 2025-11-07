#include "space_invaders_core.h"
#include "8080Core.h"
#include "8080Memory.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

// Global emulator state
si_state_t si_state = {0};

// === Port I/O Handlers ===

uint8_t si_port_in(int port) {
    switch (port) {
        case 0:
            return si_state.config.dip_switches[0];
        case 1:
            return si_state.input_state;
        case 2:
            return si_state.config.dip_switches[2];
        case 3:
            // Hardware shift register read
            return si_state.shift_reg >> (8 - si_state.shift_offset);
        default:
            #ifdef DEBUG
            fprintf(stderr, "Port read %d\n", port);
            #endif
            break;
    }
    return 0x00;
}

void si_port_out(int port, uint8_t value) {
    switch (port) {
        case 2:
            // Shift register offset (0-7)
            si_state.shift_offset = value & 7;
            break;
        case 3:
            // Sound port 1 (bits for UFO, shot, player die, invader die)
            // TODO: Sound implementation in Phase 2
            break;
        case 4:
            // Hardware shift register write
            si_state.shift_reg = (si_state.shift_reg >> 8) | ((uint16_t)value << 8);
            break;
        case 5:
            // Sound port 2 (fleet movement sounds, UFO hit)
            // TODO: Sound implementation in Phase 2
            break;
        case 6:
            // Watchdog (write to reset watchdog timer)
            // Not needed for emulation
            break;
        default:
            #ifdef DEBUG
            fprintf(stderr, "Port write %d = 0x%02X\n", port, value);
            #endif
            break;
    }
}

// === Initialization ===

int si_init(const char *rom_h, const char *rom_g, const char *rom_f, const char *rom_e) {
    si_config_t default_config = {
        .headless = false,
        .speed_multiplier = 1.0f,
        .uncapped = false,
        .dip_switches = {0x0E, 0x08, 0x00}  // Default DIP settings
    };
    return si_init_with_config(rom_h, rom_g, rom_f, rom_e, &default_config);
}

int si_init_with_config(const char *rom_h, const char *rom_g,
                        const char *rom_f, const char *rom_e,
                        const si_config_t *config) {
    // Clear state
    memset(&si_state, 0, sizeof(si_state));

    // Copy configuration
    if (config) {
        si_state.config = *config;
    }

    // Reset CPU to address 0x0001
    reset8080(0x0001);

    // Register ROM bank (0x0000-0x2000, read-only)
    uint8_t *rom_buf = registerBank(0x0000, 4 * 0x0800, NULL, 1);
    if (!rom_buf) {
        fprintf(stderr, "Failed to register ROM bank\n");
        return -1;
    }

    // Load ROM files
    const char *rom_files[] = {rom_h, rom_g, rom_f, rom_e};
    for (int i = 0; i < 4; i++) {
        FILE *fp = fopen(rom_files[i], "rb");
        if (!fp) {
            fprintf(stderr, "Failed to open ROM file: %s\n", rom_files[i]);
            return -1;
        }

        size_t bytes_read = fread(rom_buf + (i * 0x0800), 1, 0x0800, fp);
        fclose(fp);

        if (bytes_read != 0x0800) {
            fprintf(stderr, "Failed to read ROM file %s (got %zu bytes, expected 2048)\n",
                    rom_files[i], bytes_read);
            return -1;
        }
    }

    // Patch byte 0 with JMP instruction (for CP/M compatibility)
    rom_buf[0] = 0xc3;

    // Register RAM bank (0x2000-0x4000, read-write)
    uint8_t *ram_buf = registerBank(SI_RAM_START, SI_RAM_SIZE, NULL, 0);
    if (!ram_buf) {
        fprintf(stderr, "Failed to register RAM bank\n");
        return -1;
    }

    // Set port I/O handlers
    e8080.portIn = si_port_in;
    e8080.portOut = si_port_out;

    // Initialize state
    si_state.shift_reg = 0x0000;
    si_state.shift_offset = 0;
    si_state.input_state = 0x08;  // Default input state
    si_state.frame_count = 0;
    si_state.cycle_count = 0;
    si_state.initialized = true;

    return 0;
}

void si_destroy(void) {
    // Memory cleanup is handled by memory system
    // Just clear our state
    memset(&si_state, 0, sizeof(si_state));
}

void si_reset(void) {
    // Save critical pointers (reset8080 clears the entire e8080 structure)
    Mem *saved_ram = e8080.ram;
    uint8_t (*saved_portIn)(int) = e8080.portIn;
    void (*saved_portOut)(int, uint8_t) = e8080.portOut;

    // Reset CPU
    reset8080(0x0001);

    // Restore critical pointers
    e8080.ram = saved_ram;
    e8080.portIn = saved_portIn;
    e8080.portOut = saved_portOut;

    // Reset hardware state
    si_state.shift_reg = 0x0000;
    si_state.shift_offset = 0;
    si_state.input_state = 0x08;
    si_state.frame_count = 0;
    si_state.cycle_count = 0;

    // Clear RAM (but not ROM)
    for (uint32_t addr = SI_RAM_START; addr < SI_RAM_START + SI_RAM_SIZE; addr++) {
        writeByte(0x00, addr);
    }

    // Re-enable interrupts if needed
    e8080.IE = 1;
}

// === Execution ===

int si_step_frame(void) {
    // Space Invaders runs at 2MHz with interrupts at mid-screen and end-screen
    // Each frame is 1/60th second = ~33333 cycles
    // Split into two halves for mid-frame and end-frame interrupts

    const int half_frame_cycles = 17066;  // Approximately half of 33333

    // First half of frame
    int cycles1 = emulate8080(half_frame_cycles);
    causeInt(8);  // RST 1 interrupt (address 0x08) - mid-screen

    // Second half of frame
    int cycles2 = emulate8080(half_frame_cycles);
    causeInt(16); // RST 2 interrupt (address 0x10) - end-screen

    si_state.frame_count++;
    si_state.cycle_count += (cycles1 + cycles2);

    return cycles1 + cycles2;
}

int si_step_cycles(int cycles) {
    int executed = emulate8080(cycles);
    si_state.cycle_count += executed;
    return executed;
}

// === State Management ===

int si_save_state(const char *filename) {
    FILE *fp = fopen(filename, "wb");
    if (!fp) {
        fprintf(stderr, "Failed to open save state file: %s\n", filename);
        return -1;
    }

    // Write magic header
    const char magic[] = "SI80";
    fwrite(magic, 1, 4, fp);

    // Write version
    uint32_t version = 1;
    fwrite(&version, sizeof(version), 1, fp);

    // Write CPU state (e8080 struct)
    fwrite(&e8080, sizeof(e8080), 1, fp);

    // Write emulator state
    fwrite(&si_state, sizeof(si_state), 1, fp);

    // Write RAM contents (0x2000-0x4000)
    for (uint32_t addr = SI_RAM_START; addr < SI_RAM_START + SI_RAM_SIZE; addr++) {
        uint8_t byte = readByte(addr);
        fwrite(&byte, 1, 1, fp);
    }

    fclose(fp);
    return 0;
}

int si_load_state(const char *filename) {
    FILE *fp = fopen(filename, "rb");
    if (!fp) {
        fprintf(stderr, "Failed to open save state file: %s\n", filename);
        return -1;
    }

    // Read and verify magic header
    char magic[4];
    if (fread(magic, 1, 4, fp) != 4 || memcmp(magic, "SI80", 4) != 0) {
        fprintf(stderr, "Invalid save state file (bad magic)\n");
        fclose(fp);
        return -1;
    }

    // Read and verify version
    uint32_t version;
    if (fread(&version, sizeof(version), 1, fp) != 1 || version != 1) {
        fprintf(stderr, "Incompatible save state version\n");
        fclose(fp);
        return -1;
    }

    // Read CPU state
    if (fread(&e8080, sizeof(e8080), 1, fp) != 1) {
        fprintf(stderr, "Failed to read CPU state\n");
        fclose(fp);
        return -1;
    }

    // Read emulator state
    if (fread(&si_state, sizeof(si_state), 1, fp) != 1) {
        fprintf(stderr, "Failed to read emulator state\n");
        fclose(fp);
        return -1;
    }

    // Read RAM contents
    for (uint32_t addr = SI_RAM_START; addr < SI_RAM_START + SI_RAM_SIZE; addr++) {
        uint8_t byte;
        if (fread(&byte, 1, 1, fp) != 1) {
            fprintf(stderr, "Failed to read RAM contents\n");
            fclose(fp);
            return -1;
        }
        writeByte(byte, addr);
    }

    fclose(fp);
    return 0;
}

// === Input Control ===

void si_set_input(uint8_t buttons) {
    // Port 1 input layout:
    // Bit 0: Coin (active high)
    // Bit 1: P2 Start (active high)
    // Bit 2: P1 Start (active high)
    // Bit 4: P1 Fire (active high)
    // Bit 5: Left (active high)
    // Bit 6: Right (active high)

    // Base state has bit 3 set (always 1)
    si_state.input_state = (buttons & 0x77) | 0x08;
}

uint8_t si_get_input(void) {
    return si_state.input_state;
}

// === Display Access ===

void si_update_framebuffer(void) {
    // Convert VRAM to ARGB framebuffer
    // VRAM is bit-packed: each byte represents 8 vertical pixels
    // Screen is rotated 90 degrees counterclockwise

    uint32_t *screen_ptr = (uint32_t*)si_state.screen_buf;
    uint16_t vram_addr = SI_VRAM_START;

    while (vram_addr < SI_VRAM_END) {
        uint8_t b = readByte(vram_addr);

        // Each bit is a pixel (1 = white, 0 = black)
        *screen_ptr++ = ((b >> 0) & 1) ? 0xFFFFFFFF : 0xFF000000;
        *screen_ptr++ = ((b >> 1) & 1) ? 0xFFFFFFFF : 0xFF000000;
        *screen_ptr++ = ((b >> 2) & 1) ? 0xFFFFFFFF : 0xFF000000;
        *screen_ptr++ = ((b >> 3) & 1) ? 0xFFFFFFFF : 0xFF000000;
        *screen_ptr++ = ((b >> 4) & 1) ? 0xFFFFFFFF : 0xFF000000;
        *screen_ptr++ = ((b >> 5) & 1) ? 0xFFFFFFFF : 0xFF000000;
        *screen_ptr++ = ((b >> 6) & 1) ? 0xFFFFFFFF : 0xFF000000;
        *screen_ptr++ = ((b >> 7) & 1) ? 0xFFFFFFFF : 0xFF000000;

        vram_addr++;
    }
}

const uint8_t* si_get_framebuffer(int *width, int *height) {
    if (width) *width = SI_SCREEN_WIDTH;
    if (height) *height = SI_SCREEN_HEIGHT;
    return si_state.screen_buf;
}

void si_get_framebuffer_grayscale(uint8_t *buffer) {
    if (!buffer) return;

    // Convert ARGB to grayscale (just use R channel, since it's B&W)
    const uint32_t *screen_ptr = (const uint32_t*)si_state.screen_buf;
    for (int i = 0; i < SI_SCREEN_WIDTH * SI_SCREEN_HEIGHT; i++) {
        // Extract white/black: 0xFFFFFFFF -> 255, 0xFF000000 -> 0
        buffer[i] = (screen_ptr[i] & 0x00FFFFFF) ? 255 : 0;
    }
}

// === Game State Queries ===
// Note: These require reverse-engineering RAM locations
// For now, returning placeholder values. Will implement in Phase 3.

uint32_t si_get_score(void) {
    // Space Invaders stores P1 score at 0x20F8 (LSB) and 0x20F9 (MSB) as BCD
    // Source: computerarcheology.com/Arcade/SpaceInvaders/RAMUse.html

    uint8_t bcd_lsb = readByte(0x20F8);  // Lower 2 digits
    uint8_t bcd_msb = readByte(0x20F9);  // Upper 2 digits

    uint32_t score = ((bcd_msb >> 4) * 1000) +
                     ((bcd_msb & 0x0F) * 100) +
                     ((bcd_lsb >> 4) * 10) +
                     (bcd_lsb & 0x0F);

    return score;
}

int si_get_lives(void) {
    // Space Invaders stores P1 ships remaining at 0x21FF
    // This is "ships remaining AFTER current dies" so we need to add 1 if player alive
    // Source: computerarcheology.com/Arcade/SpaceInvaders/RAMUse.html

    uint8_t ships_remaining = readByte(0x21FF);  // Reserve ships
    uint8_t player_alive = readByte(0x20E7);     // 1 if alive, 0 if dead

    // Total lives = reserve ships + current ship (if alive)
    int total_lives = ships_remaining + (player_alive ? 1 : 0);

    // Lives should be 0-6
    if (total_lives > 6) return 0;
    return total_lives;
}

bool si_is_game_over(void) {
    // Game is over when:
    // 1. Emulator halted, OR
    // 2. Both player is dead AND no reserve ships
    uint8_t ships_remaining = readByte(0x21FF);  // Reserve ships
    uint8_t player_alive = readByte(0x20E7);     // 1 if alive, 0 if dead

    return e8080.halt || (player_alive == 0 && ships_remaining == 0);
}

int si_get_level(void) {
    // TODO: Reverse engineer level/wave counter
    // For now, estimate based on frame count (placeholder)
    return (si_state.frame_count / 3600) + 1;  // ~60 seconds per level
}

// === Structured State Observations ===

uint8_t si_get_player_x(void) {
    return readByte(0x201B);  // playerXr
}

uint8_t si_get_player_y(void) {
    return readByte(0x201A);  // playerYr
}

bool si_get_player_alive(void) {
    return readByte(0x20E7) != 0;  // player1Alive
}

void si_get_alien_grid(uint8_t *grid) {
    // Read 55 alien alive flags from RAM
    for (int i = 0; i < 55; i++) {
        grid[i] = readByte(0x2100 + i);
    }
}

uint8_t si_get_alien_count(void) {
    return readByte(0x2082);  // alienCount
}

uint8_t si_get_player_shot(uint8_t *x, uint8_t *y) {
    uint8_t status = readByte(0x2025);  // plyrShotStatus
    if (x) *x = readByte(0x202A);  // obj1CoorXr
    if (y) *y = readByte(0x2029);  // obj1CoorYr
    return status;
}

uint8_t si_get_rolling_shot(uint8_t *x, uint8_t *y) {
    // Check if shot is active (Y != 0 usually means active)
    uint8_t shot_y = readByte(0x203D);  // rolShotYr
    uint8_t shot_x = readByte(0x203E);  // rolShotXr
    if (x) *x = shot_x;
    if (y) *y = shot_y;
    return (shot_y != 0) ? 1 : 0;
}

uint8_t si_get_plunger_shot(uint8_t *x, uint8_t *y) {
    uint8_t shot_y = readByte(0x204D);  // pluShotYr
    uint8_t shot_x = readByte(0x204E);  // pluShotXr
    if (x) *x = shot_x;
    if (y) *y = shot_y;
    return (shot_y != 0) ? 1 : 0;
}

uint8_t si_get_squiggly_shot(uint8_t *x, uint8_t *y) {
    uint8_t shot_y = readByte(0x205D);  // squShotYr
    uint8_t shot_x = readByte(0x205E);  // squShotXr
    if (x) *x = shot_x;
    if (y) *y = shot_y;
    return (shot_y != 0) ? 1 : 0;
}

bool si_get_ufo_active(uint8_t *x, uint8_t *y) {
    bool active = readByte(0x2084) != 0;  // saucerActive
    if (active) {
        if (x) *x = readByte(0x207C);  // UFO uses alien shot X register
        if (y) *y = readByte(0x207B);  // UFO uses alien shot Y register
    }
    return active;
}

// === Configuration ===

void si_set_speed(float multiplier) {
    si_state.config.speed_multiplier = multiplier;
    if (multiplier == 0.0f) {
        si_state.config.uncapped = true;
    }
}

void si_set_uncapped(bool uncapped) {
    si_state.config.uncapped = uncapped;
}

void si_set_dip_switches(uint8_t dip0, uint8_t dip1, uint8_t dip2) {
    si_state.config.dip_switches[0] = dip0;
    si_state.config.dip_switches[1] = dip1;
    si_state.config.dip_switches[2] = dip2;
}

// === Statistics ===

uint32_t si_get_frame_count(void) {
    return si_state.frame_count;
}

uint64_t si_get_cycle_count(void) {
    return si_state.cycle_count;
}
