import matplotlib.pyplot as plt
import numpy
import sys

# row in file
iworst, irandom, ibest, ismart = 0,1,2,3
# column in statistics
nstats = 13
jstat = 0

x = []
y = []
z = []

for filename in sys.argv[1:]:
	stats = numpy.loadtxt(filename, dtype=int)
	# randomness statistic: variance in "best"
	randomness = stats[ibest,jstat + nstats] - stats[ibest,jstat] 
	#randomness = stats[irandom,jstat + nstats] - stats[irandom,jstat] 
	# intelligence statistic: difference between median smart and best
	intelligence = stats[ismart,jstat] - stats[ibest,jstat]
	# normalisation: median best
	normalisation = stats[ibest,jstat]
	goal = stats[ismart,jstat]
	
	x.append(randomness * 1. / normalisation)
	y.append(intelligence * 1. / randomness)
	#z.append(numpy.log10(normalisation+1))
	ncolors = int(filename.split('/')[1].split('_')[2])
	z.append(ncolors)
	if intelligence > randomness:
		print(filename, randomness * 1. / normalisation < 1 and intelligence * 1. / normalisation > 0.6)

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


