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
    table = None

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
        self.table = [0 for i in range(self.sim.NUM_NODES)]
        self.myGUI = GuiTextArea.GuiTextArea("  Output window for Router #" + str(ID) + "  ")

        self.costs = deepcopy(costs)
        for i in range(self.sim.NUM_NODES):
            if(self.costs[i] == self.sim.INFINITY):
                self.table[i] = self.sim.INFINITY
            else:
                self.table[i] = i

        print("Costs", self.myID, ":", self.costs, "| Next hop:", self.table)
        
        tmpPkt = RouterPacket.RouterPacket(self.myID, 0, [6,2,1])
        self.sendUpdate(tmpPkt)

    # --------------------------------------------------
    def recvUpdate(self, pkt):
        print("Packet recieved!", pkt.sourceid, pkt.destid, pkt.mincost)

        for i in range(self.sim.NUM_NODES):
            if(pkt.mincost[i] > self.costs[i]):
                self.costs[i] = pkt.mincost[i]


    # --------------------------------------------------
    def sendUpdate(self, pkt):
        self.sim.toLayer2(pkt)


    # --------------------------------------------------
    def printDistanceTable(self):
        self.myGUI.println("Current table for " + str(self.myID) +
                           "  at time " + str(self.sim.getClocktime()))
        #self.myGUI.println("Node " + str(self.myID) + ": " + str(self.costs))


    # --------------------------------------------------
    def updateLinkCost(self, dest, newcost):
        pass

    # --------------------------------------------------
    def bellmanFord():
        pass