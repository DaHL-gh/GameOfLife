import math
import pygame
import sys
import time


class Window:
    def __init__(self, width: int, height: int, buttons_height: int, toggle_width: int, menu_width: int,
                 fps_limit=20, game_stopped=True,
                 scale=20, camera_pos=(0, 0)):

        self.width = width
        self.height = height

        self.last_frame_time = time.monotonic()
        self.fps_limit = fps_limit
        self.update_interval = 1 / fps_limit
        self.game_stopped = game_stopped

        self.widgets = []
        self.layouts = []

        self.layout_base = BasicLayout(self, rotation="vertical")
        self.layout_base.set_shape((0, 0), width, height)
        self.sim_field = SimulationField(self, scale, list(camera_pos))
        self.layout_buttons = BasicLayout(self, rotation="horizontal", size_hint=0.1)
        self.toggle = GameToggle(self, game_stopped)
        self.layout_speed_control = BasicLayout(self, rotation="horizontal", size_hint=0.2)
        self.game_speed_scroll_changer = GameSpeedScrollChanger(self)
        self.layout_speed_buttons = BasicLayout(self, rotation="vertical", size_hint=0.2)
        self.game_speed_button_up = GameSpeedButtonUp(self)
        self.game_speed_button_down = GameSpeedButtonDown(self)
        self.clear_button = ClearButton(self, size_hint=0.2)

        self.layout_base.add_widget(self.sim_field)
        self.layout_base.add_widget(self.layout_buttons)
        self.layout_buttons.add_widget(self.toggle)
        self.layout_buttons.add_widget(self.layout_speed_control)
        self.layout_speed_control.add_widget(self.game_speed_scroll_changer)
        self.layout_speed_control.add_widget(self.layout_speed_buttons)
        self.layout_speed_buttons.add_widget(self.game_speed_button_up)
        self.layout_speed_buttons.add_widget(self.game_speed_button_down)
        self.layout_buttons.add_widget(self.clear_button)

        self.calculate_layout_shapes()

        self.display = pygame.display.set_mode((width, height))
        self.draw_screen()

    def calculate_layout_shapes(self):
        for layout in self.layouts:
            layout.calculate_shapes()

    def on_release(self, mouse_pos: tuple):
        for widget in reversed(self.widgets):
            if widget.is_mouse_on_object(mouse_pos):
                widget.on_release()
                break

    def update(self):
        if not self.game_stopped:
            if time.monotonic() - self.last_frame_time > self.update_interval:
                self.sim_field.calculate_next_gen()

                self.draw_screen()
                pygame.display.flip()

                self.last_frame_time += self.update_interval

    def draw_screen(self):
        for widget in self.widgets:
            widget.draw(self.display)

        pygame.display.flip()




class Widget:
    def __init__(self, window: Window, size_hint=1.0):
        self._window = window
        self._pos = (0, 0)
        self._width = 0
        self._height = 0
        self._size_hint = size_hint

        self._shape = pygame.Rect(self._pos[0], self._pos[1], self._width, self._height)

    def set_shape(self, pos=None, width=None, height=None):
        if pos is not None:
            self._pos = pos
        if width is not None:
            self._width = width
        if height is not None:
            self._height = height
        self._shape = pygame.Rect(self._pos[0], self._pos[1], width, height)

    def get_size_hint(self):
        return self._size_hint

    def draw(self, display: pygame.Surface):
        pass

    def on_release(self):
        pass

    def scroll(self, value):
        pass

    def key_down(self, key_number):
        pass

    def is_mouse_on_object(self, mouse_pos: tuple):
        return self._shape.collidepoint(mouse_pos)


class BasicLayout(Widget):
    def __init__(self, window: Window, rotation="vertical", size_hint=1.0):
        super().__init__(window, size_hint=size_hint)
        self.rotation = rotation

        self._window.layouts.append(self)

        self.widgets = []
        self.size_hints = []

    def add_widget(self, widget: Widget):
        self.widgets.append(widget)
        self._window.widgets.append(widget)
        self.size_hints.append(widget.get_size_hint())

    def calculate_shapes(self):

        if self.size_hints.count(1) > 0:
            smart_size_hint = (1 - sum(self.size_hints)) / self.size_hints.count(1) + 1
        else:
            smart_size_hint = 1

        widget_pos = {"horizontal": self._pos[0], "vertical": self._pos[1]}
        for index in range(len(self.widgets)):
            layout_size = {"horizontal": self._width, "vertical": self._height}
            widget_size = layout_size
            if self.size_hints[index] == 1:
                widget_size[self.rotation] = layout_size[self.rotation] * smart_size_hint
            else:
                widget_size[self.rotation] = layout_size[self.rotation] * self.size_hints[index]

            self.widgets[index].set_shape(pos=(widget_pos["horizontal"], widget_pos["vertical"]),
                                          width=widget_size["horizontal"], height=widget_size["vertical"])

            widget_pos[self.rotation] += widget_size[self.rotation]


class SimulationField(Widget):
    possible_key_numbers = (pygame.K_UP, pygame.K_w,
                            pygame.K_LEFT, pygame.K_a,
                            pygame.K_DOWN, pygame.K_s,
                            pygame.K_RIGHT, pygame.K_d)
    offsets = ((-1, -1), (0, -1), (1, -1),
               (-1, 0), (1, 0),
               (-1, 1), (0, 1), (1, 1))

    def __init__(self, window: Window, scale: int, camera_pos: list, size_hint=1):
        super().__init__(window=window, size_hint=size_hint)

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

    def on_release(self):
        mouse_pos = pygame.mouse.get_pos()
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


class GameToggle(Widget):
    possible_key_numbers = (pygame.K_SPACE,)

    def __init__(self, window: Window, game_stopped: bool, size_hint=1):
        super().__init__(window=window, size_hint=size_hint)

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


class GameSpeedScrollChanger(Widget):
    def __init__(self, window: Window, size_hint=1):
        super().__init__(window=window, size_hint=size_hint)

    def draw(self, display: pygame.Surface):
        font_size = 40
        font = pygame.font.SysFont('couriernew', font_size)

        text = str(self._window.fps_limit) + " fps"
        widget_text = font.render(text, True, (255, 255, 255))
        place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

        pygame.draw.rect(display, (100, 100, 100), self._shape, 0)
        display.blit(widget_text, place)

    def scroll(self, value):
        self._window.fps_limit = max(1, self._window.fps_limit + value)
        self._window.update_interval = 1 / self._window.fps_limit


class GameSpeedButtonUp(Widget):
    def __init__(self, window: Window, size_hint=1):
        super().__init__(window=window, size_hint=size_hint)
        self.__color = (100, 200, 100)
        self.__font_size = 20
        self.__text = "+"

    def draw(self, display: pygame.Surface):
        font = pygame.font.SysFont('couriernew', self.__font_size)

        widget_text = font.render(self.__text, True, (255, 255, 255))
        place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

        pygame.draw.rect(display, self.__color, self._shape, 0)
        display.blit(widget_text, place)

    def on_release(self):
        self._window.fps_limit += 1
        self._window.update_interval = 1 / self._window.fps_limit


class GameSpeedButtonDown(Widget):
    def __init__(self, window: Window, size_hint=1):
        super().__init__(window=window, size_hint=size_hint)
        self.__color = (200, 100, 100)
        self.__font_size = 20
        self.__text = "-"

    def draw(self, display: pygame.Surface):
        font = pygame.font.SysFont('couriernew', self.__font_size)

        widget_text = font.render(self.__text, True, (255, 255, 255))
        place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

        pygame.draw.rect(display, self.__color, self._shape, 0)
        display.blit(widget_text, place)

    def on_release(self):
        self._window.fps_limit = max(1, self._window.fps_limit - 1)
        self._window.update_interval = 1 / self._window.fps_limit


class ClearButton(Widget):

    def __init__(self, window: Window, size_hint=1):
        super().__init__(window=window, size_hint=size_hint)
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

        self.window.draw_screen()

    def mouse_button_up(self, key_number: int):

        if key_number == 1:
            self.window.on_release(pygame.mouse.get_pos())

        self.window.draw_screen()

    def mouse_wheel(self, mouse_pos: tuple, value: int):
        for widget in self.window.widgets:
            if widget.is_mouse_on_object(mouse_pos):
                widget.scroll(value)

        self.window.draw_screen()


if __name__ == "__main__":
    pygame.init()

    # ЛКМ - взаимодействие с объектами
    # Прокрутка колеса - изменение масштаба отображения
    # WASD | стрелочки - управление камерой
    # Пробел - вкл/выкл паузу

    window_width = 1600
    window_height = 900
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
