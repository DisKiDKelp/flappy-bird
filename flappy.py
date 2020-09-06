import os
import pygame
import neat
import time
import random

pygame.font.init()
gen = 0
WIN_WIDTH = 500
WIN_HEIGHT = 800
WIN = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("IMGS", "bird1.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("IMGS", "bird2.png"))), pygame.transform.scale2x(pygame.image.load(os.path.join("IMGS", "bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("IMGS", "pipe.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("IMGS", "base.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("IMGS", "bg.png")))
STAT_FONT = pygame.font.SysFont("comic-sans", 50)

class Bird:
    IMGS = BIRD_IMGS
    MAX_ROTATION = 25
    ROT_VEL = 20
    ANIMATION_TIME = 5

    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.tilt = 0
        self.tick_count = 0
        self.vel = 0
        self.height = self.y
        self.img_count = 0
        self.img = self.IMGS[0]

    def jump(self):
        self.vel = -10.5
        self.tick_count = 0
        self.height = self.y

    def move(self):
        self.tick_count += 1

        d = self.vel * self.tick_count + 1.5*self.tick_count**2

        if d >= 16:
            d = 16

        if d < 0:
            d -=2

        self.y = self.y + d

        if d < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count < self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count < self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count < self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count < self.ANIMATION_TIME*4 + 1 :
            self.img = self.IMGS[0]
            self.img_count = 0

        if self.tilt <= -80:
            self.img = self.IMGS[1]
            self.img_count = self.ANIMATION_TIME*2

        rotated_image = pygame.transform.rotate(self.img, self.tilt)
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)

    def get_mask(self):
        return pygame.mask.from_surface(self.img)


class Pipe:
    GAP = 200
    VEL = 3

    def __init__(self, x):
        self.x  = x
        self.height = 0
        self.gap = 100

        self.top = 0
        self.bottom = 0
        self.PIPE_TOP = pygame.transform.flip(PIPE_IMG, False, True)
        self.PIPE_BOTTOM = PIPE_IMG

        self.passed = False
        self.set_height()

    def set_height(self):
        self.height = random.randrange(50, 450)
        self.top = self.height - self.PIPE_TOP.get_height()
        self.bottom = self.height + self.GAP

    def move(self):
        self.x -= self.VEL

    def draw(self, win):
        win.blit(self.PIPE_TOP, (self.x, self.top))
        win.blit(self.PIPE_BOTTOM, (self.x, self.bottom))

    def collide(self, bird):
        bird_mask = bird.get_mask()
        top_mask = pygame.mask.from_surface(self.PIPE_TOP)
        bottom_mask = pygame.mask.from_surface(self.PIPE_BOTTOM)

        top_offset = (self.x - bird.x, self.top - round(bird.y))
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        b_point = bird_mask.overlap(bottom_mask, bottom_offset)
        t_point = bird_mask.overlap(top_mask, top_offset)

        if b_point or t_point:
            return True

        return False


class Base:
    VEL = 3
    WIDTH = BASE_IMG.get_width()
    IMG = BASE_IMG

    def __init__(self, y):
        self.y = y
        self.x1 = 0
        self.x2 = self.WIDTH

    def move(self):
        self.x1 -= self.VEL
        self.x2 -= self.VEL

        if self.x1 + self.WIDTH < 0:
            self.x1 = self.x2 + self.WIDTH

        if self.x2 + self.WIDTH < 0:
            self.x2 = self.x1 + self.WIDTH

    def draw(self, win):
        win.blit(self.IMG, (self.x1, self.y))
        win.blit(self.IMG, (self.x2, self.y))



def draw_window(win, birds, pipes, base, score, gen):
    win.blit(BG_IMG, (0,0))

    for pipe in pipes:
        pipe.draw(win)

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    # score
    score_label = STAT_FONT.render("Score: " + str(score),1,(255,255,255))
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))

    # generations
    score_label = STAT_FONT.render("Gens: " + str(gen-1),1,(255,255,255))
    win.blit(score_label, (10, 10))

    # alive
    score_label = STAT_FONT.render("Alive: " + str(len(birds)),1,(255,255,255))
    win.blit(score_label, (10, 50))
    
    pygame.display.update()


def main(genomes, config):
    nets = []
    ge = []
    birds = []

    global WIN, gen
    win = WIN
    gen += 1

    for _,g in genomes:
        nets.append(neat.nn.FeedForwardNetwork.create(g, config))
        g.fitness = 0
        ge.append(g)
        birds.append(Bird(200,200))

    pipes = [Pipe(300)]
    base = Base(700)
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))
    run = True
    score = 0

    while run:
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
                run = False

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1
        else:
            run = False
            break

        for i, bird in enumerate(birds):
            bird.move()
            ge[i].fitness += 0.1

            output = nets[i].activate((bird.y, abs(bird.y - pipes[pipe_ind].height), abs(bird.y - pipes[pipe_ind].bottom)))
            

            if output[0] > 0.5:
                bird.jump()

            if bird.y + bird.img.get_height() >= 730 or bird.y + bird.img.get_height() <= 0:
                birds.pop(i)
                nets.pop(i)
                ge.pop(i)

        add_pipe = False
        rem = []
        for pipe in pipes:
            for i, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[i].fitness -= 1
                    birds.pop(i)
                    nets.pop(i)
                    ge.pop(i)

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

            if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                rem.append(pipe)
            pipe.move()

        if add_pipe:
            score += 1
            for g in ge:
                g.fitness += 5
            pipes.append(Pipe(700))

        for r in rem:
            pipes.remove(r)
            

        base.move()

        draw_window(win, birds, pipes, base, score, gen)

def run(config_path):
    config = neat.config.Config(neat.DefaultGenome, neat.DefaultReproduction, neat.DefaultSpeciesSet, neat.DefaultStagnation, config_path)

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(main,50)

if __name__ == "__main__":
    local_dir = os.path.dirname(__file__)
    config = os.path.join(local_dir, "config-feedingforward.txt")
    run(config)