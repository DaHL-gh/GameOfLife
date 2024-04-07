import math

import pygame
import sys
import time


class Window:
	def __init__(self, width:int, height:int, button_height:int, scale:int, game_stopped:bool, camera_pos:list):
		display = pygame.display.set_mode((width, height))

		self.game_stopped = game_stopped

		self.sim_field = SimulationField((0, 0), width, height - button_height, scale, camera_pos)

		self.button = StopButton((0, height - button_height), width, button_height, game_stopped)

		self.drawer = Drawer(self, display)

	def on_click(self, mouse_pos:tuple):
		if mouse_pos[1] < window_height - button_height:
			self.sim_field.on_click(mouse_pos)
		else:
			self.game_stopped = self.button.on_click(self.game_stopped)


class Widget:
	def __init__(self, pos, width, height):
		self.__pos = pos
		self.__width = width
		self.__height = height
		self.__shape = pygame.Rect(pos[0], pos[1], width, height)

	def draw(self):
		pass

	def on_click(self):
		pass

	def is_mouse_on_object(self, mouse_pos:tuple):
		if mouse_pos[0] < self.__pos[0] or mouse_pos[0] >= self.__pos[0] + self.__width:
			return False
		elif mouse_pos[1] < self.__pos[1] or mouse_pos[1] >= self.__pos[1] + self.__height:
			return False
		else:
			return True


class Drawer:
	def __init__(self, window:Window, display:pygame.Surface):
		self.window = window
		self.display = display

		self.draw_button()
		self.draw_game_field()

	def draw_button(self):
		self.window.button.draw(self.display)

	def draw_game_field(self):
		self.window.sim_field.draw(self.display)




class SimulationField:
	def __init__(self, pos:tuple, width:int, height:int, scale:int, camera_pos:list):
		self.__pos = pos
		self.__width = width
		self.__height = height
		self.__scale = scale
		self.camera_pos = camera_pos

		self.__shape = pygame.Rect(pos[0], pos[1], width, height)

		self.__positions_of_alive_cells = set()

	def draw(self, display:pygame.Surface):
		pygame.draw.rect(display, 0, self.__shape, 0)

		for pos in self.__positions_of_alive_cells:
			x = pos[0] - self.camera_pos[0]
			y = pos[1] - self.camera_pos[1]

			half_width = self.__width / 2
			half_height = self.__height / 2

			cuts, out_of_bound = self.__check_for_cuts((x, y), half_width, half_height)

			if not out_of_bound:
				self.__draw_cell((x, y), half_width, half_height, cuts, display)

	def __check_for_cuts(self, pos:tuple, half_width:int, half_height:int):
		cuts = set()

		out_of_bound = False

		if pos[0] * self.__scale < -half_width - self.__scale:
			out_of_bound = True
		elif pos[0] * self.__scale < -half_width:
			cuts.add("left")

		elif pos[0] * self.__scale >= half_width:
			out_of_bound = True
		elif pos[0] * self.__scale >= half_width - self.__scale:
			cuts.add("right")

		if pos[1] * self.__scale < -half_height - self.__scale:
			out_of_bound = True
		elif pos[1] * self.__scale < -half_height:
			cuts.add("up")

		elif pos[1] * self.__scale >= half_height:
			out_of_bound = True
		elif pos[1] * self.__scale >= half_height - self.__scale:
			cuts.add("bottom")

		return cuts, out_of_bound

	def __draw_cell(self, pos:tuple, half_width:int, half_height:int, cuts:set, display:pygame.Surface):
		x = pos[0] * self.__scale + half_width
		y = pos[1] * self.__scale + half_height

		cell_width = self.__scale
		cell_height = self.__scale

		if "left" in cuts:
			cell_width = x + self.__scale
			x = 0
		elif "right" in cuts:
			cell_width = math.ceil(half_width * 2 - x)

		if "up" in cuts:
			cell_height = y + self.__scale
			y = 0
		elif "bottom" in cuts:
			cell_height = math.ceil(half_height * 2 - y)

		shape = pygame.Rect(x + self.__pos[0], y + self.__pos[1], cell_width, cell_height)
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

	def on_click(self, mouse_pos:tuple):
		cell_pos = ((self.camera_pos[0] - (self.__width / 2 - mouse_pos[0] + self.__pos[0] - 1) / self.__scale) // 1,
					(self.camera_pos[1] - (self.__height / 2 - mouse_pos[1] + self.__pos[1] - 1) / self.__scale) // 1)

		if cell_pos in self.__positions_of_alive_cells:
			self.__positions_of_alive_cells.discard(cell_pos)
		else:
			self.__positions_of_alive_cells.add(cell_pos)

	def is_mouse_on_object(self, mouse_pos:tuple):
		if mouse_pos[0] < self.__pos[0] or mouse_pos[0] >= self.__pos[0] + self.__width:
			return False
		elif mouse_pos[1] < self.__pos[1] or mouse_pos[1] >= self.__pos[1] + self.__height:
			return False
		else:
			return True


class StopButton:
	def __init__(self, pos:tuple, width:int, height:int, game_stopped:bool):
		self.__pos = pos
		self.__width = width
		self.__height = height
		self.__shape = pygame.Rect(pos[0], pos[1], width, height)

		self.__font_size = 40
		self.__change_text_and_color(game_stopped)

	def draw(self, display:pygame.Surface):
		font = pygame.font.SysFont('couriernew', self.__font_size)

		widget_text = font.render(self.__text, True, (255, 255, 255))
		place = widget_text.get_rect(center=(self.__pos[0] + self.__width // 2, self.__pos[1] + self.__height // 2))

		pygame.draw.rect(display, self.__color, self.__shape, 0)
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

	def check_for_mouse_pos(self, mouse_pos:tuple):
		if mouse_pos[0] < self.__pos[0] or mouse_pos[0] >= self.__pos[0] + self.__width:
			return False
		elif mouse_pos[1] < self.__pos[1] or mouse_pos[1] >= self.__pos[1] + self.__height:
			return False
		else:
			return True


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
	button_height = 50

	pause_from_start = True

	window = Window(window_width, window_height, button_height, sim_field_scale, pause_from_start, camera_position)

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
					pass

				window.drawer.draw_game_field()

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

				window.drawer.draw_game_field()
				window.drawer.draw_button()


			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

			pygame.display.flip()