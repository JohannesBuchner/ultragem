import matplotlib.pyplot as plt
import numpy
import sys

numpy.random.seed(1)
scores = ['score', 'ndestroyed', 'nunlocked', 
	'nstripe', 'nbomb', 'nzapper', 22,42,44,51,52,54,55]
scores_preferences = [['nunlocked', 22,42,44,52,54,55], ['nstripe', 'nbomb', 'nzapper'], ['score']]

# row in file
#iworst, irandom, ibest, ismart = 0,1,2,3
# column in statistics
nstats = 13

x = []
y = []
z = []
game_sequence = []

for filename in sys.argv[1:]:
	# has 26 rows, because there are 13 scores and each is measure twice
	ncolors = int(filename.split('/')[1].split('_')[2])
	best = numpy.loadtxt(filename + '/best.txt', dtype=int).reshape((-1, 2, 13))
	random = numpy.loadtxt(filename + '/random.txt', dtype=int).reshape((-1, 2, 13))
	smart = numpy.loadtxt(filename + '/smart.txt', dtype=int).reshape((-1, 2, 13))
	board = open(filename + '/board.txt').read()
	used = False
	for scoregroup in scores_preferences:
		js = [scores.index(scorename) for scorename in scoregroup]
		numpy.random.shuffle(js)
		for goalid in js:
			# randomness statistic: variance in "best"
			randomness = best[:,1,goalid] - best[:,0,goalid]
			# intelligence statistic: difference between median smart and best
			intelligence = smart[:,0,goalid] - best[:,0,goalid]
			# normalisation: median best
			normalisation = best[:,0,goalid]
			goal = smart[:,0,goalid]
			nsteps = numpy.arange(len(smart)) + 1
			
			# choose number of swaps
			mask = numpy.logical_and(numpy.logical_and(goal > 0, nsteps >= 10), 
				intelligence > randomness*0.75)
			mask1 = numpy.logical_and(mask, goal > 1)

			if mask.sum() <= 1:
				continue
			used = True
			
			# lets prefer longer games with 2 items
			if mask1.sum() > 1:
				idxmin = numpy.where(mask1)[0][1]
			else:
				idxmin = numpy.where(mask)[0][1]
			
			ngoal = goal[idxmin]
			
			difficulty_estimate = random[idxmin,1,goalid] * 1. / smart[idxmin,0,goalid]
			game_sequence.append((int(difficulty_estimate*20)/20., board, ncolors, idxmin, goalid, ngoal))
			break
			
	
	x.append((randomness * 1. / normalisation)[-1])
	y.append((intelligence * 1. / randomness)[-1])
	z.append(ncolors)

x = numpy.asarray(x)
y = numpy.asarray(y)
z = numpy.asarray(z)
plt.scatter(x, y, c=z)
plt.xlabel('randomness')
#plt.xscale('log')
#plt.yscale('log')
plt.ylabel('intelligence')
plt.xlim(0, 3)
#hi = max(x.max(), y.max())
#lo = min(x.max(), y.max())
#plt.xlim(0, hi)
#plt.ylim(0, hi)
#plt.plot([0,lo], [0,lo], color='k', lw=1)
plt.colorbar()
plt.savefig('stats.pdf', bbox_inches='tight')
plt.close()

#import random
#random.seed(1)
#random.shuffle(game_sequence)

last_game = None
last_goalid = 0
last_goalgroup = -1
last_ncolors = 0
i = 0
goal_groups = {}
for j, scoregroup in enumerate(scores_preferences):
	for score in scoregroup:
		goal_groups[scores.index(score)] = j
print(goal_groups)

while game_sequence:
	# select probabilistically -- decrease probability if similar to previous
	# decrease if hard
	
	score = [1/(0.05 + difficulty + (goalid == last_goalid)*1 + (goal_groups[goalid] == goal_groups[last_goalid])*10 + (last_ncolors == ncolors)*2) 
		for difficulty, board, ncolors, nswaps, goalid, ngoal in game_sequence]
	score = numpy.array(score)
	score /= score.sum()
	j = numpy.random.choice(range(len(game_sequence)), p=score)
	i += 1
	difficulty, board, ncolors, nswaps, goalid, ngoal = game_sequence.pop(j)
	print(difficulty, ncolors, scores[goalid], ngoal)
	with open('journey-auto/%d' % (i), 'w') as f:
		f.write('NCOLORS: %d\n' % ncolors)
		f.write('MAXSWAPS: %d\n' % nswaps)
		f.write('GOALNAME: %s\n' % scores[goalid])
		f.write('GOALID: %d\n' % goalid)
		f.write('NMIN: %d\n' % ngoal)
		f.write('DIFFICULTY: %.2f\n' % difficulty)
		f.write(board)
print()
print(len(game_sequence))

