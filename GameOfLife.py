import math

import pygame
import sys
import time


class Window:
    def __init__(self, width: int, height: int, buttons_height: int, toggle_width: int, menu_width: int,
                 fps_limit=60, game_stopped=True,
                 scale=20, camera_pos=None):
        if camera_pos is None:
            camera_pos = [0, 0]

        self.width = width
        self.height = height

        self.last_frame_time = time.monotonic()
        self.fps_limit = fps_limit
        self.update_interval = 1 / fps_limit
        self.game_stopped = game_stopped

        self.sim_field = SimulationField((0, 0), width, height - buttons_height, self, scale, camera_pos)
        self.game_speed_changer = GameSpeedChanger((toggle_width, height - buttons_height), menu_width, buttons_height, self)
        self.toggle = GameToggle((0, height - buttons_height), toggle_width, buttons_height, self, game_stopped)
        self.clear_button = ClearButton((toggle_width + menu_width, height - buttons_height),
                                        width - toggle_width - menu_width, buttons_height,
                                        self)

        self.buttons = (self.toggle, self.clear_button)
        self.scrollable = (self.sim_field, self.game_speed_changer)

        display = pygame.display.set_mode((width, height))
        self.drawer = Drawer(self, display)

    def on_release(self, mouse_pos: tuple):
        for button in self.buttons:
            if button.is_mouse_on_object(mouse_pos):
                button.on_release()
                break

        if self.sim_field.is_mouse_on_object(mouse_pos):
            self.sim_field.on_release(mouse_pos)

    def update(self):
        if not self.game_stopped:
            if time.monotonic() - self.last_frame_time > self.update_interval:
                self.sim_field.calculate_next_gen()

                self.drawer.draw_screen()
                pygame.display.flip()

                self.last_frame_time += self.update_interval


class Drawer:
    def __init__(self, window: Window, display: pygame.Surface):
        self.window = window
        self.display = display

        self.draw_screen()

    def draw_screen(self):
        self.window.sim_field.draw(self.display)

        for button in self.window.buttons:
            button.draw(self.display)

        self.window.game_speed_changer.draw(self.display)

        pygame.display.flip()


class Widget:
    def __init__(self, pos: tuple, width: int, height: int, window: Window):
        self._pos = pos
        self._width = width
        self._height = height
        self._shape = pygame.Rect(pos[0], pos[1], width, height)
        self._window = window

    def draw(self, display: pygame.Surface):
        pass

    def on_release(self, *args):
        pass

    def scroll(self, value):
        pass

    def key_down(self, key_number):
        pass

    def is_mouse_on_object(self, mouse_pos: tuple):
        return self._shape.collidepoint(mouse_pos)


class SimulationField(Widget):
    possible_key_numbers = (pygame.K_UP, pygame.K_w,
                            pygame.K_LEFT, pygame.K_a,
                            pygame.K_DOWN, pygame.K_s,
                            pygame.K_RIGHT, pygame.K_d)
    offsets = ((-1, -1), (0, -1), (1, -1),
               (-1,  0),          (1,  0),
               (-1,  1), (0,  1), (1,  1))

    def __init__(self, pos: tuple, width: int, height: int, window: Window, scale: int, camera_pos: list):
        super().__init__(pos, width, height, window)

        self.scale = scale
        self.camera_pos = camera_pos

        self.__positions_of_alive_cells = set()

    def draw(self, display: pygame.Surface):
        pygame.draw.rect(display, 0, self._shape, 0)

        for pos in self.__positions_of_alive_cells:
            x = pos[0] - self.camera_pos[0]
            y = pos[1] - self.camera_pos[1]

            half_width = self._width // 2
            half_height = self._height // 2

            cuts, out_of_bound = self.__check_for_cuts((x, y), half_width, half_height)

            if not out_of_bound:
                self.__draw_cell((x, y), half_width, half_height, cuts, display)

    def on_release(self, mouse_pos: tuple):
        cell_pos = ((self.camera_pos[0] - (self._width / 2 - mouse_pos[0] + self._pos[0] - 1) / self.scale) // 1,
                    (self.camera_pos[1] - (self._height / 2 - mouse_pos[1] + self._pos[1] - 1) / self.scale) // 1)

        if cell_pos in self.__positions_of_alive_cells:
            self.__positions_of_alive_cells.discard(cell_pos)
        else:
            self.__positions_of_alive_cells.add(cell_pos)

    def scroll(self, value):
        self._window.sim_field.scale = max(1, self._window.sim_field.scale + value)

    def key_down(self, key_number):
        window_width = self._window.width
        camera_pos = self._window.sim_field.camera_pos

        if key_number == pygame.K_UP or key_number == pygame.K_w:
            camera_pos[1] -= window_width / 20 / self.scale

        elif key_number == pygame.K_LEFT or key_number == pygame.K_a:
            camera_pos[0] -= window_width / 20 / self.scale

        elif key_number == pygame.K_DOWN or key_number == pygame.K_s:
            camera_pos[1] += window_width / 20 / self.scale

        elif key_number == pygame.K_RIGHT or key_number == pygame.K_d:
            camera_pos[0] += window_width / 20 / self.scale

    def calculate_next_gen(self):
        # Получает статистику о живых клетках рядом
        # 0 0 0 0 0 | 1 1 2 1 1
        # 0 1 0 1 0 | 1 0 2 0 1
        # 0 0 0 0 0 | 1 1 2 1 1
        stat = self.__get_stat()  # -> dict {pos: count}

        new_positions = set()

        for item in stat.items():
            if item[1] == 3:
                new_positions.add(item[0])
            elif item[1] == 2:
                if item[0] in self.__positions_of_alive_cells:
                    new_positions.add(item[0])

        self.__positions_of_alive_cells = new_positions

    def clear_sim_field(self):
        self.__positions_of_alive_cells = set()

    def __check_for_cuts(self, pos: tuple, half_width: int, half_height: int):
        cuts = set()

        out_of_bound = False

        if pos[0] * self.scale < -half_width - self.scale:
            out_of_bound = True
        elif pos[0] * self.scale < -half_width:
            cuts.add("left")

        elif pos[0] * self.scale >= half_width:
            out_of_bound = True
        elif pos[0] * self.scale >= half_width - self.scale:
            cuts.add("right")

        if pos[1] * self.scale < -half_height - self.scale:
            out_of_bound = True
        elif pos[1] * self.scale < -half_height:
            cuts.add("up")

        elif pos[1] * self.scale >= half_height:
            out_of_bound = True
        elif pos[1] * self.scale >= half_height - self.scale:
            cuts.add("bottom")

        return cuts, out_of_bound

    def __draw_cell(self, pos: tuple, half_width: int, half_height: int, cuts: set, display: pygame.Surface):
        x = pos[0] * self.scale + half_width
        y = pos[1] * self.scale + half_height

        cell_width = self.scale
        cell_height = self.scale

        if "left" in cuts:
            cell_width = x + self.scale
            x = 0
        elif "right" in cuts:
            cell_width = math.ceil(half_width * 2 - x)

        if "up" in cuts:
            cell_height = y + self.scale
            y = 0
        elif "bottom" in cuts:
            cell_height = math.ceil(half_height * 2 - y)

        shape = pygame.Rect(x + self._pos[0], y + self._pos[1], cell_width, cell_height)
        pygame.draw.rect(display, (255, 255, 255), shape, 0)

    def __get_stat(self):
        stat = {}

        for pos in self.__positions_of_alive_cells:
            for offset in self.offsets:
                new_pos = (pos[0] + offset[0], pos[1] + offset[1])
                if new_pos in stat:
                    stat[new_pos] += 1
                else:
                    stat[new_pos] = 1

        return stat


class GameSpeedChanger(Widget):
    def __init__(self, pos: tuple, width: int, height: int, window:Window):
        super().__init__(pos, width, height, window)

    def draw(self, display: pygame.Surface):
        font_size = 40
        font = pygame.font.SysFont('couriernew', font_size)

        text = str(self._window.fps_limit)
        widget_text = font.render(text, True, (255, 255, 255))
        place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

        pygame.draw.rect(display, (100, 100, 100), self._shape, 0)
        display.blit(widget_text, place)

    def scroll(self, value):
        self._window.fps_limit = max(1, self._window.fps_limit + value)
        self._window.update_interval = 1 / self._window.fps_limit


class GameToggle(Widget):
    possible_key_numbers = (pygame.K_SPACE,)

    def __init__(self, pos: tuple, width: int, height: int, window: Window, game_stopped: bool):
        super().__init__(pos, width, height, window)

        self.__font_size = 40
        self.__change_text_and_color(game_stopped)

    def draw(self, display: pygame.Surface):
        font = pygame.font.SysFont('couriernew', self.__font_size)

        widget_text = font.render(self.__text, True, (255, 255, 255))
        place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

        pygame.draw.rect(display, self.__color, self._shape, 0)
        display.blit(widget_text, place)

    def on_release(self):
        game_stopped = not self._window.game_stopped

        self.__change_text_and_color(game_stopped)

        self._window.game_stopped = game_stopped

        if not game_stopped:
            self._window.last_frame_time = time.monotonic()

    def key_down(self, key_number):
        if key_number == pygame.K_SPACE:
            self.on_release()

    def __change_text_and_color(self, game_stopped: bool):
        if game_stopped:
            self.__text = "Продолжить"
            self.__color = (200, 100, 100)
        else:
            self.__text = "Остановить"
            self.__color = (100, 200, 100)


class ClearButton(Widget):
    def __init__(self, pos: tuple, width: int, height: int, window: Window):
        super().__init__(pos, width, height, window)
        self.__color = (100, 100, 100)
        self.__font_size = 40
        self.__text = "Clear"

    def draw(self, display: pygame.Surface):
        font = pygame.font.SysFont('couriernew', self.__font_size)

        widget_text = font.render(self.__text, True, (255, 255, 255))
        place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

        pygame.draw.rect(display, self.__color, self._shape, 0)
        display.blit(widget_text, place)

    def on_release(self):
        self._window.sim_field.clear_sim_field()


class EventHandler:
    def __init__(self, window: Window):
        self.window = window

    def key_down(self, key_number: int):
        if key_number in self.window.sim_field.possible_key_numbers:
            self.window.sim_field.key_down(key_number)
        elif key_number in self.window.toggle.possible_key_numbers:
            self.window.toggle.key_down(key_number)

        self.window.drawer.draw_screen()

    def mouse_button_up(self, key_number: int):

        if key_number == 1:
            self.window.on_release(pygame.mouse.get_pos())

        self.window.drawer.draw_screen()

    def mouse_wheel(self, mouse_pos: tuple, value: int):
        for widget in self.window.scrollable:
            if widget.is_mouse_on_object(mouse_pos):
                widget.scroll(value)

        self.window.drawer.draw_screen()


if __name__ == "__main__":
    pygame.init()

    # ЛКМ - взаимодействие с объектами
    # Прокрутка колеса - изменение масштаба отображения
    # WASD | стрелочки - управление камерой
    # Пробел - вкл/выкл паузу

    window_width = 1000
    window_height = 600
    buttons_height = window_height // 12
    toggle_width = window_width // 2
    menu_width = window_width // 4

    window = Window(window_width, window_height, buttons_height, toggle_width, menu_width)

    event_handler = EventHandler(window)

    while True:
        window.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                event_handler.key_down(event.dict["key"])

            elif event.type == pygame.MOUSEBUTTONUP:
                event_handler.mouse_button_up(event.dict["button"])

            elif event.type == pygame.MOUSEWHEEL:
                value = event.dict["y"]
                event_handler.mouse_wheel(pygame.mouse.get_pos(), value)

            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
