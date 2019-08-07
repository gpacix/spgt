YELLOW = (255,255,255,0)
WHITE =  (0,255,255,255)
BLACK =  (0,0,0,0)
GRAY  =  (0,128,128,128)
ORANGE = (0, 255, 192, 128)
RED    = (0, 255, 0, 0)
GREEN  = (0, 0, 255, 0)
BLUE   = (0, 0, 0, 255)

# convert argb to single-byte color:
argbtoi = {BLACK: 0, RED: 1, GREEN: 2, BLUE: 3, YELLOW: 4, ORANGE: 7, GRAY: 128, WHITE: 255}

itoargb = {0: BLACK, 1: RED, 2: GREEN, 3: BLUE, 4: YELLOW, 7: ORANGE, 128: GRAY, 255: WHITE}
