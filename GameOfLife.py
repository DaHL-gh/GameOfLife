import math

import pygame
import sys
import time


class Window:
	def __init__(self, width:int, height:int, buttons_height:int, toggle_width:int, scale:int, game_stopped:bool, camera_pos:list):
		display = pygame.display.set_mode((width, height))

		self.game_stopped = game_stopped

		self.sim_field = SimulationField((0, 0), width, height - buttons_height, scale, camera_pos)

		self.toggle = GameToggle((0, height - buttons_height), toggle_width, buttons_height, game_stopped)

		self.clear_button = ClearButton((toggle_width, height - buttons_height), width - toggle_width, buttons_height)

		self.drawer = Drawer(self, display)

	def on_click(self, mouse_pos:tuple):
		if self.sim_field.is_mouse_on_object(mouse_pos):
			self.sim_field.on_click(mouse_pos)

		elif self.toggle.is_mouse_on_object(mouse_pos):
			self.game_stopped = self.toggle.on_click(self.game_stopped)

		elif self.clear_button.is_mouse_on_object(mouse_pos):
			self.clear_button.on_click(self.sim_field)


class Widget:
	def __init__(self, pos:tuple, width:int, height:int):
		self._pos = pos
		self._width = width
		self._height = height
		self._shape = pygame.Rect(pos[0], pos[1], width, height)

	def draw(self, display:pygame.Surface):
		pass

	def is_mouse_on_object(self, mouse_pos:tuple):
		return self._shape.collidepoint(mouse_pos)



class Drawer:
	def __init__(self, window:Window, display:pygame.Surface):
		self.window = window
		self.display = display

		self.draw_screen()

	def draw_screen(self):
		self.window.toggle.draw(self.display)
		self.window.sim_field.draw(self.display)
		self.window.clear_button.draw(self.display)

	def draw_buttons(self):
		self.window.toggle.draw(self.display)
		self.window.clear_button.draw(self.display)

	def draw_game_field(self):
		self.window.sim_field.draw(self.display)




class SimulationField(Widget):
	def __init__(self, pos:tuple, width:int, height:int, scale:int, camera_pos:list):
		super().__init__(pos, width, height)

		self.scale = scale
		self.camera_pos = camera_pos

		self.__positions_of_alive_cells = set()

	def draw(self, display:pygame.Surface):
		pygame.draw.rect(display, 0, self._shape, 0)

		for pos in self.__positions_of_alive_cells:
			x = pos[0] - self.camera_pos[0]
			y = pos[1] - self.camera_pos[1]

			half_width = self._width / 2
			half_height = self._height / 2

			cuts, out_of_bound = self.__check_for_cuts((x, y), half_width, half_height)

			if not out_of_bound:
				self.__draw_cell((x, y), half_width, half_height, cuts, display)

	def __check_for_cuts(self, pos:tuple, half_width:int, half_height:int):
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

	def __draw_cell(self, pos:tuple, half_width:int, half_height:int, cuts:set, display:pygame.Surface):
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

	def __get_stat(self):
		stat = {}

		for pos in self.__positions_of_alive_cells:
			for x_offset in range(-1, 2):
				for y_offset in range(-1, 2):
					if y_offset == 0 and x_offset == 0:
						pass
					else:
						new_pos = (pos[0] + x_offset, pos[1] + y_offset)
						if new_pos in stat:
							stat[new_pos] += 1
						else:
							stat[new_pos] = 1

		return stat

	def clear_sim_field(self):
		self.__positions_of_alive_cells = set()

	def on_click(self, mouse_pos:tuple):
		cell_pos = ((self.camera_pos[0] - (self._width / 2 - mouse_pos[0] + self._pos[0] - 1) / self.scale) // 1,
					(self.camera_pos[1] - (self._height / 2 - mouse_pos[1] + self._pos[1] - 1) / self.scale) // 1)

		if cell_pos in self.__positions_of_alive_cells:
			self.__positions_of_alive_cells.discard(cell_pos)
		else:
			self.__positions_of_alive_cells.add(cell_pos)


class GameToggle(Widget):
	def __init__(self, pos:tuple, width:int, height:int, game_stopped:bool):
		super().__init__(pos, width, height)

		self.__font_size = 40
		self.__change_text_and_color(game_stopped)

	def draw(self, display:pygame.Surface):
		font = pygame.font.SysFont('couriernew', self.__font_size)

		widget_text = font.render(self.__text, True, (255, 255, 255))
		place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

		pygame.draw.rect(display, self.__color, self._shape, 0)
		display.blit(widget_text, place)

	def __change_text_and_color(self, game_stopped:bool):
		if game_stopped:
			self.__text = "Продолжить"
			self.__color = (200, 100, 100)
		else:
			self.__text = "Остановить"
			self.__color = (100, 200, 100)

	def on_click(self, game_stopped:bool):
		game_stopped = not game_stopped

		self.__change_text_and_color(game_stopped)

		return game_stopped


class ClearButton(Widget):
	def __init__(self, pos:tuple, width:int, height:int):
		super().__init__(pos, width, height)
		self.__color = (100, 100, 100)
		self.__font_size = 20
		self.__text = "Clear"

	def draw(self, display:pygame.Surface):
		font = pygame.font.SysFont('couriernew', self.__font_size)

		widget_text = font.render(self.__text, True, (255, 255, 255))
		place = widget_text.get_rect(center=(self._pos[0] + self._width // 2, self._pos[1] + self._height // 2))

		pygame.draw.rect(display, self.__color, self._shape, 0)
		display.blit(widget_text, place)

	def on_click(self, sim_field:SimulationField):
		sim_field.clear_sim_field()


if __name__ == "__main__":
	pygame.init()

	# ЛКМ - взаимодействие с объектами
	# Прокрутка колеса - изменение масштаба отображения
	# WASD | стрелочки - управление камерой
	# Пробел - вкл/выкл паузу

	sim_field_scale = 10
	camera_position = [0, 0]

	window_width = 1600
	window_height = 900
	buttons_height = 50
	toggle_width = 1500

	pause_from_start = True

	window = Window(window_width, window_height, buttons_height, toggle_width, sim_field_scale, pause_from_start, camera_position)

	last_frame_time = time.monotonic()

	fps = 30
	update_interval = 1 / fps

	while True:
		if not window.game_stopped:
			if time.monotonic() - last_frame_time > update_interval:
				window.sim_field.calculate_next_gen()
				window.drawer.draw_game_field()

				pygame.display.flip()

				last_frame_time = time.monotonic()

		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.dict["key"] == pygame.K_UP or event.dict["key"] == pygame.K_w:
					window.sim_field.camera_pos[1] -= window_width / 20 / sim_field_scale

				elif event.dict["key"] == pygame.K_LEFT or event.dict["key"] == pygame.K_a:
					window.sim_field.camera_pos[0] -= window_width / 20 / sim_field_scale

				elif event.dict["key"] == pygame.K_DOWN or event.dict["key"] == pygame.K_s:
					window.sim_field.camera_pos[1] += window_width / 20 / sim_field_scale

				elif event.dict["key"] == pygame.K_RIGHT or event.dict["key"] == pygame.K_d:
					window.sim_field.camera_pos[0] += window_width / 20 / sim_field_scale

				elif event.dict["key"] == pygame.K_SPACE:
					window.game_stopped = window.toggle.on_click(window.game_stopped)

				window.drawer.draw_screen()

			if event.type == pygame.MOUSEBUTTONUP:
				if event.dict["button"] == 1:
					window.on_click(pygame.mouse.get_pos())

				elif event.dict["button"] == 4:
					sim_field_scale += 1

					window.sim_field.scale = sim_field_scale

				elif event.dict["button"] == 5:
					sim_field_scale -= 1
					sim_field_scale = max(1, sim_field_scale)

					window.sim_field.scale = sim_field_scale

				window.drawer.draw_screen()


			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

			pygame.display.flip()