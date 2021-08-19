import pygame
import random as rnd
import sys
import frames1 as frames
import sounds1 as sounds

from pygame.locals import (
    K_ESCAPE,
    K_BACKSPACE,
    K_RETURN,
    K_LEFT,
    K_RIGHT,
    K_SPACE,
    K_a,
    K_d,
    KEYDOWN)

screen_w = 512
screen_h = 704
pygame.display.set_caption("Jump For Your Life!")



def main():
    pygame.init()
    game = State()
    running = True
    while running:

        if game.showing_title:
            game.show_title()

        elif game.showing_selection:
            game.show_character_selection()

        elif game.showing_leaderboard:
            game.show_leaderboard()

        elif game.showing_options: 
            game.show_options(None)

        elif game.showing_help:
            game.show_help(None)

        elif game.showing_about:
            game.show_about(None)
        
        elif game.running:
            game.run_game()

        elif game.showing_death:
            game.show_death_screen()

        else:
            running = False

    pygame.display.quit()
    pygame.quit()
    sys.exit()

class State:

    def __init__(self):
    
        self.screen = pygame.display.set_mode((screen_w, screen_h))
        self.clock = pygame.time.Clock()
        
        # font untuk teks
        self.large_font = pygame.font.Font('pou.ttf', 45)
        self.medium_font = pygame.font.Font('pou.ttf', 30)
        self.small_yellow_font = pygame.font.Font('pou.ttf', 20)
        self.small_font = pygame.font.Font('pou.ttf', 18)
        self.small_helpfont = pygame.font.SysFont(None, 24)
        
        self.fps = 60

        # meletakkan background agar bisa bergerak
        self.background1 = Background(screen_w//2)
        self.background2 = Background(screen_w//2-704)

        # menentukan screen yang akan ditunjukkan dengan boolean
        self.running = False
        self.paused = False
        self.showing_title = True
        self.showing_leaderboard = False
        self.showing_selection = False
        self.showing_death = False
        self.showing_options = False
        self.showing_help = False
        self.showing_about = False

        self.character = None
        self.difficulty = None

        self.leaderboard = get_leaderboard()
        self.highscore = False
        self.score = 0

    def run_game(self) -> None:
    
        """
        Hal-hal yang terjadi saat game sedang dimainkan.
        """

        # menyatukan objek yang bergerak kedalam sebuah grup 
        dynamic_sprites = pygame.sprite.Group()
        dynamic_sprites.add([self.background1, self.background2])
        
        # membuat platform lompatan
        number_of_platforms = 15
        pos = [rnd.uniform(100, screen_w-100), screen_h-25]  # platform yang paling bawah
        platforms = [Platform(pos)]
        for i in range(1, number_of_platforms):
            platforms.append(Platform(platforms[i-1].rect.center))  # membuat platform secara random
        dynamic_sprites.add(platforms)

        player = Player(platforms[1].rect.center[0], platforms[1].rect.top, self.character)

        origin = Origin(player.rect.center)  # skor ditentukan dengan jarak vertikal terhadap posisi awal
        dynamic_sprites.add(origin)

        # membuat grup yang akan diisi dengan objek yang diam
        static_sprites = pygame.sprite.Group()

        # penempatan gambar power up
        lives_marker = Powerup(screen_w-155, 30, 'lives')
        d_jump_marker = Powerup(screen_w-155, 60, 'double_jump')
        waterball_marker = Powerup(screen_w-155, 90, 'waterball')
        static_sprites.add([lives_marker, d_jump_marker, waterball_marker, player])
        
        if self.difficulty == 'easy':
            enemy_chance = 20  # peluang 1:20 untuk kemunculan musuh dalam tiap platform
            projectile_chance = 200  # peluang 1:200 untuk kemunculan waterball dalam tiap frame
            projectile_speed = 4
            powerup_chance = 5  # peluang 1:5 untuk kemunculan power up dalam tiap platform
            enemy_speed = 3

        elif self.difficulty == 'medium':
            enemy_chance = 10
            projectile_chance = 100
            projectile_speed = 6
            powerup_chance = 10
            enemy_speed = 5

        else:
            enemy_chance = 5
            projectile_chance = 50
            projectile_speed = 8
            powerup_chance = 20
            enemy_speed = 7

        self.score = 0

        while self.running:
            for event in pygame.event.get():

                if event.type == KEYDOWN:

                    if event.key == K_ESCAPE:
                        self.pause_game()
                        self.show_pause_screen()

                    if event.key == K_SPACE:

                        # menggunakan power up double jump
                        if player.powerups['double_jump'] > 0:
                            player.powerups['double_jump'] -= 1
                            player.is_jumping = True
                            player.time = 0
                            pygame.mixer.Sound.play(sounds.jump_sound)

                # menembakkan waterball
                if event.type == pygame.MOUSEBUTTONDOWN and player.powerups['waterball'] > 0 and player.projectile is None:
                    player.powerups['waterball'] -= 1
                    mouse_pos = pygame.mouse.get_pos()
                    player.create_projectile(mouse_pos, dynamic_sprites)

                if event.type == pygame.QUIT:
                    self.exit()
                    
            pressed_keys = pygame.key.get_pressed()
            player.move(pressed_keys, dynamic_sprites)

            # menentukan gerakan waterball
            if player.projectile is not None:
                player.projectile.move()
                if player.projectile.hits_boundary():
                    player.remove_projectile()

            # membentuk platform baru saat platform paling bawah sudah diluar layar
            if platforms[0].rect.top > screen_h+50:
                platforms[0].remove_platform(platforms)
                platforms.append(Platform(platforms[-1].rect.center))
                dynamic_sprites.add(platforms[-1])
                
                # membuat musuh baru
                if rnd.choice(range(enemy_chance)) == 0:
                    platforms[-1].create_enemy(dynamic_sprites, enemy_speed)
                    
                # membuat power up baru
                if rnd.choice(range(powerup_chance)) == 0:
                    platforms[-1].create_powerup(dynamic_sprites)

            
            current_platform = True  # cek posisi pemain terhadap platform
            for platform in platforms:

                if current_platform:
                
                    if player.falls_off(platform):
                        current_platform = False
                    
                    # memberi suara saat pemain menginjak platform
                    elif player.lands_on(platform, platform.lastYPos, dynamic_sprites):
                        pygame.mixer.Sound.play(sounds.step_sound)
                        current_platform = False
                        
                platform.lastYPos = platform.rect.top

                # menambahkan power up ketika pemain menyentuh power up
                if platform.powerup is not None and player.touches(platform.powerup):
                    player.consumes(platform.powerup)
                    platform.remove_powerup()

                # menggerakkan musuh
                if platform.enemy is not None:
                    platform.enemy.move()
                    
                    # mengecek apakah pemain membunuh musuh
                    if player.projectile is not None and player.projectile.hits(platform.enemy):
                        pygame.mixer.Sound.play(sounds.explosion_sound)
                        platform.remove_enemy()
                        self.score += 500
                        
                    # mengecek apakah musuh membunuh pemain
                    elif player.touches(platform.enemy):
                        self.go_to_death_screen()

                # musuh mengeluarkan waterball
                if platform.projectile is not None:
                    platform.projectile.move()
                    
                    if platform.projectile.hits(player):
                        pygame.mixer.Sound.play(sounds.explosion_sound)
                        
                        # mengecek apakah pemain punya cadangan lives
                        if player.powerups['lives'] > 1:
                            player.powerups['lives'] -= 1
                            platform.remove_projectile()
                          
                        else:
                            self.go_to_death_screen()

                    # menghilangkan waterball saat terkena batas layar
                    elif platform.projectile.hits_boundary():
                        platform.remove_projectile()
                
                # musuh mengeluarkan waterball baru
                elif platform.enemy is not None and rnd.choice(range(projectile_chance)) == 0:
                    platform.create_projectile(projectile_speed, dynamic_sprites)

            # player kalah jika berada di bawah platform paling bawah
            if player.falls_below(platforms[0]):
                self.go_to_death_screen()
                pygame.mixer.Sound.play(sounds.fall_sound)

            player.animate()

            # background bergerak
            self.background1.check_background()
            self.background2.check_background()

            # menghitung skor
            if origin.rect.center[1]-player.rect.center[1] > self.score:
                self.score = origin.rect.center[1]-player.rect.center[1]

            # membuat teks
            scoreboard_surf, scoreboard_rect = render_text(self.small_font, 'Score: {}'.format(self.score), left=20,
                                                           top=20)
            lives_surf, lives_rect = render_text(self.small_font, 'Lives: {}'.format(player.powerups['lives']),
                                                 left=lives_marker.rect.right+10, top=lives_marker.rect.top+5)
            d_jump_surf, d_jump_rect = render_text(self.small_font, 'Double Jump: {}'.format(player.powerups['double_jump']),
                                                   left=d_jump_marker.rect.right+10, top=d_jump_marker.rect.top+5)
            waterball_surf, waterball_rect = render_text(self.small_font, 'Waterball: {}'.format(player.powerups['waterball']),
                                                       left=waterball_marker.rect.right+10, top=waterball_marker.rect.top+5)

            # memunculkan gambar ke layar
            for entity in dynamic_sprites:
                self.screen.blit(entity.surf, entity.rect)
            for entity in static_sprites:
                self.screen.blit(entity.surf, entity.rect)
            self.screen.blit(scoreboard_surf, scoreboard_rect)
            self.screen.blit(lives_surf, lives_rect)
            self.screen.blit(d_jump_surf, d_jump_rect)
            self.screen.blit(waterball_surf, waterball_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)
            
    def show_title(self) -> None:
    
        """
        Menampilkan pilihan yang disediakan di layar: play game, leaderboards, options, help
        """
    
        # memperbesar dan mengubah teks menjadi warna kuning saat tersentuh kursor
        title_surf, title_rect = render_text(self.large_font, 'Jump For Your Life!', x=screen_w//2, y=1.5*screen_h//5)
        play_game_surf_w, play_game_rect_w = render_text(self.small_font, 'Play Game', x=screen_w//2, y=2*screen_h//5)
        play_game_surf_y, play_game_rect_y = render_text(self.small_yellow_font, 'Play Game', x=screen_w//2, y=2*screen_h//5,
                                                         color=(255, 255, 0))
        leaderboard_surf_w, leaderboard_rect_w = render_text(self.small_font, 'Leaderboards', x=screen_w//2,
                                                             y=2.5*screen_h//5)
        leaderboard_surf_y, leaderboard_rect_y = render_text(self.small_yellow_font, 'Leaderboards', x=screen_w//2,
                                                             y=2.5*screen_h//5, color=(255, 255, 0))
        options_surf_w, options_rect_w = render_text(self.small_font, 'Options', x=screen_w//2, y=3*screen_h//5)
        options_surf_y, options_rect_y = render_text(self.small_yellow_font, 'Options', x=screen_w//2, y=3*screen_h//5,
                                                     color=(255, 255, 0))
        help_surf_w, help_rect_w = render_text(self.small_font, 'Help', x=screen_w//2, y=3.5*screen_h//5)
        help_surf_y, help_rect_y = render_text(self.small_yellow_font, 'Help', x=screen_w//2, y=3.5*screen_h//5,
                                               color=(255, 255, 0))
        about_surf_w, about_rect_w = render_text(self.small_font, 'About', x=screen_w//2, y=4*screen_h//5)
        about_surf_y, about_rect_y = render_text(self.small_yellow_font, 'About', x=screen_w//2, y=4*screen_h//5,
                                               color=(255, 255, 0))

        while self.showing_title:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()

                # mengecek pilihan yang dipilih pemain
                if play_game_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_character_selection()

                if leaderboard_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_leaderboard()

                if options_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_options()

                if help_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_help()

                if about_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_about()

            # memunculkan background dan title
            self.scrolling_background()
            self.screen.blit(title_surf, title_rect)
            
            # cek apakah mouse menyentuh salah satu pilihan
            if play_game_rect_w.collidepoint(mouse_pos):
                self.screen.blit(play_game_surf_y, play_game_rect_y)
            else:
                self.screen.blit(play_game_surf_w, play_game_rect_w)

            if leaderboard_rect_w.collidepoint(mouse_pos):
                self.screen.blit(leaderboard_surf_y, leaderboard_rect_y)
            else:
                self.screen.blit(leaderboard_surf_w, leaderboard_rect_w)

            if options_rect_w.collidepoint(mouse_pos):
                self.screen.blit(options_surf_y, options_rect_y)
            else:
                self.screen.blit(options_surf_w, options_rect_w)

            if help_rect_w.collidepoint(mouse_pos):
                self.screen.blit(help_surf_y, help_rect_y)
            else:
                self.screen.blit(help_surf_w, help_rect_w)

            if about_rect_w.collidepoint(mouse_pos):
                self.screen.blit(about_surf_y, about_rect_y)
            else:
                self.screen.blit(about_surf_w, about_rect_w)

            pygame.display.flip()
            self.clock.tick(self.fps)

    def show_character_selection(self) -> None:
    
        """
        Layar menampilkan pilihan karakter dan tingkat kesulitan.
        """
    
        difficulty_surf, difficulty_rect = render_text(self.medium_font, 'Choose Your Difficulty', x=screen_w//2,
                                                       y=screen_h//6)
        easy_surf_w, easy_rect_w = render_text(self.small_font, 'Easy', x=0.75*screen_w//3, y=1.5*screen_h//6)
        easy_surf_y, easy_rect_y = render_text(self.small_yellow_font, 'Easy', x=0.75*screen_w//3, y=1.5*screen_h//6,
                                               color=(255, 255, 0))
        medium_surf_w, medium_rect_w = render_text(self.small_font, 'Medium', x=1.5*screen_w//3, y=1.5*screen_h//6)
        medium_surf_y, medium_rect_y = render_text(self.small_yellow_font, 'Medium', x=1.5*screen_w//3, y=1.5*screen_h//6,
                                                   color=(255, 255, 0))
        hard_surf_w, hard_rect_w = render_text(self.small_font, 'Hard', x=2.25*screen_w//3, y=1.5*screen_h//6)
        hard_surf_y, hard_rect_y = render_text(self.small_yellow_font, 'Hard', x=2.25*screen_w//3, y=1.5*screen_h//6,
                                               color=(255, 255, 0))

        character_surf, character_rect = render_text(self.medium_font, 'Choose Your Character', x=screen_w//2,
                                                     y=2*screen_h//6)
        bunny = Player(screen_w//2, screen_h//2, 'Bunny')
        bunny_surf_w, bunny_rect_w = render_text(self.small_font, 'Bunny', x=screen_w//2, y=screen_h//2 + 10)
        bunny_surf_y, bunny_rect_y = render_text(self.small_yellow_font, 'Bunny', x=screen_w//2, y=screen_h//2 + 10,
                                             color=(255, 255, 0))

        sprites = pygame.sprite.Group()
        sprites.add([bunny])

        play_game_surf_w, play_game_rect_w = render_text(self.small_font, 'Play Game', x=screen_w//3, y=5*screen_h//6)
        play_game_surf_y, play_game_rect_y = render_text(self.small_yellow_font, 'Play Game', x=screen_w//3, y=5*screen_h//6,
                                                         color=(255, 255, 0))
        back_surf_w, back_rect_w = render_text(self.small_font, 'Main Menu', x=2*screen_w//3, y=5*screen_h//6)
        back_surf_y, back_rect_y = render_text(self.small_yellow_font, 'Main Menu', x=2*screen_w//3, y=5*screen_h//6,
                                               color=(255, 255, 0))
        error_surf, error_rect = render_text(self.small_yellow_font, 'Select Your Character/Difficulty', x=screen_w//2,
                                             y=5.5*screen_h//6, color=(255, 0, 0))

        error = False  # agar game tidak dimulai sebelum karakter dan tingkat kesulitan dipilih

        while self.showing_selection:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()

                if play_game_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                    
                        # cek apakah karakter dan tingkat kesulitan sudah dipilih
                        if self.difficulty is not None and self.character is not None:
                            self.go_to_game()
                        else:
                            error = True

                if back_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_title()
                        
                # menyesuaikan tingkat kesulitan dengan pilihan pemain
                elif easy_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.difficulty != 'easy':
                            self.difficulty = 'easy'
                        else:
                            self.difficulty = None

                elif medium_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.difficulty != 'medium':
                            self.difficulty = 'medium'
                        else:
                            self.difficulty = None

                elif hard_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.difficulty != 'hard':
                            self.difficulty = 'hard'
                        else:
                            self.difficulty = None

                # menentukan karakter sesuai pilihan pemain
        

                elif bunny_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.character != 'bunny':
                            self.character = 'bunny'
                        else:
                            self.character = None

            self.scrolling_background()
            self.screen.blit(difficulty_surf, difficulty_rect)
            self.screen.blit(character_surf, character_rect)
            
            # memperbesar dan mengubah font menjadi kuning saat terkena kursor
            if self.difficulty == 'easy' or easy_rect_w.collidepoint(mouse_pos):
                self.screen.blit(easy_surf_y, easy_rect_y)
            else:
                self.screen.blit(easy_surf_w, easy_rect_w)

            if self.difficulty == 'medium' or medium_rect_w.collidepoint(mouse_pos):
                self.screen.blit(medium_surf_y, medium_rect_y)
            else:
                self.screen.blit(medium_surf_w, medium_rect_w)

            if self.difficulty == 'hard' or hard_rect_w.collidepoint(mouse_pos):
                self.screen.blit(hard_surf_y, hard_rect_y)
            else:
                self.screen.blit(hard_surf_w, hard_rect_w)

            if self.character == 'bunny' or bunny_rect_w.collidepoint(mouse_pos):
                self.screen.blit(bunny_surf_y, bunny_rect_y)
                bunny.selection_animate()
            else:
                self.screen.blit(bunny_surf_w, bunny_rect_w)
                bunny.surf = bunny.stationary_image[0]

            if play_game_rect_w.collidepoint(mouse_pos):
                self.screen.blit(play_game_surf_y, play_game_rect_y)
            else:
                self.screen.blit(play_game_surf_w, play_game_rect_w)

            if back_rect_w.collidepoint(mouse_pos):
                self.screen.blit(back_surf_y, back_rect_y)
            else:
                self.screen.blit(back_surf_w, back_rect_w)
                
            
            # memunculkan kalimat error jika pemain sudah memulai game tetapi belum memilih karakter dan tingkat kesulitan
            if error:
                self.screen.blit(error_surf, error_rect)

            for entity in sprites:
                self.screen.blit(entity.surf, entity.rect)

            pygame.display.flip()
            self.clock.tick(self.fps)

    def show_options(self, entities: list) -> None:
    
       # state layar options
        
       
    
        title_surf, title_rect = render_text(self.medium_font, 'Options', x=screen_w//2, y=2*screen_h//5)
        plus_volume_surf_w, plus_volume_rect_w = render_text(self.small_font, '+', x=3.1*screen_w//5, y=2.5*screen_h//5)
        plus_volume_surf_y, plus_volume_rect_y = render_text(self.small_yellow_font, '+', x=3.1*screen_w//5,
                                                             y=2.5*screen_h//5, color=(255, 255, 0))
        minus_volume_surf_w, minus_volume_rect_w = render_text(self.small_font, '-', x=3.2*screen_w//5,
                                                               y=2.5*screen_h//5)
        minus_volume_surf_y, minus_volume_rect_y = render_text(self.small_yellow_font, '-', x=3.2*screen_w//5,
                                                               y=2.5*screen_h//5, color=(255, 255, 0))
        back_surf_w, back_rect_w = render_text(self.small_font, 'Back', x=screen_w//2, y=3*screen_h//5)
        back_surf_y, back_rect_y = render_text(self.small_yellow_font, 'Back', x=screen_w//2, y=3*screen_h//5,
                                               color=(255, 255, 0))

        while self.showing_options:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()

                if back_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.running:
                            self.pause_game()
                        else:
                            self.go_to_title()

                elif plus_volume_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        current_sound = sounds.waterball_sound.get_volume()
                        if current_sound > 0.85:
                            sounds.adjust_volume(1)
                        else:
                            sounds.adjust_volume(current_sound+0.1)

                elif minus_volume_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        current_sound = sounds.waterball_sound.get_volume()
                        if current_sound < 0.15:
                            sounds.adjust_volume(0)
                        else:
                            sounds.adjust_volume(current_sound-0.1)

            if entities is None:
                self.scrolling_background()
            else:
                self.screen.blit(entities[0], entities[1])
            self.screen.blit(title_surf, title_rect)

            if back_rect_w.collidepoint(mouse_pos):
                self.screen.blit(back_surf_y, back_rect_y)
            else:
                self.screen.blit(back_surf_w, back_rect_w)

            if plus_volume_rect_w.collidepoint(mouse_pos):
                self.screen.blit(plus_volume_surf_y, plus_volume_rect_y)
            else:
                self.screen.blit(plus_volume_surf_w, plus_volume_rect_w)

            if minus_volume_rect_w.collidepoint(mouse_pos):
                self.screen.blit(minus_volume_surf_y, minus_volume_rect_y)
            else:
                self.screen.blit(minus_volume_surf_w, minus_volume_rect_w)

            volume_surf, volume_rect = render_text(self.small_font, 'Volume: {:<3.0f}'.format(100*round(sounds.waterball_sound.get_volume(), 1)),
                                                   x=screen_w//2, y=2.5*screen_h//5)
            self.screen.blit(volume_surf, volume_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)

    def show_help(self, entities: list) -> None:
    
        
        # state layar help
      
        controls_surf, controls_rect = render_text(self.medium_font, 'Controls', x=screen_w//2, y=screen_h//5)
        jump_surf, jump_rect = render_text(self.small_helpfont, '<SPACE> - Use Double Jump while in the air', x=screen_w//2, y=1.25*screen_h//5)
        move_right_surf, move_right_rect = render_text(self.small_helpfont, '<RIGHT ARROW or D Key> - Jump Right',
                                                       x=screen_w//2, y=1.5*screen_h//5)
        move_left_surf, move_left_rect = render_text(self.small_helpfont, '<LEFT ARROW or A Key> - Jump Left',
                                                     x=screen_w//2, y=1.75 * screen_h//5)
        shoot_surf, shoot_rect = render_text(self.small_helpfont, '<MOUSE CLICK> - Shoot Waterball', x=screen_w//2,
                                             y=2*screen_h//5)

        tips_surf, tips_rect = render_text(self.medium_font, 'Help', x=screen_w//2, y=2.5*screen_h//5)

        lives_surf, lives_rect = render_text(self.small_helpfont, 'Collect          to gain extra lives when hit by an enemy!',
                                             x=screen_w//2, y=2.75*screen_h//5)
        jumps_surf, jumps_rect = render_text(self.small_helpfont, 'Collect          to gain extra jumps to use in the air!',
                                             x=screen_w//2, y=3*screen_h//5)
        waterballs_surf, waterballs_rect = render_text(self.small_helpfont, 'Collect          to gain waterballs to shoot at enemies!',
                                                     x=screen_w//2, y=3.25*screen_h//5)
        sprite_surfs = [controls_surf, jump_surf, move_right_surf, move_left_surf, shoot_surf, tips_surf, lives_surf, jumps_surf, waterballs_surf]
        sprite_rects = [controls_rect, jump_rect, move_right_rect, move_left_rect, shoot_rect, tips_rect, lives_rect, jumps_rect, waterballs_rect]

        marker_sprites = pygame.sprite.Group()
        lives_marker = Powerup(screen_w//2-130, 2.75*screen_h//5+10, 'lives')
        d_jump_marker = Powerup(screen_w//2-110, 3*screen_h//5+10, 'double_jump')
        waterball_marker = Powerup(screen_w//2-120, 3.25*screen_h//5+10, 'waterball')
        marker_sprites.add([lives_marker, d_jump_marker, waterball_marker])

        back_surf_w, back_rect_w = render_text(self.small_font, 'Back', x=screen_w//2, y=4*screen_h//5)
        back_surf_y, back_rect_y = render_text(self.small_yellow_font, 'Back', x=screen_w//2, y=4*screen_h//5,
                                               color=(255, 255, 0))

        while self.showing_help:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()

                if back_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.running:
                            self.pause_game()
                        else:
                            self.go_to_title()

            if entities is None:
                self.scrolling_background()
            else:
                self.screen.blit(entities[0], entities[1])

            for surf, rect in zip(sprite_surfs, sprite_rects):
                self.screen.blit(surf, rect)

            for entity in marker_sprites:
                self.screen.blit(entity.surf, entity.rect)

            if back_rect_w.collidepoint(mouse_pos):
                self.screen.blit(back_surf_y, back_rect_y)
            else:
                self.screen.blit(back_surf_w, back_rect_w)

            pygame.display.flip()
            self.clock.tick(self.fps)

    def show_about(self, entities: list) -> None:
    
        
        # state layar about

        judul_surf, judul_rect = render_text(self.medium_font, 'DTS WIT Kelas G - Kelompok H', x=screen_w//2, y=screen_h//5)
        nama1_surf, nama1_rect = render_text(self.small_font, 'Rahma Aulia Zahra', x=screen_w//2, y=1.25*screen_h//5)
        nama2_surf, nama2_rect = render_text(self.small_font, 'Sri Utami',
                                                       x=screen_w//2, y=1.5*screen_h//5)
        nama3_surf, nama3_rect = render_text(self.small_font, 'Feybe Anjeli Sitanggang',
                                                     x=screen_w//2, y=1.75*screen_h//5)
        nama4_surf, nama4_rect = render_text(self.small_font, 'Prenzeline Tyasamesi', x=screen_w//2,
                                             y=2*screen_h//5)
        nama5_surf, nama5_rect = render_text(self.small_font, 'Dianisa Wulandari', x=screen_w//2,
                                             y=2.25*screen_h//5)

        kredit_surf, kredit_rect = render_text(self.medium_font, 'Credit', x=screen_w//2, y=2.75*screen_h//5)

        alex_surf, alex_rect = render_text(self.small_font, 'Dungeon Jump from alexk-1998',
                                             x=screen_w//2, y=3*screen_h//5)
        tileset_surf, tileset_rect = render_text(self.small_font, 'Dungeon Tileset',
                                             x=screen_w//2, y=3.25*screen_h//5)
        bunny_surf, bunny_rect = render_text(self.small_font, 'Bunny Games Asset Source',
                                                     x=screen_w//2, y=3.5*screen_h//5)
        sprite_surfs = [judul_surf, nama1_surf, nama2_surf, nama3_surf, nama4_surf, nama5_surf, kredit_surf, alex_surf, tileset_surf, bunny_surf]
        sprite_rects = [judul_rect, nama1_rect, nama2_rect, nama3_rect, nama4_rect, nama5_rect, kredit_rect, alex_rect, tileset_rect, bunny_rect]

        marker_sprites = pygame.sprite.Group()
        marker_sprites.add()

        back_surf_w, back_rect_w = render_text(self.small_font, 'Back', x=screen_w//2, y=4*screen_h//5)
        back_surf_y, back_rect_y = render_text(self.small_yellow_font, 'Back', x=screen_w//2, y=4*screen_h//5,
                                               color=(255, 255, 0))

        while self.showing_about:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()

                if back_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        if self.running:
                            self.pause_game()
                        else:
                            self.go_to_title()

            if entities is None:
                self.scrolling_background()
            else:
                self.screen.blit(entities[0], entities[1])

            for surf, rect in zip(sprite_surfs, sprite_rects):
                self.screen.blit(surf, rect)

            for entity in marker_sprites:
                self.screen.blit(entity.surf, entity.rect)

            if back_rect_w.collidepoint(mouse_pos):
                self.screen.blit(back_surf_y, back_rect_y)
            else:
                self.screen.blit(back_surf_w, back_rect_w)

            pygame.display.flip()
            self.clock.tick(self.fps)

    def show_leaderboard(self) -> None:
    
        """
        State layar leaderboard
        """
    
        title_surf, title_rect = render_text(self.medium_font, 'Leaderboards', x=screen_w//2, y=screen_h//4)
        leaderboards = []
        text_y = screen_h//4+35
        i = 0
        for entry in self.leaderboard[:10]:
            i += 1
            text_y += 25
            text = '{}.  '.format(i)+' '.join(map(str, entry))
            leaderboards.append(render_text(self.small_font, text, x=screen_w//2, y=text_y))
        play_game_surf_w, play_game_rect_w = render_text(self.small_font, 'Play Game', x=screen_w//3,
                                                         y=leaderboards[-1][1].bottom+50)
        play_game_surf_y, play_game_rect_y = render_text(self.small_yellow_font, 'Play Game', x=screen_w//3,
                                                         y=leaderboards[-1][1].bottom+50, color=(255, 255, 0))
        back_surf_w, back_rect_w = render_text(self.small_font, 'Main Menu', x=2*screen_w//3,
                                               y=leaderboards[-1][1].bottom+50)
        back_surf_y, back_rect_y = render_text(self.small_yellow_font, 'Main Menu', x=2*screen_w//3,
                                               y=leaderboards[-1][1].bottom+50, color=(255, 255, 0))

        while self.showing_leaderboard:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.exit()

                if play_game_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_character_selection()

                if back_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_title()

            self.scrolling_background()
            self.screen.blit(title_surf, title_rect)

            if play_game_rect_w.collidepoint(mouse_pos):
                self.screen.blit(play_game_surf_y, play_game_rect_y)
            else:
                self.screen.blit(play_game_surf_w, play_game_rect_w)

            if back_rect_w.collidepoint(mouse_pos):
                self.screen.blit(back_surf_y, back_rect_y)
            else:
                self.screen.blit(back_surf_w, back_rect_w)

            for entity in leaderboards:
                self.screen.blit(entity[0], entity[1])

            pygame.display.flip()
            self.clock.tick(self.fps)

    def show_pause_screen(self) -> None:
    
        """
        Menampilkan layar Pause Game
        """
    
        title_surf, title_rect = render_text(self.medium_font, 'Paused', x=screen_w//2, y=2*screen_w//5)
        resume_surf_w, resume_rect_w = render_text(self.small_font, 'Resume', x=screen_w//2, y=2.5*screen_w//5)
        resume_surf_y, resume_rect_y = render_text(self.small_yellow_font, 'Resume', x=screen_w//2, y=2.5*screen_w//5,
                                                   color=(255, 255, 0))
        options_surf_w, options_rect_w = render_text(self.small_font, 'Options', x=screen_w//2, y=3*screen_w//5)
        options_surf_y, options_rect_y = render_text(self.small_yellow_font, 'Options', x=screen_w//2, y=3*screen_w//5,
                                                     color=(255, 255, 0))
        help_surf_w, help_rect_w = render_text(self.small_font, 'Help', x=screen_w//2, y=3.5*screen_w//5)
        help_surf_y, help_rect_y = render_text(self.small_yellow_font, 'Help', x=screen_w//2, y=3.5*screen_w//5,
                                               color=(255, 255, 0))
        menu_surf_w, menu_rect_w = render_text(self.small_font, 'Main Menu', x=screen_w//2, y=4*screen_w//5)
        menu_surf_y, menu_rect_y = render_text(self.small_yellow_font, 'Main Menu', x=screen_w//2, y=4*screen_w//5,
                                               color=(255, 255, 0))
        
        box_surf = self.screen.subsurface((0, 0, screen_w, screen_h)).copy()
        box_rect = box_surf.get_rect()

        while self.paused:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
                if event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.go_to_game()

                if event.type == pygame.QUIT:
                    self.exit()

                if resume_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_game()

                if options_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_options()
                        self.show_options([box_surf, box_rect])

                if help_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_help()
                        self.show_help([box_surf, box_rect])

                if menu_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_title()

            self.screen.blit(box_surf, box_rect)
            self.screen.blit(title_surf, title_rect)

            if resume_rect_w.collidepoint(mouse_pos):
                self.screen.blit(resume_surf_y, resume_rect_y)
            else:
                self.screen.blit(resume_surf_w, resume_rect_w)

            if options_rect_w.collidepoint(mouse_pos):
                self.screen.blit(options_surf_y, options_rect_y)
            else:
                self.screen.blit(options_surf_w, options_rect_w)

            if help_rect_w.collidepoint(mouse_pos):
                self.screen.blit(help_surf_y, help_rect_y)
            else:
                self.screen.blit(help_surf_w, help_rect_w)

            if menu_rect_w.collidepoint(mouse_pos):
                self.screen.blit(menu_surf_y, menu_rect_y)
            else:
                self.screen.blit(menu_surf_w, menu_rect_w)

            pygame.display.flip()
            self.clock.tick(self.fps)

    def show_death_screen(self):
    
       
        # Memunculkan Tampilan pada saat player mati
        

        title_surf, title_rect = render_text(self.medium_font, 'You Died!', x=screen_w//2, y=screen_h//5)
        restart_surf_w, restart_rect_w = render_text(self.small_font, 'Restart', x=screen_w//2, y=2*screen_h//5)
        restart_surf_y, restart_rect_y = render_text(self.small_yellow_font, 'Restart', x=screen_w//2, y=2*screen_h//5,
                                                     color=(255, 255, 0))
        selection_surf_w, selection_rect_w = render_text(self.small_font, 'Change Character/Difficulty', x=screen_w//2,
                                                         y=2.5*screen_h//5)
        selection_surf_y, selection_rect_y = render_text(self.small_yellow_font, 'Change Character/Difficulty', x=screen_w//2,
                                                         y=2.5*screen_h//5, color=(255, 255, 0))
        menu_surf_w, menu_rect_w = render_text(self.small_font, 'Main Menu', x=screen_w//2, y=3*screen_h//5)
        menu_surf_y, menu_rect_y = render_text(self.small_yellow_font, 'Main Menu', x=screen_w//2, y=3*screen_h//5,
                                               color=(255, 255, 0))

        highscore = self.new_highscore()
        name = ''
        if highscore:
            highscore_surf, highscore_rect = render_text(self.small_font, 'New Highscore: {}'.format(self.score),
                                                         x=screen_w//2, y=3.5*screen_h//5)
            enter_surf, enter_rect = render_text(self.small_font, 'Press ENTER to save player name', x=screen_w//2,
                                                 y=4*screen_h//5)
        else:
            highscore_surf = None
            highscore_rect = None
            enter_surf = None
            enter_rect = None

        while self.showing_death:
            mouse_pos = pygame.mouse.get_pos()

            for event in pygame.event.get():
            
                # untuk menuliskan nama di highscore
                if event.type == KEYDOWN and highscore:
                    if event.key == K_BACKSPACE:
                        name = name[:-1]
                    elif event.key == K_RETURN:
                        self.update_leaderboard(name)
                        self.go_to_leaderboard()
                    else:
                        name += event.unicode

                if event.type == pygame.QUIT:
                    self.exit()

                if restart_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_game()

                if selection_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_character_selection()

                if menu_rect_w.collidepoint(mouse_pos):
                    if event.type == pygame.MOUSEBUTTONDOWN:
                        self.go_to_title()

            self.scrolling_background()
            self.screen.blit(title_surf, title_rect)

            if restart_rect_w.collidepoint(mouse_pos):
                self.screen.blit(restart_surf_y, restart_rect_y)
            else:
                self.screen.blit(restart_surf_w, restart_rect_w)

            if selection_rect_w.collidepoint(mouse_pos):
                self.screen.blit(selection_surf_y, selection_rect_y)
            else:
                self.screen.blit(selection_surf_w, selection_rect_w)

            if menu_rect_w.collidepoint(mouse_pos):
                self.screen.blit(menu_surf_y, menu_rect_y)
            else:
                self.screen.blit(menu_surf_w, menu_rect_w)

            if highscore_surf is not None:
                name_surf, name_rect = render_text(self.small_font, 'Enter Your Name: {}'.format(name), x=screen_w//2,
                                                   y=3.75*screen_h//5)
                self.screen.blit(highscore_surf, highscore_rect)
                self.screen.blit(name_surf, name_rect)
                self.screen.blit(enter_surf, enter_rect)

            pygame.display.flip()
            self.clock.tick(self.fps)
        self.highscore = False

    # fungsi untuk mengolah game states
    def go_to_title(self) -> None:
    
        
        # Mengubah game state untuk menampilkan layar judul
    
        self.showing_title = True
        self.showing_selection = False
        self.showing_leaderboard = False
        self.showing_options = False
        self.showing_help = False
        self.showing_about = False
        self.running = False
        self.paused = False
        self.showing_death = False

    def go_to_character_selection(self) -> None:
    
        #Mengubah game state untuk menampilkan layar seleksi karakter
        
        self.showing_selection = True
        self.showing_title = False
        self.showing_leaderboard = False
        self.running = False
        self.showing_death = False

    def go_to_leaderboard(self) -> None:
     
        # Mengubah game state untuk menampilkan layar leaderboard
        
        self.showing_leaderboard = True
        self.showing_title = False
        self.showing_death = False

    def go_to_options(self) -> None:
    
        # Mengubah game state untuk menampilkan layar options

        self.showing_options = True
        self.showing_title = False
        self.paused = False

    def go_to_help(self) -> None:
    
        # Mengubah game state untuk menampilkan layar help
    
        self.showing_help = True
        self.showing_title = False
        self.paused = False

    def go_to_about(self) -> None:
    
        # Mengubah game state untuk menampilkan layar about
    
        self.showing_about = True
        self.showing_title = False
        self.paused = False

    def go_to_game(self) -> None:
    
        # Mengubah game state untuk run game
    
        self.running = True
        self.showing_title = False
        self.showing_selection = False
        self.paused = False
        self.showing_death = False

    def pause_game(self) -> None:
    
        # Mengubah game state untuk menampilkan paused
        
        self.paused = True
        self.showing_help = False
        self.showing_about = False
        self.showing_options = False

    def go_to_death_screen(self) -> None:
    
        # Mengubah game state untuk menampilkan death screen
    
        self.showing_death = True
        self.running = False

    def exit(self) -> None:
    
        # Keluar dari semua state dan screen
        
        self.showing_death = False
        self.running = False
        self.showing_title = False
        self.showing_selection = False
        self.showing_leaderboard = False
        self.showing_help = False
        self.showing_about = False
        self.paused = False
        self.showing_options = False
        pygame.display.quit()
        pygame.quit()
        sys.exit()

    def new_highscore(self) -> bool:
    
        # Mengembalikan nilai boolean yang mengindikasi pemain telah mencapai top 10 score
    
        self.leaderboard.append(['temp', self.score])
        self.leaderboard = sorted(self.leaderboard, reverse=True, key=lambda x: x[1])
        return ['temp', self.score] in self.leaderboard[:10]

    def update_leaderboard(self, name) -> None:
    
        """
        Memperbarui file txt leaderboard
        name: nama pemain untuk menyimpan score
        """
    
        self.leaderboard[self.leaderboard.index(['temp', self.score])][0] = name
        entry_text = [' '.join(map(str, entry)) for entry in self.leaderboard[:10]]
        open('leaderboard.txt', 'w').write('\n'.join(entry_text))

    def scrolling_background(self) -> None:
        
        # Menggerakkan gambar background 1 pixel per frame
    
        self.background1.rect.top += 1
        self.background2.rect.top += 1
        self.background1.check_background()
        self.background2.check_background()
        self.screen.blit(self.background1.surf, self.background1.rect)
        self.screen.blit(self.background2.surf, self.background2.rect)


class Player(pygame.sprite.Sprite):

    def __init__(self, x, y, name):
        super().__init__()
        self.name = name
        self.v_x = 5
        self.v_y = 8.5
        self.g = 6
        self.time = 0
        self.dt = 0.135
        self.on_platform = True
        self.is_jumping = False
        self.is_falling = False
        self.face_right = True
        self.is_stationary = True
        self.powerups = {'lives': 1, 'double_jump': 0, 'waterball': 0}
        self.projectile = None
        self.frame = 0

    
        self.run_right = frames.bunny_run_right_img
        self.run_left = frames.bunny_run_left_img
        self.jump_image = frames.bunny_jump_img
        self.stationary_image = frames.bunny_idle_img
        self.surf = self.stationary_image[0]
        self.w, self.h = self.surf.get_size()
        self.rect = self.surf.get_rect()
        self.rect.center = (round(x), 0)
        self.rect.bottom = round(y)

    def move(self, pressed_keys: list, dynamic_sprites: pygame.sprite.Group) -> None:
    
        """
        Menggerakkan grup dynamic_sprites secara vertikal menghitung jarak antar frame berdasarkan persamaan pergerakan projectile
        Menggerakkan pemain secara horizontal berdasarkan tombol yang ditekan
        pressed_keys: daftar dari keys yang ditekan
        dynamic_sprites: grup dari sprites untuk digerakkan secara vertikal
        jumping * 1.5 untuk lompat lebih tinggi
        """

        if pressed_keys[K_LEFT] or pressed_keys[K_a]:
            if self.on_platform:
                self.is_jumping = True
                self.on_platform = False
                self.time = 0
                pygame.mixer.Sound.play(sounds.jump_sound)
            self.rect.move_ip((-self.v_x, 0))
            self.face_right = False
            self.frame += 1
            self.is_stationary = False
            if self.rect.center[0] < 0:
                self.rect.right = screen_w+self.w//2
        elif pressed_keys[K_RIGHT] or pressed_keys[K_d]:
            if self.on_platform:
                self.is_jumping = True
                self.on_platform = False
                self.time = 0
                pygame.mixer.Sound.play(sounds.jump_sound)
            self.rect.move_ip((self.v_x, 0))
            self.face_right = True
            self.frame += 1
            self.is_stationary = False
            if self.rect.center[0] > screen_w:
                self.rect.left = -self.w//2
        else:
            self.frame = 0
            self.is_stationary = True

        dy = 0
        if self.is_jumping:
            self.time += self.dt
            dy = round(self.v_y*self.time*1.36-0.5*self.g*self.time ** 2)  # persamaan pergerakan projectile dy = v_y*t - 0.5*g*t**2
        elif self.is_falling:
            self.time += self.dt
            dy = round(-0.3*self.g*self.time ** 2)  # persamaan pergerakan projectile dy = - 0.5*g*t**2
        if dy < -1.6*self.v_y:
            dy = -14
        if dy != 0:
            for sprite in dynamic_sprites:
                sprite.rect.move_ip((0, dy))

    def touches(self, enemy: pygame.sprite.Sprite) -> bool:
    
        """
        enemy: mengecek objek sprite untuk collision dengan pemain
        mengembaikan nilai kebenaran dari collision
        """
    
        return self.rect.colliderect(enemy.rect)

    def falls_below(self, platform: pygame.sprite.Sprite) -> bool:
    
        """
        platform: sprite object to compare height with player
        Return true if player is below the platform
        """
    
        if self.rect.top > platform.rect.bottom:
            self.rect.move_ip((0, 5))
            if self.rect.top >= screen_h:
                return True
        return False

    def lands_on(self, platform: pygame.sprite.Sprite, last_top_pos: int, dynamic_sprites: pygame.sprite.Group) -> bool:
    
        """
        platform: objek sprite untuk dicek jika pemain mendarat
        last_top_pos: nilai integer dari frame posisi atas platform sebelumnya
        dynamic_sprites: grup dari sprites untuk di gerakkan secara vertikal jika dibutuhkan untuk menghindari masalah dengan rounding
        Return true jika pemain mendarat di platform
        mengangkat semua dynamic sprites untuk menghindari rounding errors 
        """
    
        if not self.on_platform and (self.rect.left <= platform.rect.right) and (self.rect.right >= platform.rect.left):
            if platform.rect.top <= self.rect.bottom <= last_top_pos:
                dy = round(platform.rect.top-self.rect.bottom)
                
                # menangani rounding errors
                for sprite in dynamic_sprites:
                    sprite.rect.move_ip((0, -dy))
                self.on_platform = True
                self.is_jumping = False
                self.is_falling = False
                self.time = 0
                return True
        return False

    def falls_off(self, platform: pygame.sprite.Sprite) -> bool:
    
        """
        platform: sprite object untuk mengecek jika pemain jatuh
        Returns nilai boolean jika pemain keluar dari platform tanpa melompat
        """
     
        if (self.rect.left > platform.rect.right) or (self.rect.right < platform.rect.left):
            if self.rect.bottom == platform.rect.top:
                self.on_platform = False
                self.is_falling = True
                return True
        return False

    def consumes(self, powerup: pygame.sprite.Sprite) -> None:
    
        """
        powerup: untuk menambahkan powerup di inventory pemain
        """
    
        self.powerups[powerup.name] += 1

    def animate(self) -> None:
    
        """
       untuk mengelola animasi pemain
        """
    
        if self.face_right:
            if self.is_jumping:
                self.surf = self.run_right[0]
            elif self.is_falling:
                self.surf = self.stationary_image[0]
            elif self.is_stationary:
                self.surf = self.stationary_image[0]
            else:
                self.surf = self.run_right[self.frame//5 % 2]
        else:
            if self.is_jumping or self.is_falling:
                self.surf = self.run_left[0]
            elif self.is_stationary:
                self.surf = self.stationary_image[0]
            else:
                self.surf = self.run_left[self.frame//5 % 2]

    def selection_animate(self) -> None:
    
        """
        untuk mengelola animasi di layar pemilihan karakter
        """
    
        self.surf = self.run_right[self.frame//5 % 2]
        self.frame += 1

    def create_projectile(self, pos, dynamic_sprites: pygame.sprite.Group) -> None:
    
        """
        membuat bola air berdasarkan klik mouse
        pos: posisi mouse saat mengklik untuk menembakkan projectile
        dynamic_sprites: sprite group to ditambahkan projectile
        """
    
        v = pygame.math.Vector2()
        v.xy = (pos[0]-self.rect.center[0]) / 40, (pos[1]-self.rect.center[1]) / 40
        norm = v.length()
        if norm < 6:
            v = v*6 / norm
        self.projectile = Projectile(self.rect.center, round(v[0]), round(v[1]))
        dynamic_sprites.add(self.projectile)
        pygame.mixer.Sound.play(sounds.waterball_sound)

    def remove_projectile(self) -> None:
    
        """
        menghapus projectile
        """
    
        self.projectile.kill()
        self.projectile = None


class Platform(pygame.sprite.Sprite):

    def __init__(self, pos):
        super().__init__()
        self.lastYPos = 0
        self.enemy = None
        self.powerup = None
        self.projectile = None
        self.surf = frames.platform_img
        self.w, self.h = self.surf.get_size()
        self.rect = self.surf.get_rect()
        self.rect.center = self.create_platform(pos)

    def create_platform(self, pos: tuple) -> tuple:
    
        """
        membuat platform baru menggunakan random number generation dan berdasarkan koordinat sebelumnya
        pos : tuple berisi posisi dari platform lain untuk digunakan sebagai basis untuk koordinat platform baru
        return tuple berisi posisi platform selanjutnya
        """
    
        x_i = pos[0]
        y_i = pos[1]
        v_x = 5
        v_y = 8.5
        y_max = v_y ** 2  # 12*(v_y**2)/(2*G)
        x_max = 4*v_x*v_y  # 24*v_x*v_y/G
        
        
        # secara acak menentukan posisi platform baru
        x = x_i+rnd.uniform(-x_max, x_max)
        y = y_i-rnd.uniform(2*y_max, 1.5*y_max)

        # mengecek validitas posisi platform baru
        if x <= self.w:
            x = x_i+rnd.uniform(0.5*x_max, x_max)
        elif x >= screen_w-self.w:
            x = x_i-rnd.uniform(0.5*x_max, x_max)
        if (x-x_i < 0.5*x_max) and (x-x_i > 0):
            x = x_i+rnd.uniform(0.5*x_max, x_max)
        if (x-x_i > -0.5*x_max) and (x-x_i < 0):
            x = x_i-rnd.uniform(0.5*x_max, x_max)
        if x < self.w//2:
            x = self.w//2
        if x > screen_w-self.w//2:
            x = screen_w-self.w//2
        return round(x), round(y)

    def create_enemy(self, dynamic_sprites: pygame.sprite.Group, speed: int) -> None:
    
        """
        membuat enemy sprite dan menambahkannya ke dynamic sprites group
        """
    
        self.enemy = Enemy(self.rect.center[0], self.rect.top, speed)
        dynamic_sprites.add(self.enemy)

    def create_powerup(self, dynamic_sprites: pygame.sprite.Group) -> None:
    
        """
        membuat powerup sprites dan menambahkannya ke dynamic sprites group
        """
    
        num = rnd.randint(0, 6)
        if num == 0:
            self.powerup = Powerup(self.rect.center[0], self.rect.top, 'lives')
        elif num in [1, 2, 3]:
            self.powerup = Powerup(self.rect.center[0], self.rect.top, 'double_jump')
        elif num in [4, 5, 6]:
            self.powerup = Powerup(self.rect.center[0], self.rect.top, 'waterball')
        dynamic_sprites.add(self.powerup)

    def create_projectile(self, v_y: int, dynamic_sprites: pygame.sprite.Group) -> None:
    
        """
        membuat projectile sprites dan menambahkannya ke dynamic sprites group
        v_y: kecepatan vertikal dari sprites
        """
    
        self.projectile = Projectile(self.enemy.rect.center, 0, v_y)
        dynamic_sprites.add(self.projectile)
        pygame.mixer.Sound.play(sounds.waterball_sound)

    def remove_platform(self, platforms: list) -> None:
    
        """
        Remove platform pertama dari list platform (paling rendah di layar)
        platforms: list dari platform yang aktif
        """
    
        platforms.pop(0)
        if self.enemy is not None:
            self.remove_enemy()
        if self.projectile is not None:
            self.remove_projectile()
        if self.powerup is not None:
            self.remove_powerup()
        self.kill()

    def remove_enemy(self) -> None:
    
        """
        Remove enemy terasosiasi dengan platform
        """
    
        self.enemy.kill()
        self.enemy = None

    def remove_powerup(self) -> None:
    
        """
        Remove powerup terasosiasi platform
        """
    
        self.powerup.kill()
        self.powerup = None

    def remove_projectile(self) -> None:
    
        """
        Remove projectile terasosiasi platform
        """
    
        self.projectile.kill()
        self.projectile = None


class Enemy(pygame.sprite.Sprite):

    def __init__(self, x, y, v_x):
        super().__init__()
        self.v_x = v_x
        self.face_right = rnd.randint(0, 1)
        self.frame = 0
        self.run_right = frames.demon_run_right_img
        self.run_left = frames.demon_run_left_img
        if self.face_right:
            self.surf = self.run_right[0]
        else:
            self.surf = self.run_left[0]
        self.rect = self.surf.get_rect()
        self.rect.center = (x, 0)
        self.rect.bottom = y

    def move(self) -> None:
    
        """
        menggerakkan jarak enemy (v_x, v_y) per frame
        """
    
        if self.face_right:
            self.rect.move_ip((self.v_x, 0))
            self.frame += 1
            self.surf = self.run_right[self.frame//4 % 4]
            if self.rect.right > screen_w:
                self.face_right = False
        else:
            self.rect.move_ip((-self.v_x, 0))
            self.frame += 1
            self.surf = self.run_left[self.frame//4 % 4]
            if self.rect.left < 0:
                self.face_right = True


class Projectile(pygame.sprite.Sprite):

    def __init__(self, pos, v_x, v_y):
        super().__init__()
        self.v_x = v_x
        self.v_y = v_y
        self.surf = frames.water_img
        self.rect = self.surf.get_rect()
        self.rect.center = (pos[0], pos[1])
        self.new_projectile = True

    def move(self) -> None:
    
        """
        menggerakkan jarak projectile (v_x, v_y) per frame
        """
    
        self.rect.move_ip((self.v_x, self.v_y))

    def hits(self, obj: pygame.sprite.Sprite) -> bool:
    
        """
        obj: pygame.sprite.Sprite object yang mungkin telah tercollition dengan platform
        Return nilai boolean mengindikasikan collision
        """
    
        if self.rect.colliderect(obj.rect):
            return True
        return False

    def hits_boundary(self) -> bool:
    
        """
        Return a boolean indicating whether the projectile has moved out of bounds
        """
    
        if self.new_projectile and self.rect.bottom <= 0:
            return False
        else:
            self.new_projectile = False
        if self.rect.left >= screen_w or self.rect.right <= 0:
            return True
        if self.rect.top >= screen_h or self.rect.bottom <= 0:
            return True
        return False


class Powerup(pygame.sprite.Sprite):

    def __init__(self, x, y, name):
        super().__init__()
        self.name = name
        if self.name == 'lives':
            self.surf = frames.heart_img
        elif self.name == 'double_jump':
            self.surf = frames.blue_flask_img
        elif self.name == 'waterball':
            self.surf = frames.red_flask_img
        self.rect = self.surf.get_rect()
        self.rect.center = (round(x), 0)
        self.rect.bottom = round(y)


class Origin(pygame.sprite.Sprite):

    def __init__(self, pos):
        super().__init__()
        self.surf = pygame.Surface((1, 1))
        self.rect = self.surf.get_rect()
        self.rect.center = (pos[0], pos[1])


class Background(pygame.sprite.Sprite):

    def __init__(self, y):
        super().__init__()
        self.surf = frames.background_img
        self.rect = self.surf.get_rect()
        self.w, self.h = self.surf.get_size()
        self.rect.left = 0
        self.rect.top = y

    def check_background(self) -> None:
    
        """
        mengecek apakah background telah terangkat keluar layar
        mengangkat background untuk menutupi seluruh layar game
        """
    
        if self.rect.top > screen_h:
            self.rect.bottom = self.rect.top-self.h
        if self.rect.bottom < 0:
            self.rect.top = self.rect.bottom+self.h
            

def get_leaderboard() -> list:

    """
    Return daftar dari semua masukan leaderboard aktif
    """

    entries = []
    for entry in open('leaderboard.txt', 'r').readlines():
        name, score = entry.split()
        entries.append([name, int(score)])
    return entries


def render_text(font: pygame.font.Font, text: str, **args) -> tuple:

    """
    font: font yang digunakan
    text: text untuk dirender
    mengembalikan pygame surfaced dan rect object untuk memasukkan teks ke layar
    """

    # untuk menempatkan teks
    x = args.get('x', None)
    y = args.get('y', None)
    left = args.get('left', None)
    right = args.get('right', None)
    top = args.get('top', None)
    bottom = args.get('bottom', None)
    color = args.get('color', (255, 255, 255))

    _surf = font.render(text, True, color)
    _rect = _surf.get_rect()
    if x is not None:
        _rect.center = (round(x), round(y))
    else:
        if left is not None:
            _rect.left = round(left)
        else:
            _rect.right = round(right)
        if top is not None:
            _rect.top = round(top)
        else:
            _rect.bottom = round(bottom)
    return _surf, _rect


if __name__ == '__main__':
    main()
