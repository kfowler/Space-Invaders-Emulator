# Space Invaders RAM Memory Map

Complete memory map for the Space Invaders arcade game, based on reverse engineering and documentation from [Computer Archeology](https://www.computerarcheology.com/Arcade/SpaceInvaders/RAMUse.html).

## Memory Layout Overview

| Address Range | Size | Description |
|--------------|------|-------------|
| 0x0000-0x1FFF | 8KB | ROM (Program code) |
| 0x2000-0x23FF | 1KB | Work RAM (Game state) |
| 0x2400-0x3FFF | 7KB | Video RAM (Display buffer) |

## Player State

### Player 1

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x201A | playerYr | uint8 | Player sprite Y coordinate (LSB) |
| 0x201B | playerXr | uint8 | Player sprite X coordinate (MSB) |
| 0x2015 | playerAlive | uint8 | Player alive flag (0xFF=alive, toggles for explosion) |
| 0x2016 | expAnimateTimer | uint8 | Explosion animation timer |
| 0x2017 | expAnimateCnt | uint8 | Explosion animation frames remaining |
| 0x20E7 | player1Alive | uint8 | 1 if player 1 alive, 0 if dead |
| 0x21FF | p1ShipsRem | uint8 | Player 1 reserve ships (after current dies) |
| 0x20E5 | player1Ex | uint8 | Extra ship awarded flag |

**Note**: Total lives = `p1ShipsRem + player1Alive` (reserve ships + current ship)

### Player 2

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x22FF | p2ShipsRem | uint8 | Player 2 reserve ships |
| 0x20E8 | player2Alive | uint8 | 1 if player 2 alive, 0 if dead |
| 0x20E6 | player2Ex | uint8 | Extra ship awarded flag |

## Scoring

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x20F4-0x20F7 | HiScor | BCD | High score value and descriptors |
| 0x20F8 | P1ScorL | BCD | Player 1 score LSB (lower 2 digits) |
| 0x20F9 | P1ScorM | BCD | Player 1 score MSB (upper 2 digits) |
| 0x20FA | P1ScorDsp1 | uint8 | P1 score display coord 1 |
| 0x20FB | P1ScorDsp2 | uint8 | P1 score display coord 2 |
| 0x20FC-0x20FF | P2Scor | BCD | Player 2 score (same layout) |
| 0x20F2-0x20F3 | scoreDelta | BCD | Score adjustment amount |

**Note**: Scores are stored in BCD (Binary Coded Decimal) format. Each byte stores 2 decimal digits.

Example: Score = 1234 points
- 0x20F8 = 0x34 (lower 2 digits: 34)
- 0x20F9 = 0x12 (upper 2 digits: 12)

## Alien State

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x2004 | alienRow | uint8 | Current alien row number (0-4) |
| 0x2006 | alienCurIndex | uint8 | Alien cursor index (0-54) |
| 0x2009 | refAlienYr | uint8 | Reference alien Y coordinate |
| 0x200A | refAlienXr | uint8 | Reference alien X coordinate |
| 0x200B-0x200C | alienPos | uint16 | Alien cursor bit position |
| 0x2082 | alienCount | uint8 | Number of aliens remaining |
| 0x2100-0x2136 | Player1Aliens | 55 bytes | P1 alien alive flags (55 aliens in grid) |
| 0x2200-0x2236 | Player2Aliens | 55 bytes | P2 alien alive flags |

**Alien Grid Layout**: 11 columns × 5 rows = 55 aliens
- Row 0 (top): 11 squids (30 points)
- Row 1-2: 22 crabs (20 points)
- Row 3-4: 22 octopuses (10 points)

## Shots/Bullets

### Player Shot

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x2025 | plyrShotStatus | uint8 | Player shot state (0=available, 1-5=flying/exploding) |
| 0x2029 | obj1CoorYr | uint8 | Player shot Y coordinate |
| 0x202A | obj1CoorXr | uint8 | Player shot X coordinate |

### Alien Shots

There are 3 types of alien shots, each with different movement patterns:

#### Rolling Shot
| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x203D | rolShotYr | uint8 | Rolling shot Y position |
| 0x203E | rolShotXr | uint8 | Rolling shot X position |

#### Plunger Shot
| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x204D | pluShotYr | uint8 | Plunger shot Y position |
| 0x204E | pluShotXr | uint8 | Plunger shot X position |

#### Squiggly Shot
| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x205D | squShotYr | uint8 | Squiggly shot Y position |
| 0x205E | squShotXr | uint8 | Squiggly shot X position |

## Game Control Flags

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x20EF | gameMode | uint8 | 1=game running, 0=demo/splash screens |
| 0x20E9 | suspendPlay | uint8 | 1=game active, 0=suspended |
| 0x2068 | playerOK | uint8 | 1=functional, 0=exploding |
| 0x2069 | enableAlienFire | uint8 | Alien firing permission flag |
| 0x206D | invaded | uint8 | Set to 1 when aliens reach bottom |
| 0x2072 | vblankStatus | uint8 | 0x80=drawing, 0x00=blanking |

## Mystery Ship (UFO)

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x2083 | saucerStart | uint8 | Mystery ship trigger flag |
| 0x2084 | saucerActive | uint8 | Mystery ship on screen indicator |
| 0x207B | alienShotYr | uint8 | Also used for UFO Y coordinate |
| 0x207C | alienShotXr | uint8 | Also used for UFO X coordinate |

## Timers and Counters

| Address | Name | Type | Description |
|---------|------|------|-------------|
| 0x2012 | playerTaskTimer | uint8 | One-byte timer for player tasks |
| 0x20C0 | generalCounter | uint8 | General-purpose timing counter |
| 0x2080 | shotSyncFlag | uint8 | Sync flag for shot timing |

## Shield State

The shields are part of the video RAM and don't have dedicated state bytes. Shield damage is represented directly in VRAM at addresses 0x2400-0x3FFF.

## Hardware Ports

Not RAM, but important for input/output:

| Port | Direction | Description |
|------|-----------|-------------|
| 0 | IN | DIP Switch 0 (lives, extra ship, etc.) |
| 1 | IN | Player inputs (coin, start, fire, left, right) |
| 2 | IN/OUT | DIP Switch 2 / Shift register offset |
| 3 | IN/OUT | Shift register read / Sound port 1 |
| 4 | OUT | Shift register write |
| 5 | OUT | Sound port 2 |
| 6 | OUT | Watchdog reset |

## DIP Switch 0 (Port 0) Settings

| Bit | Description |
|-----|-------------|
| 0-1 | Number of lives (00=3, 01=4, 10=5, 11=6) |
| 2 | Tilt option |
| 3 | Extra ship (0=1500, 1=1000) |
| 7 | Coin info displayed in attract mode |

## Input Port 1 Bit Layout

| Bit | Button | Description |
|-----|--------|-------------|
| 0 | COIN | Insert coin (active high) |
| 1 | P2_START | Player 2 start (active high) |
| 2 | P1_START | Player 1 start (active high) |
| 3 | - | Always 1 |
| 4 | P1_FIRE | Player 1 fire (active high) |
| 5 | LEFT | Move left (active high) |
| 6 | RIGHT | Move right (active high) |
| 7 | - | Unused |

## Usage Notes

1. **BCD Format**: Scores are stored in Binary Coded Decimal. Each nibble (4 bits) represents one decimal digit (0-9).

2. **Lives Calculation**: Total lives = reserve ships (0x21FF) + current ship alive flag (0x20E7). A typical game starts with 3 lives: 2 in reserve + 1 current = 3 total.

3. **Alien Grid**: Aliens are indexed 0-54 in a packed format. To check if alien N is alive, read byte at (0x2100 + N) for player 1.

4. **Coordinates**: Y coordinates increase downward, X coordinates increase rightward. The screen is rotated 90° CCW, so the player moves on the "Y" axis.

5. **Game Over Detection**: Game is over when both `player1Alive == 0` AND `p1ShipsRem == 0`.

## References

- [Computer Archeology - Space Invaders RAM Usage](https://www.computerarcheology.com/Arcade/SpaceInvaders/RAMUse.html)
- [Computer Archeology - Space Invaders Code](https://www.computerarcheology.com/Arcade/SpaceInvaders/)
- Intel 8080 Programmer's Manual

## Changelog

- 2025-11-07: Initial documentation based on reverse engineering and Computer Archeology resources
