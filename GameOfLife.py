import math
import sys
import time
import pygame

def time_counter(func):
    def wrapper(*args, **kwargs):
        t = time.monotonic()
        result = func(*args, **kwargs)
        print(func.__name__, math.ceil((time.monotonic() - t) * 1000))
        return result
    return wrapper


class Window:
    def __init__(self, width: int, height: int,
                 fps_limit=20,
                 scale=20, camera_pos=(0, 0)):
        self.width = width
        self.height = height

        self.game_screen = GameScreen(self, scale, camera_pos, fps_limit)
        self.main_menu = MainMenu(self)
        self.settings_menu = SettingsMenu(self)
        self.screens = [self.game_screen, self.main_menu, self.settings_menu]

        self.current_screen = self.main_menu

        self.display = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.draw()

    def update(self):
        self.current_screen.update()

    def resize(self, w, h):
        for screen in self.screens:
            screen.set_shape(width=w, height=h)
            screen.calculate_shapes()

        self.draw()

    def draw(self):
        self.current_screen.draw(self.display)

        pygame.display.flip()


class EventHandler:
    def __init__(self, window: Window):
        self._window = window

    def key_down(self, key_number: int):
        if key_number in self._window.game_screen.sim_field.possible_key_numbers:
            self._window.game_screen.sim_field.key_down(key_number)

        self._window.draw()

    def mouse_button_down(self, key_number: int):
        if key_number == 1:
            self._window.current_screen.on_press()

        self._window.draw()

    def mouse_button_up(self, key_number: int):

        if key_number == 1:
            self._window.current_screen.on_release()

        self._window.draw()

    def mouse_wheel(self, value: int):
        self._window.current_screen.scroll(value)

        self._window.draw()

    def resize(self, w, h):
        self._window.resize(w, h)

        self._window.draw()

    def window_leave(self):
        if self._window.current_screen.pressed_widget is not None:
            self._window.current_screen.on_press_cancel()
            self._window.current_screen.pressed_widget = None

            window.draw()


class Widget:
    def __init__(self, size_hint=1.0):
        self._pos = (0, 0)
        self._width = 0
        self._height = 0
        self._shape = pygame.Rect(self._pos[0], self._pos[1], self._width, self._height)
        self._size_hint = size_hint

    def set_shape(self, pos=(0, 0), width=0, height=0):
        self._pos = pos
        self._width = width
        self._height = height
        self._shape = pygame.Rect(self._pos[0], self._pos[1], self._width, self._height)

    def get_size_hint(self):
        return self._size_hint

    def get_widgets(self):
        return [self]

    def draw(self, display: pygame.Surface):
        pass

    def on_press(self):
        pass

    def on_press_cancel(self):
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
    def __init__(self, size_hint=1):
        super().__init__(size_hint=size_hint)

        self._widgets = []
        self._size_hints = []
        self.pressed_widget = None

    def draw(self, display: pygame.Surface):
        for widget in self._widgets:
            widget.draw(display)

    def add_widget(self, widget: Widget):
        self._widgets.append(widget)
        self._size_hints.append(widget.get_size_hint())
        self.calculate_shapes()

    def get_widgets(self):
        widgets = []
        for widget in self._widgets:
            for inner_widget in widget.get_widgets():
                widgets.append(inner_widget)
        return widgets

    def calculate_shapes(self):
        pass

    def on_press(self):
        for widget in self.get_widgets():
            if widget.is_mouse_on_object(pygame.mouse.get_pos()):
                widget.on_press()
                self.pressed_widget = widget

    def on_press_cancel(self):
        self.pressed_widget.on_press_cancel()

    def on_release(self):
        for widget in reversed(self.get_widgets()):
            if widget.is_mouse_on_object(pygame.mouse.get_pos()):
                if self.pressed_widget == widget:
                    widget.on_release()
                else:
                    self.pressed_widget.on_press_cancel()
                self.pressed_widget = None
                break

    def scroll(self, value):
        for widget in self._widgets:
            if widget.is_mouse_on_object(pygame.mouse.get_pos()):
                widget.scroll(value)


class MenuLayout(BasicLayout):
    def __init__(self, size_hint=1, direction="up", closed=True, text="MenuLayout"):
        super().__init__(size_hint=size_hint)
        self._direction = direction
        self._closed = closed
        self._hidden_widgets = []

        self._main_button = Button(text=text, on_release=self.main_btn_on_release)
        self.add_widget(self._main_button)

    def add_widget(self, widget: Widget):
        if not self._closed or self._widgets == []:
            self._widgets.append(widget)
        else:
            self._hidden_widgets.append(widget)
        self._size_hints.append(widget.get_size_hint())
        self.calculate_shapes()

    def calculate_shapes(self):
        all_widgets = self._widgets + self._hidden_widgets
        for i in range(len(all_widgets)):
            if self._direction == "up":
                widget_pos = (self._pos[0], self._pos[1] - self._height * i)
            elif self._direction == "down":
                widget_pos = (self._pos[0], self._pos[1] + self._height * i)
            elif self._direction == "left":
                widget_pos = (self._pos[0] - self._width * i, self._pos[1])
            elif self._direction == "right":
                widget_pos = (self._pos[0] + self._width * i, self._pos[1])
            else:
                raise Exception

            all_widgets[i].set_shape(pos=widget_pos, height=self._height, width=self._width)

            if hasattr(all_widgets[i], "calculate_shapes"):
                all_widgets[i].calculate_shapes()

    def main_btn_on_release(self):
        if not self._closed:
            color = tuple(x * 1.25 for x in self._main_button.get_color())
            self._main_button.set_color(color)

            self._widgets.remove(self._main_button)
            self._hidden_widgets = self._widgets
            self._widgets = [self._main_button]

        else:
            color = tuple(x * 0.8 for x in self._main_button.get_color())
            self._main_button.set_color(color)

            self._hidden_widgets.append(self._main_button)
            self._widgets = self._hidden_widgets
            self._hidden_widgets = []

        self._closed = not self._closed


class BoxLayout(BasicLayout):
    def __init__(self, rotation="vertical", size_hint=1.0):
        super().__init__(size_hint=size_hint)
        self._rotation = rotation

    def calculate_shapes(self):

        if self._size_hints.count(1) > 0:
            sum_not_1_sh = sum(self._size_hints) - self._size_hints.count(1)
            smart_size_hint = (1 - sum_not_1_sh) / self._size_hints.count(1)
        else:
            smart_size_hint = 1

        widget_pos = {"horizontal": self._pos[0], "vertical": self._pos[1]}
        for index in range(len(self._widgets)):
            layout_size = {"horizontal": self._width, "vertical": self._height}
            widget_size = layout_size
            if self._size_hints[index] == 1:
                widget_size[self._rotation] = math.ceil(layout_size[self._rotation] * smart_size_hint)
            else:
                widget_size[self._rotation] = math.ceil(layout_size[self._rotation] * self._size_hints[index])

            self._widgets[index].set_shape(pos=(widget_pos["horizontal"], widget_pos["vertical"]),
                                           width=widget_size["horizontal"], height=widget_size["vertical"])

            if hasattr(self._widgets[index], "calculate_shapes"):
                self._widgets[index].calculate_shapes()

            widget_pos[self._rotation] += widget_size[self._rotation]


class Screen(BoxLayout):
    def __init__(self, window: Window):
        super().__init__()
        self._window = window
        self._width = self._window.width
        self._height = self._window.height
        self.set_shape(width=self._width, height=self._height)

        self._widgets = []

    def update(self):
        pass

    def draw(self, display: pygame.Surface):
        for widget in self._widgets:
            widget.draw(display)


class Button(Widget):
    def __init__(self, size_hint=1, text="", font="couriernew", font_size=30, color=(100, 100, 100),
                 on_press=None, on_release=None, scroll=None,
                 outline_width=1, outline_colour=(200, 200, 200)):
        super().__init__(size_hint)
        self._text = text
        self._font = font
        self._font_size = font_size
        self._color = color

        self._outline_width = outline_width
        self._outline_colour = outline_colour

        blank_func = lambda *args, **kwargs: None

        self._on_press_action = on_press if on_press is not None else blank_func
        self._on_release_action = on_release if on_release is not None else blank_func
        self._scroll_action = scroll if scroll is not None else blank_func

    def on_press(self):
        self._color = tuple(x * 0.8 for x in self._color)
        self._on_press_action()

    def on_press_cancel(self):
        self._color = tuple(x * 1.25 for x in self._color)

    def on_release(self):
        self._color = tuple(x * 1.25 for x in self._color)
        self._on_release_action()

    def scroll(self, value):
        self._scroll_action(value)

    def draw(self, display: pygame.Surface):
        pygame.draw.rect(display, self._color, self._shape, 0)
        if self._outline_width != 0:
            pygame.draw.rect(display, self._outline_colour, self._shape, self._outline_width)

        font = pygame.font.SysFont(self._font, self._font_size)
        widget_text = font.render(self._text, True, (255, 255, 255))
        place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

        display.blit(widget_text, place)

    def set_text(self, text: str):
        self._text = text

    def get_text(self):
        return self._text

    def set_color(self, color: tuple):
        self._color = color

    def get_color(self):
        return self._color


class GameScreen(Screen):
    def __init__(self, window: Window, scale, camera_pos, fps_limit):
        super().__init__(window)
        self.layout_base = BoxLayout(rotation="vertical")
        self.add_widget(self.layout_base)

        self.last_frame_time = time.monotonic()
        self.fps_limit = fps_limit
        self.update_interval = 1 / fps_limit
        self.game_stopped = True

        dot = dict(name="точка", data=[(0, 0)])
        glider = dict(name="глайдер", data=[(0, -1), (1, 0), (-1, 1), (0, 1), (1, 1)])
        ship = dict(name='корабль', data=[(3, 2), (-1, -1), (2, -1), (1, 2), (2, 2), (3, 1), (3, 0), (0, 2), (-1, 1)])
        cross = dict(name='крест',
                     data=[(4, 0), (3, -1), (-3, 0), (1, -3), (2, 2), (-2, -1), (-1, 4), (-1, -1), (-1, -2), (4, 2),
                           (-3, 2), (2, -2), (2, 4), (2, -1), (0, 4), (-1, -3), (-1, 3), (4, -1), (3, 2), (-1, 2),
                           (4, 1), (-3, -1), (0, -3), (-3, 1), (2, -3), (1, 4), (2, 3), (-2, 2)])
        galaxy = dict(name='галактика',
                      data=[(4, 0), (3, 4), (4, -3), (4, 3), (3, 1), (-3, -3), (3, -1), (-3, 0), (0, -4), (-3, 3),
                            (1, -3), (2, -4), (1, 3), (-4, -2), (-4, -1), (-4, 4), (-4, 1), (-1, 4), (-2, 4), (3, -3),
                            (4, -4), (4, 2), (3, 0), (3, 3), (-3, -4), (1, -4), (0, 4), (-4, -3), (-4, 0), (-1, -3),
                            (-4, 3), (-2, 3), (-1, 3), (4, -1), (3, 2), (3, -4), (4, 1), (4, 4), (-3, -2), (0, -3),
                            (-3, -1), (-3, 4), (-3, 1), (2, -3), (0, 3), (1, 4), (-4, -4), (-1, -4)])

        self.brushes = [dot, glider, ship, cross, galaxy]
        self.current_brush_index = 0

        # Описание экрана
        if True:
            self.sim_field = SimulationField(scale, list(camera_pos))
            self.layout_base.add_widget(self.sim_field)

            self.layout_buttons = BoxLayout(size_hint=0.1, rotation="horizontal")
            self.layout_base.add_widget(self.layout_buttons)
            if True:
                self.toggle = Button(on_release=self.toggle_on_release, text="Продолжить", color=(200, 100, 100))
                self.layout_buttons.add_widget(self.toggle)

                self.layout_speed_control = BoxLayout(size_hint=0.15, rotation="horizontal")
                self.layout_buttons.add_widget(self.layout_speed_control)
                if True:
                    self.game_speed_scroll_changer = Button(scroll=self.gs_changer_scroll, text=f"{self.fps_limit} fps")
                    self.layout_speed_control.add_widget(self.game_speed_scroll_changer)

                    self.layout_speed_buttons = BoxLayout(size_hint=0.2, rotation="vertical")
                    self.layout_speed_control.add_widget(self.layout_speed_buttons)
                    if True:
                        self.game_speed_button_up = Button(text="+", color=(100, 200, 100), on_release=self.gs_btn_up_on_release)
                        self.layout_speed_buttons.add_widget(self.game_speed_button_up)

                        self.game_speed_button_down = Button(text="-", color=(200, 100, 100), on_release=self.gs_btn_down_on_release)
                        self.layout_speed_buttons.add_widget(self.game_speed_button_down)
                self.clear_button = Button(size_hint=0.15, text="Очистить", on_release=self.clear_btn_on_release)
                self.layout_buttons.add_widget(self.clear_button)

                self.brush_menu = MenuLayout(size_hint=0.15, text="Кисти")
                self.layout_buttons.add_widget(self.brush_menu)
                for i in range(len(self.brushes)):
                    self.add_brush_button(i)

                self.save_menu = MenuLayout(size_hint=0.15, text="Сохранение")
                self.layout_buttons.add_widget(self.save_menu)
                if True:
                    self.save_button = Button(text="Сохранить", on_release=self.save_game)
                    self.save_menu.add_widget(self.save_button)

                    self.save_button = Button(text="Загрузить", on_release=self.load_game)
                    self.save_menu.add_widget(self.save_button)

                self.back_button = Button(size_hint=0.15, text="Меню", on_release=self.back_btn_on_release)
                self.layout_buttons.add_widget(self.back_button)

    def update(self):
        if not self.game_stopped:
            if time.monotonic() - self.last_frame_time > self.update_interval:
                self.sim_field.calculate_next_gen()

                self._window.draw()

                self.last_frame_time += self.update_interval

    def toggle_on_release(self):
        game_stopped = not self.game_stopped

        if game_stopped:
            self.toggle.set_text("Продолжить")
            self.toggle.set_color((200, 100, 100))
        else:
            self.toggle.set_text("Остановить")
            self.toggle.set_color((100, 200, 100))

        self.game_stopped = game_stopped

        if not game_stopped:
            self.last_frame_time = time.monotonic()

    def gs_changer_scroll(self, value):
        self.fps_limit = max(1, self.fps_limit + value)
        self.update_interval = 1 / self.fps_limit
        self.last_frame_time = time.monotonic()
        self.game_speed_scroll_changer.set_text(f"{self.fps_limit} fps")

    def gs_btn_up_on_release(self):
        self.fps_limit += 1
        self.update_interval = 1 / self.fps_limit
        self.game_speed_scroll_changer.set_text(f"{self.fps_limit} fps")

    def gs_btn_down_on_release(self):
        self.fps_limit = max(1, self.fps_limit - 1)
        self.update_interval = 1 / self.fps_limit
        self.game_speed_scroll_changer.set_text(f"{self.fps_limit} fps")

    def clear_btn_on_release(self):
        self.sim_field.clear_sim_field()

    def add_brush_button(self, i):
        on_release = lambda: self.set_brush(i)

        self.brush_button = Button(text=self.brushes[i]["name"], on_release=on_release)
        self.brush_menu.add_widget(self.brush_button)

        if self.current_brush_index == i:
            color = [x * 0.8 for x in self.brush_button.get_color()]
            self.brush_button.set_color(color)

    def set_brush(self, i):
        color = [x * 0.8 for x in self.brush_menu.get_widgets()[i].get_color()]
        self.brush_menu.get_widgets()[i].set_color(color)

        color = [x * 1.25 for x in self.brush_menu.get_widgets()[self.current_brush_index].get_color()]
        self.brush_menu.get_widgets()[self.current_brush_index].set_color(color)

        self.sim_field.brush = self.brushes[i]["data"]
        self.current_brush_index = i

    def save_game(self):
        try:
            with open("save1.txt", mode="w") as file:
                file.write(str(self.sim_field.get_positions_of_alive_cells()))
        except FileNotFoundError:
            with open("save1.txt", mode="x") as file:
                file.write(str(self.sim_field.get_positions_of_alive_cells()))

    def load_game(self):
        try:
            with open("save1.txt") as file:
                string = file.readline()
                al_cells = set()

                if string != "set()":
                    num = False
                    num_value = ''
                    pos = []
                    for l in string:
                        if l == "(":
                            num = True

                        elif l == ",":
                            if num:
                                pos.append(int(num_value))
                                num_value = ''

                        elif l == ")":
                            pos.append(int(num_value))
                            al_cells.add(tuple(pos))
                            pos = []
                            num_value = ''
                            num = False

                        elif l == " ":
                            pass

                        elif num:
                            num_value += l

                self.sim_field.set_positions_of_alive_cells(al_cells)
        except FileNotFoundError:
            self.sim_field.set_positions_of_alive_cells(set())

    def back_btn_on_release(self):
        self._window.current_screen = self._window.main_menu
        if not self.game_stopped:
            self.toggle.on_release()


class SimulationField(Widget):
    possible_key_numbers = (pygame.K_UP, pygame.K_w,
                            pygame.K_LEFT, pygame.K_a,
                            pygame.K_DOWN, pygame.K_s,
                            pygame.K_RIGHT, pygame.K_d)
    offsets = ((-1, -1), (0, -1), (1, -1),
               (-1, 0), (1, 0),
               (-1, 1), (0, 1), (1, 1))

    def __init__(self, scale: int, camera_pos: list, size_hint=1):
        super().__init__(size_hint=size_hint)

        self._scale = scale
        self._camera_pos = camera_pos

        self.brush = ((0, 0),)
        self.rule = [(2, 3), (3,)]
        self._positions_of_alive_cells = set()

    @time_counter
    def draw(self, display: pygame.Surface):
        pygame.draw.rect(display, 0, self._shape, 0)

        for pos in self._positions_of_alive_cells:
            x = pos[0] - self._camera_pos[0]
            y = pos[1] - self._camera_pos[1]

            half_width = self._width // 2
            half_height = self._height // 2

            cuts, out_of_bound = self._check_for_cuts((x, y), half_width, half_height)

            if not out_of_bound:
                self._draw_cell((x, y), half_width, half_height, cuts, display)

    def on_release(self):
        mouse_pos = pygame.mouse.get_pos()
        mouse_on_cell_pos = ((self._camera_pos[0] - (self._width / 2 - mouse_pos[0] + self._pos[0] - 1) / self._scale) // 1,
                             (self._camera_pos[1] - (self._height / 2 - mouse_pos[1] + self._pos[1] - 1) / self._scale) // 1)

        for offset in self.brush:
            cell_pos = (int(mouse_on_cell_pos[0] + offset[0]), int(mouse_on_cell_pos[1] + offset[1]))
            if cell_pos in self._positions_of_alive_cells:
                self._positions_of_alive_cells.discard(cell_pos)
            else:
                self._positions_of_alive_cells.add(cell_pos)

    def scroll(self, value):
        self._scale = max(1, self._scale + value)

    def key_down(self, key_number):
        if key_number == pygame.K_UP or key_number == pygame.K_w:
            self._camera_pos[1] -= self._width / 20 / self._scale

        elif key_number == pygame.K_LEFT or key_number == pygame.K_a:
            self._camera_pos[0] -= self._width / 20 / self._scale

        elif key_number == pygame.K_DOWN or key_number == pygame.K_s:
            self._camera_pos[1] += self._width / 20 / self._scale

        elif key_number == pygame.K_RIGHT or key_number == pygame.K_d:
            self._camera_pos[0] += self._width / 20 / self._scale

    def set_positions_of_alive_cells(self, positions: set):
        self._positions_of_alive_cells = positions

    def get_positions_of_alive_cells(self):
        return self._positions_of_alive_cells

    @time_counter
    def calculate_next_gen(self):
        # Получает статистику о живых клетках рядом
        # 0 0 0 0 0 | 1 1 2 1 1
        # 0 1 0 1 0 | 1 0 2 0 1
        # 0 0 0 0 0 | 1 1 2 1 1
        stat = self._get_stat()  # -> dict {pos: count}

        new_positions = set()

        for item in stat.items():
            if item[1] in self.rule[1]:
                new_positions.add(item[0])
            elif item[1] in self.rule[0] and item[0] in self._positions_of_alive_cells:
                new_positions.add(item[0])

        self._positions_of_alive_cells = new_positions
        print(len(self._positions_of_alive_cells))

    def clear_sim_field(self):
        self._positions_of_alive_cells = set()

    def _check_for_cuts(self, pos: tuple, half_width: int, half_height: int):
        cuts = set()

        out_of_bound = False

        if pos[0] * self._scale < -half_width - self._scale:
            out_of_bound = True
        elif pos[0] * self._scale < -half_width:
            cuts.add(0)

        elif pos[0] * self._scale >= half_width:
            out_of_bound = True
        elif pos[0] * self._scale >= half_width - self._scale:
            cuts.add(1)

        if pos[1] * self._scale < -half_height - self._scale:
            out_of_bound = True
        elif pos[1] * self._scale < -half_height:
            cuts.add(2)

        elif pos[1] * self._scale >= half_height:
            out_of_bound = True
        elif pos[1] * self._scale >= half_height - self._scale:
            cuts.add(3)

        return cuts, out_of_bound

    def _draw_cell(self, pos: tuple, half_width: int, half_height: int, cuts: set, display: pygame.Surface):
        x = pos[0] * self._scale + half_width
        y = pos[1] * self._scale + half_height

        cell_width = self._scale
        cell_height = self._scale

        if 0 in cuts:
            cell_width = x + self._scale
            x = 0
        elif 1 in cuts:
            cell_width = math.ceil(half_width * 2 - x)

        if 2 in cuts:
            cell_height = y + self._scale
            y = 0
        elif 3 in cuts:
            cell_height = math.ceil(half_height * 2 - y)

        shape = pygame.Rect(x + self._pos[0], y + self._pos[1], cell_width, cell_height)
        pygame.draw.rect(display, (255, 255, 255), shape, 0)

    def _get_stat(self):
        stat = {}

        for pos in self._positions_of_alive_cells:
            for offset in self.offsets:
                new_pos = (pos[0] + offset[0], pos[1] + offset[1])
                if new_pos in stat:
                    stat[new_pos] += 1
                else:
                    stat[new_pos] = 1

        return stat


class MainMenu(Screen):
    def __init__(self, window: Window):
        super().__init__(window)

        self._play_button = Button(text="Играть", on_release=self._play_btn_on_release)
        self.add_widget(self._play_button)
        self._settings_button = Button(text="Настройки", on_release=self._settings_btn_on_release)
        self.add_widget(self._settings_button)
        self._exit_button = Button(text="Выход", on_release=self._exit_btn_on_release)
        self.add_widget(self._exit_button)

    def _play_btn_on_release(self):
        self._window.current_screen = self._window.game_screen

    def _settings_btn_on_release(self):
        self._window.current_screen = self._window.settings_menu

    @staticmethod
    def _exit_btn_on_release():
        pygame.quit()
        sys.exit()


class SettingsMenu(Screen):
    def __init__(self, window: Window):
        super().__init__(window)
        _standard_rules = dict(name="Стандартные правила", data=[(2, 3), (3,)])
        _high_life_rules = dict(name="Правила High Life", data=[(2, 3), (3,6)])
        _life_34_rules = dict(name="Правила 34 Life", data=[(3, 4), (3, 4)])
        self._rules = [_standard_rules, _high_life_rules, _life_34_rules]
        self._current_rules_index = 0

        for i in range(len(self._rules)):
            self._add_rules_btn(i)

        self._back_button = Button(text="Назад", on_release=self._back_btn_on_release)
        self.add_widget(self._back_button)

    def _add_rules_btn(self, rule_number):
        on_release = lambda: self._set_rule(rule_number)

        self.rules_btn = Button(text=self._rules[rule_number]["name"], on_release=on_release)
        self.add_widget(self.rules_btn)

        if self._current_rules_index == rule_number:
            color = [x * 0.8 for x in self.rules_btn.get_color()]
            self.rules_btn.set_color(color)

    def _set_rule(self, rule_number):
        color = [x * 0.8 for x in self.get_widgets()[rule_number].get_color()]
        self.get_widgets()[rule_number].set_color(color)

        color = [x * 1.25 for x in self.get_widgets()[self._current_rules_index].get_color()]
        self.get_widgets()[self._current_rules_index].set_color(color)

        self._window.game_screen.sim_field.rule = self._rules[rule_number]["data"]
        self._current_rules_index = rule_number

    def _back_btn_on_release(self):
        self._window.current_screen = self._window.main_menu


if __name__ == "__main__":
    pygame.init()
    clock = pygame.time.Clock()

    # ЛКМ - взаимодействие с объектами
    # Прокрутка колеса - изменение масштаба отображения | изменение скорости игры
    # WASD | стрелочки - управление камерой

    window_width = 1000
    window_height = 600

    window = Window(window_width, window_height)

    event_handler = EventHandler(window)

    while True:
        window.update()

        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                event_handler.key_down(event.dict["key"])

            if event.type == pygame.MOUSEBUTTONDOWN:
                event_handler.mouse_button_down(event.dict["button"])

            elif event.type == pygame.MOUSEBUTTONUP:
                event_handler.mouse_button_up(event.dict["button"])

            elif event.type == pygame.MOUSEWHEEL:
                event_handler.mouse_wheel(event.dict["y"])

            elif event.type == pygame.WINDOWLEAVE:
                event_handler.window_leave()

            elif event.type == pygame.VIDEORESIZE:
                event_handler.resize(event.dict["w"], event.dict["h"])

            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
