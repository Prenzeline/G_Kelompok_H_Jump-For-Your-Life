import pygame

pygame.mixer.init()

jump_sound = pygame.mixer.Sound('sounds/jump.wav')
step_sound = pygame.mixer.Sound('sounds/step2.wav')
waterball_sound = pygame.mixer.Sound('sounds/waterball.wav')
explosion_sound = pygame.mixer.Sound('sounds/waterball_explosion.wav')
fall_sound = pygame.mixer.Sound('sounds/fall.wav')


def adjust_volume(volume: float) -> None:

    """
    volume: float value between 0 and 1 representing the volume of sound effects
    Sets the volume of all sound effects to the value volume
    """

    jump_sound.set_volume(volume)
    step_sound.set_volume(volume)
    waterball_sound.set_volume(volume)
    explosion_sound.set_volume(volume)
    fall_sound.set_volume(volume)


adjust_volume(0.5)
