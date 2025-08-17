import pgzrun
from pgzero.actor import Actor
import math
import random

# configuração da tela
WIDTH = 800         # largura da tela
HEIGHT = 600        # altura da tela

# estado inicial do jogo (menu, jogando, derrota, vitória)
GAME_STATE_MENU = "menu"
GAME_STATE_PLAYING = "playing"
GAME_STATE_GAMEOVER = "game_over"
GAME_STATE_VICTORY = "victory"
game_state = GAME_STATE_MENU    #começa no menu

music_on = True  # controla de música on/off
game_over_sound_played = False  # para não repetir o som de derrota
victory_sound_played = False    # para não repetir o som de vitória

# criando os frame da princesa
HERO_IDLE_FRAMES = ["princess_idle_00", "princess_idle_01", "princess_idle_02"]
HERO_WALK_FRAMES = ["princess_walk_00", "princess_walk_01", "princess_walk_02", "princess_walk_03"]

# frame do inimigo(usado para andar e parado)
ENEMY_WALK_FRAMES = ["enemy_walk_00", "enemy_walk_01"]

# Menu buttons
start_button = Actor("start_button", (WIDTH // 2, 500))
music_button = Actor("music_button", (WIDTH // 2, 535))
exit_button = Actor("exit_button", (WIDTH // 2, 570))

# objetos de cenário
home = Actor("home", (650, 430))
tree = Actor("tree", (100, 550))
tree1 = Actor("tree_1", (600, 100))
tree2 = Actor("tree_2", (400, 300))
plant1 = Actor("plant_1", (390, 100))
plant2 = Actor("plant_2", (200, 450))
plant3 = Actor("plant_3", (100, 200))

# as classes
class SpriteAnimator:
    # controla animação (parado ou atacando) de qualquer pessonagem
    def __init__(self, actor: Actor, idle_frames, walk_frames, idle_rate=12, walk_rate=8):
        self.actor = actor
        self.idle_frames = idle_frames
        self.walk_frames = walk_frames
        self.idle_rate = idle_rate
        self.walk_rate = walk_rate
        self._timer = 0 # contador frame
        self._index = 0 # indice atual do frame
        self._state = "idle"    #estado inicial que é parado
        if self.idle_frames:
            self.actor.image = self.idle_frames[0]

    def set_state(self, state: str):
        # troca de idle para walk
        if state != self._state:
            self._state = state
            self._timer = 0
            self._index = 0

    def update_animation(self):
        # atualiza frames da amimação
        frames = self.idle_frames if self._state == "idle" else self.walk_frames
        if not frames:
            return
        rate = self.idle_rate if self._state == "idle" else self.walk_rate
        self._timer += 1
        if self._timer >= rate:
            self._timer = 0
            self._index = (self._index + 1) % len(frames)
            self.actor.image = frames[self._index]

class Hero:
    # classe do jogador controla movimento e animação
    def __init__(self, pos=(64, 64), speed=3.0):
        self.actor = Actor(HERO_IDLE_FRAMES[0], pos=pos)
        self.speed = speed
        self.anim = SpriteAnimator(self.actor, HERO_IDLE_FRAMES, HERO_WALK_FRAMES, idle_rate=15, walk_rate=7)

    def update(self):
        self._move_with_keyboard()
        self.anim.update_animation()

    def _move_with_keyboard(self):
        # limita a saida do personagem da tela e movimenta o personagem usando a seta do teclado
        vx, vy = 0, 0
        if keyboard.left: vx -= 1
        if keyboard.right: vx += 1
        if keyboard.up: vy -= 1
        if keyboard.down: vy += 1

        # movimento diagonal e velocidade constante
        moving = (vx != 0 or vy != 0)
        if moving:
            length = math.hypot(vx, vy)
            if length > 0:
                vx /= length
                vy /= length
                self.actor.x += vx * self.speed
                self.actor.y += vy * self.speed

            # mantém o herói dentro da tela
            self.actor.x = max(self.actor.width // 2, min(WIDTH - self.actor.width // 2, self.actor.x))
            self.actor.y = max(self.actor.height // 2, min(HEIGHT - self.actor.height // 2, self.actor.y))

        self.anim.set_state("walk" if moving else "idle")

    def draw(self):
        self.actor.draw()

class Enemy:

    # classe dos inimigo. cada inimigo patrulha um território e perseguem o jogador
    def __init__(self, pos, territory, speed=1.2):
        self.territory = territory # área patrulhada
        self.actor = Actor(ENEMY_WALK_FRAMES[0], pos=pos)
        self.speed = speed
        self.anim = SpriteAnimator(self.actor, idle_frames=ENEMY_WALK_FRAMES, walk_frames=ENEMY_WALK_FRAMES, idle_rate=18, walk_rate=10)
        self._target = self._random_point_in_territory()
        self.sound_played = False

    def _random_point_in_territory(self):
        # random escolhe um ponto aleatório dentro do território do inimigo
        x1, y1, x2, y2 = self.territory
        return (random.randint(x1, x2), random.randint(y1, y2))

    def _point_in_territory(self, p):
        #verifica ponto está no território do inimigo
        x, y = p
        x1, y1, x2, y2 = self.territory
        return x1 <= x <= x2 and y1 <= y <= y2

    def _move_towards(self, tx, ty):
        # move em direção ao ponto alvo
        dx, dy = tx - self.actor.x, ty - self.actor.y
        dist = math.hypot(dx, dy)
        if dist < 0.5:
            return False
        self.actor.x += (dx / dist) * self.speed
        self.actor.y += (dy / dist) * self.speed
        return True

    def update(self, hero_pos):
        # atualizar a patrulha ou a perseguição do jogador
        chasing_hero = self._point_in_territory(hero_pos)
        if chasing_hero:
            moving = self._move_towards(hero_pos[0], hero_pos[1])
            self.anim.set_state("walk" if moving else "idle")
            if not self.sound_played:
                try: sounds.monster.play()
                except Exception: pass
                self.sound_played = True
        else:
            if not self._move_towards(self._target[0], self._target[1]):
                self._target = self._random_point_in_territory()
            self.anim.set_state("walk")
            self.sound_played = False
        self.anim.update_animation()

    def draw(self):
        self.actor.draw()

# objeto do jogo

hero = Hero(pos=(80, 80), speed=3.2)

# localização das áreas de patrulha dos inimigos
enemy_quadrants = [
    (50, 50, 250, 250),
    (300, 50, 500, 250),
    (550, 50, 750, 250),
    (50, 300, 250, 550),
    (300, 300, 500, 550),
    (550, 300, 750, 550),
]

# cria inimigos em posição aleatórias dentro de seus territórios
enemies = [
    Enemy(pos=(random.randint(q[0], q[2]), random.randint(q[1], q[3])), territory=q, speed=1.0 + random.random()*0.5)
    for q in enemy_quadrants
]

# funções do jogo
def start_game():
    # reinicia o fogo e o jogador e inimigos valtam a posições iniciais

    global game_state, hero, enemies, game_over_sound_played, victory_sound_played

    hero.actor.pos = (80, 80)

    # reseta inimigos
    for idx, q in enumerate(enemy_quadrants):
        enemies[idx].actor.pos = (random.randint(q[0], q[2]), random.randint(q[1], q[3]))
        enemies[idx]._target = enemies[idx]._random_point_in_territory()
        enemies[idx].sound_played = False

    game_over_sound_played = False
    victory_sound_played = False
    game_state = GAME_STATE_PLAYING

    # Para música antiga
    music.stop()

    # Toca música de batalha
    if music_on:
        music.play("battle")

# loop principal
def draw():
    # desenha todos os elementos na tela
    screen.clear()
    screen.fill("forestgreen")

    # cenário
    tree.draw(); tree1.draw(); tree2.draw()
    plant1.draw(); plant2.draw(); plant3.draw()
    home.draw()
    # personagem
    hero.draw()
    for e in enemies: e.draw()

    # os botões sempre visíveis
    start_button.draw()
    music_button.draw()
    exit_button.draw()

    # mensagem quando o jogar perde
    if game_state == GAME_STATE_GAMEOVER:
        screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2), fontsize=60, color="red")
        screen.draw.text("Clique em Start para reiniciar", center=(WIDTH//2, HEIGHT//2 + 80), fontsize=30, color="white")

    # mensagem quando o jogador ganha
    if game_state == GAME_STATE_VICTORY:
        screen.draw.text("VOCÊ VENCEU!", center=(WIDTH//2, HEIGHT//2), fontsize=60, color="yellow")
        screen.draw.text("Clique em Start para jogar novamente", center=(WIDTH//2, HEIGHT//2 + 80), fontsize=30, color="white")

def update():
    # atualização da lógica do jogo
    global game_state, game_over_sound_played, victory_sound_played

    if game_state != GAME_STATE_PLAYING:
        return

    hero.update()
    hero_pos = (hero.actor.x, hero.actor.y)

    # Vitória se herói chegar ao castelo (home)
    if hero.actor.colliderect(home):
        game_state = GAME_STATE_VICTORY
        music.stop()  # para música de batalha
        if not victory_sound_played:
            try: sounds.victory.play()
            except Exception: pass
            victory_sound_played = True
        return

    # derrota quando colide com o inimigo
    for e in enemies:
        e.update(hero_pos)
        if hero.actor.colliderect(e.actor):
            game_state = GAME_STATE_GAMEOVER
            music.stop()  # para música de batalha
            if not game_over_sound_played:
                try: sounds.game_over.play()
                except Exception: pass
                game_over_sound_played = True

def on_mouse_down(pos):
    # função dos cliques dos botões do menu
    global music_on
    if start_button.collidepoint(pos):
        start_game()
    elif music_button.collidepoint(pos):
        music_on = not music_on
        if music_on:
            music.play("battle")
        else:
            music.stop()
    elif exit_button.collidepoint(pos):
        exit()

pgzrun.go()
