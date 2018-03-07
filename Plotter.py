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

def main():
    p = Plotter("htt_mt.inputs-sm-13TeV-ML.root", [])
    p.makePlots()
    p.combineImages()

class Plotter():

    def __init__(self, filename, naming):
        self.filename = filename
        self.images = []
        self.tiles = []
        self.sig = ["ggH125","qqH125","sig"]
        self.bkg = ["TT","TTT","TTJ","VV","VVT","VVJ","QCD","ZTT","ZL","ZJ","W"]
        self.naming = ["ggH125","qqH125","TTT","TTJ","QCD","VVT","VVJ","ZTT","ZL","ZJ","W"]
        self.naming.sort()
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
            if isinstance( self.file.Get( dirname ), R.TDirectory):
                histos[dirname] = { "stack": R.THStack(dirname, dirname), "leg": R.TLegend(0.82, 0.03, 0.98, 0.92) }
                TDir = self.file.Get( dirname )
                hists = [ t.GetName() for t  in TDir.GetListOfKeys() ]
                hists.sort()
#                hists = ["VVT","TTT","ZL","ZTT","QCD","VVJ","TTJ","ZJ","W","data_obs"]
                for hist in hists:
                    if hist in self.naming:
                        tmp = copy.deepcopy( TDir.Get( hist ) )
                        tmp.SetFillColor( self.getColor( hist ) )

                        histos[dirname]["leg"].AddEntry(tmp, hist)
                        histos[dirname]["stack"].Add( tmp  )

                    elif hist == "data_obs":
                        histos[dirname]["data"] =  copy.deepcopy( TDir.Get( hist ) ) 
                        histos[dirname]["data"].GetXaxis().SetLabelSize(0)
                        histos[dirname]["data"].GetYaxis().SetLabelFont(63)
                        histos[dirname]["data"].GetYaxis().SetLabelSize(14)


                stack = histos[dirname]["stack"].GetHists()
                try:
                    histos[dirname]["ratio"] = copy.deepcopy( stack[0] )
                    for i in xrange( 1, len(stack) ):
                        if stack[i] in self.sig: continue
                        histos[dirname]["ratio"].Add( copy.deepcopy( stack[i] ) )

                    histos[dirname]["ratio"].Divide( histos[dirname]["data"] )
                    histos[dirname]["ratio"].GetYaxis().SetRangeUser(0.5, 1.5)
                    histos[dirname]["ratio"].GetYaxis().SetNdivisions(6)
                    histos[dirname]["ratio"].GetXaxis().SetNdivisions(10)
                    histos[dirname]["ratio"].GetXaxis().SetLabelFont(63)
                    histos[dirname]["ratio"].GetXaxis().SetLabelSize(14)
                    histos[dirname]["ratio"].GetYaxis().SetLabelFont(63)
                    histos[dirname]["ratio"].GetYaxis().SetLabelSize(14)
                    histos[dirname]["ratio"].SetTitle("")

                except KeyError as e:
                    print "missing histogram(s) for: ", e, " in ", TDir
                    print "Check root files!"
                    sys.exit(0)

                except IndexError as e:
                    print "No histograms found to add in ", TDir
                    print "Check root files!"
                    sys.exit(0)


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
        for h in hists :
            for i,d in enumerate( TDirs ):
                if i == 0:
                    inclusive[h] = totalHists[d][h]
                else:
                    inclusive[h].Add( totalHists[d][h] )
        
        self.histos["_incl"] = { "stack": R.THStack("incl", "incl"), "leg": R.TLegend(0.82, 0.03, 0.98, 0.92) }
        inclhist = inclusive.keys()
        inclhist.sort()
        for hist in inclhist:
            if hist in self.naming:
                tmp = copy.deepcopy( inclusive[hist] )
                tmp.SetFillColor( self.getColor( hist ) )

                self.histos["_incl"]["leg"].AddEntry(tmp, hist)
                self.histos["_incl"]["stack"].Add( tmp  )

            elif hist == "data_obs":
                self.histos["_incl"]["data"] =  copy.deepcopy( inclusive[hist] )
                self.histos["_incl"]["data"].GetXaxis().SetLabelSize(0)
                self.histos["_incl"]["data"].GetYaxis().SetLabelFont(63)
                self.histos["_incl"]["data"].GetYaxis().SetLabelSize(14)

        stack = self.histos["_incl"]["stack"].GetHists()
        try:
            self.histos["_incl"]["ratio"] = copy.deepcopy( stack[0] )
            for i in xrange( 1, len(stack) ):
                if stack[i] in self.sig: continue
                self.histos["_incl"]["ratio"].Add( copy.deepcopy( stack[i] ) )

            self.histos["_incl"]["ratio"].Divide( self.histos["_incl"]["data"] )
            self.histos["_incl"]["ratio"].GetYaxis().SetRangeUser(0.5, 1.5)
            self.histos["_incl"]["ratio"].GetYaxis().SetNdivisions(6)
            self.histos["_incl"]["ratio"].GetXaxis().SetNdivisions(10)
            self.histos["_incl"]["ratio"].GetXaxis().SetLabelFont(63)
            self.histos["_incl"]["ratio"].GetXaxis().SetLabelSize(14)
            self.histos["_incl"]["ratio"].GetYaxis().SetLabelFont(63)
            self.histos["_incl"]["ratio"].GetYaxis().SetLabelSize(14)
            self.histos["_incl"]["ratio"].SetTitle("")
        except KeyError as e:
            print "missing histogram(s) for: ", e, " in ", TDir
            print "Check root files!"
            sys.exit(0)

        except IndexError as e:
            print "No histograms found to add in ", TDir
            print "Check root files!"
            sys.exit(0)
  

    def makePlots(self):

        for cat in self.histos.keys():


            cv= self.createRatioCanvas("cv"+cat)
            maxVal = max(self.histos[cat]["data"].GetMaximum(), self.histos[cat]["stack"].GetMaximum() )*1.10
            cv.cd(2)
            tmp = copy.deepcopy( self.histos[cat]["data"] )

            tmp.SetTitle("")
            tmp.GetYaxis().SetRangeUser( 0.1, maxVal / 100 )
            tmp.Draw("e1")
            self.histos[cat]["stack"].Draw("same HIST")
            tmp.Draw("same e1")
            

            cv.cd(1)
            self.histos[cat]["data"].GetYaxis().SetRangeUser(maxVal / 100,  maxVal)
            self.histos[cat]["data"].Draw("e1")
            self.histos[cat]["stack"].Draw("same HIST")
            self.histos[cat]["data"].Draw("same e1")
            self.histos[cat]["leg"].Draw()
            R.gPad.RedrawAxis()
            
            cv.cd(3)
            self.histos[cat]["ratio"].Draw()

            cv.cd(2)
            R.gPad.RedrawAxis()

            cv.Print(cat+'.png')
            self.images.append( cat+'.png' )       


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
        plt.savefig("comb.png")

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
        else: return R.kYellow

if __name__ == '__main__':
    main()