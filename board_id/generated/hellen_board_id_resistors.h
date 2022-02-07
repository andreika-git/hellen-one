//
// was generated automatically by Hellen Board-ID generation tool gen_hellen_board_id_resistors.py 2022-02-07 12:25:30.654958
//

#pragma once

// major_idx = 0..15
#define HELLEN_BOARD_ID_MAJOR_RESISTORS	510, 620, 750, 1000, 1200, 1500, 1800, 2200, 2700, 3300, 3900, 4700, 5600, 6800, 8200, 10000, 

// minor_idx = 0..11
#define HELLEN_BOARD_ID_MINOR_RESISTORS	560, 680, 820, 1100, 2000, 2400, 3000, 3600, 4300, 5100, 6200, 7500, 

// C = 1.0uF
#define HELLEN_BOARD_ID_CAPACITOR 1.0f

// R1_IDX = 0..15, R2_IDX = 0..27 (max. 448 boardIds)
#define HELLEN_GET_BOARD_ID(R1_IDX, R2_IDX) ((R1_IDX) * 100 + (R2_IDX))
