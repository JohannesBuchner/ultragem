from gemengine import *
import scipy.stats
import os

def scoring_function(events):
	nspecial = [0, 0, 0]
	ncombispecial_index = {22:0,42:1,44:2,51:3,52:4,54:5,55:6}
	ncombispecial = [0, 0, 0, 0, 0, 0, 0]
	nunlocked = 0
	ndestroyed = 0
	score = 0
	for type, value in events:
		if type == 'activated':
			if value in (2,3):
				nspecial[0] += 1
			elif value == 4:
				nspecial[1] += 1
			elif value == 5:
				nspecial[2] += 1
			score += 10 * value
		elif type == 'unlocked':
			nunlocked += value
		elif type == 'destroyed':
			ndestroyed += value
			score += value
		elif type == 'combined':
			ncombispecial[ncombispecial_index[value]] += 1
	return [score, ndestroyed, nunlocked] + nspecial + ncombispecial

def create_scenario(nrows, ncols, ncolors, seed):
	rng = numpy.random.RandomState(seed)
	board = Board(nrows=nrows, ncols=ncols)
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
	topfill = NastyTopFiller(board, ncolors=ncolors)
	return board, topfill

def create_scenario_unique(nrows, ncols, ncolors, seed):
	board, topfill = create_scenario(nrows, ncols, ncolors, seed)
	for i in range(1, seed):
		board2, _ = create_scenario(nrows, ncols, ncolors, i)
		if (board2.status == board.status).all() and (board2.type == board.type).all() and (board2.color == board.color).all():
			raise Exception("Board with seed=%d same as seed=%d" % (i, seed))
	return board, topfill


scenario = list(map(int,sys.argv[1:]))

board, topfill = create_scenario_unique(*scenario)
print('ANALYSING SCENARIO:', ' '.join(['%d' % i for i in scenario]))
print(board)

with open('gamestats/%s-board.txt' % '_'.join(['%d' % i for i in scenario]), 'w') as f:
	f.write(str(board))

maxswaps = 40
Nruns = 40
verbose = False

output = []
outfilename = 'gamestats/%s.txt' % '_'.join(['%d' % i for i in scenario])

if os.path.exists(outfilename):
	print('Already analysed.')
	sys.exit(0)

for move_selector, selector_name in zip([worst_move_selector, random_move_selector, best_move_selector, smart_move_selector], ['worst', 'random', 'best', 'smart']):
	scores = []
	for run in range(Nruns):
		sys.stderr.write('Game %d/%d with strategy "%s" ...   \r' % (run+1,Nruns, selector_name))
		numpy.random.seed((run+1))
		board, topfill = create_scenario(*scenario)
		grav = BoardGravityPuller(board)
		comb = Combiner(board)
		paircomb = PairCombiner(board)
		acto = Activater(board)
		
		nstep = 0
		ncomb = 0
		nswaps = 0
		nshuffles = 0
		while True:
			# dropping phase
			anychange = True
			while anychange:
				nstep += 1
				if verbose: print(('STEP %d' % nstep))
				anychange = grav.run()
				if anychange: 
					if verbose: print(board, 'grav')
				nstep += 1
				if verbose: print(('STEP %d' % nstep))
				anychange += topfill.run()
				if anychange: 
					if verbose: print(board, 'topfill')
			
			nstep += 1
			if verbose: print(('STEP %d: combining phase...' % nstep))
			# combining phase
			anychange  = comb.run()
			if anychange:
				if verbose: print(board)
			nstep += 1
			if verbose: print(('STEP %d: activation...' % nstep))
			anychange += acto.run()
			if anychange:
				ncomb += 1
				nstep += 1
				if verbose: print(board)
				continue
			
			if nswaps >= maxswaps:
				if verbose: print('moves used up.')
				break
			if ncomb > (nswaps + 1) * 40:
				if selector_name in ['random', 'worst']:
					raise Exception('STOPPING UNPLAYABLE GAME (many shuffles)')
				else:
					print('STOPPING TRIVIAL GAME')
					break
			if nshuffles > 100:
				if selector_name != 'random':
					print('STOPPING UNPLAYABLE GAME (many shuffles)')
					break
				else:
					raise Exception('STOPPING UNPLAYABLE GAME (many shuffles)')
					break
			# ok, the board settled down now
			# we should ask the agent/user what they want to do now
			nstep += 1
			if verbose: print(('STEP %d: finding valid moves ...' % nstep))
			moves = list(paircomb.enumerate_valid_moves())
			if len(moves) == 0:
				# no moves left -- shuffle
				if verbose: print(('STEP %d: shuffling ...' % nstep))
				nshuffles += 1
				paircomb.shuffle()
				if verbose: print(board)
				continue
				
			#for fromj,fromi,toj,toi in moves:
			#	print '  could swap %d|%d -> %d|%d' % (fromj,fromi,toj,toi)
			
			# move selector
			move = move_selector(board, moves)
			
			nstep += 1
			if verbose: print(('STEP %d: swapping ...' % nstep))
			paircomb.run(*move)
			nswaps += 1
			comb.set_last_interaction(*move)
			if verbose: print(board)

			nstep += 1
			if verbose: print(('STEP %d: combining phase...' % nstep))
			# combining phase
			anychange  = comb.run()
			if anychange:
				if verbose: print(board)

			nstep += 1
			if verbose: print(('STEP %d: activation...' % nstep))
			anychange += acto.run()
			if anychange:
				nstep += 1
				if verbose: print(board)
				continue
		scores.append(scoring_function(board.events))
	
	sys.stderr.write('\n')
	scores = numpy.array(scores)
	print(selector_name)
	q = scipy.stats.mstats.mquantiles(scores, [0.5, 0.95], axis=0).astype(int)
	print(q)
	output.append(q.flatten())

numpy.savetxt(outfilename, output, header='scores for worst/random/best/smart move selector strategies. scores are 50% and 95% quantiles (based on 40 games) of: game score, #destroyed, #unlocked, #stripes, #bombs, #zappers', fmt='%d')


