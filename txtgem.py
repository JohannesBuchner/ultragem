import sys
import numpy
import scipy.signal
from numpy import random
from collections import defaultdict, Counter


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
		self.type = numpy.zeros(self.shape, dtype=int)
		self.color = numpy.zeros(self.shape, dtype=int)
		self.status = numpy.zeros(self.shape, dtype=int)
		self.events = []
	
	def copy(self):
		nrows,ncols = self.shape
		b = Board(nrows=nrows,ncols=ncols)
		b.type = self.type.copy()
		b.color = self.color.copy()
		b.status = self.status.copy()
		b.events = list(self.events)
		return b
	
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
	def __init__(self, board, nrows_disable=0, ncols_disable=0,
		double_locked_rows=0, double_locked_cols=0, lock_border=True, rng=None):
		self.board = board
		self.double_locked_rows = double_locked_rows
		self.double_locked_cols = double_locked_cols
		self.nrows_disable = nrows_disable
		self.ncols_disable = ncols_disable
		self.lock_border = lock_border
		#self.unusable_fraction = unusable_fraction
		self.rng = rng
	
	def run(self):
		# mark some squares as out-of-service
		nrows, ncols = self.board.type.shape
		
		# choose some columns and rows at random and mark them as out-of-service
		if self.ncols_disable > 0 or self.nrows_disable:
			left_disable = self.rng.choice(numpy.arange(ncols), size=self.ncols_disable, replace=False)
			right_disable = ncols - left_disable - 1
			bottom_disable = self.rng.choice(numpy.arange(nrows), size=self.nrows_disable, replace=False)
			top_disable = nrows - bottom_disable - 1
			
			self.board.type[:,tuple(top_disable)] = -1
			self.board.type[:,tuple(bottom_disable)] = -1
			self.board.type[tuple(top_disable),:] = -1
			self.board.type[tuple(bottom_disable),:] = -1
		
		if self.lock_border:
			# mark some squares as locked
			# the strategy is to do this symmetrically horizontally
			self.board.status[:,:self.double_locked_cols] = 2
			self.board.status[:,ncols-self.double_locked_cols:] = 2
			#board.status[:self.double_locked_rows,:] = 2
			self.board.status[nrows-self.double_locked_rows:,:] = 2
		else:
			# mark some squares as locked
			cols_locked = self.rng.choice(numpy.arange(ncols), size=self.double_locked_cols, replace=False)
			rows_locked = self.rng.choice(numpy.arange(nrows), size=self.double_locked_rows, replace=False)

			# the strategy is to do this symmetrically horizontally
			self.board.status[:,cols_locked] = 2
			self.board.status[rows_locked,:] = 2
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
		board = self.board
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
		self.board.type[toj, toi] = self.board.type[fromj, fromi]
		self.board.color[toj, toi] = self.board.color[fromj, fromi]
		self.board.status[toj, toi] = self.board.status[fromj, fromi]
		# mark origin as empty
		self.board.type[fromj, fromi] = 0
		self.board.color[fromj, fromi] = 0
		self.board.status[fromj, fromi] = 0
		
	def run(self):
		board = self.board
		nrows, ncols = self.board.shape
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
			self.board.events.append(('activated', self.board.type[j,i]))
			self.board.status[j,i] = 0
			self.board.color[j,i] = 0
			self.board.type[j,i] = 0

			mask_locked = numpy.logical_and(mask, self.board.status > 0)
			mask_notlocked = numpy.logical_and(mask, self.board.status == 0)
			nchanged += mask_locked.sum()
			self.board.status[mask_locked] = self.board.status[mask_locked] - 1
			if mask_locked.any():
				self.board.events.append(('unlocked', mask_locked.sum()))
			mask_notlocked_simple = numpy.logical_and(mask_notlocked, self.board.type == 1)
			nchanged += mask_notlocked_simple.sum()
			if mask_notlocked_simple.any():
				self.board.events.append(('destroyed', mask_notlocked_simple.sum()))
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
		if self.board.type[fromj, fromi] > 1:
			self.board.events.append(('activated', self.board.type[fromj, fromi]))
		if self.board.type[toj, toi] > 1:
			self.board.events.append(('activated', self.board.type[toj, toi]))
		# remove the two triggers
		self.board.status[fromj, fromi] = 0
		self.board.type[fromj, fromi] = 0
		self.board.color[fromj, fromi] = 0
		self.board.status[toj, toi] = 0
		self.board.type[toj, toi] = 0
		self.board.color[toj, toi] = 0
		
		nrows, ncols = self.board.shape
		# change the status of all the selected fields
		mask = numpy.zeros(self.board.shape, dtype=bool)
		mask[rows,cols] = True
		# explode these (decrease field status, activate or set to empty)
		mask_locked = numpy.logical_and(mask, self.board.status > 0)
		mask_notlocked = numpy.logical_and(mask, self.board.status == 0)
		self.board.status[mask_locked] = self.board.status[mask_locked] - 1
		if mask_locked.any():
			self.board.events.append(('unlocked', mask_locked.sum()))
		mask_notlocked_simple = numpy.logical_and(mask_notlocked, self.board.type == 1)
		self.board.type[mask_notlocked_simple] = 0
		if mask_notlocked_simple.any():
			self.board.events.append(('destroyed', mask_notlocked_simple.sum()))
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
		assert self.board.status[fromj,fromi] == 0, self.board.status[fromj,fromi]
		assert self.board.status[toj,toi] == 0, self.board.status[toj,toi]
		assert self.board.type[fromj,fromi] > 0, self.board.type[fromj,fromi]
		assert self.board.type[toj,toi] > 0, self.board.type[toj,toi]
		
		# swap
		self.board.status[toj, toi], self.board.status[fromj, fromi] = self.board.status[fromj, fromi], self.board.status[toj, toi]
		self.board.type[toj, toi], self.board.type[fromj, fromi] = self.board.type[fromj, fromi], self.board.type[toj, toi]
		self.board.color[toj, toi], self.board.color[fromj, fromi] = self.board.color[fromj, fromi], self.board.color[toj, toi]
		
		# 
		aj, ai = fromj, fromi
		bj, bi = toj, toi
		if self.board.type[aj,ai] > self.board.type[bj,bi]:
			# switch so that a contains the smaller type
			aj, ai, bj, bi = bj, bi, aj, ai
		
		if self.board.type[bj,bi] == 5 and self.board.type[aj,ai] == 5:
			# zapper+zapper -> activate entire board
			rows, cols = numpy.where(numpy.logical_and(self.board.type > 0, self.board.status == 0))
			self.board.events.append(('combined', 55))
			self.activate(rows, cols, fromj, fromi, toj, toi)
		elif self.board.type[bj,bi] == 5 and 1 <= self.board.type[aj,ai] <= 4:
			# zapper+something -> change all of that color to bombs/stripe and activate them
			color = self.board.color[aj,ai]
			type = self.board.type[aj,ai]
			rows, cols = numpy.where(numpy.logical_and(numpy.logical_and(self.board.color == color, self.board.type == 1), self.board.status == 0))
			if type == 4:
				self.board.type[rows,cols] = type
				self.board.events.append(('combined', 54))
			elif type in [2,3]:
				self.board.type[rows,cols] = 2+numpy.random.randint(1, size=rows.size)
				self.board.events.append(('combined', 52))
			elif type == 1: # normal gem
				# no change. just activate them.
				self.board.events.append(('combined', 51))
				pass
			
			self.activate(rows, cols, fromj, fromi, toj, toi)
		elif self.board.type[bj,bi] == 4 and self.board.type[aj,ai] == 4:
			# bomb+bomb -> make 5x5 explosion
			loj, hij = max(0, toj-2), min(nrows, toj+3)
			loi, hii = max(0, toi-2), min(ncols, toi+3)
			
			self.activate(slice(loj,hij), slice(loi,hii), fromj, fromi, toj, toi)
			self.board.events.append(('combined', 44))
		elif self.board.type[bj,bi] == 4 and 2 <= self.board.type[aj,ai] <= 3:
			# bomb+stripe -> eliminate 3xvertical+horizontal from toj,toi
			loj, hij = max(0, toj-1), min(nrows, toj+2)
			loi, hii = max(0, toi-1), min(ncols, toi+2)
			
			self.activate(Ellipsis, slice(loi,hii), fromj, fromi, toj, toi)
			self.activate(slice(loj,hij), Ellipsis, fromj, fromi, toj, toi)
			self.board.events.append(('combined', 42))
		elif 2 <= self.board.type[bj,bi] <= 3 and 2 <= self.board.type[aj,ai] <= 3:
			# stripe+stripe -> eliminate 1xvertical+horizontal from toj,toi
			self.activate(Ellipsis, toi, fromj, fromi, toj, toi)
			self.activate(toj, Ellipsis, fromj, fromi, toj, toi)
			self.board.events.append(('combined', 22))
	
	def enumerate_valid_moves_oneway(self):
		# list valid moves
		# a move is valid if it either
		# - leads to a combination of 3 same-color gems
		# - combines two special gems
		# - combines zapper with a normal gem
		board = self.board
		nrows, ncols = self.board.shape
		moves = []
		Hmoves = []
		Vmoves = []
		for fromj in range(nrows-1):
			for fromi in range(ncols-1):
				if self.board.status[fromj,fromi] != 0:
					continue
				# swap right
				fromtype = self.board.type[fromj,fromi]
				toj, toi = fromj, fromi+1
				# make sure that both are unlocked
				if self.board.status[toj,toi] == 0:
					totype = self.board.type[toj,toi]
					if fromtype > 1 and totype > 1 or (fromtype,totype) in [(5,1),(1,5)]:
						yield (fromj,fromi,toj,toi,fromtype+totype)
					elif fromtype > 0 and totype > 0:
						Hmoves.append((fromj,fromi,toj,toi))
				
				# swap down
				toj, toi = fromj+1, fromi
				if self.board.status[toj,toi] == 0:
					totype = self.board.type[toj,toi]
					if fromtype > 1 and totype > 1 or (fromtype,totype) in [(5,1),(1,5)]:
						yield (fromj,fromi,toj,toi,fromtype+totype)
					elif fromtype > 0 and totype > 0:
						Vmoves.append((fromj,fromi,toj,toi))
		
		# note: at the moment we are not checking whether things are locked
		for j,lefti,_,righti in Hmoves:
			assert (j,lefti) != (j,righti)
			# horizontal swap can lead to horizontal 3s
			leftcolor = self.board.color[j,lefti]
			rightcolor = self.board.color[j,righti]
			if leftcolor == rightcolor: 
				# can not swap gems of same color
				continue
			# check if next to to(right) are 2 of from-color
			if righti+2 < ncols and (board.color[j,righti+1:righti+2+1] == leftcolor).all():
				yield (j,lefti,j,righti,1)
			if lefti >= 2 and (board.color[j,lefti-2:lefti] == rightcolor).all():
				yield (j,lefti,j,righti,1)
			# no horizontal match. Lets find a vertical match
			# vertical matches can happen if it completes a row
			# two above are completed at the right position
			if j+2 < nrows and (board.color[j+1:j+2+1,righti] == leftcolor).all():
				yield (j,lefti,j,righti,1)
			# two below are completed at the right position
			if j >= 2 and (board.color[j-2:j,righti] == leftcolor).all():
				yield (j,lefti,j,righti,1)
			# one above, one below are completed at the right position
			if j >= 1 and j+1 < nrows and board.color[j-1,righti] == leftcolor == board.color[j+1,righti]:
				yield (j,lefti,j,righti,1)
			# two below are completed at the left position
			if j+2 < nrows and (board.color[j+1:j+2+1,lefti] == rightcolor).all():
				yield (j,lefti,j,righti,1)
			# two above are completed at the left position
			if j >= 2 and (board.color[j-2:j,lefti] == rightcolor).all():
				yield (j,lefti,j,righti,1)
			# one above, one below are completed at the left position
			if j >= 1 and j+1 < nrows and board.color[j-1,lefti] == rightcolor == board.color[j+1,lefti]:
				yield (j,lefti,j,righti,1)
		
		for topj,i,bottomj,_ in Vmoves:
			assert (topj,i) != (bottomj,i)
			topcolor = self.board.color[topj,i]
			bottomcolor = self.board.color[bottomj,i]
			if topcolor == bottomcolor: 
				# can not swap gems of same color
				continue
			# vertical swap can lead to vertical 3s
			# check if above/below to(bottom) are 2 of from-color
			if bottomj+2 < nrows and (board.color[bottomj+1:bottomj+2+1,i] == topcolor).all():
				yield (topj,i,bottomj,i,1)
			if topj >= 2 and (board.color[topj-2:topj] == bottomcolor).all():
				yield (topj,i,bottomj,i,1)
			# no vertical match. Lets find a horizontal match
			# horizontal matches can happen if it completes a column
			# two right are completed at the bottom position
			if i+2 < ncols and (board.color[bottomj,i+1:i+2+1] == topcolor).all():
				yield (topj,i,bottomj,i,1)
			# two left are completed at the bottom position
			if i >= 2 and (board.color[bottomj,i-2:i] == topcolor).all():
				yield (topj,i,bottomj,i,1)
			# one left, one right are completed
			if i >= 1 and i+1 < ncols and board.color[bottomj,i-1] == topcolor == board.color[bottomj,i+1]:
				yield (topj,i,bottomj,i,1)
			# two right are completed at the top position
			if i+2 < ncols and (board.color[topj,i+1:i+2+1] == bottomcolor).all():
				yield (topj,i,bottomj,i,1)
			# two left are completed at the top position
			if i >= 2 and (board.color[topj,i-2:i] == bottomcolor).all():
				yield (topj,i,bottomj,i,1)
			# one right, one left are completed at the top position
			if i >= 1 and i+1 < ncols and board.color[topj,i-1] == bottomcolor == board.color[topj,i+1]:
				yield (topj,i,bottomj,i,1)
		
	def enumerate_valid_moves(self):
		# for each swap there is the reverse swap also possible,
		# which makes a difference in special candies (existing or created)
		scores = Counter()
		for fromj,fromi,toj,toi,score in self.enumerate_valid_moves_oneway():
			assert (fromj,fromi) != (toj,toi)
			scores[(fromj,fromi,toj,toi)] += score
		for (fromj,fromi,toj,toi),score in scores.most_common():
			yield (fromj,fromi,toj,toi),score
			yield (toj,toi,fromj,fromi),score
			#yield toj,toi,fromj,fromi
	
	def shuffle(self):
		mask = numpy.logical_and(self.board.status == 0, self.board.type == 1)
		irows, icols = numpy.where(mask)
		idx = numpy.arange(len(irows))
		numpy.random.shuffle(idx)
		orows, ocols = irows[idx], icols[idx]
		self.board.color[orows,ocols] = self.board.color[irows,icols]
		

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
			# if pattern is bigger than board, it can never match
			if nrows > self.board.shape[0]: continue
			if ncols > self.board.shape[1]: continue
			maskarr = numpy.array([[c=='1' for c in shaperow] for shaperow in shapeparts])
			self.log((maskarr*1, name))
			assert maskarr.shape == (nrows, ncols)
			self.patterns.append((name, maskarr, maskarr.sum()))
		self.fromj, self.fromi = None, None
		self.toj, self.toi = None, None
	
	def log(self, *args):
		#print(args)
		pass
	
	def set_last_interaction(self, fromj,fromi, toj,toi):
		self.fromj, self.fromi = fromj, fromi
		self.toj, self.toi = toj, toi
	
	def run(self):
		board = self.board
		nrows, ncols = self.board.shape
		matches = []
		changed = False
		# find longest sequences of gems
		if False:
			for name, mask, Nmask in self.patterns:
				mrows, mcols = mask.shape
				for j in range(nrows):
					for i in range(ncols):
						if j + mrows >= nrows or i + mcols >= ncols:
							#self.log((j,i,name,'excluded because outside'))
						#	assert False
							continue
						matched_type = board.type[j:j+mrows,i:i+mcols][mask]
						if not (matched_type > 0).all():
							# some non-fields or empty fields
							#self.log((j,i,name,'excluded because non-fields/empty'))
							continue
						matched_status = board.status[j:j+mrows,i:i+mcols][mask]
						if not (matched_status == 0).all():
							# some locked fields
							#self.log((j,i,name,'excluded because locked', matched_status))
							continue
						matched_color = board.color[j:j+mrows,i:i+mcols][mask]
						if not (matched_color == matched_color[0]).all():
							# not all have the same color
							#self.log((j,i,name,'excluded because different colors'))
							continue
						boardmask = numpy.pad(mask, ((j,nrows-mrows-j), (i,ncols-mcols-i)), 'constant', constant_values=False)
						assert boardmask.shape == self.board.shape
						#self.log(('found a match:', j,i,name))
						#print boardmask*1, 'is a match for', name, j, i
						matches.append((j, i, name, matched_color[0], boardmask))
		else:
			# within mask, these have to be true:scenario2.out3
			# type has to be > 0
			# status has to be == 0
			matchable = numpy.logical_and(self.board.type > 0, self.board.status == 0)
			# and color has to be the same
			
			
			# the trick here is basically a bitmask. 
			# colors 1,2,3 are substituted for 10 100 1000
			# If the result is Nmask * 100, then we have Nmask of color=2. 
			# That value can not be reached by fewer color=3 stones or more color=1 stones.
			boardcolors = 10**self.board.color * matchable
			maxcolor = self.board.color.max()
			for name, mask, Nmask in self.patterns:
				#print 'MATCHING:', name
				mrows, mcols = mask.shape
				valid_results = 10**numpy.arange(1,maxcolor+1) * Nmask
				
				values = scipy.signal.correlate2d(boardcolors, mask, mode='valid')
				
				ohas_valid_results = numpy.in1d(values.flatten(), valid_results).reshape(values.shape)
				colors = numpy.log10(values * 1. / Nmask).astype(int)
				colors[colors < 0] = 0
				has_valid_results = 10**colors * Nmask == values
				#print self.board.color
				#print values, valid_results*1
				#print 'where are valid results?:', has_valid_results*1
				assert numpy.all(has_valid_results == ohas_valid_results), (has_valid_results*1, ohas_valid_results*1)
				if not has_valid_results.any(): 
					continue
				#print numpy.where(has_valid_results, numpy.log10(values/Nmask).astype(int), 0), 'for', name
				rows, cols = numpy.where(has_valid_results)
				for j, i, color in zip(rows, cols, colors[has_valid_results]):
					boardmask = numpy.pad(mask, ((j,nrows-mrows-j), (i,ncols-mcols-i)), 'constant', constant_values=False)
					assert boardmask.shape == self.board.shape
					assert color > 0 and color <= maxcolor, color
					matches.append((j, i, name, color, boardmask))
		
		#print [(name, j, i) for (j, i, name, color, boardmask) in omatches]
		#print [(name, j, i) for (j, i, name, color, boardmask) in matches]
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
		
		#print 'extending matches (have %d)...' % (len(matches_accepted))
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
			if mask_locked.any():
				self.board.events.append(('unlocked', mask_locked.sum()))
			#print 'after unlocking those:'
			#print self.board
			mask_notlocked_simple = numpy.logical_and(mask_notlocked, self.board.type == 1)
			self.board.type[mask_notlocked_simple] = 0
			if mask_notlocked_simple.any():
				self.board.events.append(('destroyed', mask_notlocked_simple.sum()))
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
		
		self.fromj, self.fromi = None, None
		self.toj, self.toi = None, None
		
		return changed

def best_move_selector(board, moves):
	return moves[0][0]

def worst_move_selector(board, moves):
	return moves[-1][0]

def random_move_selector(board, moves):
	i = numpy.random.randint(len(moves))
	return moves[i][0]

def smart_move_selector(board, moves):
	# store seed and board
	orig_state = numpy.random.get_state()
	orig_board = board.copy()
	totalscores = []
	for move, score in moves:
		# emulate move
		# make a copy of the board here.
		board.type = orig_board.type.copy()
		board.status = orig_board.status.copy()
		board.color = orig_board.color.copy()
		board.events = list(orig_board.events)
		
		# also, set a new seed, and restore later
		numpy.random.seed(1)
		
		paircomb.run(*move)
		comb.set_last_interaction(*move)
		anychange  = comb.run()
		anychange += acto.run()
		while True:
			if grav.run(): continue
			anychange  = comb.run()
			anychange += acto.run()
			if anychange:
				continue
		# ok, the board settled down now
		moves = list(paircomb.enumerate_valid_moves())
		subscore = moves[0][1]
		intermediatescore = 0
		
		for type, value in board.events[len(orig_board.events):]:
			if type == 'activated':
				intermediatescore += value*10
			elif type == 'unlocked':
				intermediatescore += value
			elif type == 'destroyed':
				intermediatescore += value
			elif type == 'combined':
				intermediatescore += value*20
		
		totalscores.append((score + subscore)*10 + intermediatescore)

	numpy.random.set_state(orig_state)
	board.type = orig_board.type.copy()
	board.status = orig_board.status.copy()
	board.color = orig_board.color.copy()
	board.events = list(orig_board.events)
	

if __name__ == '__main__':
	numpy.random.seed(1)
	scenario = 2
	
	maxswaps = 40
	if scenario == 0:
		board = Board(nrows=10, ncols=10)
		InitialFiller(board, double_locked_rows=2, double_locked_cols=2).run()
		topfill = TopFiller(board, ncolors=3)
	elif scenario == 1:
		board = Board(nrows=10, ncols=10)
		InitialFiller(board, double_locked_rows=2, double_locked_cols=2).run()
		topfill = TopFiller(board, ncolors=4)
	elif scenario == 2:
		board = Board(nrows=6, ncols=6)
		InitialFiller(board).run()
		topfill = TopFiller(board, ncolors=6)
	
	move_selector = random_move_selector
	import time
	waitfunction = lambda: time.sleep(0.5)
	waitfunction = lambda: None
	
	print board
	
	grav = BoardGravityPuller(board)
	comb = Combiner(board)
	paircomb = PairCombiner(board)
	acto = Activater(board)
	
	waitfunction()
	nstep = 0
	ncomb = 0
	nswaps = 0
	while True:
		# dropping phase
		while True:
			nstep += 1
			print('STEP %d' % nstep)
			anychange = grav.run()
			if anychange: 
				print board, 'grav'
				waitfunction()
			nstep += 1
			print('STEP %d' % nstep)
			anychange += topfill.run()
			if anychange: 
				print board, 'topfill'
				waitfunction()
			if not anychange:
				break
		
		nstep += 1
		print('STEP %d: combining phase...' % nstep)
		# combining phase
		anychange  = comb.run()
		if anychange:
			print board
			waitfunction()
		nstep += 1
		print('STEP %d: activation...' % nstep)
		anychange += acto.run()
		if anychange:
			ncomb += 1
			nstep += 1
			print board
			waitfunction()
			continue
		
		if nswaps >= maxswaps:
			print 'moves used up.'
			break
		if ncomb > (nswaps + 1) * 40:
			print 'STOPPING TRIVIAL GAME'
			break
		# ok, the board settled down now
		# we should ask the agent/user what they want to do now
		nstep += 1
		print('STEP %d: finding valid moves ...' % nstep)
		moves = list(paircomb.enumerate_valid_moves())
		if len(moves) == 0:
			# no moves left -- shuffle
			print('STEP %d: shuffling ...' % nstep)
			paircomb.shuffle()
			print board
			continue
			
		#for fromj,fromi,toj,toi in moves:
		#	print '  could swap %d|%d -> %d|%d' % (fromj,fromi,toj,toi)
		
		# move selector
		move = move_selector(board, moves)
		
		nstep += 1
		print('STEP %d: swapping ...' % nstep)
		paircomb.run(*move)
		nswaps += 1
		comb.set_last_interaction(*move)
		print board

		nstep += 1
		print('STEP %d: combining phase...' % nstep)
		# combining phase
		anychange  = comb.run()
		if anychange:
			print board
			waitfunction()

		nstep += 1
		print('STEP %d: activation...' % nstep)
		anychange += acto.run()
		if anychange:
			nstep += 1
			print board
			waitfunction()
			continue


