#!/usr/bin/env python
from msilib.schema import tables
from re import T
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

    # --------------------------------------------------
    def __init__(self, ID, sim, costs):
        self.myID = ID
        self.sim = sim
        self.routeTable = [0 for i in range(self.sim.NUM_NODES)]
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

        print("Node:", self.myID)
        print("\t# Poison reverse:", self.sim.POISONREVERSE)
        print("\t# Cost changes:", self.sim.LINKCHANGES)
        print("\t# Distance table:")
        for x in self.distanceTable:
            print("\t\t#", x)
        print("\t# Route table:")
        print("\t\t#", self.routeTable)
        #self.updateAll()
        

    # --------------------------------------------------
    def recvUpdate(self, pkt):
        #print("Packet recieved!", pkt.sourceid, pkt.destid, pkt.mincost)
        if(self.bellmanFord(pkt)):
            self.updateAll()


    # --------------------------------------------------
    def sendUpdate(self, pkt):
        self.sim.toLayer2(pkt)


    # --------------------------------------------------
    def updateAll(self):
        for i in range(self.sim.NUM_NODES):
            if(i != self.myID):
                tmpPkt = RouterPacket.RouterPacket(self.myID, i, self.costs)
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
            if(x != self.myID):
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
        self.costs[dest] = newcost
        self.updateAll()

    # --------------------------------------------------
    def bellmanFord(self):
        changed = False
        for x in range(self.sim.NUM_NODES):
            toCost = self.distanceTable[self.myID][x]
            for y in range(self.sim.NUM_NODES):
                
        # toCost = self.costs[pkt.sourceid]
        # for i in range(self.sim.NUM_NODES):
        #     if(self.costs[i] > pkt.mincost[i] + toCost):
        #         self.costs[i] = pkt.mincost[i] + toCost
        #         if(self.costs[i] > (pkt.mincost[pkt.sourceid] + pkt.mincost[i])):
        #             self.routeTable[i] = self.routeTable[pkt.sourceid]
        #         else:
        #             self.routeTable[i] = pkt.sourceid
        #         changed = True
        #         # print("New cost and route set in node:", self.myID)
        #         # print("Node:", i, " |  Src:", pkt.sourceid, " |  New cost:", self.costs[i], " |  Next hop:", self.routeTable[i], "\n")
        # return changed