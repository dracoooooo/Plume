#!/usr/bin/env python3
from monosat import *
import argparse
from itertools import tee
import random
def pairwise(iterable):
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)
parser = argparse.ArgumentParser(description='BGAMapper')


parser.add_argument("--seed",type=int,help="Random seed",default=None)


parser.add_argument('--decide-theories',dest='decide_theories',help="Show stats",action='store_true')
parser.add_argument('--no-decide-theories',dest='decide_theories',help="",action='store_false')
parser.set_defaults(decide_theories=False)

parser.add_argument('--stats',dest='stats',help="Show stats",action='store_true')
parser.add_argument('--no-stats',dest='stats',help="",action='store_false')
parser.set_defaults(stats=True)

parser.add_argument("--width",type=int,help="Width of grid",default=10)
parser.add_argument("--height",type=int,help="Height of grid (=width if unset)",default=None)

parser.add_argument("--constraints",type=float,help="Multiple of the edges number of random, at-most-one cardinality constraints to add (default: 2)",default=5)
parser.add_argument("--clause-size",type=int,help="Number of edges in each random at-most-one constraint (>1)",default=2)
#parser.add_argument("-n",type=int,help="Number of reachability constraints",default=1)
parser.add_argument("--max-flow-percent",type=float,help="Max flow in graph as percentage of grid width  ",default=None)
parser.add_argument("--max-flow",type=int,help="Max flow in graph as percentage of grid width  ",default=2)
args = parser.parse_args()

if args.height is None:
    args.height = args.width

if args.seed is None:
    args.seed = random.randint(1,1000000)
print("Random seed: %d"%(args.seed))
random.seed(args.seed)
Monosat().newSolver("-verb=1 -rnd-seed=%d -theory-order-vsids -vsids-both %s   -lazy-maxflow-decisions -conflict-min-cut -conflict-min-cut-maxflow -reach-underapprox-cnf "%(args.seed, "-decide-theories" if args.decide_theories else "-no-decide-theories" ))
g= Graph()

source = g.addNode()
dest = g.addNode()

grid = dict()
nodes = dict()
for x in range(args.width):
    for y in range(args.height):
        grid[(x,y)] = g.addNode()
        nodes[grid[(x,y)]] = (x,y)

for x in range(args.width):
    Assert(g.addEdge(source,grid[x,0]))
    Assert(g.addEdge(grid[x,args.height-1],dest))

edges = dict()
edgemap = dict()
for x in range(args.width):
    for y in range(args.height):
        n1 = (x,y)
        if x+1 < args.width:
            n2 = (x+1,y)
            #print(str(n1) + "->" + str(n2))
            edges[(n1,n2)] = e1 = g.addEdge(grid[n1],grid[n2])
            edges[(n2,n1)] = e1b = g.addEdge(grid[n2],grid[n1])
            edgemap[e1]  = (n1,n2)
            edgemap[e1b]  = (n2,n1)
        if y+1 < args.height:
            n2 = (x,y+1)
            edges[(n1,n2)] = e2 = g.addEdge(grid[n1],grid[n2])
            edges[(n2,n1)] = e2b = g.addEdge(grid[n2],grid[n1])
            edgemap[e2]  = (n1,n2)
            edgemap[e2b]  = (n2,n1)

edgelist = list(edges.values())

n_constraints = int(args.constraints * len(edgelist))
print("#nodes %d #edges %d, #constraints %d"%(g.numNodes() ,g.numEdges(), n_constraints))
for n in range(n_constraints):
    n1 = random.randint(0,len(edgelist)-1)
    n2 = random.randint(0,len(edgelist)-2)
    if n2 >= n1:
        n2+=1

    AssertLessEqPB((edgelist[n1], edgelist[n2] ), 1) #At most one of these edges may be selected

#top left node must reach bottom right node, with a path of not more than max_distance steps
if args.max_flow_percent is not None:
    mf =  int(args.max_flow * args.width)
else:
    mf = args.max_flow
maxflow = g.maxFlowGreaterOrEqualTo(source, dest, mf)
Assert(maxflow)
print("Maxflow is %d"%(mf))
print("Solving...")
result = Solve()
print(result)

if result:
    #If the result is SAT, you can find the nodes that make up a satisfying path:
    flow = g.getMaxFlow(maxflow)
    print("Maxflow = %d"%(flow))
    assert(flow>=mf)

    pathset = set()
    for e in edgelist:
        v = e.value()
        if g.getEdgeFlow(maxflow,e,False)>0:
            assert(v)
            pathset.add(edgemap[e])

    for y in range(args.width):
        curline = ""
        nextline = ""
        for x in range(args.height):
            n1 = (x,y)
            curline +=(".")

            if x+1 < args.width:
                n2 = (x+1,y)
                #print(str(n1) + "->" + str(n2))
                #if edges[(n1,n2)].value() and edges[(n2,n1)].value():
                if (n1,n2) in pathset and (n2,n1) in pathset:
                    curline+=("↔")
                elif (n1,n2)in pathset:
                #elif edges[(n1,n2)].value():
                    curline+=("→")
                elif (n2,n1) in pathset:
                #elif edges[(n2,n1)].value():
                    curline+=("←")
                else:
                    curline+=(" ")
            if y+1 < args.height:
                n2 = (x,y+1)
                #if edges[(n1,n2)].value() and edges[(n2,n1)].value():
                if (n1,n2) in pathset and (n2,n1) in pathset:
                    nextline+=("↕")
                #elif edges[(n1,n2)].value():
                elif (n1,n2)in pathset:
                    nextline+=("↓")
                #elif edges[(n2,n1)].value():
                elif (n2,n1) in pathset:
                    nextline+=("↑")
                else:
                    nextline+=(" ")
            nextline += (" ")
        print(curline)
        print(nextline)