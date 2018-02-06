import sys
import numpy
from numpy import random

# 

# there are turns: the board and the player



# the player only has one move: connect two gems

# the board does:
# step 1: do action player initiated
# 1) if 3 are next to each other, remove them and add score.
# 2) if 4 are next to each other, remove, place with stripe thing where connection was made
# 3) if 5 are next to each other, remove, place with magic thing where connection was made
# 4) if 5 are in a corner to each other, remove, place bomb thing where connection was made
# 5) if magic thing touched color, activate all of those
# 6) if magic thing touched stripe, replace all of those color with stripe, activate them
# 7) if magic thing touched bomb, replace all of those color with bombs, activate them
# 8) if magic thing touched magic thing, activate all on the board

# activation of gems: 
#   - if normal gem, remove
#   - if stripe gem, destroy row
#   - if bomb gem, two phases: destroy 9x9 around it, wait, again.
#   - if magic gem, 

# types of objects:

field_type = {
	-1: 'non-field',
	0: 'empty',
	1: 'simple',
	2: 'stripeH',
	3: 'stripeV',
	4: 'bomb',
	5: 'zapper',
}
field_color = {
	0: 'colorless',
	1: 'blue',
	2: 'red',
	3: 'green',
	4: 'orange',
	5: 'yellow',
	6: 'brown'
}
field_status = {
	0: 'normal',
	1: 'locked', 
	2: 'double-locked',
}


class Board(object):
	def __init__(self, nrows=10, ncols=10):
		self.shape = (nrows,ncols)
		self.type = numpy.zeros(self.shape)
		self.color = numpy.zeros(self.shape)
		self.status = numpy.zeros(self.shape)
	
	def __str__(self):
		#return 'BOARD:'
		t = 'BOARD: %dx%d\n' % (self.type.shape)
		for rowtype, rowcolor, rowstatus in zip(self.type, self.color, self.status):
			for type, color, status in zip(rowtype, rowcolor, rowstatus):
				if type == -1:
					t += ' X'
				elif type == 0:
					if status == 2:
						t += ' B'
					elif status == 1:
						t += ' b'
					else:
						t += '  '
				elif type == 1:
					t += ' %d' % color
				elif type == 2:
					t += '=%d' % color
				elif type == 3:
					t += '|%d' % color
				elif type == 4:
					t += 'X%d' % color
				elif type == 5:
					t += ' #'
			t += '\n'
		return t

class InitialFiller(object):
	"""
	Fill the board at the start.
	"""
	def __init__(self, board, unusable_fraction=0.0, 
		double_locked_rows=0, double_locked_cols=0):
		self.board = board
		self.double_locked_rows = double_locked_rows
		self.double_locked_cols = double_locked_cols
		self.unusable_fraction = unusable_fraction
	
	def run(self):
		# mark some squares as out-of-service
		nrows, ncols = self.board.type.shape
		if not self.unusable_fraction == 0:
			raise NotImplementedError()
		
		# choose some columns and rows at random and mark them as out-of-service
		nrows_disable = int(random.uniform(0, self.unusable_fraction*nrows))
		ncols_disable = int(random.uniform(0, self.unusable_fraction*ncols))
		left_disable = random.choice(numpy.arange(ncols), size=ncols_disable, replace=False)
		right_disable = ncols - left_disable - 1
		bottom_disable = random.choice(numpy.arange(nrows), size=nrows_disable, replace=False)
		top_disable = nrows - bottom_disable - 1
		
		board.type[:,tuple(top_disable)] = -1
		board.type[:,tuple(bottom_disable)] = -1
		board.type[tuple(top_disable),:] = -1
		board.type[tuple(bottom_disable),:] = -1
		
		# mark some squares as locked
		# the strategy is to do this symmetrically horizontally
		board.status[:,:self.double_locked_cols] = 2
		board.status[:,ncols-self.double_locked_cols:] = 2
		#board.status[:self.double_locked_rows,:] = 2
		board.status[nrows-self.double_locked_rows:,:] = 2
		return True

class TopFiller(object):
	def __init__(self, board, ncolors, locked_empty_fraction=0.0):
		self.board = board
		self.ncolors = ncolors
		self.locked_empty_fraction = locked_empty_fraction
	def run(self):
		nrows, ncols = board.shape
		changed = False
		# handle empty cells:
		for i in range(ncols):
			if board.type[0,i] == 0 and board.status[0,i] == 0:
				if random.uniform() < self.locked_empty_fraction:
					board.type[0,i] = 0
					board.color[0,i] = 0
					board.status[0,i] = 1
				else:
					board.type[0,i] = 1
					board.color[0,i] = 1 + random.randint(self.ncolors)
					board.status[0,i] = 1
				changed = True
		return changed

class BoardGravityPuller(object):
	def __init__(self, board):
		self.board = board
	
	def drop(self, fromj,fromi, toj,toi):
		board.type[toj, toi] = board.type[fromj, fromi]
		board.color[toj, toi] = board.color[fromj, fromi]
		board.status[toj, toi] = board.status[fromj, fromi]
		# mark origin as empty
		board.type[fromj, fromi] = 0
		board.color[fromj, fromi] = 0
		board.status[fromj, fromi] = 0
		
	def run(self):
		nrows, ncols = board.shape
		# handle empty cells starting from below:
		changed = False
		for j in list(range(1,nrows))[::-1]:
			for i in range(ncols):
				if board.type[j,i] == 0 and board.status[j,i] == 0:
					# this field is empty
					# check if field above (or otherwise to the side is filled and can fall)
					if board.type[j-1,i] > 0:
						self.drop(j-1,i,j,i)
						changed = True
						continue
					left = random.randint(2) * 2 - 1
					right = -left
					if 0 <= i+left < ncols and board.type[j-1,i+left] > 0:
						self.drop(j-1,i+left,j,i)
						changed = True
						continue
					elif 0 <= i+right < ncols and board.type[j-1,i+right] > 0:
						self.drop(j-1,i+right,j,i)
						changed = True
						continue
		return changed


class Combiner(object):
	SHAPES = [
"""H3
111
""",
"""H4
1111
""",
"""H5
11111
""",
"""V3
1
1
1
""",
"""V4
1
1
1
""",
"""V5
1
1
1
1
1
""",
"""TVD
111
010
010
""",
"""TVU
010
010
111
""",
"""THR
100
111
100
""",
"""THL
001
111
001
""",
	]
	
	def __init__(self, board):
		self.board = board
		self.patterns = []
		for shapestr in Combiner.SHAPES:
			shapeparts = shapestr.split('\n')[:-1]
			name = shapeparts[0]
			shapeparts = shapeparts[1:]
			nrows = len(shapeparts)
			ncols = len(shapeparts[0])
			maskarr = numpy.array([[c=='1' for c in shaperow] for shaperow in shapeparts])
			assert maskarr.shape == (nrows, ncols)
				self.patterns.append((name, maskarr))
		self.fromj, self.fromi = None, None
		self.toj, self.toi = None, None
	
	def set_last_interaction(self, fromj,fromi, toj,toi):
		self.fromj, self.fromi = fromj, fromi
		self.toj, self.toi = toj, toi
	
	
	def run(self):
		nrows, ncols = self.board.shape
		matches = []
		changed = False
		# find longest sequences of gems
		for j in range(nrows):
			for i in range(ncols):
				# apply mask here, if possible
				for name, mask in self.patterns:
					mrows, mcols = mask.shape
					if j + mrows >= nrows or i + mcols >= ncols:
						continue
					matched_type = board.type[j:j+mrows,i:i+mcols][mask]
					if not (matched_type > 0).all():
						# some non-fields or empty fields
						continue
					matched_color = board.color[j:j+mrows,i:i+mcols][mask]
					if not (matched_color == matched_color[0]).all():
						# not all have the same color
						continue
					boardmask = numpy.pad(mask, ((j,nrows-mrows-j), (i,ncols-mcols-i)), 'constant', constant_values=True)
					assert boardmask.shape == self.board.shape
					matches.append((j, i, name, matched_color, boardmask))
		
		# check for conflicts
		matches_accepted = []
		# if two matches affect the same idx, always choose the longer one
		for i, match in enumerate(matches):
			j, i, name, matched_color, mask = match
			any_conflicts = False
			for match in matches[:i]:
				j2, i2, name2, matched_color2, mask2 = match
				if numpy.logical_and(mask, mask2).any() and mask2.sum() >= mask.sum():
					# conflict
					any_conflicts = True
			
			if not any_conflicts:
				matches_accepted.append(match)
		
		# if two matches have the same length
		
		return changed

if __name__ == '__main__':
	board = Board()
	print board
	InitialFiller(board, double_locked_rows=2, double_locked_cols=2).run()
	print board
	grav = BoardGravityPuller(board)
	topfill = TopFiller(board, ncolors=3)
	while True:
		anychange = grav.run()
		print board
		anychange += topfill.run()
		print board
		if not anychange:
			break
		
	
	


