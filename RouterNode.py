#!/usr/bin/env python
import GuiTextArea, RouterPacket, F
from copy import deepcopy

class RouterNode():
    myID = None
    myGUI = None
    sim = None
    costs = None
    routeTable = None
    distanceTable = None

    # Access simulator variables with:
    # self.sim.POISONREVERSE, self.sim.NUM_NODES, etc.

    # Example tables: Figure 5 (4 nodes)
    # node 0: 0   1   3   7		|   nexthop: 0   1   2   3
    # node 1: 1   0   1   inf  	|   nexthop: 0   1   2   inf
    # node 2: 3   1   0   2		|   nexthop: 0   1   2   3 
    # node 3: 7   inf 2   0		|   nexthop: 0   inf 2   3

    # Example tables: Figure 5 (3 nodes)
    # Initially:
    #   Node 0:
    #       Costs: [0,4,1]
    #       routeTable: [0,1,2]
    #       distanceTable: [0,4,1]
    #                      [inf,0,inf]
    #                      [inf,inf,0]
    # At end:
    #   Node 0:
    #       Costs: [0,4,1]
    #       routeTable: [0,1,2]
    #       distanceTable: [0,4,1]
    #                      [4,0,5]
    #                      [1,5,0]    

    # --------------------------------------------------
    def __init__(self, ID, sim, costs):
        self.myID = ID
        self.sim = sim
        # routeTable contains next hop
        self.routeTable = [0 for i in range(self.sim.NUM_NODES)]
        # distnceTable contains costs for us and all neighbours
        self.distanceTable =  [[0]*self.sim.NUM_NODES for i in range(self.sim.NUM_NODES)]

        self.myGUI = GuiTextArea.GuiTextArea("  Output window for Router #" + str(ID) + "  ")
        self.costs = deepcopy(costs)

        # Initialize route table
        for i in range(self.sim.NUM_NODES):
            if(self.costs[i] == self.sim.INFINITY):
                self.routeTable[i] = self.sim.INFINITY
            else:
                self.routeTable[i] = i
        # Initialize distance table
        for x in range(self.sim.NUM_NODES):
            for y in range(self.sim.NUM_NODES):
                if(x == y):
                    self.distanceTable[y][x] = 0
                elif(y == self.myID):
                    self.distanceTable[self.myID][x] = self.costs[x]
                else:
                    self.distanceTable[y][x] = self.sim.INFINITY
        
        self.updateAll()
        

    # --------------------------------------------------
    def recvUpdate(self, pkt):
        #Update our distance table with latest from neighbour
        self.distanceTable[pkt.sourceid] = pkt.mincost

        #If bellmanFord changed something then update neighbours
        if(self.bellmanFord()):
            self.updateAll()


    # --------------------------------------------------
    def sendUpdate(self, pkt):
        # Probable poison reverse location
        if(self.sim.POISONREVERSE):
            for i in range(self.sim.NUM_NODES):
                # If we find the destination id in distTable (we should always)
                if(self.distanceTable[self.myID][i] == pkt.destid):
                    pkt.mincost[i] = self.sim.INFINITY
        self.sim.toLayer2(pkt)


    # --------------------------------------------------
    def updateAll(self):
        newCosts = self.distanceTable[self.myID]
        #print("Updating all: sending costs:", newCosts)
        for i in range(self.sim.NUM_NODES):
            if(i != self.myID ): # Don't send to ourself 
                tmpPkt = RouterPacket.RouterPacket(self.myID, i, newCosts)
                self.sendUpdate(tmpPkt)


    # --------------------------------------------------
    def printTableStart(self):
        self.myGUI.print("     dst\t|") 
        for n in range(self.sim.NUM_NODES):
            self.myGUI.print('\t' + str(n))
        self.myGUI.print("\n--------")
        for n in range(self.sim.NUM_NODES):
            self.myGUI.print("---------")
        self.myGUI.print("\n")

    # --------------------------------------------------
    def printDistanceTable(self):
        self.myGUI.println("Current table for " + str(self.myID) +
                           "  at time " + str(self.sim.getClocktime()))

        # Print distance table
        self.myGUI.println("Distancetable:")
        self.printTableStart()
        for x in range(self.sim.NUM_NODES):
            # if(x != self.myID):
            self.myGUI.print(" nbr" + str(x) + "    |\t\t")
            for y in range(self.sim.NUM_NODES):
                self.myGUI.print(str(self.distanceTable[x][y]) + "\t")
            self.myGUI.print('\n')
        self.myGUI.println("")

        # Print costs and routes
        self.myGUI.println("Costs and routes:")
        self.printTableStart()
        self.myGUI.print(" cost    |\t")
        for i in range(self.sim.NUM_NODES):
            self.myGUI.print('\t'+ str(self.costs[i]))
        self.myGUI.print("\n")
        self.myGUI.print(" route   |\t")
        for i in range(self.sim.NUM_NODES):
            self.myGUI.print('\t'+ str(self.routeTable[i]))
        self.myGUI.print("\n\n")

    # --------------------------------------------------
    def updateLinkCost(self, dest, newcost):
        # print("updateLinkCost called: | Updating distanceTable", self.distanceTable[self.myID][dest], "with", newcost, "| Destination:", dest)
        # Setting both so that one can be used as 'memory' when calculating costEstimate later
        self.costs[dest] = newcost
        self.distanceTable[self.myID][dest] = newcost

        # Works without but not optimal, rougly 2x faster with
        if(self.bellmanFord()):
            self.updateAll()

    # --------------------------------------------------
    def bellmanFord(self):
        # Dx(y) = min { C(x,v) + Dv(y), Dx(y) } for each node y ∈ N
        print("bellmanFord entered:")

        updateNeighbours = False

        # First loop, for checking entire distanceTable, the x direction
        for x in range(self.sim.NUM_NODES):
            print("# for x loop entered, x =", x)
            nextNode = self.routeTable[x]                       # Which node is next after x
            toNext = self.distanceTable[self.myID][nextNode]    # Distance to nextNode from us
            nextToDest = self.distanceTable[nextNode][x]        # Distance from next to destination
            costEstimate = toNext + nextToDest                  # Total cost, cost to next + cost from next to dest

            # If stored cost is not estimated cost then we need to update our tables
            if(self.distanceTable[self.myID][x] != costEstimate):
                print(" # Stored cost != estimate statement entered, dstTable[" + str(x) + "] cost:", self.distanceTable[self.myID][x], ",estimate:", costEstimate)              
                # Check if new estimated cost is bigger than the saved cost in costs table, 
                # costEstimate is incorrect
                if(costEstimate > self.costs[x]):
                    print("  # Cost estimate too big, resetting. Estimate:", costEstimate, ", costs[" + str(x) + "]:", self.costs[x]) 
                    self.distanceTable[self.myID][x] = self.costs[x]    # Update distanceTable with costs
                    self.routeTable[x] = x                              # Update routeTable
                else:
                    print("  # Cost estimate smaller or equal to old cost, setting estimate:", costEstimate)
                    self.distanceTable[self.myID][x] = costEstimate     # Update distanceTable with estimate
                updateNeighbours = True

            # Second loop, for checking entire distanceTable, the y direction
            for y in range(self.sim.NUM_NODES):
                print(" # for y loop entered, y =", y)
                currCost = self.distanceTable[self.myID][y]
                newCost = self.distanceTable[self.myID][x] + self.distanceTable[x][y]
                
                if(newCost < currCost):
                    print("  # New cost smaller than current, setting new cost in node:", self.myID)
                    #print(" # Oldcost:", currentCost)
                    #print(" # New cost:", newCost)
                    self.distanceTable[self.myID][y] = newCost
                    self.routeTable[y] = self.routeTable[x]
                    updateNeighbours = True
        print("\n")
        return updateNeighbours