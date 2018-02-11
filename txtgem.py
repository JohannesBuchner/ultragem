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
	-1: 'exploding',
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
					t += '# '
				if status == 2:
					s = 'L'
				elif status == 1:
					s = 'l'
				else:
					s = ' '
				t += '%s ' % s
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
	"""
	Refills the board from the top, if there are empty fields
	"""
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
					# locked, colorless
					board.type[0,i] = 0
					board.color[0,i] = 0
					board.status[0,i] = 1
				else:
					# normal, not locked, simple things
					board.type[0,i] = 1
					board.color[0,i] = 1 + random.randint(self.ncolors)
					board.status[0,i] = 0
				changed = True
		return changed

class BoardGravityPuller(object):
	"""
	Makes gems fall down if there are empty fields below
	"""
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
					if board.type[j-1,i] == 0 and board.status[j-1,i] == 0:
						# above is also empty
						continue
					if board.type[j-1,i] > 0:
						self.drop(j-1,i,j,i)
						changed = True
						continue
					left = random.randint(2) * 2 - 1
					right = -left
					assert left in [-1,1], left
					assert right in [-1,1], right
					assert left != right, (left,right)
					# maybe down-left/down-right dropping should only be allowed if
					# the neighbor is filled (supported)
					if 0 <= i+left < ncols and board.type[j-1,i+left] > 0 and board.type[j,i+left] > 0:
						self.drop(j-1,i+left,j,i)
						changed = True
						continue
					elif 0 <= i+right < ncols and board.type[j-1,i+right] > 0 and board.type[j,i+right] > 0:
						self.drop(j-1,i+right,j,i)
						changed = True
						continue
					#elif 0 <= i+left < ncols and board.type[j-1,i+left] > 0 and 0 <= i+right < ncols and board.type[j-1,i+right] > 0:
						#print 'not dropping to', j,i,',',board.type[j,i+left],board.type[j,i+right]
						
		return changed

class Activater(object):
	"""
	When gems are marked for activation, explodes them based on their type
	"""
	def __init__(self, board):
		self.board = board
	
	def run(self):
		mask = self.board.status == -1
		nrows, ncols = self.board.shape
		rows, cols = numpy.where(mask)
		changed = False
		nchanged = 0
		#print 'candidates for activation:'
		#print mask*1
		idx = numpy.arange(len(rows))
		numpy.random.shuffle(idx)
		for j, i in zip(rows[idx], cols[idx]):
			# deal with that one
			#print j,i, j.shape,i.shape
			affects_surrounding = False
			type = self.board.type[j,i]
			if type == 5:
				# choose a random color and mark those for explosion
				colors = numpy.unique(self.board.color)
				color = numpy.random.choice(colors[colors > 0])
				mask = self.board.color == color
				affects_surrounding = True
			elif type == 4:
				# explode 3x3
				loj, hij = max(0, j-1), min(nrows, j+2)
				loi, hii = max(0, i-1), min(ncols, i+2)
				mask = numpy.zeros(self.board.shape, dtype=bool)
				mask[loj:hij,loi:hii] = True
				affects_surrounding = True
			elif type == 3:
				# explode vertically
				mask = numpy.zeros(self.board.shape, dtype=bool)
				mask[Ellipsis,i] = True
			elif type == 2:
				# explode horizontally
				mask = numpy.zeros(self.board.shape, dtype=bool)
				mask[j,Ellipsis] = True
			elif type == 1:
				# simply remove. 
				mask = numpy.zeros(self.board.shape, dtype=bool)
				mask[j,i] = True
				# But decrease surrounding status.
				affects_surrounding = True
			elif type == 0:
				continue
			
			#print mask*1, 'activating, type %d' % type
			# remove this one
			self.board.status[j,i] = 0
			self.board.color[j,i] = 0
			self.board.type[j,i] = 0

			mask_locked = numpy.logical_and(mask, self.board.status > 0)
			mask_notlocked = numpy.logical_and(mask, self.board.status == 0)
			nchanged += mask_locked.sum()
			self.board.status[mask_locked] = self.board.status[mask_locked] - 1
			mask_notlocked_simple = numpy.logical_and(mask_notlocked, self.board.type == 1)
			nchanged += mask_notlocked_simple.sum()
			self.board.type[mask_notlocked_simple] = 0
			self.board.color[mask_notlocked_simple] = 0
			# mark special ones for explosion
			mask_notlocked_complex = numpy.logical_and(mask_notlocked, self.board.type > 1)
			nchanged += mask_notlocked_complex.sum()
			self.board.status[mask_notlocked_complex] = -1
			
			if affects_surrounding:
				# surrounding, decreasing field status
				rows, cols = numpy.where(mask)
				rows_selected = numpy.hstack([rows-1,rows,rows+1,rows])
				cols_selected = numpy.hstack([cols,cols-1,cols,cols+1])
				valid_top    = numpy.logical_and(rows_selected>=0, cols_selected>=0)
				valid_bottom = numpy.logical_and(rows_selected<nrows, cols_selected<ncols)
				valid = numpy.logical_and(valid_top, valid_bottom)
				rows_selected, cols_selected = rows_selected[valid], cols_selected[valid]
				for j,i in zip(rows_selected, cols_selected):
					if mask[j,i]: continue # not the fields themselves
					if self.board.status[j,i] > 0:
						nchanged += 1
						self.board.status[j,i] -= 1
		return nchanged > 0
		

class PairCombiner(object):
	"""
	When two gems are swapped, takes the right action if they are special
	"""
	def __init__(self, board):
		self.board = board
	
	def activate(self, rows, cols, fromj,fromi, toj,toi):
		# remove the two triggers
		self.board.status[fromj, fromi] = 0
		self.board.type[fromj, fromi] = 0
		self.board.color[fromj, fromi] = 0
		self.board.status[toj, toi] = 0
		self.board.type[toj, toi] = 0
		self.board.color[toj, toi] = 0
		
		# change the status of all the selected fields
		mask = numpy.zeros(self.board.shape, dtype=bool)
		mask[rows,cols] = True
		# explode these (decrease field status, activate or set to empty)
		mask_locked = numpy.logical_and(mask, self.board.status > 0)
		mask_notlocked = numpy.logical_and(mask, self.board.status == 0)
		self.board.status[mask_locked] = self.board.status[mask_locked] - 1
		mask_notlocked_simple = numpy.logical_and(mask_notlocked, self.board.type == 1)
		self.board.type[mask_notlocked_simple] = 0
		# mark for explosion
		mask_notlocked_complex = numpy.logical_and(mask_notlocked, self.board.type > 1)
		self.board.status[mask_notlocked_complex] = -1
		# surrounding, decreasing field status
		rows, cols = numpy.where(mask)
		rows_selected = numpy.hstack([rows-1,rows,rows+1,rows])
		cols_selected = numpy.hstack([cols,cols-1,cols,cols+1])
		valid_top    = numpy.logical_and(rows_selected>=0, cols_selected>=0)
		valid_bottom = numpy.logical_and(rows_selected<nrows, cols_selected<ncols)
		valid = numpy.logical_and(valid_top, valid_bottom)
		rows_selected, cols_selected = rows_selected[valid], cols_selected[valid]
		for j,i in zip(rows_selected, cols_selected):
			if mask[j,i]: continue
			if self.board.status[j,i] > 0:
				self.board.status[j,i] -= 1
	
	def run(self, fromj,fromi, toj,toi):
		# check if stripe+bomb, stripe+stripe, bomb+bomb, 
		changed = False
		# both have to be unlocked and filled
		nrows, ncols = self.board.shape
		if self.board.status[fromj,fromi] == 0 and self.board.status[toj,toi] == 0 and self.board.type[fromj,fromi] > 0 and self.board.type[toj,toi] > 0:
			aj, ai = fromj, fromi
			bj, bi = toj, toi
			if self.board.type[aj,ai] > self.board.type[bj,bi]:
				# switch so that a contains the smaller type
				aj, ai, bj, bi = bj, bi, aj, ai
			
			if self.board.type[bj,bi] == 5 and self.board.type[aj,ai] == 5:
				# zapper+zapper -> activate entire board
				rows, cols = numpy.where(numpy.logical_and(self.board.type > 0, self.board.status == 0))
				self.activate(rows, cols, fromj, fromi, toj, toi)
			elif self.board.type[bj,bi] == 5 and 1 <= self.board.type[aj,ai] <= 4:
				# zapper+something -> change all of that color to bombs/stripe and activate them
				color = self.board.color[aj,ai]
				type = self.board.type[aj,ai]
				rows, cols = numpy.where(numpy.logical_and(numpy.logical_and(self.board.color == color, self.board.type == 1), self.board.status == 0))
				if type == 4:
					self.board.type[rows,cols] = type
				elif type in [2,3]:
					self.board.type[rows,cols] = 2+numpy.random.randint(1, size=rows.size)
				elif type == 1: # normal gem
					# no change. just activate them.
					pass
				
				self.activate(rows, cols, fromj, fromi, toj, toi)
			elif self.board.type[bj,bi] == 4 and self.board.type[aj,ai] == 4:
				# bomb+bomb -> make 5x5 explosion
				loj, hij = max(0, toj-2), min(nrows, toj+3)
				loi, hii = max(0, toi-2), min(ncols, toi+3)
				
				self.activate(slice(loj,hij), slice(loi,hii), fromj, fromi, toj, toi)
			elif self.board.type[bj,bi] == 4 and 2 <= self.board.type[aj,ai] <= 3:
				# bomb+stripe -> eliminate 3xvertical+horizontal from toj,toi
				loj, hij = max(0, toj-1), min(nrows, toj+2)
				loi, hii = max(0, toi-1), min(ncols, toi+2)
				
				self.activate(Ellipsis, slice(loi,hii), fromj, fromi, toj, toi)
				self.activate(slice(loj,hij), Ellipsis, fromj, fromi, toj, toi)
			elif 2 <= self.board.type[bj,bi] <= 3 and 2 <= self.board.type[aj,ai] <= 3:
				# stripe+stripe -> eliminate 1xvertical+horizontal from toj,toi
				self.activate(Ellipsis, toi, fromj, fromi, toj, toi)
				self.activate(toj, Ellipsis, fromj, fromi, toj, toi)
				
			
			

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
"""LUL
111
100
100
""",
"""LLL
100
100
111
""",
"""LLR
001
001
111
""",
"""LUR
111
001
001
""",
	]
	"""
	Collapses any gem sequences on the current board
	"""
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
			self.log((maskarr*1, name))
			assert maskarr.shape == (nrows, ncols)
			self.patterns.append((name, maskarr))
		self.fromj, self.fromi = None, None
		self.toj, self.toi = None, None
	
	def log(self, *args):
		#print(*args)
		pass
	
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
						self.log((j,i,name,'excluded because outside'))
						continue
					matched_type = board.type[j:j+mrows,i:i+mcols][mask]
					if not (matched_type > 0).all():
						# some non-fields or empty fields
						self.log((j,i,name,'excluded because non-fields/empty'))
						continue
					matched_status = board.status[j:j+mrows,i:i+mcols][mask]
					if not (matched_status == 0).all():
						# some locked fields
						self.log((j,i,name,'excluded because locked', matched_status))
						continue
					matched_color = board.color[j:j+mrows,i:i+mcols][mask]
					if not (matched_color == matched_color[0]).all():
						# not all have the same color
						self.log((j,i,name,'excluded because different colors'))
						continue
					boardmask = numpy.pad(mask, ((j,nrows-mrows-j), (i,ncols-mcols-i)), 'constant', constant_values=False)
					assert boardmask.shape == self.board.shape
					self.log(('found a match:', j,i,name))
					#print boardmask*1, 'is a match for', name, j, i
					matches.append((j, i, name, matched_color[0], boardmask))
		
		# check for conflicts
		matches_accepted = []
		matches_remaining = []
		self.log(('have %d potential matches' % len(matches)))
		# if two matches affect the same idx, always choose the longer one
		#print 'finding non-conflicting matches...'
		for k, match in enumerate(matches):
			j, i, name, matched_color, mask = match
			conflict_status = 0
			for match2 in matches[:k] + matches[k+1:]:
				j2, i2, name2, matched_color2, mask2 = match2
				if numpy.logical_and(mask, mask2).any():
					# conflict
					if mask2.sum() > mask.sum():
						# there is a larger one, so match should be removed
						conflict_status = 2
						#print 'discarding', mask*1, 'because of', mask2*1
					elif mask2.sum() == mask.sum() and conflict_status == 0:
						# there is one of the same length
						conflict_status = 1
						#print 'stalling', mask*1, 'because of', mask2*1
				
			if conflict_status == 0:
				matches_accepted.append(match)
				#print 'accepting match', mask*1
			elif conflict_status == 1:
				matches_remaining.append(match)
		
		print 'extending matches (have %d)...' % (len(matches_accepted))
		# at this point, we have secure matches in matches_accepted
		# matches_remaining may have several equally good options.
		# accept them greedily
		for match in matches_remaining:
			j, i, name, matched_color, mask = match
			conflict_free = True
			for match2 in matches_accepted:
				j2, i2, name2, matched_color2, mask2 = match2
				if numpy.logical_and(mask, mask2).any():
					# conflict with already accepted one
					conflict_free = False
					#print 'discarding', mask*1, 'because of', mask2*1
					break
			
			if conflict_free:
				matches_accepted.append(match)
				#print 'accepting match', mask*1
			else:
				#print 'not accepting match', mask*1
				pass
		
		self.log(('acting on matches:'))
		# we have now a set of matches (ideally just one)
		changed = len(matches_accepted) > 0
		for match in matches_accepted:
			j, i, name, matched_color, mask = match
			#print 'match:', j,i,name,matched_color, 'mask:'
			#print mask*1
			
			# explode these (decrease field status, activate or set to empty)
			
			mask_locked = numpy.logical_and(mask, self.board.status > 0)
			mask_notlocked = numpy.logical_and(mask, self.board.status == 0)
			self.board.status[mask_locked] = self.board.status[mask_locked] - 1
			#print 'after unlocking those:'
			#print self.board
			mask_notlocked_simple = numpy.logical_and(mask_notlocked, self.board.type == 1)
			self.board.type[mask_notlocked_simple] = 0
			#print 'after removing simple ...'
			#print self.board
			# mark for explosion
			mask_notlocked_complex = numpy.logical_and(mask_notlocked, self.board.type > 1)
			self.board.status[mask_notlocked_complex] = -1
			# surrounding, decreasing field status
			#print 'after removing those ...'
			#print self.board
			#print 'marking nearby ...'
			rows, cols = numpy.where(mask)
			rows_selected = numpy.hstack([rows-1,rows,rows+1,rows])
			cols_selected = numpy.hstack([cols,cols-1,cols,cols+1])
			valid_top    = numpy.logical_and(rows_selected>=0, cols_selected>=0)
			valid_bottom = numpy.logical_and(rows_selected<nrows, cols_selected<nrows)
			valid = numpy.logical_and(valid_top, valid_bottom)
			rows_selected, cols_selected = rows_selected[valid], cols_selected[valid]
			#print rows_selected, cols_selected
			for j,i in zip(rows_selected, cols_selected):
				if mask[j,i]: continue
				if self.board.status[j,i] > 0:
					self.board.status[j,i] -= 1
			
			# if T.*|X4|X5 replace one location in the pattern with the special item of the right color
			if name[1] == '4' or name[1] == '5' or name.startswith('T') or name.startswith('L'):
				# the preferred location is to, from or random otherwise
				k = numpy.random.randint(len(rows))
				j, i = rows[k], cols[k]
				if self.toi is not None and mask[self.toj,self.toi]:
					j, i = self.toj,self.toi
				elif self.fromi is not None and mask[self.fromj,self.fromi]:
					j, i = self.fromj,self.fromi
				if name == 'H4':
					self.board.color[j,i] = matched_color
					self.board.type[j,i] = 2
					self.board.status[j,i] = 0
				elif name == 'V4':
					self.board.color[j,i] = matched_color
					self.board.type[j,i] = 3
					self.board.status[j,i] = 0
				elif name.startswith('T') or name.startswith('L'):
					self.board.color[j,i] = matched_color
					self.board.type[j,i] = 4
					self.board.status[j,i] = 0
				elif name[1] == '5': 
					self.board.color[j,i] = 0
					self.board.type[j,i] = 5
					self.board.status[j,i] = 0
		
		return changed

if __name__ == '__main__':
	numpy.random.seed(1)
	board = Board()
	print board
	InitialFiller(board, double_locked_rows=2, double_locked_cols=2).run()
	print board
	
	grav = BoardGravityPuller(board)
	topfill = TopFiller(board, ncolors=5)
	comb = Combiner(board)
	paircomb = PairCombiner(board)
	acto = Activater(board)
	
	import time
	T = 0.5
	time.sleep(T)
	nstep = 0
	while True:
		# dropping phase
		while True:
			nstep += 1
			print('STEP %d' % nstep)
			anychange = grav.run()
			if anychange: 
				print board, 'grav'
				time.sleep(T)
			nstep += 1
			print('STEP %d' % nstep)
			anychange += topfill.run()
			if anychange: 
				print board, 'topfill'
				time.sleep(T)
			if not anychange:
				break
		
		nstep += 1
		print('STEP %d: combining phase...' % nstep)
		# combining phase
		anychange  = comb.run()
		if anychange:
			print board
			time.sleep(T)
		nstep += 1
		print('STEP %d: activation...' % nstep)
		anychange += acto.run()
		if anychange:
			nstep += 1
			print board
			time.sleep(T)
			continue
		
		# ok, the board settled down now
		# we should ask the user what they want to do now
		break
		# comb.set_last_interaction(fromj, fromi, toj, toi)
		
	
	


