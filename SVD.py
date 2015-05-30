#!/usr/env/bin python

import numpy, scipy

# Load the data
infile = open('elements-by-episode.csv','rb')
columnNames = infile.readline().strip().split(',')[2:]
episodeNumbers = []
episodeNames = []
rows = []
for line in infile:
	line = line.strip().split(',')
	episodeNumbers.append(line[0])
	episodeNames.append(line[1].replace('"',''))
	rows.append([int(x) for x in line[2:]])

infile.close()

# SVD
dataMat = numpy.matrix(rows)

U, s, V = numpy.linalg.svd(dataMat)

outfile = open('U.csv', 'wb')
outfile.write('Episode,Name,' + ','.join([str(x+1) for x in xrange(len(episodeNames))]) + '\n')
for i,row in enumerate(U.tolist()):
	outfile.write(','.join(["%.6f" % v for v in row]) + '\n')
outfile.close()

outfile = open('SV.csv', 'wb')
outfile.write('Singular Value,' + ','.join(columnNames) + '\n')
s = s.tolist()
for i,row in enumerate(V.transpose().tolist()):
	outfile.write("%.6f," % s[i] + ','.join(["%.6f" % v for v in row]) + '\n')
outfile.close()