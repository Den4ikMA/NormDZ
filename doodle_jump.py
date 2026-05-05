import pygame
import random
import sys

pygame.init()

SCREEN_WIDTH = 400
SCREEN_HEIGHT = 800
FPS = 60
JUMP_RANGE = 220
TARGET_PLATFORMS = 8

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GRAY = (128, 128, 128)
YELLOW = (255, 255, 0)
ORANGE = (255, 165, 0)
BROWN = (139, 69, 19)   
PURPLE = (128, 0, 128)  


class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.image.fill(BLUE)
        pygame.draw.circle(self.image, WHITE, (15, 15), 13)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 100
        self.shoot_cooldown = 0
        self.jetpack_active = False
        self.jetpack_timer = 0
        self.shield_active = False
        self.shield_timer = 0
        
        self.vel_y = 0
        self.jump_power = -11
        self.gravity = 0.5
        self.speed_x = 0
        self.move_speed = 3

    def update(self, platforms, bullets):
        keys = pygame.key.get_pressed()
        self.speed_x = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.speed_x = -self.move_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.speed_x = self.move_speed
        if keys[pygame.K_SPACE] and self.shoot_cooldown == 0:
            bullet = Bullet(self.rect.centerx, self.rect.top - 5)
            bullets.add(bullet)
            self.shoot_cooldown = 8
   
        self.rect.x += self.speed_x
        if self.rect.right < 0:
            self.rect.left = SCREEN_WIDTH
        elif self.rect.left > SCREEN_WIDTH:
            self.rect.right = 0
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
   
        self.vel_y += self.gravity
  
        if self.jetpack_active:
            self.vel_y = -15  
            self.jetpack_timer -= 1
            if self.jetpack_timer <= 0:
                self.jetpack_active = False
                self.vel_y = 0

        if self.shield_active:
            self.shield_timer -= 1
            if self.shield_timer <= 0:
                self.shield_active = False

        for platform in platforms:
            if (self.rect.colliderect(platform.rect) and 
                self.vel_y > 0 and
                self.rect.bottom >= platform.rect.top): 
        
                self.rect.bottom = platform.rect.top
                self.vel_y = getattr(platform, 'jump_power', self.jump_power)
        
                if platform.type == "breakable":
                    platform.kill()
                break
 
        self.rect.y += self.vel_y

class Platform(pygame.sprite.Sprite):
    def __init__(self, x, y, platform_type="static"):
        super().__init__()
        self.type = platform_type
        self.rect = pygame.Rect(x, y, 60, 15)
        
        if platform_type == "static":
            self.color = GREEN
        elif platform_type == "moving":
            self.color = YELLOW
            self.direction = random.choice([-1, 1])
            self.speed = random.uniform(1, 2)
        elif platform_type == "disappearing":
            self.color = GRAY
            self.timer = 180
        elif platform_type == "spring":
            self.color = RED
            self.jump_power = -24
        elif platform_type == "breakable":  # новый тип платформ
            self.color = BLUE
        else:
            self.color = GREEN

    def update(self, camera_y):
        if self.type == "moving":
            self.rect.x += self.direction * self.speed
            if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
                self.direction *= -1
                
        if self.type == "disappearing":
            self.timer -= 1
            if self.timer <= 0:
                self.kill()
        
        if self.rect.top > camera_y + SCREEN_HEIGHT + 200:
            self.kill()
            
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((5, 10))
        self.image.fill(BLACK)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = -12  
        self.distance = 0
        self.max_distance = 200

    def update(self, camera_y):
        self.rect.y += self.speed_y 
        self.distance += abs(self.speed_y)
    
        if (self.distance > 500 or 
            self.rect.top > 0 + 1000):  
            self.kill()

class Enemy(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((25, 25))
        self.image.fill(RED)
        pygame.draw.circle(self.image, (200, 50, 50), (12, 12), 11)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = 2
        self.speed_x = 0.5  
        self.direction = random.choice([-1, 1])  

    def update(self, camera_y): 
        self.rect.x += self.direction * self.speed_x
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.direction *= -1
        if self.rect.top > camera_y + SCREEN_HEIGHT + 100:
            self.kill()

class Powerup(pygame.sprite.Sprite):
    def __init__(self, x, y, p_type):
        super().__init__()
        self.type = p_type
        self.image = pygame.Surface((30, 30))
        points = [(15, 5), (5, 25), (25, 25)]  
        if p_type == "jetpack":
            self.image.fill(BROWN)
        else:  
            self.image.fill(PURPLE)
        pygame.draw.polygon(self.image, (255,255,255), points)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed_y = 1.5  

    def update(self, camera_y):
        self.rect.y += self.speed_y
        if self.rect.top > camera_y + SCREEN_HEIGHT + 100:
            self.kill()


def spawn_platform(platforms, player, camera_y, enemies, powerups):
    safe_y = player.rect.y - random.randint(100, JUMP_RANGE)
    safe_x = random.randint(20, SCREEN_WIDTH - 80)
    
    new_rect = pygame.Rect(safe_x, safe_y, 60, 15)
    too_close = False
    
    for plat in platforms:
        if new_rect.colliderect(plat.rect):
            too_close = True
            break
        if abs(safe_x + 30 - plat.rect.centerx) < 70 and abs(safe_y - plat.rect.centery) < 50:
            too_close = True
            break
    
    if not too_close:
        if random.random() < 0.5:  
            plat_type = "static"
        elif random.random() < 0.5:
            plat_type = random.choice(["spring", "moving", "disappearing", "breakable"]) #новый тип платформ
        else:
            plat_type = "static"  
    
        plat = Platform(safe_x, safe_y, plat_type)
        platforms.add(plat)
        
        if random.random() < 0.1:
            enemy_x = safe_x + random.randint(-30, 30)
            enemy_y = safe_y - random.randint(50, 100)
            enemy = Enemy(enemy_x, enemy_y)
            enemies.add(enemy)
        
        if random.random() < 0.01:
            px = safe_x + random.randint(-20, 20)
            py = safe_y - random.randint(30, 60)
            p_type = random.choice(["jetpack", "shield"])
            powerup = Powerup(px, py, p_type)
            powerups.add(powerup)

    return True

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Doodle Jump - МЕЖЕ ПЛАТФОРМ")
    clock = pygame.time.Clock()
    
    all_sprites = pygame.sprite.Group()
    platforms = pygame.sprite.Group()
    
    bullets = pygame.sprite.Group()
    all_sprites.add(bullets)

    enemies = pygame.sprite.Group()

    powerups = pygame.sprite.Group()

    player = Player()
    all_sprites.add(player)
    
    start_platform = Platform(player.rect.centerx - 30, player.rect.bottom + 5, "static")
    platforms.add(start_platform)
    all_sprites.add(start_platform)
    
    player.rect.bottom = start_platform.rect.top
    player.vel_y = 0
    
    
    for i in range(8):
        y_pos = player.rect.top - 40 - i * 60  
        x_pos = 40 + (i * 40) % (SCREEN_WIDTH - 100)
        plat_type = "static" if random.random() < 0.9 else "moving"
        plat = Platform(x_pos, y_pos, plat_type)
        platforms.add(plat)
        all_sprites.add(plat)
    
    font = pygame.font.Font(None, 36)
    score = 0
    game_over = False
    camera_y = 0
    
    running = True
    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE and not game_over:
                    pass
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and game_over:
                    player.rect.centerx = SCREEN_WIDTH // 2
                    player.rect.bottom = SCREEN_HEIGHT - 100
                    player.vel_y = 0
                    camera_y = 0
                    score = 0
                    platforms.empty()
                    bullets.empty()
                    enemies.empty()
                    all_sprites.empty()
                    all_sprites.add(player)
                    
                    start_platform = Platform(player.rect.centerx - 30, player.rect.bottom + 5, "static")
                    platforms.add(start_platform)
                    all_sprites.add(start_platform)
                    player.rect.bottom = start_platform.rect.top
                    player.vel_y = 0
                    
                    for i in range(8):  
                        y_pos = player.rect.top - 40 - i * 60
                        x_pos = 40 + (i * 40) % (SCREEN_WIDTH - 100)
                        plat_type = "static" if random.random() < 0.9 else "moving"
                        plat = Platform(x_pos, y_pos, plat_type)
                        platforms.add(plat)
                        all_sprites.add(plat)
                    game_over = False
        
        if not game_over:
            for plat in platforms:
                plat.update(camera_y)
            for bullet in bullets:
                bullet.update(camera_y)

            
            player.update(platforms.sprites(), bullets)
            
            for bullet in bullets:
                hit_enemies = pygame.sprite.spritecollide(bullet, enemies, True)  # True = kill enemy
                if hit_enemies:
                    bullet.kill()  
            powerup_hits = pygame.sprite.spritecollide(player, powerups, True)

            for powerup in powerup_hits:
                if powerup.type == "jetpack":
                    player.jetpack_active = True
                    player.jetpack_timer = 180
                    player.vel_y = -15
                elif powerup.type == "shield":
                    player.shield_active = True
                    player.shield_timer = 300  

            if player.shield_active:
                shield_hits = pygame.sprite.spritecollide(player, enemies, True)
                if shield_hits:
                    player.shield_active = False
                    player.shield_timer = 0

            if not (player.shield_active or player.jetpack_active):
                if pygame.sprite.spritecollide(player, enemies, False):
                    game_over = True

            target_camera_y = player.rect.centery - SCREEN_HEIGHT // 3
            camera_y += (target_camera_y - camera_y) * 0.2
            score = max(score, int(-player.rect.y / 10))
            
            
            platforms_ahead = [p for p in platforms if p.rect.top < player.rect.top - 100]
            
            if len(platforms_ahead) < 2 or len(platforms) < TARGET_PLATFORMS: 
                if spawn_platform(platforms, player, camera_y, enemies, powerups):
                    pass
            
            if player.rect.top > camera_y + SCREEN_HEIGHT:
                game_over = True
        
        screen.fill(WHITE)
        
        for plat in platforms:
            screen_y = plat.rect.y - camera_y
            if -100 < screen_y < SCREEN_HEIGHT + 100:
                pygame.draw.rect(screen, plat.color,
                               (plat.rect.x, screen_y, plat.rect.width, plat.rect.height))
        for bullet in bullets:
            screen_y = bullet.rect.y - camera_y
            if -50 < screen_y < SCREEN_HEIGHT:
                screen.blit(bullet.image, (bullet.rect.x, screen_y))
        for enemy in enemies:
            enemy.update(camera_y)
        for enemy in enemies:
            screen_y = enemy.rect.y - camera_y
            if -50 < screen_y < SCREEN_HEIGHT:
                screen.blit(enemy.image, (enemy.rect.x, screen_y))
        for powerup in powerups:
            powerup.update(camera_y)
        for powerup in powerups:
            screen_y = powerup.rect.y - camera_y
            if -50 < screen_y < SCREEN_HEIGHT:
                screen.blit(powerup.image, (powerup.rect.x, screen_y))
        
        if pygame.sprite.spritecollide(player, enemies, False):
            if not (player.shield_active or player.jetpack_active):
                game_over = True
            else:
                if player.shield_active:
                    player.shield_active = False  
                
        
        player_screen_y = player.rect.y - camera_y
        if player.shield_active:
            pygame.draw.rect(screen, PURPLE, (player.rect.x-3, player_screen_y-3, 36, 36), 3)  # Контур
        screen.blit(player.image, (player.rect.x, player_screen_y))

        score_text = font.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        if game_over:
            game_over_text = font.render("GAME OVER! R to restart", True, RED)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            screen.blit(game_over_text, text_rect)
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
