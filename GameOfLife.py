import math

import pygame
import sys
import time


class Window:
	def __init__(self, width, height, button_height, scale, game_stopped, camera_pos):
		display = pygame.display.set_mode((width, height))

		self.drawer = Drawer(display)

		self.sim_field = SimulationField((0, 0), width, height - button_height, scale, self.drawer, camera_pos)

		self.button_field = StopButton((0, height - button_height), width, button_height, self.drawer, game_stopped)

	def on_click(self, mouse_pos):
		if mouse_pos[1] < window_height - button_height:
			self.sim_field.on_click(mouse_pos)
		else:
			self.button_field.on_click()


class Drawer:
	def __init__(self, display):
		self.display = display

	def draw_button(self, pos, width, height, shape, game_stopped):

		font_size = 40
		font = pygame.font.SysFont('couriernew', font_size)

		if game_stopped:
			text = font.render(f"Продолжить", True, (255, 255, 255))
			pygame.draw.rect(self.display, (200, 100, 100), shape, 0)
		else:
			text = font.render(f"Остановить", True, (255, 255, 255))
			pygame.draw.rect(self.display, (100, 200, 100), shape, 0)

		place = text.get_rect(center=(pos[0] + width // 2, pos[1] + height // 2))
		self.display.blit(text, place)

	def draw_game_field(self, game_field_pos, width, height, scale, positions_of_live_cells, camera_pos):
		self.clear_game_field(game_field_pos, width, height)

		cell_size = scale

		for pos in positions_of_live_cells:
			x = pos[0] - camera_pos[0]
			y = pos[1] - camera_pos[1]

			half_width = width / 2
			half_height = height / 2

			out_of_bound = False

			cut = set()

			if x * cell_size < -half_width - cell_size:
				out_of_bound = True
			elif x * cell_size < -half_width:
				cut.add("left")

			elif x * cell_size >= half_width:
				out_of_bound = True
			elif x * cell_size >= half_width - cell_size:
				cut.add("right")

			if y * cell_size < -half_height - cell_size:
				out_of_bound = True
			elif y * cell_size < -half_height:
				cut.add("up")

			elif y * cell_size >= half_height:
				out_of_bound = True
			elif y * cell_size >= half_height - cell_size:
				cut.add("bottom")

			if not out_of_bound:
				self.draw_cell((x, y), cell_size, half_width, half_height, cut, game_field_pos)

	def draw_cell(self, pos, scale, half_width, half_height, cut, game_field_pos):
		x = pos[0] * scale + half_width
		y = pos[1] * scale + half_height

		cell_width = scale
		cell_height = scale

		if "left" in cut:
			cell_width = x + scale
			x = 0
		elif "right" in cut:
			cell_width = math.ceil(half_width * 2 - x)

		if "up" in cut:
			cell_height = y + scale
			y = 0
		elif "bottom" in cut:
			cell_height = math.ceil(half_height * 2 - y)

		shape = pygame.Rect(x + game_field_pos[0], y + game_field_pos[1], cell_width, cell_height)
		pygame.draw.rect(self.display, (255, 255, 255), shape, 0)

	def clear_game_field(self, pos, width, height):
		shape = pygame.Rect(pos[0], pos[1], width, height)
		pygame.draw.rect(self.display, 0, shape, 0)


class SimulationField:
	def __init__(self, pos, width, height, scale, drawer, camera_pos):
		self.pos = pos
		self.width = width
		self.height = height
		self.scale = scale
		self.camera_pos = camera_pos

		self.shape = pygame.Rect(pos[0], pos[1], width, height)

		self.drawer = drawer

		self.positions_of_alive_cells = set()

		self.drawer.draw_game_field(self.pos, self.width, self.height, self.scale, self.positions_of_alive_cells,
									self.camera_pos)

	def update(self, create_new_frame=True):
		if create_new_frame:
			self.calculate_next_gen()

		self.drawer.draw_game_field(self.pos, self.width, self.height, self.scale, self.positions_of_alive_cells,
									self.camera_pos)

	def calculate_next_gen(self):
		# Получает статистику о живых клетках рядом
		# 0 0 0 0 0 | 1 1 2 1 1
		# 0 1 0 1 0 | 1 0 2 0 1
		# 0 0 0 0 0 | 1 1 2 1 1
		stat = self.get_stat()  # -> dict {pos: count}

		new_positions = set()

		for item in stat.items():
			if item[1] == 3:
				new_positions.add(item[0])
			elif item[1] == 2:
				if item[0] in self.positions_of_alive_cells:
					new_positions.add(item[0])

		self.positions_of_alive_cells = new_positions

	def get_stat(self):
		stat = {}

		for pos in self.positions_of_alive_cells:
			stat = self.get_stat_for_cell(pos[0], pos[1], stat)

		return stat

	@staticmethod
	def get_stat_for_cell(x, y, stat):
		for x_offset in range(-1, 2):
			for y_offset in range(-1, 2):
				if y_offset == 0 and x_offset == 0:
					pass
				else:
					new_pos = (x + x_offset, y + y_offset)
					if new_pos in stat:
						stat[new_pos] += 1
					else:
						stat[new_pos] = 1

		return stat

	def on_click(self, mouse_pos):
		if mouse_pos[0] < self.pos[0] or mouse_pos[0] >= self.pos[0] + self.width:
			pass
		elif mouse_pos[1] < self.pos[1] or mouse_pos[1] >= self.pos[1] + self.height:
			pass
		else:
			cell_pos = ((self.camera_pos[0] - (self.width / 2 - mouse_pos[0] + self.pos[0] - 1) / self.scale) // 1,
						(self.camera_pos[1] - (self.height / 2 - mouse_pos[1] + self.pos[1] - 1) / self.scale) // 1)

			if cell_pos in self.positions_of_alive_cells:
				self.positions_of_alive_cells.discard(cell_pos)
			else:
				self.positions_of_alive_cells.add(cell_pos)

			self.update(create_new_frame=False)


class StopButton:
	def __init__(self, pos, width, height, drawer, game_stopped):
		self.pos = pos
		self.width = width
		self.height = height
		self.shape = pygame.Rect(pos[0], pos[1], width, height)
		self.game_stopped = game_stopped

		self.drawer = drawer

		self.drawer.draw_button(self.pos, self.width, self.height, self.shape, self.game_stopped)

	def on_click(self):
		self.game_stopped = not self.game_stopped

		self.drawer.draw_button(self.pos, self.width, self.height, self.shape, self.game_stopped)


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
		if not window.button_field.game_stopped:
			if time.monotonic() - last_frame_time > update_interval:
				window.sim_field.update(sim_field_scale)
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
					window.button_field.on_click()

				window.sim_field.update(create_new_frame=False)

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

				window.sim_field.update(create_new_frame=False)

			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

			pygame.display.flip()
