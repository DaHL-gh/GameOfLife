import pygame
import sys
import time


class Window:
	def __init__(self, width, height, cell_size, button_height):
		pygame.display.set_mode((width, height))

		self.game_stopped = False
		self.sim_field = Simulation_Field(width, height - button_height, cell_size)

		self.button_field = Stop_Button(width, button_height, height - button_height)

	def update(self):
		if not self.game_stopped:
			self.sim_field.generate_next_gen_matrix()

	def on_click(self, mouse_pos, pressed_buttons):
		if mouse_pos[1] < self.sim_field.height:
			self.sim_field.on_click(mouse_pos, pressed_buttons)
		else:
			if pressed_buttons[0]:
				self.game_stopped = self.button_field.on_click(self.game_stopped)


class Simulation_Field:
	def __init__(self, width, height, cell_size):
		self.width = width
		self.height = height
		self.shape = pygame.Rect(0, 0, self.width, self.height)

		self.cell_size = cell_size
		self.matrix_width = width // cell_size
		self.matrix_height = height // cell_size
		self.matrix_sizes = (self.matrix_width, self.matrix_height)

		self.game_matrix = [[Cell((x, y), cell_size) for x in range(self.matrix_width)] for y in range(self.matrix_height)]

	def on_click(self, mouse_pos, pressed_buttons):
		x = mouse_pos[0] // cell_size
		y = mouse_pos[1] // cell_size

		if pressed_buttons[0]:
			self.game_matrix[y][x].revive_cell()
		elif pressed_buttons[2]:
			self.game_matrix[y][x].kill_cell()

	def generate_next_gen_matrix(self):
		next_gen_matrix = [[None for _ in range(self.matrix_sizes[0])] for _ in range(self.matrix_sizes[1])]

		self.clear_field()

		for x in range(self.matrix_sizes[1]):
			for y in range(self.matrix_sizes[0]):
				next_gen_matrix[x][y] = self.game_matrix[x][y].compute_next_gen_cell(self.game_matrix)

		self.game_matrix = next_gen_matrix

	def clear_field(self):
		pygame.draw.rect(pygame.display.get_surface(), 0, self.shape, 0)

	def print_matrix(self):
		for x in self.game_matrix:
			for y in x:
				print(y.count_alive_neighbors(self.game_matrix), end=" ")
			print()

		for x in self.game_matrix:
			for y in x:
				print(y.is_alive, end=" ")
			print()


class Cell:
	def __init__(self, cords, size, is_alive=False):
		self.is_alive = is_alive
		self.cords = cords
		self.size = size
		self.shape = pygame.Rect(self.cords[0] * self.size, self.cords[1] * self.size, self.size, self.size)

		if is_alive:
			self.revive_cell()

	def count_alive_neighbors(self, matrix_of_game):
		count = 0

		x_len = len(matrix_of_game[0])
		y_len = len(matrix_of_game)

		x = self.cords[0]
		y = self.cords[1]

		for x_offset in range(-1, 2):
			for y_offset in range(-1, 2):
				if x_offset == 0 and y_offset == 0:
					pass
				elif matrix_of_game[(y + y_offset + y_len) % y_len][(x + x_offset + x_len) % x_len].is_alive:
					count += 1

		return count

	def compute_next_gen_cell(self, matrix_of_game):
		count = self.count_alive_neighbors(matrix_of_game)

		if self.is_alive and (count == 2 or count == 3):
			new_state = True
		elif count == 3:
			new_state = True
		else:
			new_state = False

		return Cell(self.cords, self.size, new_state)

	def revive_cell(self):
		self.is_alive = True
		pygame.draw.rect(pygame.display.get_surface(), (255, 255, 255), self.shape, 0)

	def kill_cell(self):
		self.is_alive = False
		pygame.draw.rect(pygame.display.get_surface(), 0, self.shape, 0)


class Stop_Button:
	def __init__(self, width, height, vertical_offset):
		self.width = width
		self.height = height
		self.vertical_offset = vertical_offset
		self.shape = pygame.Rect(0, vertical_offset, width, height)

		self.stop_sign()

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
			self.stop_sign()
		else:
			self.ongoing_sign()

		return not game_stopped


if __name__ == "__main__":
	pygame.init()

	# ЛКМ - создать клетку
	# ПКМ - удалить клетку
	cell_size = 20
	x_cell_count = 20
	y_cell_count = 20
	button_height = 100

	window = Window(cell_size * x_cell_count, cell_size * y_cell_count + button_height, cell_size, button_height)

	time_start = time.monotonic()
	update_interval = 0.1

	while True:
		if time.monotonic() - time_start > update_interval:
			window.update()
			pygame.display.flip()
			time_start = time.monotonic()

		for event in pygame.event.get():
			if event.type == pygame.MOUSEBUTTONDOWN:
				pressed_buttons = pygame.mouse.get_pressed()

			if event.type == pygame.MOUSEBUTTONUP:
				window.on_click(pygame.mouse.get_pos(), pressed_buttons)

			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()

			pygame.display.flip()