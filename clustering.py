#!/usr/env/bin python

import json, random

class Painting:
    def __init__(self, name, season, episode, elements):
        self.name = name
        self.season = season
        self.episode = episode
        self.elements = elements
        self.clusterDistances = {}
    
    def resetClusterDistances(self):
        self.clusterDistances = {}
    
    def toDict(self):
        return { 'name' : self.name, 'season' : self.season, 'episode' : self.episode, 'clusterDistances' : self.clusterDistances}
        
    def __iter__(self):
        return self.iterChildren()
    
    def iterChildren(self):
        yield self  # we're a leaf, so there's only one thing to iterate over
    
    @staticmethod
    def jaccardDistance(paintingA, paintingB):
        if len(paintingA.elements.union(paintingB.elements)) == 0:
            # some paintings have no elements flagged... for our purposes, we can't tell a distance between them
            return 0.0
        similarity = len(paintingA.elements.intersection(paintingB.elements)) / float(len(paintingA.elements.union(paintingB.elements)))
        return 1.0 - similarity

class Element:
    def __init__(self, name, paintings):
        self.name = name
        self.paintings = paintings
        self.clusterDistances = {}
    
    def resetClusterDistances(self):
        self.clusterDistances = {}
    
    def toDict(self):
        return { 'name' : self.name, 'clusterDistances' : self.clusterDistances }
    
    def __iter__(self):
        return self.iterChildren()
    
    def iterChildren(self):
        yield self  # we're a leaf, so there's only one thing to iterate over
    
    @staticmethod
    def jaccardDistance(elementA, elementB):
        if len(elementA.paintings.union(elementB.paintings)) == 0:
            # some elements have no elements flagged... for our purposes, we can't tell a distance between them
            return 0.0
        similarity = len(elementA.paintings.intersection(elementB.paintings)) / float(len(elementA.paintings.union(elementB.paintings)))
        return 1.0 - similarity

class Parent:
    def __init__(self, leftChildren, rightChildren):
        self.leftChildren = leftChildren
        self.rightChildren = rightChildren
    
    def __iter__(self):
        return self.iterChildren()
    
    def iterChildren(self):
        if not isinstance(self.leftChildren, Parent):
            yield self.leftChildren
        else:
            for p in self.leftChildren.iterChildren():
                yield p
        if not isinstance(self.rightChildren, Parent):
            yield self.rightChildren
        else:
            for p in self.rightChildren.iterChildren():
                yield p
    
    def toDict(self):
        return { 'name' : '', 'children' : [self.leftChildren.toDict(), self.rightChildren.toDict()] }

def loadData():
    infile = open('elements-by-episode.csv','rb')
    columnNames = infile.readline().strip().split(',')[2:]
    elements = [Element(c, set()) for c in columnNames]
    paintings = []
    for line in infile:
        line = line.strip().split(',')
        temp = []
        for i,x in enumerate(line[2:]):
            if x == '1':
                temp.append(columnNames[i])
                elements[i].paintings.add(line[0])
        paintings.append(Painting(line[1].replace('"',''), int(line[0][1:3]), int(line[0][4:6]), set(temp)))

    infile.close()
    
    return (elements, paintings)

def writeCenteredClusters(clusters, centers, cost, path):
    outfile = open(path, 'wb')
    result = {'cost' : cost, 'centers' : [], 'points' : []}
    for i,c in enumerate(centers):
        result['centers'].append(c.name)
        for p in clusters[i]:
            temp = p.toDict()
            temp['center'] = c.name
            result['points'].append(temp)
    outfile.write(json.dumps(result))
    outfile.close()


################ kMedioids ########################

def kMedioidsStep(data, clusters, centers, cost, distanceFunction):
    for i, center in enumerate(centers):
        minCost = float('inf')
        newCenter = None
        for pCenter in clusters[i]:
            # what is the cost if p is the new center?
            cost = 0
            for p in clusters[i]:
                cost += distanceFunction(pCenter, p)
            if cost < minCost:
                minCost = cost
                newCenter = pCenter
        centers[i] = newCenter
    
    clusters = [set([c]) for c in centers]
    
    totalCost = 0.0
    for p in data:
        minDistance = float('inf')
        closestCenter = None
        p.resetClusterDistances()
        for i,c in enumerate(centers):
            distance = distanceFunction(p,c)
            p.clusterDistances[c.name] = distance
            if distance < minDistance:
                minDistance = distance
                closestCenter = i
        clusters[closestCenter].add(p)
        totalCost += minDistance
    return (clusters, centers, totalCost)

def kMedioidsUntilConvergence(data, clusters, centers, cost, distanceFunction):
    lastCenters = None
    while True:
        if lastCenters != None:
            sameCenters = True
            for i,c in enumerate(lastCenters):
                if c != centers[i]:
                    sameCenters = False
                    break
            if sameCenters:
                break
        lastCenters = centers
        clusters, centers, cost = kMedioidsStep(data, clusters, centers, cost, distanceFunction)
    return (clusters, centers, cost)

############# Hierarchical clustering ################
def hierarchicalCluster(data, maxClusters, distanceStrategy, distanceFunction):
    clusters = [p for p in data]    # need a shallow copy of the array
    
    while len(clusters) > maxClusters:
        minDistance = float('inf')
        iToMerge = None
        jToMerge = None
        for i, c_i in enumerate(clusters):
            for j, c_j in enumerate(clusters[i+1:]):
                j = i+j+1
                distance = distanceStrategy(distanceFunction, c_i, c_j)
                if distance < minDistance:
                    minDistance = distance
                    iToMerge = i
                    jToMerge = j
        clusters[iToMerge] = Parent(clusters[iToMerge], clusters.pop(jToMerge))
    return clusters

def singleLinkDistance(distanceFunction, setA, setB):
    # return the shortest link length
    minDistance = float('inf')
    for a in setA:
        for b in setB:
            distance = distanceFunction(a,b)
            minDistance = min(minDistance, distance)
    return minDistance

def completeLinkDistance(distanceFunction, setA, setB):
    # return the longest link length
    maxDistance = -1.0
    for a in setA:
        for b in setB:
            distance = distanceFunction(a,b)
            maxDistance = max(maxDistance, distance)
    return maxDistance

def meanLinkDistance(distanceFunction, setA, setB):
    # return the mean link length
    distance = 0.0
    count = 0
    for a in setA:
        for b in setB:
            distance += distanceFunction(a,b)
            count += 1
    return distance / count

def jsonifyHierarchicalClusters(clusters, path):
    outfile = open(path, 'wb')
    outfile.write(json.dumps({'name' : 'root', 'children' : [c.toDict() for c in clusters]}))
    outfile.close()

def runHierarchicalClustering(elements, paintings, clusterRange):
    print 'Computing single-link distance painting clusters...'
    clusters = hierarchicalCluster(paintings, clusterRange[0], singleLinkDistance, Painting.jaccardDistance)
    print 'Writing results...'
    jsonifyHierarchicalClusters(clusters, 'singleLinkPaintings.json')
    
    print 'Computing single-link distance element clusters...'
    clusters = hierarchicalCluster(elements, clusterRange[0], singleLinkDistance, Element.jaccardDistance)
    print 'Writing results...'
    jsonifyHierarchicalClusters(clusters, 'singleLinkElements.json')
    
    print 'Computing complete-link distance painting clusters...'
    clusters = hierarchicalCluster(paintings, clusterRange[0], completeLinkDistance, Painting.jaccardDistance)
    print 'Writing results...'
    jsonifyHierarchicalClusters(clusters, 'completeLinkPaintings.json')
    
    print 'Computing single-link distance element clusters...'
    clusters = hierarchicalCluster(elements, clusterRange[0], completeLinkDistance, Element.jaccardDistance)
    print 'Writing results...'
    jsonifyHierarchicalClusters(clusters, 'completeLinkElements.json')
    
    print 'Computing mean-link distance painting clusters...'
    clusters = hierarchicalCluster(paintings, clusterRange[0], meanLinkDistance, Painting.jaccardDistance)
    print 'Writing results...'
    jsonifyHierarchicalClusters(clusters, 'meanLinkPaintings.json')
    
    print 'Computing mean-link distance element clusters...'
    clusters = hierarchicalCluster(elements, clusterRange[0], meanLinkDistance, Element.jaccardDistance)
    print 'Writing results...'
    jsonifyHierarchicalClusters(clusters, 'meanLinkElements.json')


################ Gonzalez Clustering ###################

def gonzalezCluster(data, numClusters, distanceFunction):
    clusterCenters = [random.choice(data)]
    
    while len(clusterCenters) < numClusters:
        maxDistance = -1.0
        farthestPoint = None
        for p in data:
            distance = 0.0
            for c in clusterCenters:
                distance += distanceFunction(p,c)
            if distance > maxDistance:
                maxDistance = distance
                farthestPoint = p
        clusterCenters.append(farthestPoint)
    
    clusters = [set([c]) for c in clusterCenters]
    
    totalCost = 0.0
    for p in data:
        minDistance = float('inf')
        closestCenter = None
        p.resetClusterDistances()
        for i,c in enumerate(clusterCenters):
            distance = distanceFunction(p,c)
            p.clusterDistances[c.name] = distance
            if distance < minDistance:
                minDistance = distance
                closestCenter = i
        clusters[closestCenter].add(p)
        totalCost += minDistance
    return (clusters, clusterCenters, totalCost)

def runGonzalezClustering(elements, paintings, clusterRange):
    for c in xrange(*clusterRange):
        print 'Computing ' + str(c) + '-center Gonzalez painting clusters...'
        clusters, centers, totalCost = gonzalezCluster(paintings, c, Painting.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'gonzalez_' + str(c) + '_paintings.json')
        print 'Running k-Medioids until convergence...'
        clusters, centers, totalCost = kMedioidsUntilConvergence(paintings, clusters, centers, totalCost, Painting.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'gonzalezMedioids_' + str(c) + '_paintings.json')
    for c in xrange(*clusterRange):
        print 'Computing ' + str(c) + '-center Gonzalez element clusters...'
        clusters, centers, totalCost = gonzalezCluster(elements, c, Element.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'gonzalez_' + str(c) + '_elements.json')
        print 'Running k-Medioids until convergence...'
        clusters, centers, totalCost = kMedioidsUntilConvergence(elements, clusters, centers, totalCost, Element.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'gonzalezMedioids_' + str(c) + '_elements.json')

################# kMeans++ Clustering ####################

def kMeansPlusPlusCluster(data, numClusters, distanceFunction):
    clusterCenters = [random.choice(data)]
    
    while len(clusterCenters) < numClusters:
        distances = []
        totalDistance = 0.0
        for p in data:
            distance = float('inf')
            for c in clusterCenters:
                distance = min(distance, distanceFunction(p,c))
            totalDistance += distance
            distances.append(distance)
        sample = random.random()*totalDistance
        for i,d in enumerate(distances):
            sample = sample - d
            if sample < 0:
                clusterCenters.append(data[i])
                break
    
    clusters = [set([c]) for c in clusterCenters]
    
    totalCost = 0.0
    for p in data:
        minDistance = float('inf')
        closestCenter = None
        p.resetClusterDistances()
        for i,c in enumerate(clusterCenters):
            distance = distanceFunction(p,c)
            p.clusterDistances[c.name] = distance
            if distance < minDistance:
                minDistance = distance
                closestCenter = i
        clusters[closestCenter].add(p)
        totalCost += minDistance
    return (clusters, clusterCenters, totalCost)

def runkMeansPlusPlusClustering(elements, paintings, clusterRange):
    for c in xrange(*clusterRange):
        print 'Computing ' + str(c) + '-center kMeans++ painting clusters...'
        clusters, centers, totalCost = kMeansPlusPlusCluster(paintings, c, Painting.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'kMeansPlusPlus_' + str(c) + '_paintings.json')
        print 'Running k-Medioids until convergence...'
        clusters, centers, totalCost = kMedioidsUntilConvergence(paintings, clusters, centers, totalCost, Painting.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'kMeansPlusPlusMedioids_' + str(c) + '_paintings.json')
    for c in xrange(*clusterRange):
        print 'Computing ' + str(c) + '-center kMeans++ element clusters...'
        clusters, centers, totalCost = kMeansPlusPlusCluster(elements, c, Element.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'kMeansPlusPlus_' + str(c) + '_elements.json')
        print 'Running k-Medioids until convergence...'
        clusters, centers, totalCost = kMedioidsUntilConvergence(elements, clusters, centers, totalCost, Element.jaccardDistance)
        print 'Writing results...'
        writeCenteredClusters(clusters, centers, totalCost, 'kMeansPlusPlusMedioids_' + str(c) + '_elements.json')

if __name__ == '__main__':
    elements, paintings = loadData()
    
    #runHierarchicalClustering(elements, paintings, (1, 1))
    runGonzalezClustering(elements, paintings, (2, 11))
    runkMeansPlusPlusClustering(elements, paintings, (2, 11))