from gemengine import *

def check_board(test_steps, steps, prevboard2, newboard2):
	steps.append((prevboard2, newboard2))
	print('TESTING STEP %d' % len(steps))
	if test_steps is None:
		return
	prevboard, newboard = test_steps.pop(0)
	for a,b in [(prevboard, prevboard2), (newboard, newboard2)]:
		#assert a.events == b.events, (a.events, b.events)
		assert numpy.all(a.type == b.type), (a.type, b.type)
		assert numpy.all(a.color == b.color), (a.color, b.color)
		assert numpy.all(a.status == b.status), (a.status, b.status)

def run_scenario(scenario):
	numpy.random.seed(1)
	maxswaps = 40
	test_steps = []
	for prevtype, prevcolor, prevstatus, nexttype, nextcolor, nextstatus in numpy.load('testdata_%s.npy' % scenario):
		nrows,ncols = prevtype.shape
		prevboard = Board(nrows=nrows,ncols=ncols)
		prevboard.type = prevtype
		prevboard.color = prevcolor
		prevboard.status = prevstatus
		nextboard = Board(nrows=nrows,ncols=ncols)
		nextboard.type = nexttype
		nextboard.color = nextcolor
		nextboard.status = nextstatus
		test_steps.append((prevboard, nextboard))
	#test_steps = None
	steps = []
	if scenario == 0:
		board = Board(nrows=10, ncols=10)
		before = board.copy()
		InitialFiller(board, double_locked_rows=2, double_locked_cols=2).run()
		check_board(test_steps, steps, before, board.copy())
		topfill = TopFiller(board, ncolors=3)
	elif scenario == 1:
		board = Board(nrows=10, ncols=10)
		before = board.copy()
		InitialFiller(board, double_locked_rows=2, double_locked_cols=2).run()
		check_board(test_steps, steps, before, board.copy())
		topfill = TopFiller(board, ncolors=4)
	elif scenario == 2:
		board = Board(nrows=6, ncols=6)
		before = board.copy()
		InitialFiller(board).run()
		check_board(test_steps, steps, before, board.copy())
		topfill = TopFiller(board, ncolors=6)
	
	move_selector = random_move_selector
	waitfunction = lambda: None
	
	before = board.copy()
	grav = BoardGravityPuller(board)
	comb = Combiner(board)
	paircomb = PairCombiner(board)
	acto = Activater(board)
	check_board(test_steps, steps, before, board.copy())
	
	nstep = 0
	ncomb = 0
	nswaps = 0
	while True:
		# dropping phase
		while True:
			nstep += 1
			print(('STEP %d' % nstep))
			before = board.copy()
			anychange = grav.run()
			if anychange: 
				print(board, 'grav')
				waitfunction()
			check_board(test_steps, steps, before, board.copy())
			nstep += 1
			print(('STEP %d' % nstep))
			before = board.copy()
			anychange += topfill.run()
			check_board(test_steps, steps, before, board.copy())
			if anychange: 
				print(board, 'topfill')
				waitfunction()
			if not anychange:
				break
		
		nstep += 1
		print(('STEP %d: combining phase...' % nstep))
		before = board.copy()
		# combining phase
		anychange  = comb.run()
		check_board(test_steps, steps, before, board.copy())
		if anychange:
			print(board)
			waitfunction()
		nstep += 1
		print(('STEP %d: activation...' % nstep))
		before = board.copy()
		anychange += acto.run()
		check_board(test_steps, steps, before, board.copy())
		if anychange:
			ncomb += 1
			nstep += 1
			print(board)
			waitfunction()
			continue
		
		if nswaps >= maxswaps:
			print('moves used up.')
			break
		if ncomb > (nswaps + 1) * 40:
			print('STOPPING TRIVIAL GAME')
			break
		# ok, the board settled down now
		# we should ask the agent/user what they want to do now
		nstep += 1
		print(('STEP %d: finding valid moves ...' % nstep))
		before = board.copy()
		moves = list(paircomb.enumerate_valid_moves())
		check_board(test_steps, steps, before, board.copy())
		if len(moves) == 0:
			# no moves left -- shuffle
			print(('STEP %d: shuffling ...' % nstep))
			paircomb.shuffle()
			print(board)
			continue
			
		#for fromj,fromi,toj,toi in moves:
		#	print '  could swap %d|%d -> %d|%d' % (fromj,fromi,toj,toi)
		
		# move selector
		move = move_selector(board, moves)
		
		nstep += 1
		print(('STEP %d: swapping ...' % nstep))
		before = board.copy()
		paircomb.run(*move)
		check_board(test_steps, steps, before, board.copy())
		nswaps += 1
		comb.set_last_interaction(*move)
		print(board)

		nstep += 1
		print(('STEP %d: combining phase...' % nstep))
		# combining phase
		before = board.copy()
		anychange  = comb.run()
		check_board(test_steps, steps, before, board.copy())
		if anychange:
			print(board)
			waitfunction()

		nstep += 1
		print(('STEP %d: activation...' % nstep))
		before = board.copy()
		anychange += acto.run()
		check_board(test_steps, steps, before, board.copy())
		if anychange:
			nstep += 1
			print(board)
			waitfunction()
			continue
	
	# store 
	numpy.save('testdata_%s_proposed.npy' % scenario, numpy.array([[prevboard.type,prevboard.color,prevboard.status,nextboard.type,nextboard.color,nextboard.status] for prevboard, nextboard in steps]))
	
if __name__ == '__main__':
	run_scenario(0)
	run_scenario(1)
	run_scenario(2)

