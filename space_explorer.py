import pygame
import random
import math
import json
import os

# Initialize Pygame
pygame.init()

# Game Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)
CYAN = (0, 255, 255)

class Particle:
    def __init__(self, x, y, color, velocity):
        self.x = x
        self.y = y
        self.color = color
        self.velocity = velocity
        self.lifetime = 30
        self.max_lifetime = 30
    
    def update(self):
        self.x += self.velocity[0]
        self.y += self.velocity[1]
        self.lifetime -= 1
        
    def draw(self, screen):
        alpha = int(255 * (self.lifetime / self.max_lifetime))
        color_with_alpha = (*self.color, alpha)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), 3)

class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 5
        self.health = 100
        self.max_health = 100
        self.score = 0
        self.radius = 15
        self.weapon_cooldown = 0
        self.shield = 0
        self.power_level = 1
        
    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.y -= self.speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.y += self.speed
            
        # Keep player on screen
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
        
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= 1
            
    def shoot(self, bullets):
        if self.weapon_cooldown == 0:
            if self.power_level == 1:
                bullets.append(Bullet(self.x, self.y - 20, 0, -8, YELLOW))
            elif self.power_level == 2:
                bullets.append(Bullet(self.x - 10, self.y - 20, 0, -8, YELLOW))
                bullets.append(Bullet(self.x + 10, self.y - 20, 0, -8, YELLOW))
            else:  # power_level >= 3
                bullets.append(Bullet(self.x, self.y - 20, 0, -8, YELLOW))
                bullets.append(Bullet(self.x - 15, self.y - 20, -2, -8, YELLOW))
                bullets.append(Bullet(self.x + 15, self.y - 20, 2, -8, YELLOW))
            self.weapon_cooldown = 10
    
    def draw(self, screen):
        # Draw shield if active
        if self.shield > 0:
            pygame.draw.circle(screen, CYAN, (int(self.x), int(self.y)), self.radius + 5, 2)
        
        # Draw player ship
        points = [
            (self.x, self.y - self.radius),
            (self.x - self.radius, self.y + self.radius),
            (self.x, self.y + self.radius//2),
            (self.x + self.radius, self.y + self.radius)
        ]
        pygame.draw.polygon(screen, GREEN, points)
        
        # Draw health bar
        bar_width = 60
        bar_height = 8
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.radius - 15
        
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int(bar_width * (self.health / self.max_health))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))

class Enemy:
    def __init__(self, x, y, enemy_type="basic"):
        self.x = x
        self.y = y
        self.enemy_type = enemy_type
        self.speed = random.uniform(1, 3)
        self.radius = 12
        self.health = 20 if enemy_type == "basic" else 50
        self.max_health = self.health
        self.shoot_cooldown = random.randint(30, 90)
        self.color = RED if enemy_type == "basic" else PURPLE
        
    def update(self, player, enemy_bullets):
        self.y += self.speed
        
        # Simple AI to move towards player
        if self.enemy_type == "smart":
            dx = player.x - self.x
            if abs(dx) > 5:
                self.x += 1 if dx > 0 else -1
        
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0 and self.y > 50:
            if self.enemy_type == "basic":
                enemy_bullets.append(Bullet(self.x, self.y + 15, 0, 4, RED))
                self.shoot_cooldown = random.randint(60, 120)
            else:  # smart enemy
                dx = player.x - self.x
                dy = player.y - self.y
                distance = math.sqrt(dx*dx + dy*dy)
                if distance > 0:
                    vel_x = (dx / distance) * 3
                    vel_y = (dy / distance) * 3
                    enemy_bullets.append(Bullet(self.x, self.y, vel_x, vel_y, PURPLE))
                self.shoot_cooldown = random.randint(40, 80)
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)
        
        # Draw health bar for smart enemies
        if self.enemy_type == "smart":
            bar_width = 30
            bar_height = 4
            bar_x = self.x - bar_width // 2
            bar_y = self.y - self.radius - 8
            
            pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
            health_width = int(bar_width * (self.health / self.max_health))
            pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))

class Boss:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.health = 200
        self.max_health = 200
        self.radius = 40
        self.speed = 2
        self.direction = 1
        self.shoot_cooldown = 0
        self.phase = 1
        self.attack_pattern = 0
        
    def update(self, player, enemy_bullets):
        # Move side to side
        self.x += self.speed * self.direction
        if self.x <= self.radius or self.x >= SCREEN_WIDTH - self.radius:
            self.direction *= -1
            
        self.shoot_cooldown -= 1
        
        # Different attack patterns based on health
        if self.health > 150:  # Phase 1
            if self.shoot_cooldown <= 0:
                enemy_bullets.append(Bullet(self.x, self.y + 20, 0, 5, RED))
                self.shoot_cooldown = 30
        elif self.health > 75:  # Phase 2
            if self.shoot_cooldown <= 0:
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    vel_x = math.cos(rad) * 3
                    vel_y = math.sin(rad) * 3
                    enemy_bullets.append(Bullet(self.x, self.y, vel_x, vel_y, ORANGE))
                self.shoot_cooldown = 60
        else:  # Phase 3
            if self.shoot_cooldown <= 0:
                # Aimed shots at player
                for i in range(3):
                    dx = player.x - self.x + random.randint(-50, 50)
                    dy = player.y - self.y
                    distance = math.sqrt(dx*dx + dy*dy)
                    if distance > 0:
                        vel_x = (dx / distance) * 4
                        vel_y = (dy / distance) * 4
                        enemy_bullets.append(Bullet(self.x, self.y, vel_x, vel_y, PURPLE))
                self.shoot_cooldown = 40
                
    def draw(self, screen):
        # Draw boss body
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(screen, ORANGE, (int(self.x), int(self.y)), self.radius - 10)
        
        # Draw health bar
        bar_width = 100
        bar_height = 10
        bar_x = self.x - bar_width // 2
        bar_y = self.y - self.radius - 20
        
        pygame.draw.rect(screen, RED, (bar_x, bar_y, bar_width, bar_height))
        health_width = int(bar_width * (self.health / self.max_health))
        pygame.draw.rect(screen, GREEN, (bar_x, bar_y, health_width, bar_height))

class Bullet:
    def __init__(self, x, y, vel_x, vel_y, color):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.color = color
        self.radius = 3
        
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

class PowerUp:
    def __init__(self, x, y, power_type):
        self.x = x
        self.y = y
        self.power_type = power_type
        self.radius = 8
        self.speed = 2
        self.colors = {
            "health": GREEN,
            "shield": CYAN,
            "weapon": YELLOW,
            "score": WHITE
        }
        
    def update(self):
        self.y += self.speed
        
    def draw(self, screen):
        pygame.draw.circle(screen, self.colors[self.power_type], (int(self.x), int(self.y)), self.radius)
        
        # Draw power-up symbol
        if self.power_type == "health":
            pygame.draw.line(screen, WHITE, (self.x-4, self.y), (self.x+4, self.y), 2)
            pygame.draw.line(screen, WHITE, (self.x, self.y-4), (self.x, self.y+4), 2)
        elif self.power_type == "shield":
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), 4, 1)
        elif self.power_type == "weapon":
            pygame.draw.polygon(screen, WHITE, [(self.x, self.y-4), (self.x-3, self.y+2), (self.x+3, self.y+2)])

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Space Explorer - Built with Amazon Q CLI")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        self.reset_game()
        
        # Load high score
        self.high_score = self.load_high_score()
        
    def reset_game(self):
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 100)
        self.bullets = []
        self.enemies = []
        self.enemy_bullets = []
        self.powerups = []
        self.particles = []
        self.boss = None
        
        self.enemy_spawn_timer = 0
        self.powerup_spawn_timer = 0
        self.wave = 1
        self.enemies_killed = 0
        self.boss_spawned = False
        
    def load_high_score(self):
        try:
            with open("high_score.json", "r") as f:
                data = json.load(f)
                return data.get("high_score", 0)
        except FileNotFoundError:
            return 0
            
    def save_high_score(self):
        with open("high_score.json", "w") as f:
            json.dump({"high_score": self.high_score}, f)
    
    def spawn_enemy(self):
        x = random.randint(50, SCREEN_WIDTH - 50)
        enemy_type = "smart" if random.random() < 0.3 else "basic"
        self.enemies.append(Enemy(x, -20, enemy_type))
        
    def spawn_powerup(self):
        x = random.randint(50, SCREEN_WIDTH - 50)
        power_types = ["health", "shield", "weapon", "score"]
        power_type = random.choice(power_types)
        self.powerups.append(PowerUp(x, -20, power_type))
        
    def create_explosion(self, x, y, color, count=10):
        for _ in range(count):
            vel_x = random.uniform(-5, 5)
            vel_y = random.uniform(-5, 5)
            self.particles.append(Particle(x, y, color, (vel_x, vel_y)))
    
    def check_collisions(self):
        # Player bullets vs enemies
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                distance = math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)
                if distance < bullet.radius + enemy.radius:
                    self.bullets.remove(bullet)
                    enemy.health -= 10
                    self.create_explosion(enemy.x, enemy.y, enemy.color, 5)
                    if enemy.health <= 0:
                        self.enemies.remove(enemy)
                        self.enemies_killed += 1
                        self.player.score += 10 if enemy.enemy_type == "basic" else 25
                        self.create_explosion(enemy.x, enemy.y, enemy.color, 15)
                    break
                    
        # Player bullets vs boss
        if self.boss:
            for bullet in self.bullets[:]:
                distance = math.sqrt((bullet.x - self.boss.x)**2 + (bullet.y - self.boss.y)**2)
                if distance < bullet.radius + self.boss.radius:
                    self.bullets.remove(bullet)
                    self.boss.health -= 10
                    self.create_explosion(self.boss.x, self.boss.y, RED, 8)
                    if self.boss.health <= 0:
                        self.player.score += 100
                        self.create_explosion(self.boss.x, self.boss.y, RED, 30)
                        self.boss = None
                        self.boss_spawned = False
                        self.wave += 1
        
        # Enemy bullets vs player
        for bullet in self.enemy_bullets[:]:
            distance = math.sqrt((bullet.x - self.player.x)**2 + (bullet.y - self.player.y)**2)
            if distance < bullet.radius + self.player.radius:
                self.enemy_bullets.remove(bullet)
                if self.player.shield > 0:
                    self.player.shield -= 10
                else:
                    self.player.health -= 10
                self.create_explosion(self.player.x, self.player.y, RED, 5)
                
        # Enemies vs player
        for enemy in self.enemies[:]:
            distance = math.sqrt((enemy.x - self.player.x)**2 + (enemy.y - self.player.y)**2)
            if distance < enemy.radius + self.player.radius:
                self.enemies.remove(enemy)
                if self.player.shield > 0:
                    self.player.shield -= 20
                else:
                    self.player.health -= 20
                self.create_explosion(self.player.x, self.player.y, RED, 10)
                
        # Boss vs player
        if self.boss:
            distance = math.sqrt((self.boss.x - self.player.x)**2 + (self.boss.y - self.player.y)**2)
            if distance < self.boss.radius + self.player.radius:
                if self.player.shield > 0:
                    self.player.shield -= 30
                else:
                    self.player.health -= 30
                self.create_explosion(self.player.x, self.player.y, RED, 15)
        
        # PowerUps vs player
        for powerup in self.powerups[:]:
            distance = math.sqrt((powerup.x - self.player.x)**2 + (powerup.y - self.player.y)**2)
            if distance < powerup.radius + self.player.radius:
                self.powerups.remove(powerup)
                if powerup.power_type == "health":
                    self.player.health = min(self.player.max_health, self.player.health + 30)
                elif powerup.power_type == "shield":
                    self.player.shield = min(100, self.player.shield + 50)
                elif powerup.power_type == "weapon":
                    self.player.power_level = min(3, self.player.power_level + 1)
                elif powerup.power_type == "score":
                    self.player.score += 50
                self.create_explosion(powerup.x, powerup.y, powerup.colors[powerup.power_type], 8)
    
    def update(self):
        self.player.update()
        
        # Shooting
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.player.shoot(self.bullets)
            
        # Update bullets
        for bullet in self.bullets[:]:
            bullet.update()
            if bullet.y < 0 or bullet.y > SCREEN_HEIGHT:
                self.bullets.remove(bullet)
                
        for bullet in self.enemy_bullets[:]:
            bullet.update()
            if bullet.y < 0 or bullet.y > SCREEN_HEIGHT or bullet.x < 0 or bullet.x > SCREEN_WIDTH:
                self.enemy_bullets.remove(bullet)
        
        # Update enemies
        for enemy in self.enemies[:]:
            enemy.update(self.player, self.enemy_bullets)
            if enemy.y > SCREEN_HEIGHT:
                self.enemies.remove(enemy)
                
        # Update boss
        if self.boss:
            self.boss.update(self.player, self.enemy_bullets)
            
        # Update powerups
        for powerup in self.powerups[:]:
            powerup.update()
            if powerup.y > SCREEN_HEIGHT:
                self.powerups.remove(powerup)
                
        # Update particles
        for particle in self.particles[:]:
            particle.update()
            if particle.lifetime <= 0:
                self.particles.remove(particle)
        
        # Spawn enemies
        self.enemy_spawn_timer -= 1
        if self.enemy_spawn_timer <= 0 and not self.boss:
            self.spawn_enemy()
            self.enemy_spawn_timer = max(30, 120 - self.wave * 10)
            
        # Spawn powerups
        self.powerup_spawn_timer -= 1
        if self.powerup_spawn_timer <= 0:
            if random.random() < 0.3:
                self.spawn_powerup()
            self.powerup_spawn_timer = random.randint(300, 600)
            
        # Spawn boss
        if self.enemies_killed >= self.wave * 10 and not self.boss_spawned and not self.boss:
            self.boss = Boss(SCREEN_WIDTH // 2, 100)
            self.boss_spawned = True
            self.enemies.clear()  # Clear remaining enemies
        
        self.check_collisions()
        
        # Update high score
        if self.player.score > self.high_score:
            self.high_score = self.player.score
    
    def draw(self):
        self.screen.fill(BLACK)
        
        # Draw stars background
        for i in range(50):
            x = (i * 23) % SCREEN_WIDTH
            y = (i * 17 + pygame.time.get_ticks() // 50) % SCREEN_HEIGHT
            pygame.draw.circle(self.screen, WHITE, (x, y), 1)
        
        # Draw game objects
        self.player.draw(self.screen)
        
        for bullet in self.bullets:
            bullet.draw(self.screen)
            
        for bullet in self.enemy_bullets:
            bullet.draw(self.screen)
            
        for enemy in self.enemies:
            enemy.draw(self.screen)
            
        if self.boss:
            self.boss.draw(self.screen)
            
        for powerup in self.powerups:
            powerup.draw(self.screen)
            
        for particle in self.particles:
            particle.draw(self.screen)
        
        # Draw UI
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        high_score_text = self.small_font.render(f"High Score: {self.high_score}", True, WHITE)
        self.screen.blit(high_score_text, (10, 50))
        
        wave_text = self.font.render(f"Wave: {self.wave}", True, WHITE)
        self.screen.blit(wave_text, (10, 80))
        
        health_text = self.font.render(f"Health: {self.player.health}", True, WHITE)
        self.screen.blit(health_text, (SCREEN_WIDTH - 200, 10))
        
        if self.player.shield > 0:
            shield_text = self.font.render(f"Shield: {self.player.shield}", True, CYAN)
            self.screen.blit(shield_text, (SCREEN_WIDTH - 200, 50))
            
        power_text = self.small_font.render(f"Weapon Level: {self.player.power_level}", True, YELLOW)
        self.screen.blit(power_text, (SCREEN_WIDTH - 200, 90))
        
        # Draw controls
        controls = [
            "WASD/Arrow Keys: Move",
            "Space: Shoot",
            "ESC: Quit"
        ]
        for i, control in enumerate(controls):
            text = self.small_font.render(control, True, WHITE)
            self.screen.blit(text, (SCREEN_WIDTH - 200, SCREEN_HEIGHT - 80 + i * 20))
        
        pygame.display.flip()
    
    def game_over_screen(self):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(128)
        overlay.fill(BLACK)
        self.screen.blit(overlay, (0, 0))
        
        game_over_text = self.font.render("GAME OVER", True, RED)
        score_text = self.font.render(f"Final Score: {self.player.score}", True, WHITE)
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, YELLOW)
        restart_text = self.small_font.render("Press R to Restart or ESC to Quit", True, WHITE)
        
        texts = [game_over_text, score_text, high_score_text, restart_text]
        y_offset = SCREEN_HEIGHT // 2 - 100
        
        for text in texts:
            rect = text.get_rect(center=(SCREEN_WIDTH // 2, y_offset))
            self.screen.blit(text, rect)
            y_offset += 50
            
        pygame.display.flip()
    
    def run(self):
        running = True
        game_over = False
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_r and game_over:
                        self.reset_game()
                        game_over = False
            
            if not game_over:
                if self.player.health <= 0:
                    game_over = True
                    self.save_high_score()
                else:
                    self.update()
                    self.draw()
            else:
                self.game_over_screen()
            
            self.clock.tick(FPS)
        
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
