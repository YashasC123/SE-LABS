import array
import math

import pygame
from .paddle import Paddle
from .ball import Ball
from .brick import Brick

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)
BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]
DIFFICULTY_SETTINGS = {
    "Easy": {"ball_speed": 3, "paddle_width": 120},
    "Medium": {"ball_speed": 4, "paddle_width": 100},
    "Hard": {"ball_speed": 6, "paddle_width": 80},
}
DIFFICULTY_KEYS = {
    pygame.K_1: "Easy",
    pygame.K_2: "Medium",
    pygame.K_3: "Hard",
    pygame.K_KP1: "Easy",
    pygame.K_KP2: "Medium",
    pygame.K_KP3: "Hard",
}

class GameEngine:
    def __init__(self, width, height, difficulty="Medium"):
        self.width = width
        self.height = height

        self.rows, self.cols = 5, 8
        self.font = pygame.font.SysFont("Arial", 28)
        self.end_title_font = pygame.font.SysFont("Arial", 56, bold=True)
        self.end_score_font = pygame.font.SysFont("Arial", 36)
        self.end_prompt_font = pygame.font.SysFont("Arial", 20)

        self.sounds = {}
        self._initialize_sounds()
        self._start_new_game(difficulty)

    def _initialize_sounds(self):
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sounds = {
                "brick": self._make_tone((980,), 0.07),
                "paddle": self._make_tone((520,), 0.09),
                "wall": self._make_tone((720,), 0.055),
                "win": self._make_tone((660, 880, 1100), 0.1),
                "lose": self._make_tone((440, 330, 220), 0.12),
            }
        except (pygame.error, OSError):
            self.sounds = {}

    def _make_tone(self, notes, note_duration):
        sample_rate, sample_format, channels = pygame.mixer.get_init()
        if sample_format != -16:
            raise pygame.error("Generated sounds require signed 16-bit mixer audio")

        samples = array.array("h")
        note_samples = int(sample_rate * note_duration)
        fade_samples = max(1, int(sample_rate * 0.008))
        for frequency in notes:
            for index in range(note_samples):
                envelope = min(1.0, index / fade_samples, (note_samples - index - 1) / fade_samples)
                value = int(32767 * 0.22 * envelope * math.sin(2 * math.pi * frequency * index / sample_rate))
                samples.extend([value] * channels)
        return pygame.mixer.Sound(buffer=samples.tobytes())

    def _play_sound(self, name):
        sound = self.sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def _start_new_game(self, difficulty):
        settings = DIFFICULTY_SETTINGS[difficulty]
        self.difficulty = difficulty
        self.ball_speed = settings["ball_speed"]
        paddle_width = settings["paddle_width"]
        self.paddle = Paddle(
            self.width // 2 - paddle_width // 2,
            self.height - 30,
            paddle_width,
            14,
        )
        self.ball = Ball(self.width // 2, self.height - 50, radius=8)
        self.ball.vx, self.ball.vy = self.ball_speed, -self.ball_speed
        self.bricks = self._build_bricks(self.rows, self.cols)
        self.lives = 3
        self.score = 0
        self.game_over = False
        self.result = None

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (self.width - margin * 2 - gap * (cols - 1)) // cols
        brick_h = 22
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))
        return bricks

    def handle_event(self, event):
        if not self.game_over or event.type != pygame.KEYDOWN:
            return

        difficulty = DIFFICULTY_KEYS.get(event.key)
        if difficulty is not None:
            self._start_new_game(difficulty)

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def update(self):
        if self.game_over:
            return

        previous_x, previous_y = self.ball.x, self.ball.y
        self.ball.move()

        wall_hit = False
        if self.ball.x - self.ball.radius <= 0 or self.ball.x + self.ball.radius >= self.width:
            self.ball.vx *= -1
            wall_hit = True
        if self.ball.y - self.ball.radius <= 0:
            self.ball.vy *= -1
            wall_hit = True
        if wall_hit:
            self._play_sound("wall")

        paddle_rect = self.paddle.rect()
        if self.ball.rect().colliderect(paddle_rect):
            self._resolve_collision(paddle_rect, previous_x, previous_y, paddle=True)
            self._play_sound("paddle")

        for brick in self.bricks:
            brick_rect = brick.rect()
            if brick.alive and self.ball.rect().colliderect(brick_rect):
                brick.alive = False
                self.score += 1
                self._resolve_collision(brick_rect, previous_x, previous_y)
                self._play_sound("brick")
                break

        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"
                self._play_sound("lose")
            else:
                self._reset_ball()

        if not self.game_over and all(not b.alive for b in self.bricks):
            self.game_over = True
            self.result = "win"
            self._play_sound("win")

    def _resolve_collision(self, target_rect, previous_x, previous_y, paddle=False):
        ball = self.ball
        radius = ball.radius

        if paddle:
            ball.y = target_rect.top - radius
            ball.vy = -abs(ball.vy)
            return

        previous_left = previous_x - radius
        previous_right = previous_x + radius
        previous_top = previous_y - radius
        previous_bottom = previous_y + radius

        if previous_bottom <= target_rect.top and ball.vy > 0:
            ball.y = target_rect.top - radius
            ball.vy = -abs(ball.vy)
        elif previous_top >= target_rect.bottom and ball.vy < 0:
            ball.y = target_rect.bottom + radius
            ball.vy = abs(ball.vy)
        elif previous_right <= target_rect.left and ball.vx > 0:
            ball.x = target_rect.left - radius
            ball.vx = -abs(ball.vx)
        elif previous_left >= target_rect.right and ball.vx < 0:
            ball.x = target_rect.right + radius
            ball.vx = abs(ball.vx)
        else:
            overlap_x = min(ball.x + radius - target_rect.left, target_rect.right - (ball.x - radius))
            overlap_y = min(ball.y + radius - target_rect.top, target_rect.bottom - (ball.y - radius))
            if overlap_x < overlap_y:
                if previous_x <= target_rect.centerx:
                    ball.x = target_rect.left - radius
                    ball.vx = -abs(ball.vx)
                else:
                    ball.x = target_rect.right + radius
                    ball.vx = abs(ball.vx)
            elif previous_y <= target_rect.centery:
                ball.y = target_rect.top - radius
                ball.vy = -abs(ball.vy)
            else:
                ball.y = target_rect.bottom + radius
                ball.vy = abs(ball.vy)

    def _reset_ball(self):
        self.ball.x, self.ball.y = self.width // 2, self.height - 50
        self.ball.vx, self.ball.vy = self.ball_speed, -self.ball_speed

    def render(self, screen):
        screen.fill(BG)

        if self.game_over:
            if self.result == "win":
                title, color = "YOU WIN!", (120, 220, 140)
            else:
                title, color = "GAME OVER", (230, 110, 110)

            title_text = self.end_title_font.render(title, True, color)
            score_text = self.end_score_font.render(f"Final Score: {self.score}", True, WHITE)
            easy_text = self.end_prompt_font.render(
                "1  Easy: slower ball, wider paddle", True, WHITE
            )
            medium_text = self.end_prompt_font.render(
                "2  Medium: normal ball and paddle", True, WHITE
            )
            hard_text = self.end_prompt_font.render(
                "3  Hard: faster ball, narrower paddle", True, WHITE
            )
            prompt_text = self.end_prompt_font.render(
                "Choose a difficulty to replay | Escape to quit", True, WHITE
            )
            screen.blit(title_text, title_text.get_rect(center=(self.width // 2, self.height // 2 - 70)))
            screen.blit(score_text, score_text.get_rect(center=(self.width // 2, self.height // 2)))
            screen.blit(easy_text, easy_text.get_rect(center=(self.width // 2, self.height // 2 + 48)))
            screen.blit(medium_text, medium_text.get_rect(center=(self.width // 2, self.height // 2 + 78)))
            screen.blit(hard_text, hard_text.get_rect(center=(self.width // 2, self.height // 2 + 108)))
            screen.blit(prompt_text, prompt_text.get_rect(center=(self.width // 2, self.height // 2 + 158)))
            return

        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))
