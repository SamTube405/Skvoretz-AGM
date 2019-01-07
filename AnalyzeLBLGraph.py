import snap
import sys
import os
import networkx as nx

class AnalyzeLBLGraph:

    def __init__(self, fileName):
        self.fileName = fileName
        self.rootDir=self.getRootDir()
        self.attrVal1 = attrVal1
        self.attrVal2 = attrVal2

        self.graphName = self.getGraphName()

        self.lblV = snap.TStrV()
        self.lblV.Add(attrVal1)
        self.lblV.Add(attrVal2)

        self.lblNH = snap.TStrIntH()  # Node count with attached label

        self.lblEH = snap.TIntIntH()  # Edge count with attached src dst labels

        #self.G = self.getGraph(snap.PUNGraph)
        self.G= self.getLblGraph()
        self.saveGraph()

        ufileName=os.path.abspath(self.rootDir+"/"+self.graphName+".txt")
        self.snapG = snap.LoadEdgeList(snap.PUNGraph, ufileName)
        self.nxG = nx.read_edgelist(ufileName)
        

        self.gNAH=self.getNodeIdLabel(self.G)

    def getGraphName(self):
        tags = self.fileName.split("/")
        return tags[len(tags) - 1].split(".")[0]

    def getRootDir(self):
        return os.path.dirname(self.fileName)

    def getLblGraph(self):
        context = snap.TTableContext()

        schema = snap.Schema()
        schema.Add(snap.TStrTAttrPr("srcLabel", snap.atStr))
        schema.Add(snap.TStrTAttrPr("srcId", snap.atInt))
        schema.Add(snap.TStrTAttrPr("dstLabel", snap.atStr))
        schema.Add(snap.TStrTAttrPr("dstId", snap.atInt))

        # schema.Add(snap.TStrTAttrPr("srcID", snap.atStr))
        # schema.Add(snap.TStrTAttrPr("dstID", snap.atStr))
        # schema.Add(snap.TStrTAttrPr("timestamp", snap.atInt))

        table = snap.TTable.LoadSS(schema, self.fileName, context, " ", snap.TBool(False))
        #print table

        edgeattrv = snap.TStrV()
        edgeattrv.Add("srcLabel")
        edgeattrv.Add("dstLabel")
        # edgeattrv.Add("edgeattr2")

        srcnodeattrv = snap.TStrV()
        #srcnodeattrv.Add("srcLabel")

        dstnodeattrv = snap.TStrV()
        #srcnodeattrv.Add("dstLabel")

        # net will be an object of type snap.PNEANet
        return snap.ToNetwork(snap.PNEANet, table, "srcId", "dstId", srcnodeattrv, dstnodeattrv, edgeattrv, snap.aaFirst)

    def walkNodes(self):
        print "Nodes: "
        NCount = 0
        NI = self.G.BegNI()
        while NI < self.G.EndNI():
            print NI.GetId()
            NCount += 1
            NI.Next()

    def walkNodeAttrs(self,attribute_name):
        NodeId=0
        NI = self.G.BegNAStrI(attribute_name)
        while NI < self.G.EndNAStrI(attribute_name):
            if NI.GetDat() != 0:
                print "Attribute: %s, Node: %i, Val: %d" % (attribute_name, NodeId, NI.GetDat())
            NodeId += 1
            NI.Next()

    def walkEdgeAttrs(self,attribute_name):
        EdgeId = 0
        EI = self.G.BegEAStrI(attribute_name)
        while EI < self.G.EndEAStrI(attribute_name):
            if EI.GetDat() != "NA":
                print "Attribute: %s, Edge: %i, Val: %s" % (attribute_name, EdgeId, EI.GetDat())
            EdgeId += 1
            EI.Next()

    def walkEdges(self):
        print "Edges: "
        ECount = 0
        EI = self.G.BegEI()
        while EI < self.G.EndEI():
            print EI.GetId()
            ECount += 1
            EI.Next()

    def getNodeIdLabel(self,G):
        gLH = snap.TIntStrH()
        for EI in self.G.Edges():
            srcId = EI.GetSrcNId()
            dstId = EI.GetDstNId()

            EI=G.GetEI(srcId, dstId)

            srcAttr="srcLabel"
            srcAttrVal=G.GetStrAttrDatE(EI, srcAttr)

            dstAttr="dstLabel"
            dstAttrVal =G.GetStrAttrDatE(EI, dstAttr)

            gLH[srcId]=srcAttrVal
            gLH[dstId]=dstAttrVal
        return gLH

    def getNodeLabel(self,attribute):
        indexLabel="-1"
        if(attribute in self.lblV):
            if(attribute == self.lblV[0]):
                indexLabel="0";
            else:
                indexLabel="1";
        return indexLabel



    def getEdgeLbl(self, lbl1, lbl2):
        EdgeLblId=-1
        #print lbl1, lbl2
        EdgeLblId1 = int(lbl1 + lbl2, 2)
        EdgeLblId2 = int(lbl2 + lbl1, 2)
        #print EdgeLblId1,EdgeLblId2
        if(EdgeLblId1>=EdgeLblId2):
            EdgeLblId=EdgeLblId1
        else:
            EdgeLblId=EdgeLblId2
        return EdgeLblId

    def saveGraph(self):
        outputFilePath=self.rootDir+"/"+self.graphName + ".txt"
        snap.SaveEdgeList(self.G, outputFilePath)

    def setMetrics(self):

        NI = self.G.BegNI()
        cN=0
        while NI < self.G.EndNI():
            NId = NI.GetId()
            label=self.getNodeLabel(self.gNAH[NId])
            #print label
            if (label not in self.lblNH):
                self.lblNH[label] = 0
            self.lblNH[label] += 1
            NI.Next()
            cN+=1
        #print cN

        #EI = self.G.BegEI()
        ECount = 0
        for EI in self.snapG.Edges():
            # print EI.GetId()
            srcId = EI.GetSrcNId()
            dstId = EI.GetDstNId()

            srcLbl = self.getNodeLabel(self.gNAH[srcId])
            dstLbl = self.getNodeLabel(self.gNAH[dstId])

            #print srcLbl,dstLbl

            EdgeLblId = self.getEdgeLbl(srcLbl, dstLbl)
            #self.lblEH[EdgeLblId] += 1

            if (EdgeLblId not in self.lblEH):
                self.lblEH[EdgeLblId] = 0

            self.lblEH[EdgeLblId] += 1

            # print srcId, dstId
            ECount += 1
            #EI.Next()
        #print ECount

    def getInfo(self):
        # get the number of nodes and edges in the graph
        print "# of nodes in %s: %d" % (self.graphName, self.snapG.GetNodes())
        print "# of edges in %s: %d" % (self.graphName, self.snapG.GetEdges())
        print "[Metric] Density: %f | G(%d,%d)" % (nx.density(self.nxG),nx.number_of_nodes(self.nxG),nx.number_of_edges(self.nxG))

        print "\n[Node stat]"
        counterN = 0
        p=1
        for key in self.lblNH:
            counterN += self.lblNH[key]
            cp = float(self.lblNH[key]) / self.G.GetNodes()
            if(p>=cp):
                p=cp
            print "Label: %s, # of nodes: %d, percentage: %f" % (key, self.lblNH[key],cp)
        print "Total Nodes %d" % (counterN)

        print "\n[Edge stat]"
        counterE = 0
        for key in self.lblEH:
            counterE += self.lblEH[key]
            cp = float(self.lblEH[key]) / self.snapG.GetEdges()
            print "Label: %d, # of edges: %d, percentage: %f" % (key, self.lblEH[key],cp)
        print "Total Edges %d" % (counterE)

        # p=float(min(self.lblNH[0],self.lblNH[1])) / self.G.GetNodes()

        RB=float(self.lblEH[2]) / self.snapG.GetEdges()
        tau=1-(RB/(2*p*(1-p)))
        print "[Estimation] p: %f, tau: %f" % (p,tau)
        print "[Metric] Degree_assortativity_coefficient: %f" % nx.degree_assortativity_coefficient(self.nxG)
        print "[Metric] Transitivity: %f" % nx.transitivity(self.nxG)

        # apl=0
        # try:
        #     apl=nx.average_shortest_path_length(self.nxG)
        # except nx.exception.NetworkXError as nxr:
        #     ccs=nx.connected_component_subgraphs(self.nxG)
        #     cc_count=0
        #     for cc in ccs:
        #         cc_count+=1
        #         apl+=nx.average_shortest_path_length(cc)
        #     apl/=cc_count

        # print "[Metric] Average_shortest_path_length: %f" % apl




if __name__ == '__main__':

    fileName = sys.argv[1]
    attrVal1 = sys.argv[2]
    attrVal2 = sys.argv[3]
    analyze = AnalyzeLBLGraph(fileName)
    
    analyze.setMetrics()
    analyze.getInfo()
