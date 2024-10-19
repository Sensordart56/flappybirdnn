import pygame
import random
import os
import neat
import pickle

pygame.font.init()
pygame.init()

WIDTH = 500
HEIGHT = 800
FLOOR = 730
GEN = 0

BIRD_IMGS = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird1.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird2.png"))),pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bird3.png")))]
PIPE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","pipe.png")))
BG_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","bg.png")))
BASE_IMG = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs","base.png")))

STAT_FONT = pygame.font.SysFont("comicsans", 50)
END_FONT = pygame.font.SysFont("comicsans", 70)
DRAW_LINES = False
win = pygame.display.set_mode((WIDTH, HEIGHT))


class Bird:
    MAX_ROTATION = 25
    IMGS = BIRD_IMGS
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
        displacement = self.vel * (self.tick_count) + 0.5 * 3 * (self.tick_count)**2

        if displacement >= 16:
            displacement = 16
        if displacement < 0:
            displacement -= 2

        self.y = self.y + displacement

        if displacement < 0 or self.y < self.height + 50:
            if self.tilt < self.MAX_ROTATION:
                self.tilt = self.MAX_ROTATION
        else:
            if self.tilt > -90:
                self.tilt -= self.ROT_VEL

    def draw(self, win):
        self.img_count += 1

        if self.img_count <= self.ANIMATION_TIME:
            self.img = self.IMGS[0]
        elif self.img_count <= self.ANIMATION_TIME*2:
            self.img = self.IMGS[1]
        elif self.img_count <= self.ANIMATION_TIME*3:
            self.img = self.IMGS[2]
        elif self.img_count <= self.ANIMATION_TIME*4:
            self.img = self.IMGS[1]
        elif self.img_count == self.ANIMATION_TIME*4 + 1:
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
    VEL = 5

    def __init__(self, x):
        self.x = x
        self.height = 0
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

        return bool(b_point or t_point)

class Base:
    VEL = 5
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

def draw_window(win, birds, pipes, base, score, gen=None):
    win.blit(BG_IMG, (0, 0))

    for pipe in pipes:
        pipe.draw(win)

    text = STAT_FONT.render("Score: " + str(score), 1, (255, 255, 255))
    win.blit(text, (WIDTH - 10 - text.get_width(), 10))

    if gen is not None:
        gen_text = STAT_FONT.render("Gen: " + str(gen), 1, (255, 255, 255))
        win.blit(gen_text, (10, 10))
        
        alive_text = STAT_FONT.render("Alive: " + str(len(birds)), 1, (255, 255, 255))
        win.blit(alive_text, (10, 50))

        if DRAW_LINES:
            try:
                pipe_ind = 0
                if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                    pipe_ind = 1
                for bird in birds:
                    pygame.draw.line(win, (255,0,0),
                                   (bird.x + bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                                   (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_TOP.get_width()/2, pipes[pipe_ind].height),
                                   5)
                    pygame.draw.line(win, (255,0,0),
                                   (bird.x + bird.img.get_width()/2, bird.y + bird.img.get_height()/2),
                                   (pipes[pipe_ind].x + pipes[pipe_ind].PIPE_BOTTOM.get_width()/2, pipes[pipe_ind].bottom),
                                   5)
            except:
                pass

    base.draw(win)
    for bird in birds:
        bird.draw(win)

    pygame.display.update()

def player_mode():
    bird = Bird(230, 350)
    base = Base(FLOOR)
    pipes = [Pipe(600)]
    
    clock = pygame.time.Clock()
    score = 0
    game_over = False
    run = True

    button_font = pygame.font.SysFont("comicsans", 40)
    menu_button = pygame.Rect(WIDTH // 4, HEIGHT // 2 + 50, WIDTH // 1.5, 50)

    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    mouse_pos = pygame.mouse.get_pos()
                    if menu_button.collidepoint(mouse_pos):
                        menu()
                        return
                else:
                    bird.jump()

        if not game_over:
            bird.move()
            add_pipe = False
            rem = []

            for pipe in pipes:
                if pipe.collide(bird):
                    game_over = True
                    break

                if not pipe.passed and pipe.x < bird.x:
                    pipe.passed = True
                    add_pipe = True

                if pipe.x + pipe.PIPE_TOP.get_width() < 0:
                    rem.append(pipe)
                pipe.move()

            if add_pipe:
                score += 1
                pipes.append(Pipe(700))

            for r in rem:
                pipes.remove(r)

            if bird.y + bird.img.get_height() >= FLOOR or bird.y < 0:
                game_over = True

            base.move()
            draw_window(win, [bird], pipes, base, score)
        else:
            pygame.draw.rect(win, (255, 255, 255), menu_button)
            menu_text = button_font.render("Return to Menu", 1, (0, 0, 0))
            win.blit(menu_text, (menu_button.centerx - menu_text.get_width() // 2,
                                 menu_button.centery - menu_text.get_height() // 2))
            pygame.display.update()

def eval_genomes(genomes, config):
    global GEN
    GEN += 1

    nets = []
    ge = []
    birds = []

    for _, g in genomes:
        net = neat.nn.FeedForwardNetwork.create(g, config)
        nets.append(net)
        birds.append(Bird(230, 350))
        g.fitness = 0
        ge.append(g)

    base = Base(FLOOR)
    pipes = [Pipe(600)]
    
    clock = pygame.time.Clock()
    score = 0

    run = True
    while run and len(birds) > 0:
        clock.tick(30)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()
                quit()

        pipe_ind = 0
        if len(birds) > 0:
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].PIPE_TOP.get_width():
                pipe_ind = 1

        for x, bird in enumerate(birds):
            bird.move()
            ge[x].fitness += 0.1

            output = nets[x].activate((
                bird.y,
                abs(bird.y - pipes[pipe_ind].height),
                abs(bird.y - pipes[pipe_ind].bottom)
            ))

            if output[0] > 0.5:
                bird.jump()

        add_pipe = False
        rem = []

        for pipe in pipes:
            for x, bird in enumerate(birds):
                if pipe.collide(bird):
                    ge[x].fitness -= 1
                    birds.pop(x)
                    nets.pop(x)
                    ge.pop(x)

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

        for x, bird in enumerate(birds):
            if bird.y + bird.img.get_height() >= FLOOR or bird.y < 0:
                birds.pop(x)
                nets.pop(x)
                ge.pop(x)

        base.move()
        draw_window(win, birds, pipes, base, score, GEN)
        if score > 20:                                              #OPTIONAL FOR IF SCORE GETS LARGE ENOUGH
            pickle.dump(nets[0],open("best.pickle", "wb"))
            break

def menu():
    pygame.init()
    clock = pygame.time.Clock()
    menu_running = True

    button_font = pygame.font.SysFont("comicsans", 40)
    ai_button = pygame.Rect(WIDTH // 4, HEIGHT // 2, WIDTH // 2, 50)
    player_button = pygame.Rect(WIDTH // 4, HEIGHT // 2 + 100, WIDTH // 2, 50)

    while menu_running:
        clock.tick(30)
        win.blit(BG_IMG, (0, 0))

        pygame.draw.rect(win, (255, 255, 255), ai_button)
        pygame.draw.rect(win, (255, 255, 255), player_button)

        ai_text = button_font.render("AI Play", 1, (0, 0, 0))
        player_text = button_font.render("Player Play", 1, (0, 0, 0))

        win.blit(ai_text, (ai_button.centerx - ai_text.get_width() // 2,
                          ai_button.centery - ai_text.get_height() // 2))
        win.blit(player_text, (player_button.centerx - player_text.get_width() // 2,
                              player_button.centery - player_text.get_height() // 2))

        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                menu_running = False
                pygame.quit()
                quit()
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = pygame.mouse.get_pos()
                if ai_button.collidepoint(mouse_pos):
                    local_dir = os.path.dirname(__file__)
                    config_path = os.path.join(local_dir, "config-feedforward.txt")
                    menu_running = False
                    run(config_path)
                elif player_button.collidepoint(mouse_pos):
                    menu_running = False
                    player_mode()

def run(config_file):

    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(eval_genomes, 50)

    print(f"Best genome:\n{winner}")

if __name__ == "__main__":
    menu()



def run(config_file):
    config = neat.config.Config(
        neat.DefaultGenome,
        neat.DefaultReproduction,
        neat.DefaultSpeciesSet,
        neat.DefaultStagnation,
        config_file
    )

    population = neat.Population(config)

    population.add_reporter(neat.StdOutReporter(True))
    stats = neat.StatisticsReporter()
    population.add_reporter(stats)

    winner = population.run(eval_genomes, 50)

    print(f"Best genome:\n{winner}")




