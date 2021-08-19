import pygame

#  menyimpan semua frame animasi

screen_w = 512
screen_h = 704
pygame.display.init()
screen = pygame.display.set_mode((screen_w, screen_h))

background_img = pygame.image.load('frames/background.png').convert_alpha()
platform_img = pygame.image.load('frames/platform.png').convert_alpha()
heart_img = pygame.image.load('frames/ui_heart_full.png').convert_alpha()
blue_flask_img = pygame.image.load('frames/flask_big_red.png').convert_alpha()
red_flask_img = pygame.image.load('frames/flask_big_blue.png').convert_alpha()
water_img = pygame.image.load('frames/waterball.png').convert_alpha()

demon_run_right_img = [pygame.image.load('frames/virus1.png').convert_alpha(),
                       pygame.image.load('frames/virus1.png').convert_alpha(),
                       pygame.image.load('frames/virus1.png').convert_alpha(),
                       pygame.image.load('frames/virus1.png').convert_alpha()]
demon_run_left_img = [pygame.image.load('frames/virus.png').convert_alpha(),
                      pygame.image.load('frames/virus.png').convert_alpha(),
                      pygame.image.load('frames/virus.png').convert_alpha(),
                      pygame.image.load('frames/virus.png').convert_alpha()]


bunny_run_right_img = [pygame.image.load('frames/bunny_right0.png').convert_alpha(),
                     pygame.image.load('frames/bunny_right1.png').convert_alpha()]
                    
bunny_run_left_img = [pygame.image.load('frames/bunny_left1.png').convert_alpha(),
                    pygame.image.load('frames/bunny_left0.png').convert_alpha()]
                    
bunny_idle_img = [pygame.image.load('frames/bunny_stand.png').convert_alpha()]
                
bunny_jump_img = [pygame.image.load('frames/bunny_jump.png').convert_alpha()]
    
               
