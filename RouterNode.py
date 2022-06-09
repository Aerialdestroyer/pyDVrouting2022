#!/usr/bin/env python
from asyncio.windows_events import NULL
import GuiTextArea, RouterPacket, F
from copy import deepcopy

#### TODO ####
# - Node 2 poison reverse not quite working

class RouterNode():
    myID = None
    myGUI = None
    sim = None
    costs = None
    routeTable = None
    distanceTable = None

    # --------------------------------------------------
    # Initialize all tables/variables                   
    # --------------------------------------------------
    def __init__(self, ID, sim, costs):
        self.myID = ID
        self.sim = sim

        # routeTable contains next hop
        self.routeTable = [0 for i in range(self.sim.NUM_NODES)]

        # distnceTable contains costs for us and all neighbours, initiated the same
        # way as connectcosts in RouterSimulator.py
        self.distanceTable = [[0]*self.sim.NUM_NODES for i in range(self.sim.NUM_NODES)]

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
    # Recieves updates from other nodes
    # --------------------------------------------------
    def recvUpdate(self, pkt):
        #Update our distance table with latest from neighbour
        self.distanceTable[pkt.sourceid] = pkt.mincost

        # Run bellmanFord to check for changes and find better route if necessary
        # If bellmanFord changed something/found change then update neighbours
        if(self.bellmanFord()):
            self.updateAll()


    # --------------------------------------------------
    # Sends updates to other nodes
    # --------------------------------------------------
    def sendUpdate(self, pkt):
        # if 0 routes through 2 to get to destination 1, then 0 will advertise 
        # to 2 that its distance to 1 is infinity

        # Which routes routes should be poisoned (in 3 nodes casee)? :
        # 1 -> 0 and 0 -> 1 
        #   1 and 0 route through 2 to get to each other
        #   1 advertises to 2 that cost to 0 is 999
        #   0 advertises to 2 that cost to 1 is 999
        # Possibly 2 -> 1 and 1 -> 2 at start

        # if(self.sim.POISONREVERSE):
        #     for i in range(self.sim.NUM_NODES):
        #         # Find nodes that don't use a direct route (routes via another node to 
        #         # destination)
        #         if(self.routeTable[i] == pkt.destid):
        #             pkt.mincost[i] = self.sim.INFINITY

        if(self.sim.POISONREVERSE):
            for i in range(self.sim.NUM_NODES):
                for j in range(self.sim.NUM_NODES):
                    # Check that current package destination is in routeTable 
                    if(pkt.destid == self.routeTable[j]):
                        # Find nodes that don't use a direct route (routes via another node to 
                        # destination) and poison the direct route
                        # self.routeTable[j] == i, find i in routeTable
                        # i != j, i does not route directly to j  
                        if(self.routeTable[j] == i and i != j):
                            pkt.mincost[j] = self.sim.INFINITY
                        else:
                            pkt.mincost[j] = self.costs[j]

        # pkt.mincost = self.doPoison()

        self.sim.toLayer2(pkt)

        
    # --------------------------------------------------
    # The poison reverse algorithm
    # --------------------------------------------------
    def doPoison(self):
        for i in range(self.sim.NUM_NODES):
            if(self.costs[i] != 0 and self.costs[i] != self.sim.INFINITY):
                if(self.sim.POISONREVERSE):
                    for j in range(self.sim.NUM_NODES):
                        if(self.routeTable[j] == i and i != j):
                            self.costs[i] = self.sim.INFINITY
                            print("Poison:")
                            print(" # Src:", self.myID)
                            # print(" # Dest:", NULL)
                            print(" # pCosts:", self.costs)


    # --------------------------------------------------
    # Updates all nodes that are not us
    # --------------------------------------------------
    def updateAll(self):
        newCosts = self.distanceTable[self.myID]
        for i in range(self.sim.NUM_NODES):
            if(i != self.myID): # Don't send to ourself 
                tmpPkt = RouterPacket.RouterPacket(self.myID, i, newCosts)
                self.sendUpdate(tmpPkt)


    # --------------------------------------------------
    # Prints the start of our tables, needed multiple times thus function
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
    # Prints rest of tables
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
    # Recieves updates when a link-cost change event happens
    # --------------------------------------------------
    def updateLinkCost(self, dest, newcost):
        # Setting both so that one can be used as 'memory' when calculating 
        # costEstimate later
        self.costs[dest] = newcost
        self.distanceTable[self.myID][dest] = newcost

        # Works without bellmanFord since we run on recieve but not optimal, 
        # rougly 2x faster with
        if(self.bellmanFord()):
            self.updateAll()

    # --------------------------------------------------
    # Algorithm that finds best/fastest route
    # --------------------------------------------------
    def bellmanFord(self):
        updateNeighbours = False

        # self.doPoison()

        # First loop, for checking entire distanceTable, the x direction
        for x in range(self.sim.NUM_NODES):
            nextNode = self.routeTable[x]                       # Which node is next after x
            toNext = self.distanceTable[self.myID][nextNode]    # Distance to nextNode from us
            nextToDest = self.distanceTable[nextNode][x]        # Distance from next to destination
            costEstimate = toNext + nextToDest                  # Total cost, cost to next + cost from next to dest

            # Since we update distanceTable when we recieve a cost change we might need 
            # to update our other tables accordingly.
            if(self.distanceTable[self.myID][x] != costEstimate):
                # If costEstimate is worse than distanceTable cost
                self.distanceTable[self.myID][x] = costEstimate     # Update distanceTable with estimat
                if(costEstimate > self.costs[x]):
                    self.distanceTable[self.myID][x] = self.costs[x]    # Update distanceTable with costs
                    self.routeTable[x] = x                              # Update routeTable
                    # print("Reset distanceTable with costs table. costs =", self.costs)
                updateNeighbours = True

            # Second loop, for checking entire distanceTable, the y direction
            for y in range(self.sim.NUM_NODES):
                currCost = self.distanceTable[self.myID][y]
                newCost = self.distanceTable[self.myID][x] + self.distanceTable[x][y]
                
                if(newCost < currCost):
                    self.distanceTable[self.myID][y] = newCost
                    self.routeTable[y] = self.routeTable[x]
                    updateNeighbours = True

        return updateNeighbours