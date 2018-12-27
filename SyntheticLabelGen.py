import sys
import snap
import numpy as np
import os
import pandas as pd
import time


# Author: Sameera | DSG
# python SyntheticLabelGen.py <graph file path> <# of attribute values> <p> <tau>
# E.g. python SyntheticLabelGen.py ./dataset/soc-gplus/soc-gplus.txt 2 0.5 0.75
class SyntheticLabelGen:
    def __init__(self, filename, mVals, pVal, tau):
        self.fileName = fileName
        self.mVals = mVals
        self.pVal = pVal
        self.pVals = []
        self.pVals.append(pVal)
        self.pVals.append(1 - pVal)
        self.tau = tau
        self.nLH = snap.TIntStrH()
        self.lblNH = snap.TStrIntH()  # Node count with attached label
        self.lblEH = snap.TIntIntH()  # Edge count with attached src dst labels

        self.RH = snap.TIntFltPrH()
        self.BH = snap.TIntFltPrH()

        self.cRV = snap.TIntV()
        self.cBV = snap.TIntV()

        self.G = self.getGraph(snap.PUNGraph)
        self.NG = snap.TNEANet()
        self.graphName = self.getGraphName()
        self.rootDir = self.getParentDir(self.fileName)
        self.absrootDir = os.path.abspath(self.rootDir)

        self.cR_count = 0
        self.cB_count = 0

        self.RH_count = 0
        self.BH_count = 0

    def getGraph(self, graph_type):
        return snap.LoadEdgeList(graph_type, self.fileName)

    def getGraphName(self):
        tags = self.fileName.split("/")
        return tags[len(tags) - 1].split(".")[0]

    def getParentDir(self, fileName):
        path = ""
        tags = fileName.split("/")
        for i in range(0, len(tags) - 1):
            path += tags[i] + "/"
        return path

    def getLabelVector(self):
        lblV = snap.TStrV()
        for x in xrange(0, self.mVals):
            lbl = str(bin(2 ** x)[2:].zfill(self.mVals))
            self.lblNH[lbl] = 0
        self.lblNH.GetKeyV(lblV)
        return lblV

    def addNode(self, nId):
        if (not self.NG.IsNode(nId)):
            self.NG.AddNode(nId)

    def addEdge(self, srcId, dstId, seqTag):
        if srcId != dstId and not self.NG.IsEdge(srcId, dstId):
            self.NG.AddEdge(srcId, dstId, seqTag)

    def getEdgeLbl(self, lbl1, lbl2):
        EdgeLblId = -1
        EdgeLblId1 = int(lbl1 + lbl2, 2)
        EdgeLblId2 = int(lbl2 + lbl1, 2)
        if (EdgeLblId1 >= EdgeLblId2):
            EdgeLblId = EdgeLblId1
        else:
            EdgeLblId = EdgeLblId2
        return EdgeLblId

    def setRandomLabels(self, attribute_name):
        lblV = self.getLabelVector()


        for xlbl in lblV:
            for ylbl in lblV:
                EdgeLblId = self.getEdgeLbl(xlbl, ylbl)
                self.lblEH[EdgeLblId] = 0

        NI = self.G.BegNI()
        while NI < self.G.EndNI():
            NId = NI.GetId()
            self.addNode(NId)
            randLbl = np.random.choice(lblV, 1, p=self.pVals)[0]
            self.lblNH[randLbl] += 1
            self.NG.AddStrAttrDatN(NId, randLbl, attribute_name)
            NI.Next()

        EI = self.G.BegEI()
        ECount = 0
        while EI < self.G.EndEI():
            srcId = EI.GetSrcNId()
            dstId = EI.GetDstNId()

            srcLbl = self.walkNodeAttributes(srcId)
            dstLbl = self.walkNodeAttributes(dstId)

            EdgeLblId = self.getEdgeLbl(srcLbl, dstLbl)
            self.lblEH[EdgeLblId] += 1

            ECount += 1

            self.addEdge(srcId, dstId, ECount)
            EI.Next()

    def walkNodeAttributes(self, NId):
        Val = ""

        NIdAttrName = snap.TStrV()
        self.NG.AttrNameNI(NId, NIdAttrName)
        AttrLen = NIdAttrName.Len()

        NIdAttrValue = snap.TStrV()
        self.NG.AttrValueNI(NId, NIdAttrValue)
        AttrLen = NIdAttrValue.Len()

        for i in range(AttrLen):
            Val = NIdAttrValue.GetI(i)()
            break;

        return Val

    def getIndexNeighFrac(self, NId, index):
        neighbors = 0
        indexNeighbors = 0
        lblV = self.getLabelVector()
        for Id in self.G.GetNI(NId).GetOutEdges():
            neighbors += 1
            neighborLbl = self.walkNodeAttributes(Id)
            if (neighborLbl == lblV[index]):
                indexNeighbors += 1

        return neighbors, float(indexNeighbors) / neighbors

    # only two value attributes
    def setAttractionModel(self):
        lblV = self.getLabelVector()

        NI = self.NG.BegNI()
        counter = 0
        while NI < self.NG.EndNI():
            NId = NI.GetId()
            NLbl = self.walkNodeAttributes(NId)
            if (NLbl == lblV[0]):
                self.RH[NId] = snap.TFltPr()
                Neigh, NeighFrac = self.getIndexNeighFrac(NId, 1)
                NeighPr = snap.TFltPr(Neigh, NeighFrac)
                self.RH[NId] = NeighPr
                # print "prob %f" % (self.getIndexNeighFrac(NId,1)+self.getIndexNeighFrac(NId,0))
                # print "R Node Id: %d, Neighbors: %f, B Frac. Neighbors: %f" % (NId,self.RH[NId].GetVal1(),self.RH[NId].GetVal2())
            else:
                self.BH[NId] = snap.TFltPr()
                Neigh, NeighFrac = self.getIndexNeighFrac(NId, 0)
                NeighPr = snap.TFltPr(Neigh, NeighFrac)
                self.BH[NId] = NeighPr
                # print "prob %f" % (self.getIndexNeighFrac(NId, 1)+self.getIndexNeighFrac(NId, 0))
                # print "B Node Id: %d, Neighbors: %f, R Frac. Neighbors: %f" % (NId, self.BH[NId].GetVal1(),self.BH[NId].GetVal2())

            counter += 1
            NI.Next()

        print "# of nodes: %d, R: %d, B: %d" % (self.RH.Len() + self.BH.Len(), self.RH.Len(), self.BH.Len())

    def setCandidateSet(self, index):
        candNV = snap.TIntV()

        NH = self.RH
        tld = (1 - self.tau) * (1 - self.pVal)

        if (index > 0):
            tld = (1 - self.tau) * self.pVal
            NH = self.BH

        for key in NH:
            fracNeigh = NH[key].GetVal2()
            if (fracNeigh > tld):
                candNV.Add(key)

        return candNV

    def getNeighPr(self, NId):
        NeighPr = snap.TFltPr()
        if (self.RH.IsKey(NId)):
            NeighPr = self.RH.GetDat(NId)
        else:
            NeighPr = self.BH.GetDat(NId)
        return NeighPr;

    def getSwitchLabel(self,_label):
        lblV = self.getLabelVector()
        label = lblV[0]
        if(label ==_label):
            label = lblV[1]
        return label

    def getDelta(self, cNId1, cNId2, index):
        lblV = self.getLabelVector()

        _label=lblV[index]
        delta=0
        for NeighId in self.G.GetNI(cNId1).GetOutEdges():
            if(NeighId!=cNId2):
                NeighLabel = self.walkNodeAttributes(NeighId)
                if(NeighLabel == _label):
                    delta-=1; #Ri
                else:
                    delta+=1; #Bi
        return delta

    def randomCandidateSwap(self, cRV, cBV):
        lblV = self.getLabelVector()

        tld = 2 * (1 - self.tau) * self.pVal * (1 - self.pVal) * self.G.GetEdges()
        prevRB=self.lblEH[9]
        print "[init] R-B ties: %f, Threshold: %f" % (prevRB, tld)

        # counter = 0
        while (self.lblEH[9] > tld):
            cR = np.random.choice(cRV, 1, replace=False)[0]
            cB = np.random.choice(cBV, 1, replace=False)[0]

            delta = self.getDelta(cR, cB, 0)
            delta += self.getDelta(cB, cR, 1)

            if (delta > 0):
                self.NG.AddStrAttrDatN(cR, lblV[1], "X")
                self.NG.AddStrAttrDatN(cB, lblV[0], "X")

                cRV.DelIfIn(cR)
                cBV.DelIfIn(cB)


                self.lblEH[9] -= delta
                print "[swap] R-B ties: %f, Threshold: %f" % (self.lblEH[9], tld)

        print "[swap complete] # RB Ties: prev: %d, now: %d\n" % (prevRB,self.lblEH[9])

        print "[swap complete] # of non-candidate nodes: %d, R: %d, B: %d" % (
            cRV.Len() + cBV.Len(), cRV.Len(), cBV.Len())

        self.getInfo()

    def saveNetwork(self):
        lblV = self.getLabelVector()
        EI = self.G.BegEI()
        ECount = 0
        df_matrix = []
        while EI < self.G.EndEI():
            srcId = EI.GetSrcNId()
            srcLbl = self.walkNodeAttributes(srcId)

            dstId = EI.GetDstNId()
            dstLbl = self.walkNodeAttributes(dstId)

            row = [srcLbl, srcId, dstLbl, dstId]
            df_matrix.append(row)

            ECount += 1
            EI.Next()

        df = pd.DataFrame(df_matrix, columns=('srcLbl', 'srcId', 'dstLbl', 'dstId'))
        fileName = self.absrootDir + "/" + self.graphName + "-Lbl-AttrVal-mVals-" + str(self.mVals) + "-p-" + str(
            self.pVal).replace(".", "-") + "-tau-" + str(self.tau).replace(".", "-") + ".csv"
        df.to_csv(fileName, sep=' ', encoding='utf-8', header=False, mode='w', index=False)
        print "Saved simulated labeled graph at %s, |E|=%d" % (fileName, ECount)

    def getStat(self, attribute_name):

        # get the number of nodes and edges in the graph
        print "# of nodes in %s: %d" % (self.graphName, self.G.GetNodes())
        print "# of edges in %s: %d" % (self.graphName, self.G.GetEdges())

        NI = self.G.BegNI()
        counter = 0
        while NI < self.G.EndNI():
            NId = NI.GetId()
            NVal = self.walkNodeAttributes(NId)
            NI.Next()

        print "\n[Node stat]"
        counterN = 0
        for key in self.lblNH:
            counterN += self.lblNH[key]
            print "Label: %s, # of nodes: %d" % (key, self.lblNH[key])
        print "Total Nodes %d" % (counterN)

        print "\n[Edge stat]"
        counterE = 0
        for key in self.lblEH:
            counterE += self.lblEH[key]
            print "Label: %d, # of edges: %d" % (key, self.lblEH[key])
        print "Total Edges %d" % (counterE)


    def getNEStats(self):
        lblEH = snap.TIntIntH()
        lblNH = snap.TStrIntH()

        NI = self.G.BegNI()
        cN = 0
        while NI < self.G.EndNI():
            NId = NI.GetId()
            label = self.walkNodeAttributes(NId)
            if (label not in lblNH):
                lblNH[label] = 0
            lblNH[label] += 1
            NI.Next()
            cN += 1


        EI = self.G.BegEI()
        ECount = 0
        while EI < self.G.EndEI():
            srcId = EI.GetSrcNId()
            dstId = EI.GetDstNId()

            srcLbl = self.walkNodeAttributes(srcId)
            dstLbl = self.walkNodeAttributes(dstId)

            EdgeLblId = self.getEdgeLbl(srcLbl, dstLbl)

            if (EdgeLblId not in lblEH):
                lblEH[EdgeLblId] = 0

            lblEH[EdgeLblId] += 1

            ECount += 1
            EI.Next()
        return lblNH,lblEH

    def getInfo(self):
        lblNH,lblEH=self.getNEStats()
        # get the number of nodes and edges in the graph
        print "# of nodes in %s: %d" % (self.graphName, self.G.GetNodes())
        print "# of edges in %s: %d" % (self.graphName, self.G.GetEdges())

        print "\n[Node stat]"
        counterN = 0
        for key in lblNH:
            counterN += lblNH[key]
            cp = float(lblNH[key]) / self.G.GetNodes()
            print "Label: %s, # of nodes: %d, percentage: %f" % (key, lblNH[key],cp)
        print "Total Nodes %d" % (counterN)

        print "\n[Edge stat]"
        counterE = 0
        for key in lblEH:
            counterE += lblEH[key]
            cp = float(lblEH[key]) / self.G.GetEdges()
            print "Label: %d, # of edges: %d, percentage: %f" % (key, lblEH[key],cp)
        print "Total Edges %d" % (counterE)


if __name__ == '__main__':
    start_time = time.time()
    fileName = sys.argv[1]
    # one attribute network, mVals define the number of values it could take
    mVals = sys.argv[2]


    pVal = float(sys.argv[3])
    # attraction model
    tau = sys.argv[4]

    syn = SyntheticLabelGen(fileName, int(mVals), pVal, float(tau))

    syn.setRandomLabels("X")

    syn.getStat("X")

    syn.setAttractionModel()

    cRV = syn.setCandidateSet(0)
    cBV = syn.setCandidateSet(1)

    print "# of candidate nodes: %d, R: %d, B: %d" % (cRV.Len() + cBV.Len(), cRV.Len(), cBV.Len())

    syn.randomCandidateSwap(cRV, cBV)
    print("--- %s seconds ---" % (time.time() - start_time))

    syn.saveNetwork()



