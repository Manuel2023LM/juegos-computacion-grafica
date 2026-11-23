"""Juego de Pong para dos jugadores, con recursos organizados en ``assets``."""

from __future__ import annotations

import math
import random
from pathlib import Path

import pygame


# Tamaño lógico del juego; la ventana completa se escala a partir de estas medidas.
WIDTH = 1100
HEIGHT = 615
FPS = 60
WIN_SCORE = 5
MATCH_INTRO_SECONDS = 2.5
PADDLE_SPEED = 470
BALL_RADIUS = 13
COLLISION_FLASH_SECONDS = 0.22
COURT_TOP = 67
COURT_BOTTOM = 548

# Mantiene las rutas de imágenes y audio separadas del código fuente.
PROJECT_DIR = Path(__file__).resolve().parent
ASSET_DIR = PROJECT_DIR / "assets"
IMAGE_DIR = ASSET_DIR / "images"
SOUND_DIR = ASSET_DIR / "audio"

MENU_IMAGE = "Gemini_Generated_Image_tshh6tshh6tshh6t.jpg"
COURT_IMAGE = "Gemini_Generated_Image_n0stypn0stypn0st.jpg"
# Cada nombre corresponde a un archivo dentro de assets/images.
BLUE_PADDLE_IMAGE = "jugador 2.png"
RED_PADDLE_IMAGE = "sprite-1-8 (2).png"
BALL_IMAGE = "sprite-1-4 (4).png"
BLUE_HIT_IMAGE = "sprite-1-2 (2).png"
RED_HIT_IMAGE = "sprite-1-18.png"
BALL_HIT_IMAGE = "sprite-1-9 (3).png"
# Las pistas largas se reproducen en bucle y los efectos cortos con Sound.
MUSIC_TRACKS = {
    "menu": SOUND_DIR / "tron_menu.ogg",
    "game": SOUND_DIR / "partida_daft_punk.ogg",
}

# Colores usados en textos, botones y estados de colisión.
WHITE = (244, 249, 255)
CYAN = (41, 211, 255)
RED = (255, 74, 81)


def clamp_paddle_y(y: float, half_height: float) -> float:
    """Mantiene una paleta dentro de los bordes verticales de la cancha.

    ``y`` es el centro actual de la paleta y ``half_height`` su semialtura.
    Devuelve el centro ajustado para que ninguno de sus extremos salga de juego.
    """
    return max(COURT_TOP + half_height, min(COURT_BOTTOM - half_height, y))


def scaled_rect(rect: tuple[int, int, int, int]) -> pygame.Rect:
    """Convierte una región del arte original a coordenadas de la ventana.

    ``rect`` contiene x, y, ancho y alto medidos sobre la imagen de menú
    de 1376x768 píxeles. El resultado se escala al lienzo lógico del juego.
    """
    scale_x = WIDTH / 1376
    scale_y = HEIGHT / 768
    x, y, width, height = rect
    return pygame.Rect(round(x * scale_x), round(y * scale_y),
                       round(width * scale_x), round(height * scale_y))


class PongGame:
    """Carga los recursos y administra estados, controles, física y dibujo."""

    def __init__(self) -> None:
        """Prepara todos los recursos y datos que el juego necesita.

        Separa la pantalla lógica del monitor para poder redimensionar y usar
        pantalla completa sin cambiar las coordenadas internas de la partida.
        Después carga imágenes, efectos, botones, marcador y estado del menú.
        """
        self.windowed_size = (WIDTH, HEIGHT)
        self.fullscreen = False
        self.display = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        self.screen = pygame.Surface((WIDTH, HEIGHT))
        pygame.display.set_caption("PONG — TRON LEGACY")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 42)
        self.small_font = pygame.font.Font(None, 28)
        self.large_font = pygame.font.Font(None, 72)

        # Carga las imágenes originales y crea superficies a escala para dibujarlas.
        self.menu_background = self._load_image(MENU_IMAGE, (WIDTH, HEIGHT))
        self.court_background = self._load_image(COURT_IMAGE, (WIDTH, HEIGHT))
        self.instructions_image = self._load_image("instrucciones_pong.png", (855, 570))
        self.blue_paddle = self._load_image(BLUE_PADDLE_IMAGE, (38, 108))
        self.red_paddle = self._load_image(RED_PADDLE_IMAGE, (38, 108))
        self.ball_image = self._load_image(BALL_IMAGE, (38, 38))
        self.blue_hit_image = self._load_image(BLUE_HIT_IMAGE, (58, 122))
        self.red_hit_image = self._load_image(RED_HIT_IMAGE, (58, 122))
        self.ball_hit_image = self._load_image(BALL_HIT_IMAGE, (68, 78))

        # Los sonidos cortos se leen como efectos; las canciones se cargan al cambiar de estado.
        self.hit_sound = pygame.mixer.Sound(str(SOUND_DIR / "pong_hit.wav"))
        self.hit_sound.set_volume(0.7)
        self.goal_sound = pygame.mixer.Sound(str(SOUND_DIR / "gol.wav"))
        self.goal_sound.set_volume(0.8)

        # Los rectángulos de menú coinciden con los botones ilustrados en la imagen de fondo.
        self.menu_buttons = (
            scaled_rect((455, 278, 455, 86)),
            scaled_rect((455, 385, 455, 86)),
            scaled_rect((455, 489, 455, 86)),
        )
        self.pause_button = pygame.Rect(WIDTH - 112, 17, 96, 42)
        self.fullscreen_button = pygame.Rect(WIDTH - 260, 235, 244, 36)
        self.pause_options = (
            (pygame.Rect(390, 288, 320, 56), "CONTINUAR"),
            (pygame.Rect(390, 360, 320, 56), "INSTRUCCIONES"),
            (pygame.Rect(390, 432, 320, 56), "MENU PRINCIPAL"),
        )
        self.instructions_back_button = pygame.Rect(12, 20, 104, 38)
        # Estado de partida y temporizadores de efectos visuales.
        self.state = "menu"
        self.instructions_return_state = "menu"
        self.music_track: str | None = None
        self.left_score = 0
        self.right_score = 0
        self.left_y = HEIGHT / 2
        self.right_y = HEIGHT / 2
        self.ball_x = WIDTH / 2
        self.ball_y = HEIGHT / 2
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.serve_direction = 1
        self.serve_at = 0.0
        self.winner = ""
        self.return_to_menu_at = 0.0
        self.match_intro_until = 0.0
        self.left_flash_until = 0.0
        self.right_flash_until = 0.0
        self.ball_flash_until = 0.0
        self._play_music("menu")

    @staticmethod
    def _load_image(filename: str, size: tuple[int, int]) -> pygame.Surface:
        """Carga y redimensiona una imagen transparente del directorio de sprites.

        ``filename`` es el nombre del archivo dentro de ``assets/images``;
        ``size`` es el tamaño de dibujo solicitado en píxeles.
        """
        image = pygame.image.load(str(IMAGE_DIR / filename)).convert_alpha()
        return pygame.transform.smoothscale(image, size)

    def _play_music(self, track: str) -> None:
        """Reproduce en bucle la música que corresponde al estado actual.

        ``track`` debe ser ``menu`` o ``game``. Si ya está activa esa pista,
        no se vuelve a cargar ni se reinicia.
        """
        if self.music_track == track:
            return
        pygame.mixer.music.load(str(MUSIC_TRACKS[track]))
        pygame.mixer.music.set_volume(0.35)
        pygame.mixer.music.play(-1)
        self.music_track = track

    def toggle_fullscreen(self) -> None:
        """Alterna la pantalla y recuerda el tamaño de ventana anterior.

        El lienzo del juego conserva su tamaño lógico; ``_present`` se encarga
        de escalarlo al monitor sin estirar la imagen.
        """
        if not self.fullscreen:
            self.windowed_size = self.display.get_size()
            self.fullscreen = True
            self.display = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.fullscreen = False
            self.display = pygame.display.set_mode(self.windowed_size)
            if self.display.get_size() != self.windowed_size:
                self.display = pygame.display.set_mode(
                    self.windowed_size, pygame.RESIZABLE
                )
        pygame.display.set_caption("PONG — TRON LEGACY")

    def _logical_point(self, point: tuple[int, int]) -> tuple[int, int]:
        """Traduce una posición física a la posición equivalente del lienzo.

        Compensa el escalado y las franjas negras del modo de pantalla completa
        para que los clics coincidan con los botones dibujados.
        """
        display_width, display_height = self.display.get_size()
        scale = min(display_width / WIDTH, display_height / HEIGHT)
        offset_x = (display_width - WIDTH * scale) / 2
        offset_y = (display_height - HEIGHT * scale) / 2
        return (
            round((point[0] - offset_x) / scale),
            round((point[1] - offset_y) / scale),
        )

    def _logical_mouse_position(self) -> tuple[int, int]:
        """Lee el mouse y devuelve su posición en las coordenadas internas."""
        return self._logical_point(pygame.mouse.get_pos())

    def _present(self) -> None:
        """Muestra el lienzo lógico en la ventana o el monitor.

        Usa el factor de escala que cabe en ambos ejes, rellena el espacio
        sobrante con negro y centra la imagen para conservar sus proporciones.
        """
        display_width, display_height = self.display.get_size()
        scale = min(display_width / WIDTH, display_height / HEIGHT)
        scaled_width = round(WIDTH * scale)
        scaled_height = round(HEIGHT * scale)
        scaled_screen = pygame.transform.smoothscale(
            self.screen, (scaled_width, scaled_height)
        )
        self.display.fill((0, 0, 0))
        self.display.blit(
            scaled_screen,
            ((display_width - scaled_width) // 2, (display_height - scaled_height) // 2),
        )
        pygame.display.flip()

    def _open_instructions(self, return_state: str) -> None:
        """Abre la guía y guarda a qué pantalla debe volver.

        ``return_state`` es ``menu`` si se abrió desde el menú principal y
        ``paused`` si se abrió desde las opciones de pausa.
        """
        self.instructions_return_state = return_state
        self.state = "instructions"

    def _pause_game(self) -> None:
        """Congela el movimiento y pausa la música si la partida sigue activa."""
        if not self.winner:
            self.state = "paused"
            pygame.mixer.music.pause()

    def _resume_game(self) -> None:
        """Regresa al juego y reanuda la pista que se pausó."""
        self.state = "game"
        pygame.mixer.music.unpause()

    def _return_to_menu(self) -> None:
        """Cambia al menú principal y activa su pista musical."""
        self.state = "menu"
        self._play_music("menu")

    def start_match(self) -> None:
        """Inicia una partida nueva.

        Reinicia los puntos y posiciones, muestra el objetivo durante unos
        segundos, prepara el saque inicial y cambia a la música de partida.
        """
        self.left_score = 0
        self.right_score = 0
        self.left_y = HEIGHT / 2
        self.right_y = HEIGHT / 2
        self.winner = ""
        now = pygame.time.get_ticks() / 1000
        self._reset_ball(1, now)
        self.match_intro_until = now + MATCH_INTRO_SECONDS
        self.serve_at = self.match_intro_until
        self.state = "game"
        self._play_music("game")

    def _reset_ball(self, direction: int, now: float) -> None:
        """Centra la pelota y programa un saque para después de la pausa breve.

        ``direction`` define hacia qué lado irá el saque; ``now`` es el tiempo
        actual del juego y sirve para programar el momento del siguiente saque.
        """
        self.ball_x = WIDTH / 2
        self.ball_y = HEIGHT / 2
        self.ball_vx = 0.0
        self.ball_vy = 0.0
        self.serve_direction = direction
        self.serve_at = now + 0.7
        self.left_flash_until = 0.0
        self.right_flash_until = 0.0
        self.ball_flash_until = 0.0

    def _score_goal(self, scorer: int, now: float) -> None:
        """Suma un punto al lado que anotó y determina si ganó la partida.

        ``scorer`` vale 0 para el lado rojo/izquierdo y 1 para el azul/derecho.
        Si aún nadie llegó a cinco, vuelve a centrar la pelota para otro saque.
        """
        if scorer == 0:
            self.left_score += 1
        else:
            self.right_score += 1
        self.goal_sound.play()

        if self.left_score >= WIN_SCORE or self.right_score >= WIN_SCORE:
            self.winner = "ROJO" if self.left_score >= WIN_SCORE else "AZUL"
            self.return_to_menu_at = now + 2.5
            return

        self._reset_ball(1 if scorer == 0 else -1, now)

    def _move_ball(self, delta_time: float, now: float) -> None:
        """Avanza la pelota y responde a cada colisión.

        ``delta_time`` es el tiempo desde el fotograma anterior y ``now`` el
        reloj del juego. También activa sonidos, sprites de impacto y goles.
        """
        # El saque solo comienza cuando termina la espera inicial o entre puntos.
        if self.ball_vx == 0 and now >= self.serve_at:
            self.ball_vx = 390 * self.serve_direction
            self.ball_vy = random.uniform(-190, 190)

        self.ball_x += self.ball_vx * delta_time
        self.ball_y += self.ball_vy * delta_time

        if self.ball_y - BALL_RADIUS <= COURT_TOP:
            # Reubica la pelota dentro de la cancha para evitar rebotes repetidos.
            self.ball_y = COURT_TOP + BALL_RADIUS
            self.ball_vy = abs(self.ball_vy)
            self.hit_sound.play()
            self.ball_flash_until = now + COLLISION_FLASH_SECONDS
        elif self.ball_y + BALL_RADIUS >= COURT_BOTTOM:
            # El signo de la velocidad vertical indica el sentido del rebote.
            self.ball_y = COURT_BOTTOM - BALL_RADIUS
            self.ball_vy = -abs(self.ball_vy)
            self.hit_sound.play()
            self.ball_flash_until = now + COLLISION_FLASH_SECONDS

        left_paddle = pygame.Rect(59, round(self.left_y - 54), 25, 108)
        right_paddle = pygame.Rect(WIDTH - 84, round(self.right_y - 54), 25, 108)
        ball_rect = pygame.Rect(round(self.ball_x - BALL_RADIUS),
                                round(self.ball_y - BALL_RADIUS),
                                BALL_RADIUS * 2, BALL_RADIUS * 2)

        paddle = None
        direction = 0
        if self.ball_vx < 0 and ball_rect.colliderect(left_paddle):
            paddle, direction = left_paddle, 1
        elif self.ball_vx > 0 and ball_rect.colliderect(right_paddle):
            paddle, direction = right_paddle, -1

        if paddle is not None:
            # El punto de contacto cambia el ángulo para que cada golpe varíe.
            self.ball_x = (paddle.right + BALL_RADIUS if direction > 0
                           else paddle.left - BALL_RADIUS)
            offset = (self.ball_y - (paddle.centery)) / (paddle.height / 2)
            angle = max(-0.78, min(0.78, offset * 0.85))
            speed = min(760, math.hypot(self.ball_vx, self.ball_vy) * 1.045)
            self.ball_vx = direction * speed * math.sqrt(1 - angle * angle)
            self.ball_vy = speed * angle
            self.hit_sound.play()
            self.ball_flash_until = now + COLLISION_FLASH_SECONDS
            if direction > 0:
                self.left_flash_until = now + COLLISION_FLASH_SECONDS
            else:
                self.right_flash_until = now + COLLISION_FLASH_SECONDS

        # Si la pelota cruzó un extremo, el lado contrario recibe el punto.
        if self.ball_x + BALL_RADIUS < 0:
            self._score_goal(1, now)
        elif self.ball_x - BALL_RADIUS > WIDTH:
            self._score_goal(0, now)

    def _draw_menu(self) -> None:
        """Dibuja la pantalla de inicio y sus opciones seleccionables.

        La imagen contiene los rótulos del menú; los rectángulos invisibles
        definidos en ``__init__`` reciben los clics sobre esas opciones.
        """
        self.screen.blit(self.menu_background, (0, 0))
        mouse_position = self._logical_mouse_position()
        for button in self.menu_buttons:
            if button.collidepoint(mouse_position):
                highlight = pygame.Surface(button.size, pygame.SRCALPHA)
                highlight.fill((255, 70, 75, 35))
                self.screen.blit(highlight, button.topleft)
                pygame.draw.rect(self.screen, (255, 115, 120), button, 2, border_radius=18)
        fullscreen_color = CYAN if self.fullscreen_button.collidepoint(mouse_position) else WHITE
        pygame.draw.rect(self.screen, (4, 12, 38), self.fullscreen_button, border_radius=8)
        pygame.draw.rect(self.screen, CYAN, self.fullscreen_button, 2, border_radius=8)
        mode = "PANTALLA: COMPLETA" if not self.fullscreen else "MODO VENTANA"
        label = self.small_font.render(mode, True, fullscreen_color)
        self.screen.blit(label, label.get_rect(center=self.fullscreen_button.center))

    def _draw_instructions(self) -> None:
        """Dibuja el fondo oscurecido, la guía y el control para regresar."""
        self.screen.blit(self.menu_background, (0, 0))
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((5, 5, 16, 205))
        self.screen.blit(shade, (0, 0))
        self.screen.blit(
            self.instructions_image,
            self.instructions_image.get_rect(center=(WIDTH // 2, HEIGHT // 2)),
        )
        pygame.draw.rect(self.screen, (4, 12, 38), self.instructions_back_button,
                         border_radius=8)
        pygame.draw.rect(self.screen, CYAN, self.instructions_back_button, 2,
                         border_radius=8)
        back = self.small_font.render("ESC", True, WHITE)
        self.screen.blit(back, back.get_rect(center=self.instructions_back_button.center))

    def _draw_pause_button(self) -> None:
        """Dibuja el botón interactivo de pausa sobre la cancha."""
        button = pygame.Surface(self.pause_button.size, pygame.SRCALPHA)
        button.fill((4, 12, 38, 220))
        self.screen.blit(button, self.pause_button.topleft)
        pygame.draw.rect(self.screen, CYAN, self.pause_button, 2, border_radius=8)
        label = self.small_font.render("II  PAUSA", True, WHITE)
        self.screen.blit(label, label.get_rect(center=self.pause_button.center))

    def _draw_paused(self, now: float) -> None:
        """Muestra la partida oscurecida y las opciones de pausa.

        ``now`` conserva los efectos visuales de la partida bajo la capa de pausa.
        """
        self._draw_game(now)
        shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        shade.fill((2, 4, 18, 205))
        self.screen.blit(shade, (0, 0))
        panel = pygame.Rect(355, 210, 390, 350)
        pygame.draw.rect(self.screen, (6, 14, 43), panel, border_radius=20)
        pygame.draw.rect(self.screen, CYAN, panel, 2, border_radius=20)
        title = self.large_font.render("PAUSA", True, CYAN)
        self.screen.blit(title, title.get_rect(center=(WIDTH // 2, 250)))
        mouse_position = self._logical_mouse_position()
        for button, label in self.pause_options:
            hovered = button.collidepoint(mouse_position)
            fill = (35, 91, 145) if hovered else (12, 28, 67)
            pygame.draw.rect(self.screen, fill, button, border_radius=10)
            pygame.draw.rect(self.screen, CYAN if hovered else (55, 121, 183),
                             button, 2, border_radius=10)
            text = self.font.render(label, True, WHITE)
            self.screen.blit(text, text.get_rect(center=button.center))

    def _draw_game(self, now: float) -> None:
        """Dibuja la cancha, marcador, sprites y mensajes temporales.

        ``now`` decide cuándo termina el anuncio previo y cuánto dura el
        destello de choque o la pantalla de victoria.
        """
        self.screen.blit(self.court_background, (0, 0))
        red_sprite = self.red_hit_image if now < self.left_flash_until else self.red_paddle
        blue_sprite = self.blue_hit_image if now < self.right_flash_until else self.blue_paddle
        ball_sprite = self.ball_hit_image if now < self.ball_flash_until else self.ball_image
        self.screen.blit(red_sprite, red_sprite.get_rect(center=(72, round(self.left_y))))
        self.screen.blit(
            blue_sprite, blue_sprite.get_rect(center=(WIDTH - 72, round(self.right_y)))
        )
        self.screen.blit(
            ball_sprite, ball_sprite.get_rect(center=(round(self.ball_x), round(self.ball_y)))
        )
        if not self.winner:
            self._draw_pause_button()

        left_text = self.large_font.render(str(self.left_score), True, WHITE)
        right_text = self.large_font.render(str(self.right_score), True, WHITE)
        self.screen.blit(left_text, left_text.get_rect(center=(480, 92)))
        self.screen.blit(right_text, right_text.get_rect(center=(620, 92)))

        if self.winner:
            shade = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            shade.fill((0, 0, 0, 175))
            self.screen.blit(shade, (0, 0))
            title = self.large_font.render("¡VICTORIA!", True, WHITE)
            self.screen.blit(title, title.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 46)))
            side_color = RED if self.winner == "ROJO" else CYAN
            message = self.font.render(f"GANA EL LADO {self.winner}", True, side_color)
            self.screen.blit(message, message.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 8)))
            remaining = max(0, self.return_to_menu_at - now)
            subtext = self.small_font.render(
                f"Volviendo al menu en {math.ceil(remaining)}...", True, CYAN
            )
            self.screen.blit(subtext, subtext.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 58)))
        elif now < self.match_intro_until:
            panel = pygame.Rect(130, HEIGHT // 2 - 60, WIDTH - 260, 120)
            pygame.draw.rect(self.screen, (4, 12, 38), panel, border_radius=18)
            pygame.draw.rect(self.screen, CYAN, panel, 2, border_radius=18)
            message = self.font.render(
                f"¡EL PRIMERO EN LLEGAR A {WIN_SCORE} PUNTOS GANA!", True, WHITE
            )
            self.screen.blit(message, message.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 15)))
            countdown = self.small_font.render(
                f"La partida comienza en {math.ceil(self.match_intro_until - now)}...",
                True,
                CYAN,
            )
            self.screen.blit(
                countdown, countdown.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 25))
            )
        elif self.ball_vx == 0:
            hint = self.small_font.render("PREPARATE...", True, WHITE)
            self.screen.blit(hint, hint.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 55)))

    def run(self) -> None:
        """Ejecuta el juego hasta que se elija Salir o se cierre la ventana.

        Cada ciclo procesa teclado y mouse, actualiza el estado activo, dibuja
        la pantalla correspondiente y la presenta con el escalado adecuado.
        """
        running = True
        while running:
            delta_time = min(self.clock.tick(FPS) / 1000, 0.03)
            now = pygame.time.get_ticks() / 1000

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_F11:
                        self.toggle_fullscreen()
                    elif self.state == "menu":
                        if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                            self.start_match()
                        elif event.key == pygame.K_i:
                            self._open_instructions("menu")
                        elif event.key == pygame.K_ESCAPE:
                            running = False
                    elif self.state == "instructions":
                        if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                            if self.instructions_return_state == "paused":
                                self.state = "paused"
                            else:
                                self._return_to_menu()
                    elif self.state == "game" and event.key == pygame.K_ESCAPE:
                        self._pause_game()
                    elif self.state == "paused" and event.key in (
                        pygame.K_ESCAPE, pygame.K_SPACE, pygame.K_RETURN
                    ):
                        self._resume_game()
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    position = self._logical_point(event.pos)
                    if self.state == "menu":
                        if self.fullscreen_button.collidepoint(position):
                            self.toggle_fullscreen()
                        elif self.menu_buttons[0].collidepoint(position):
                            self.start_match()
                        elif self.menu_buttons[1].collidepoint(position):
                            self._open_instructions("menu")
                        elif self.menu_buttons[2].collidepoint(position):
                            running = False
                    elif self.state == "game" and self.pause_button.collidepoint(position):
                        self._pause_game()
                    elif self.state == "paused":
                        if self.pause_options[0][0].collidepoint(position):
                            self._resume_game()
                        elif self.pause_options[1][0].collidepoint(position):
                            self._open_instructions("paused")
                        elif self.pause_options[2][0].collidepoint(position):
                            self._return_to_menu()
                    elif (
                        self.state == "instructions"
                        and self.instructions_back_button.collidepoint(position)
                    ):
                        if self.instructions_return_state == "paused":
                            self.state = "paused"
                        else:
                            self._return_to_menu()

            if self.state == "game" and not self.winner:
                if now >= self.match_intro_until:
                    keys = pygame.key.get_pressed()
                    movement = (
                        keys[pygame.K_s] - keys[pygame.K_w]
                    ) * PADDLE_SPEED * delta_time
                    self.left_y = clamp_paddle_y(self.left_y + movement, 54)
                    movement = (
                        keys[pygame.K_DOWN] - keys[pygame.K_UP]
                    ) * PADDLE_SPEED * delta_time
                    self.right_y = clamp_paddle_y(self.right_y + movement, 54)
                self._move_ball(delta_time, now)
            elif self.state == "game" and now >= self.return_to_menu_at:
                self._return_to_menu()

            if self.state == "menu":
                self._draw_menu()
            elif self.state == "instructions":
                self._draw_instructions()
            elif self.state == "paused":
                self._draw_paused(now)
            else:
                self._draw_game(now)
            self._present()

        pygame.quit()


def main() -> None:
    """Configura el mezclador de audio, inicializa Pygame y ejecuta el juego."""
    pygame.mixer.pre_init(44100, -16, 1, 512)
    pygame.init()
    PongGame().run()


if __name__ == "__main__":
    main()