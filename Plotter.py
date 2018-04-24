import ROOT as R
R.gROOT.SetBatch(True)
R.gStyle.SetOptStat(0)

import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import numpy as np
import os
import copy
from math import sqrt
import sys
import PlotUtils as pl

def main():
    p = Plotter(channel = "mt",path = "keras")
    p.makePlots()
    # p.combineImages()

class Plotter():

    def __init__(self, channel, naming = [], path = ""):
        if path:
            self.filename = "/".join([path, "htt_{0}.inputs-sm-13TeV-ML.root".format(channel) ])
        else:
            self.filename = "htt_{0}.inputs-sm-13TeV-ML.root".format(channel)
        self.channel = channel
        self.images = []
        self.tiles = []
        self.sig = ["ggH125","qqH125","sig"]
        self.bkg = ["TT","TTT","TTJ","VV","VVT","VVJ","QCD","ZTT","ZL","ZJ","W"]
        # self.naming = ["ggH125","qqH125","TTT","TTJ","QCD","VVT","VVJ","ZTT","ZL","ZJ","W"]
        self.naming = ["TTT","VVT","ZTT","ZL","jetFakes"]
        # self.naming.sort()

        self.plotPath = "/".join(["plots",path,channel])

        if not os.path.exists(self.plotPath):
            os.makedirs(self.plotPath)



        if not self.loadFile():
            print self.filename, "not found!!"
            return None

    def loadFile(self):
        if os.path.exists(self.filename):
            self.file = R.TFile(self.filename.replace(".root","") + ".root","READ")
            self.histos = self.__getHistos()
            self.makeInclusive()
            return True
        return False

    def __getHistos(self):

        histos = {}

        for key in self.file.GetListOfKeys():
            dirname = key.GetName()
            if not self.channel in dirname: continue
            if isinstance( self.file.Get( dirname ), R.TDirectory):
                histos[dirname] = {}
                TDir = self.file.Get( dirname )
                hists = [ t.GetName() for t  in TDir.GetListOfKeys() ]
                hists.sort()
#                hists = ["VVT","TTT","ZL","ZTT","QCD","VVJ","TTJ","ZJ","W","data_obs"]
                for hist in hists:
                    if hist in self.naming:
                        histos[dirname][hist] = copy.deepcopy( TDir.Get( hist ) )

                    elif hist == "data_obs":
                        histos[dirname]["data"] =  copy.deepcopy( TDir.Get( hist ) ) 



        return histos

    def makeInclusive(self):

        totalHists = {}
        TDirs = [TDir.GetName() for TDir in self.file.GetListOfKeys()]
        for TDir in TDirs:
            folder = self.file.Get( TDir )
            hists = [ hist.GetName() for hist in folder.GetListOfKeys() if not "_13TeV" in hist.GetName()]
            totalHists[ TDir ] = {}
            for hist in hists:
                totalHists[TDir][hist] = copy.deepcopy( folder.Get( hist )  )

        inclusive = {}
        cat = "{0}_incl".format(self.channel)
        
        for h in hists :
            for i,d in enumerate( TDirs ):
                if i == 0:
                    inclusive[h] = totalHists[d][h]
                else:
                    inclusive[h].Add( totalHists[d][h] )
        
        self.histos[cat] = {  }
        inclhist = inclusive.keys()
        inclhist.sort()
        for hist in inclhist:
            if hist in self.naming:
                self.histos[cat][hist] = copy.deepcopy( inclusive[hist] )

            elif hist == "data_obs":
                self.histos[cat]["data"] =  copy.deepcopy( inclusive[hist] )

  

    def makePlots(self):

        for cat in self.histos.keys():

            pl.plot(self.histos[cat], "semi", descriptions = {"plottype": "ProjectWork", "xaxis":"pred_prob", "channel":self.channel,"som": "13", "lumi":"35.9"  }, outfile = "{0}/{1}.png".format(self.plotPath,cat) )
     
    def blindBins(self, h, bins, canvas ):

        for i in xrange( h.GetNbinsX() + 1 ):
            if bins[i]:
                if canvas == "data":
                    h.SetBinContent(i, 0.)
                if canvas == "ratio":
                    h.SetBinContent(i, 1.)

    def getBinsToBlind(self, HStack):

        stack = copy.deepcopy(HStack)
        hists = stack.GetHists()
        bins = hists[0].GetNbinsX()

        blind = []
        for i in xrange(bins + 1):
            NBkg = 0
            NSig = 0
            for hist in hists:
                name = hist.GetName()

                N = hist.GetBinContent(i)
                if name in self.sig:
                    NSig += N
                if name in self.bkg:
                    NBkg += N
            blind.append( self.blindFunction(NBkg,NSig) )

        return blind

    def blindFunction(self, NBkg, NSig ):

        e = 0.09

        num = NSig
        den = 0
        if NBkg > 0:
            den = sqrt( NBkg + (e*NBkg)* (e*NBkg) )

        if den == 0:
            return False
        else:
            return (num / den) >= 0.5


    def createRatioCanvas(self,name, errorBandFillColor=14, errorBandStyle=3354 ):
        cv = R.TCanvas(name, name, 10, 10, 700, 600)

        # this is the tricky part...
        # Divide with correct margins
        cv.Divide(1, 3, 0.0, 0.0)

        # Set Pad sizes
        cv.GetPad(1).SetPad(0.0, 0.55, 1., 1.0)
        cv.GetPad(2).SetPad(0.0, 0.32, 1., 0.55)
        cv.GetPad(3).SetPad(0.0, 0.00, 1., 0.34)

        cv.GetPad(1).SetFillStyle(4000)
        cv.GetPad(2).SetFillStyle(4000)
        cv.GetPad(3).SetFillStyle(4000)

        # Set pad margins 1
        cv.cd(1)
        R.gPad.SetTopMargin(0.08)
        R.gPad.SetLeftMargin(0.1)
        R.gPad.SetRightMargin(0.2)

        cv.cd(2)
        R.gPad.SetLeftMargin(0.1)
        R.gPad.SetBottomMargin(0.03)
        R.gPad.SetRightMargin(0.2)
        R.gPad.SetLogy()

        # Set pad margins 2
        cv.cd(3)
        R.gPad.SetTopMargin(0.08)
        R.gPad.SetBottomMargin(0.35)
        R.gPad.SetLeftMargin(0.1)
        R.gPad.SetRightMargin(0.2)
        R.gPad.SetGridy()

        cv.cd(1)
        

        return cv

    def combineImages(self, cols = 2, titles = None):
        images = [ mpimg.imread(i) for i in  self.images ]
        titles = [ i.split("_")[1].replace(".png","") for i in  self.images ]

        assert((titles is None) or (len(images) == len(titles)))
        n_images = len(images)
        if titles is None: titles = ['Image (%d)' % i for i in range(1,n_images + 1)]
        fig = plt.figure()
        for n, (image, title) in enumerate(zip(images,titles)):
            a = fig.add_subplot(cols, np.ceil(n_images/float(cols)), n + 1)
            if image.ndim == 2:
                plt.gray()
            plt.imshow(image)
            a.set_title(title)
        fig.set_size_inches(np.array(fig.get_size_inches()) * n_images)
        plt.savefig("{0}/comb.png".format(self.plotPath))

    def getColor(self, name):
        if name in ["TT","TTT","TTJ"]: return R.TColor.GetColor(155,152,204)
        if name in ["sig"]:            return R.kRed
        if name in ["bkg"]:            return R.kBlue
        if name in ["qqH"]:            return R.TColor.GetColor(204,102,0)
        if name in ["ggH"]:            return R.TColor.GetColor(255,128,0)
        if name in ["W"]:              return R.TColor.GetColor(222,90,106)
        if name in ["VVT","VVJ"]:      return R.TColor.GetColor(175,35,80)
        if name in ["ZL","ZJ","ZLJ"]:  return R.TColor.GetColor(100,192,232)
        if name in ["QCD","WSS"]:      return R.TColor.GetColor(250,202,255)
        if name in ["ZTT","DY"]:       return R.TColor.GetColor(248,206,104)
        if name in ["jetFakes"]:             return R.TColor.GetColor(192,232,100)
        else: return R.kYellow

if __name__ == '__main__':
    main()
