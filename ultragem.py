# UltraGem (A Bejeweled/CandyCrush Clone)
# By Johannes Buchner <buchner.johannes@gmx.at>

# Based on Gemgem (A Bejeweled Clone)
# http://inventwithpython.com/blog
# By Al Sweigart al@inventwithpython.com

# This code is meant to be a simple tutorial for Pygame and programming in
# general. As such, the code is simple (there is no object-oriented programming,
# list comprehensions, or other advanced concepts). This is intentional to make
# the code as readable as possible.


# This program has "gem data structures", which are basically dictionaries
# with the following keys:
#   'x' and 'y' - The location of the gem on the board. 0,0 is the top left.
#                 There is also a ROWABOVEBOARD row that 'y' can be set to,
#                 to indicate that it is above the board.
#   'direction' - one of the four constant variables UP, DOWN, LEFT, RIGHT.
#                 This is the direction the gem is moving. (Not always used.)
#   'imageNum' - The integer index into GEMIMAGES to denote which image this
#                gem uses.


import random
import time
import pygame
import sys
import copy
import numpy
from pygame.locals import QUIT, KEYUP, K_ESCAPE, K_BACKSPACE, MOUSEBUTTONUP, MOUSEBUTTONDOWN
from gemengine import Board, InitialFillerDoubleLockSpecial, InitialFillerDoubleLock, InitialFillerDisable, NastyTopFiller, BoardGravityPuller, Combiner, PairCombiner, Activater

FPS = 60 # frames per second to update the screen
WINDOWWIDTH = 800  # width of the program's window, in pixels
WINDOWHEIGHT = 600 # height in pixels

GEMIMAGESIZE = 64 # width & height of each space in pixels

# NUMGEMIMAGES is the number of gem types. You will need .png image files named
# gem0.png, gem1.png, etc. up to gem(N-1).png.
NUMGEMIMAGES = 7
NUMFIREIMAGES = 30

# NUMMATCHSOUNDS is the number of different sounds to choose from when a match
# is made. The .wav files are named match0.wav, match1.wav, etc.
NUMMATCHSOUNDS = 6

MOVERATE = 5 # 1 to 100, larger num means faster animations

HIGHLIGHTCOLOR = (255, 0, 255) # color of the selected gem's border
BGCOLOR = (170, 190, 255) # background color on the screen
GRIDCOLOR = (0, 0, 255) # color of the game board
GAMEOVERCOLOR = (255, 100, 100) # color of the "Game over" text.
GAMEOVERBGCOLOR = (0, 0, 0) # background color of the "Game over" text.
SCORECOLOR = (85, 65, 0)

# Constants for the different directions. The numbers correspond to the
# keyboard's keypad, but they could be any arbitrary value.
UP = 8
RIGHT = 6
DOWN = 2
LEFT = 4

EMPTY_SPACE = -1 # an arbitrary, nonnegative value
ROWABOVEBOARD = 'row above board' # an arbitrary, noninteger value

class UltraGemGame(object):
	def __init__(self, ncolors=4):
		self.score = 0 # global variable for the score
		self.ncolors = ncolors

		self.BOARDWIDTH = 8 # how many columns in the board
		self.BOARDHEIGHT = 8 # how many rows in the board
		
		# The amount of space to the sides of the board to the edge of the window is
		# used several times, so calculate it once here and store in variables.
		self.XMARGIN = int((WINDOWWIDTH - GEMIMAGESIZE * self.BOARDWIDTH) / 2)
		self.YMARGIN = int((WINDOWHEIGHT - GEMIMAGESIZE * self.BOARDHEIGHT) / 2)
		self.rng = numpy.random
		self.rng.seed(1)

	def run(self):
		pygame.init()
		
		self.FPSCLOCK = pygame.time.Clock()
		self.WINDOWSURF = pygame.display.set_mode((WINDOWWIDTH, WINDOWHEIGHT))
		pygame.display.set_caption('Gemgem')
		self.BASICFONT = pygame.font.Font('freesansbold.ttf', 36)

		# Load the images
		GEMIMAGES = []
		for i in range(1,NUMGEMIMAGES+1):
			gemImage = pygame.image.load('gem%s.png' % i)
			if gemImage.get_size() != (GEMIMAGESIZE, GEMIMAGESIZE):
				gemImage = pygame.transform.smoothscale(gemImage, (GEMIMAGESIZE, GEMIMAGESIZE))
			GEMIMAGES.append(gemImage)
		self.GEMIMAGES = GEMIMAGES

		FIREIMAGES = []
		for i in range(1,NUMFIREIMAGES+1):
			gemImage = pygame.image.load('fire%s.png' % i)
			if gemImage.get_size() != (GEMIMAGESIZE, GEMIMAGESIZE):
				gemImage = pygame.transform.smoothscale(gemImage, (GEMIMAGESIZE, GEMIMAGESIZE))
			FIREIMAGES.append(gemImage)
		self.FIREIMAGES = FIREIMAGES

		# Load the sounds.
		GAMESOUNDS = {}
		GAMESOUNDS['bad swap'] = pygame.mixer.Sound('badswap.wav')
		GAMESOUNDS['match'] = []
		for i in range(NUMMATCHSOUNDS):
			GAMESOUNDS['match'].append(pygame.mixer.Sound('match%s.wav' % i))
		self.GAMESOUNDS = GAMESOUNDS

		BOARDRECTS = []
		for x in range(self.BOARDWIDTH):
			BOARDRECTS.append([])
			for y in range(self.BOARDHEIGHT):
				r = pygame.Rect((self.XMARGIN + (x * GEMIMAGESIZE),
					self.YMARGIN + (y * GEMIMAGESIZE),
					GEMIMAGESIZE,
					GEMIMAGESIZE))
				BOARDRECTS[x].append(r)
		self.BOARDRECTS = BOARDRECTS

		while True:
			self.runGame()
			self.score = 0
	
	def initGame(self):
		nrows, ncols, ncolors = self.BOARDWIDTH, self.BOARDHEIGHT, self.ncolors
		board = Board(nrows=nrows, ncols=ncols)
		
		rng = self.rng
		
		"""
		# make lower numbers more likely to be selected
		prows = 1. / (0.2 + numpy.arange(nrows))
		prows /= prows.sum()
		ndrows = rng.choice(numpy.arange(nrows), p=prows)
		ndlrows = rng.choice(numpy.arange(nrows), p=prows)
		pcols = 1. / (0.2+ numpy.arange(ncols))
		pcols /= pcols.sum()
		ndcols = rng.choice(numpy.arange(nrows), p=pcols)
		ndlcols = rng.choice(numpy.arange(nrows), p=pcols)
		
		if rng.uniform() < 0.1:
			types = [2,3,4,5] if rng.uniform() < 0.5 else [2,3,4]
			InitialFillerDoubleLockSpecial(board, ncolors=ncolors, types=types, nrows=ndlrows, ncols=ndlcols, rng=rng).run()
		else:
			InitialFillerDoubleLock(board, nrows=ndlrows, ncols=ndlcols, rng=rng).run()
		if rng.uniform() < 0.1:
			InitialFillerDisable(board, nrows=ndrows, ncols=ndcols, rng=rng).run()
		"""
		self.board = board
		self.topfill = NastyTopFiller(board, ncolors=ncolors)
		self.grav = BoardGravityPuller(board)
		self.comb = Combiner(board)
		self.paircomb = PairCombiner(board)
		self.acto = Activater(board)

	def fillBoardAndAnimate(self, board, points=None):
		# dropping phase
		anychange = True
		print(self.board)
		while True:
			while anychange:
				changes = self.grav.run()
				anychange = len(changes) > 0
				movingGems = []
				#print('grav changes:', changes, anychange)
				print(self.board)
				for j, i, move in changes:
					if move == 'dropped from top':
						directionx = 0
						directiony = 1
					elif move == 'dropped from top-left':
						directionx = 1
						directiony = 1
					elif move == 'dropped from top-right':
						directionx = -1
						directiony = 1
					else:
						assert False, move 
					movingGems.append(dict(imageNum=self.board.color[j,i] - 1, 
						x=i-directionx, y=j-directiony, 
						directionx=directionx, directiony=directiony))

				changes = self.topfill.run()
				anychange = anychange or len(changes) > 0
				#print('topfill changes:', changes, anychange)
				print(self.board)
				for j, i, move in changes:
					directionx = 0
					directiony = 1
					movingGems.append(dict(imageNum=self.board.color[j,i] - 1, 
						x=i-directionx, y=j-directiony, 
						directionx=directionx, directiony=directiony))

				if movingGems:
					#print('moving gems:', movingGems)
					boardCopy = self.getBoardCopyMinusGems(board, movingGems)
					self.animateMovingGems(boardCopy, movingGems, points)
					#self.moveGems(board, movingGems)
					self.updateBoard(board)
				#print('board now:', board)
			#print('final board:', board)
			
			# combining phase
			anychanges = self.comb.run()
			if anychange:
				# have to find the differences and transition
				# using fire
				boardCopy = copy.deepcopy(board)
				self.updateBoard(board)
				print(self.board)
				self.transitionBoard(boardCopy, board)
			
			#print(('STEP %d: activation...' % nstep))
			anychange = self.acto.run() or anychange
			if anychange:
				boardCopy = copy.deepcopy(board)
				self.updateBoard(board)
				print(self.board)
				self.transitionBoard(boardCopy, board)
				continue
			
			# ok, the board settled down now
			# we should ask the agent/user what they want to do now
			#print(('STEP %d: finding valid moves ...' % nstep))
			moves = list(self.paircomb.enumerate_valid_moves())
			if len(moves) == 0:
				# no moves left -- shuffle
				print(('shuffling ...'))
				boardCopy = copy.deepcopy(board)
				self.paircomb.shuffle()
				self.updateBoard(board)
				self.transitionBoard(boardCopy, board)
				print(board)
				continue
			return moves
	
	def continueGame(self, board, move):
		boardCopy = copy.deepcopy(board)
		print('paircomb-1', board)
		self.paircomb.run(*move)
		self.updateBoard(board)
		print('paircomb-2', board)
		print(self.board)
		self.transitionBoard(boardCopy, board)
		self.comb.set_last_interaction(*move)
		print(self.board)

		# combining phase
		anychange = self.comb.run()
		if anychange:
			# have to find the differences and transition
			# using fire
			boardCopy = copy.deepcopy(board)
			print('comb-1', board)
			self.updateBoard(board)
			print('comb-2', board)
			print(self.board)
			self.transitionBoard(boardCopy, board)
		
		#print(('STEP %d: activation...' % nstep))
		anychange = self.acto.run() or anychange
		if anychange:
			boardCopy = copy.deepcopy(board)
			print('acto-1', board)
			self.updateBoard(board)
			print('acto-2', board)
			print(self.board)
			self.transitionBoard(boardCopy, board)
		
		# dropping phase
		return self.fillBoardAndAnimate(board, [])
	
	def isValidMove(self, x1, y1, x2, y2):
		for (fromj,fromi,toj,toi),score in self.possible_moves:
			if x1 == fromi and y1 == fromj and x2 == toi and y2 == toj:
				return (fromj,fromi,toj,toi)
		print('moves:')
		for move, score in self.possible_moves:
			print(move)
		print()
		print('not:',x1,y1,x2,y2)
		return False

	def getBoardCopyMinusGems(self, board, gems):
		# Gems is a list of dicts, with keys 'imageNum', 'x', 'y', 'direction'.
		boardCopy = copy.deepcopy(board)

		# Remove some of the gems from this board data structure copy.
		for gem in gems:
			if gem['y'] != ROWABOVEBOARD:
				boardCopy[gem['x']][gem['y']] = EMPTY_SPACE
		return boardCopy
	
	def updateBoard(self, board):
		for x in range(self.BOARDWIDTH):
			for y in range(self.BOARDHEIGHT):
				color = self.board.color[y,x]
				type = self.board.type[y,x]
				if type == 0 or color == 0:
					board[x][y] = EMPTY_SPACE
				else:
					board[x][y] = color - 1
	
	def moveGems(self, board, movingGems):
		# movingGems is a list of dicts with keys 'x', 'y', 'direction', and 'imageNum'
		for gem in movingGems:
			if gem['y'] != ROWABOVEBOARD:
				#print('marking empty', gem['x'], gem['y'])
				board[gem['x']][gem['y']] = EMPTY_SPACE
				movex = gem['directionx']
				movey = gem['directiony']
				#print('filling', gem['x']+movex, gem['y']+movey)
				board[gem['x'] + movex][gem['y'] + movey] = gem['imageNum']
			else:
				board[gem['x']][0] = gem['imageNum'] # ignore 'direction', just move to top row

	def transitionBoard(self, oldboard, newboard):
		progress = 0 # progress at 0 represents beginning, progress at 100 represents finish.
		differences = []
		for x in range(self.BOARDWIDTH):
			for y in range(self.BOARDHEIGHT):
				if oldboard[x][y] != newboard[x][y]:
					differences.append((x,y))
		print('differences:', differences)
		if not differences: return
		while progress < NUMFIREIMAGES:
			print('transitioning...', progress)
			self.WINDOWSURF.fill(BGCOLOR)
			if progress < 22:
				self.drawBoard(oldboard)
			else:
				self.drawBoard(newboard)
			# Draw fire where they differ.
			for x,y in differences:
				self.drawFire(x, y, progress)
			self.drawScore()
			pygame.display.update()
			self.FPSCLOCK.tick(FPS)
			progress += 1
		
		self.drawBoard(newboard)
		self.drawScore()
		pygame.display.update()
	
	def drawFire(self, x, y, progress):
		pixelx = self.XMARGIN + (x * GEMIMAGESIZE)
		pixely = self.YMARGIN + (y * GEMIMAGESIZE)
		r = pygame.Rect( (pixelx, pixely, GEMIMAGESIZE, GEMIMAGESIZE) )
		self.WINDOWSURF.blit(self.FIREIMAGES[progress], r)
	
	def animateMovingGems(self, board, gems, pointsText):
		progress = 0 # progress at 0 represents beginning, progress at 100 represents finish.
		while progress <= 100:
			self.WINDOWSURF.fill(BGCOLOR)
			self.drawBoard(board)
			# Draw each gem.
			for gem in gems:
				self.drawMovingGem(gem, progress)
			self.drawScore()
			for pointText in pointsText:
				pointsSurf = self.BASICFONT.render(str(pointText['points']), 1, SCORECOLOR)
				pointsRect = pointsSurf.get_rect()
				pointsRect.center = (pointText['x'], pointText['y'])
				self.WINDOWSURF.blit(pointsSurf, pointsRect)

			pygame.display.update()
			self.FPSCLOCK.tick(FPS)
			progress += MOVERATE

	def drawMovingGem(self, gem, progress):
		movex = 0
		movey = 0
		progress *= 0.01

		#print('moving...', progress, gem)
		fraction = progress
		fraction = numpy.arctan((progress - 0.5) * 10) * 1.13 / numpy.pi + 0.5
		movex = gem['directionx'] * int(fraction * GEMIMAGESIZE)
		movey = gem['directiony'] * int(fraction * GEMIMAGESIZE)

		basex = gem['x']
		basey = gem['y']
		if basey == ROWABOVEBOARD:
			basey = -1

		pixelx = self.XMARGIN + (basex * GEMIMAGESIZE)
		pixely = self.YMARGIN + (basey * GEMIMAGESIZE)
		r = pygame.Rect( (pixelx + movex, pixely + movey, GEMIMAGESIZE, GEMIMAGESIZE) )
		self.WINDOWSURF.blit(self.GEMIMAGES[gem['imageNum']], r)

	def drawBoard(self, board):
		pygame.draw.rect(self.WINDOWSURF, BGCOLOR, 
			(self.XMARGIN, self.YMARGIN - GEMIMAGESIZE, 
			GEMIMAGESIZE * self.BOARDWIDTH, 
			GEMIMAGESIZE * (self.BOARDHEIGHT+1)), 0)
		for x in range(self.BOARDWIDTH):
			for y in range(self.BOARDHEIGHT):
				pygame.draw.rect(self.WINDOWSURF, GRIDCOLOR, self.BOARDRECTS[x][y], 1)
				gemToDraw = board[x][y]
				if gemToDraw != EMPTY_SPACE:
					self.WINDOWSURF.blit(self.GEMIMAGES[gemToDraw], self.BOARDRECTS[x][y])
	
	def drawScore(self):
		pass

	def checkForGemClick(self, pos):
		# See if the mouse click was on the board
		for x in range(self.BOARDWIDTH):
			for y in range(self.BOARDHEIGHT):
				if self.BOARDRECTS[x][y].collidepoint(pos[0], pos[1]):
					return (x, y) # Return board x and y where the click occurred.
		return None # Click was not on the board.
	
	def highlightSpace(self, x, y):
		pygame.draw.rect(self.WINDOWSURF, HIGHLIGHTCOLOR, self.BOARDRECTS[x][y], 4)

	def getSwappingGems(self, board, firstXY, secondXY):
		firstGem = dict(imageNum=board[firstXY[0]][firstXY[1]],
			x=firstXY[0], directionx=0,
			y=firstXY[1], directiony=0)
		secondGem = dict(imageNum=board[secondXY[0]][secondXY[1]],
			x=secondXY[0], directionx=0,
			y=secondXY[1], directiony=0)
		highlightedGem = None
		if firstGem['x'] == secondGem['x'] + 1 and firstGem['y'] == secondGem['y']:
			firstGem['directionx'] = -1
			secondGem['directionx'] = +1
		elif firstGem['x'] == secondGem['x'] - 1 and firstGem['y'] == secondGem['y']:
			firstGem['directionx'] = +1
			secondGem['directionx'] = -1
		elif firstGem['y'] == secondGem['y'] + 1 and firstGem['x'] == secondGem['x']:
			firstGem['directiony'] = -1
			secondGem['directiony'] = +1
		elif firstGem['y'] == secondGem['y'] - 1 and firstGem['x'] == secondGem['x']:
			firstGem['directiony'] = +1
			secondGem['directiony'] = -1
		else:
			# These gems are not adjacent and can't be swapped.
			return None, None
		return firstGem, secondGem
	
	def runGame(self):
		self.initGame()

		mainBoard = [[EMPTY_SPACE] * self.BOARDHEIGHT for x in range(self.BOARDWIDTH)]
		# Drop the initial gems.
		self.possible_moves = self.fillBoardAndAnimate(mainBoard, [])
		nswaps = 0
		firstSelectedGem = None
		lastMouseDownX = None
		lastMouseDownY = None
		isGameOver = False
		clickContinueTextSurf = None
		while True:
			clickedSpace = None
			for event in pygame.event.get():
				if event.type == QUIT:
					pygame.quit()
					sys.exit(0)

				if event.type == KEYUP:
					if event.key == K_ESCAPE:
						pygame.quit()
						sys.exit(0)
					elif event.key == K_BACKSPACE:
						return
				if event.type == MOUSEBUTTONUP:
					if isGameOver:
						return

					if event.pos == (lastMouseDownX, lastMouseDownY):
						# This is a mouse click.
						clickedSpace = self.checkForGemClick(event.pos)
					else:
						# This is the end of a mouse drag, and the first gem has already been selected.
						firstSelectedGem = self.checkForGemClick((lastMouseDownX, lastMouseDownY))
						mouseOverSpace = self.checkForGemClick(event.pos)
						if mouseOverSpace and (mouseOverSpace[0] == firstSelectedGem[0] + 1 or \
							mouseOverSpace[0] == firstSelectedGem[0] - 1 or \
							mouseOverSpace[1] == firstSelectedGem[1] + 1 or \
							mouseOverSpace[1] == firstSelectedGem[1] - 1):
							clickedSpace = mouseOverSpace

						if not firstSelectedGem or not mouseOverSpace:
							# If this MOUSEBUTTONUP was not part of a valid drag, deselect both.
							firstSelectedGem = None
							mouseOverSpace = None
				if event.type == MOUSEBUTTONDOWN:
					lastMouseDownX, lastMouseDownY = event.pos

			# Check if this is the first or second gem to be clicked.
			if clickedSpace and not firstSelectedGem:
				firstSelectedGem = clickedSpace
			elif clickedSpace and firstSelectedGem:
				# Two gems have been selected. Swap the gems.
				firstSwappingGem, secondSwappingGem = self.getSwappingGems(mainBoard, firstSelectedGem, clickedSpace)
				if firstSwappingGem is None and secondSwappingGem is None:
					firstSelectedGem = None # Deselect the first gem.
					continue

				# Show the swap animation on the screen.
				boardCopy = self.getBoardCopyMinusGems(mainBoard, (firstSwappingGem, secondSwappingGem))
				self.animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [])

				# Swap the gems in the board data structure.
				mainBoard[firstSwappingGem['x']][firstSwappingGem['y']] = secondSwappingGem['imageNum']
				mainBoard[secondSwappingGem['x']][secondSwappingGem['y']] = firstSwappingGem['imageNum']

				# See if this is a matching move.
				move = self.isValidMove(firstSwappingGem['x'],firstSwappingGem['y'],
					secondSwappingGem['x'], secondSwappingGem['y'])
				if not move:
					# Not a matching move: swap the gems back
					self.GAMESOUNDS['bad swap'].play()
					firstSwappingGem, secondSwappingGem = self.getSwappingGems(mainBoard, firstSelectedGem, clickedSpace)
					self.animateMovingGems(boardCopy, [firstSwappingGem, secondSwappingGem], [])
					mainBoard[firstSwappingGem['x']][firstSwappingGem['y']] = secondSwappingGem['imageNum']
					mainBoard[secondSwappingGem['x']][secondSwappingGem['y']] = firstSwappingGem['imageNum']
				else:
					nswaps += 1
					self.possible_moves = self.continueGame(mainBoard, move)
					
					if nswaps > 40:
						isGameOver = True

			# Draw the board.
			self.WINDOWSURF.fill(BGCOLOR)
			self.drawBoard(mainBoard)
			if firstSelectedGem != None:
				self.highlightSpace(firstSelectedGem[0], firstSelectedGem[1])
			if isGameOver:
				if clickContinueTextSurf == None:
					clickContinueTextSurf = self.BASICFONT.render('Final Score: %s (Click to continue)' % (self.score), 1, GAMEOVERCOLOR, GAMEOVERBGCOLOR)
					clickContinueTextRect = clickContinueTextSurf.get_rect()
					clickContinueTextRect.center = int(WINDOWWIDTH / 2), int(WINDOWHEIGHT / 2)
				self.WINDOWSURF.blit(clickContinueTextSurf, clickContinueTextRect)
			self.drawScore()
			pygame.display.update()
			self.FPSCLOCK.tick(FPS)


if __name__ == '__main__':
	game = UltraGemGame()
	game.run()
