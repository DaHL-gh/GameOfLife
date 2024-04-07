import math

import pygame
import sys
import time
import math


class Window:
	def __init__(self, width, height, button_height, scale, game_stopped):
		display = pygame.display.set_mode((width, height))

		self.drawer = Drawer(display)

		self.sim_field = SimulationField(width, height - button_height, scale, self.drawer)

		self.game_stopped = game_stopped
		self.button_field = StopButton(width, button_height, height - button_height, game_stopped)

	def on_click(self, mouse_pos):
		if mouse_pos[1] < window_height - button_height:
			self.sim_field.on_click(mouse_pos)
		else:
			self.game_stopped = not self.game_stopped
			self.button_field.on_click(self.game_stopped)


class Drawer:
	def __init__(self, display):
		self.display = display

	def draw_game_field(self, positions_of_live_cells, scale, width, height):
		cell_size = scale

		for pos in positions_of_live_cells:
			x = pos[0] - camera_pos[0]
			y = pos[1] - camera_pos[1]
			if (y + 1) * scale <= height:
				self.draw_cell((x, y), cell_size, width, height)
			else:
				self.draw_cut_cell((x, y), cell_size, width, height)

	def draw_cut_cell(self, pos, cell_size, width, height):
		shape = pygame.Rect(pos[0] * cell_size + width // 2, pos[1] * cell_size, cell_size + height // 2, height - pos[1] * cell_size)
		pygame.draw.rect(self.display, (255, 255, 255), shape, 0)

	def draw_cell(self, pos, cell_size, width, height):
		shape = pygame.Rect(pos[0] * cell_size + width // 2, pos[1] * cell_size + height // 2, cell_size, cell_size)
		pygame.draw.rect(self.display, (255, 255, 255), shape, 0)

	def clear_game_field(self, width, height):
		shape = pygame.Rect(0, 0, width, height)
		pygame.draw.rect(self.display, 0, shape, 0)


class SimulationField:
	def __init__(self, width, height, scale, drawer):
		self.width = width
		self.height = height
		self.scale = scale
		self.shape = pygame.Rect(0, 0, width, height)
		self.drawer = drawer

		self.positions_of_alive_cells = {(0, 1), (0, 2), (0, 3)}

		self.drawer.draw_game_field(self.positions_of_alive_cells, self.scale, self.width, self.height)

	def set_new_scale(self, scale):
		self.scale = scale

	def update(self, create_new_frame=True):
		self.drawer.clear_game_field(self.width, self.height)

		if create_new_frame:
			self.calculate_next_gen()

		self.drawer.draw_game_field(self.positions_of_alive_cells, self.scale, self.width, self.height)

	def calculate_next_gen(self):
		# Получает статистику о живых клетках рядом
		# 0 0 0 0 0 | 1 1 2 1 1
		# 0 1 0 1 0 | 1 0 2 0 1
		# 0 0 0 0 0 | 1 1 2 1 1
		stat = self.get_stat()  # -> dict {pos: count}

		new_positions = set()

		for position in stat.items():
			if position[1] == 3:
				new_positions.add(position[0])
			elif position[1] == 2:
				if position[0] in self.positions_of_alive_cells:
					new_positions.add(position[0])

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
		cell_pos = ((mouse_pos[0] - self.width // 2 + camera_pos[0] * self.scale) // self.scale , (mouse_pos[1] - self.height // 2 + camera_pos[1] * self.scale) // self.scale)

		if cell_pos in self.positions_of_alive_cells:
			self.positions_of_alive_cells.discard(cell_pos)
		else:
			self.positions_of_alive_cells.add(cell_pos)

		self.update(create_new_frame=False)


class StopButton:
	def __init__(self, width, height, vertical_offset, game_stopped):
		self.width = width
		self.height = height
		self.vertical_offset = vertical_offset
		self.shape = pygame.Rect(0, vertical_offset, width, height)

		self.on_click(game_stopped)

	def stop_sign(self):
		screen = pygame.display.get_surface()
		r = pygame.Rect(0, self.vertical_offset, self.width, self.height)
		pygame.draw.rect(screen, (100, 200, 100), r, 0)

		font_size = 40
		font = pygame.font.SysFont('couriernew', font_size)
		text = font.render(f"Остановить", True, (255, 255, 255))
		place = text.get_rect(center=(self.width // 2, self.vertical_offset + self.height // 2), )
		screen.blit(text, place)

	def ongoing_sign(self):
		screen = pygame.display.get_surface()
		r = pygame.Rect(0, self.vertical_offset, self.width, self.height)
		pygame.draw.rect(screen, (200, 100, 100), r, 0)

		font_size = 40
		font = pygame.font.SysFont('couriernew', font_size)
		text = font.render(f"Продолжить", True, (255, 255, 255))
		place = text.get_rect(center=(self.width // 2, self.vertical_offset + self.height // 2), )
		screen.blit(text, place)

	def on_click(self, game_stopped):
		if game_stopped:
			self.ongoing_sign()
		else:
			self.stop_sign()

		return not game_stopped


if __name__ == "__main__":
	pygame.init()

	sim_field_scale = 10
	camera_pos = [-1, 1]

	window_width = 1600
	window_height = 900
	button_height = 100

	game_stopped = True

	window = Window(window_width, window_height, button_height, sim_field_scale, game_stopped)

	time_start = time.monotonic()

	fps = 10
	update_interval = 1 / fps

	while True:
		if not window.game_stopped:
			if time.monotonic() - time_start > update_interval:
				window.sim_field.update(sim_field_scale)
				pygame.display.flip()

				time_start = time.monotonic()

		for event in pygame.event.get():
			if event.type == pygame.KEYDOWN:
				if event.dict["key"] == pygame.K_UP or event.dict["key"] == pygame.K_w:
					camera_pos[1] -= 10 / math.pow(sim_field_scale, 1/3)

				elif event.dict["key"] == pygame.K_LEFT or event.dict["key"] == pygame.K_a:
					camera_pos[0] -= 10 / math.pow(sim_field_scale, 1/3)

				elif event.dict["key"] == pygame.K_DOWN or event.dict["key"] == pygame.K_s:
					camera_pos[1] += 10 / math.pow(sim_field_scale, 1/3)

				elif event.dict["key"] == pygame.K_RIGHT or event.dict["key"] == pygame.K_d:
					camera_pos[0] += 10 / math.pow(sim_field_scale, 1/3)

				window.sim_field.update(create_new_frame=False)

			if event.type == pygame.MOUSEBUTTONUP:
				if event.dict["button"] == 1:
					window.on_click(pygame.mouse.get_pos())

				elif event.dict["button"] == 4:
					sim_field_scale += 1
					window.sim_field.set_new_scale(sim_field_scale)

				elif event.dict["button"] == 5:
					sim_field_scale -= 1
					sim_field_scale = max(1, sim_field_scale)
					window.sim_field.set_new_scale(sim_field_scale)

				window.sim_field.update(create_new_frame=False)

			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

			pygame.display.flip()