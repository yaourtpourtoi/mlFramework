import ROOT as R
import json
from array import array
import root_pandas as rp
import root_numpy as rn
from pandas import DataFrame,Series,concat
from utils.CutObject import Cut
import copy
import sys
import os
import math
import utils.Plotting as pl
R.gROOT.SetBatch(True)
R.gStyle.SetOptStat(0)

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='channel', help='Decay channel' ,choices = ['mt','et','tt'], default = 'mt')
    parser.add_argument('-p', dest='plot',    help='Plot fractions' , action = "store_true")
    args = parser.parse_args()

    # Frac = Fractions(args.channel, ["pt_2","pred_class"], [ (8, array("d",[0,30,35,40,45,50,50,80,200] ) ) , (8, -0.5,7.5)  ] )
    Frac = Fractions(args.channel, ["pred_prob","pred_class"], [ (30,0,1 ) , (1, -0.5,7.5)  ] )
    # Frac = Fractions(channel, ["pt_2","pred_class"], [ (5, array("d",[0,30,40,60,100,1000] ) ) , (8, array("d",[-0.5,0.5,1.5,2.5,3.5,4.5,5.5,6.5,7.5]) ) ] )
    # Frac = Fractions(channel, ["pt_2","pred_class"], [ (5, array("d",[0,30,40,60,100,1000] ) ) , (1, array("d",[-0.5,7.5]) ) ] )
    Frac.calcFractions()
    if args.plot: Frac.visualize()
    
class Fractions():

    def __init__(self, channel, var, binning):

        self.channel = channel
        self.var = var
        self.binning = binning[0] + binning[1]

        self.cut = Cut( "-ANTIISO2- && -MT- && -VETO- && -OS- && -TRIG- ", channel )

        self.weights = ["puweight","stitchedWeight","trk_sf","genweight","effweight","topWeight_run1","zPtReweightWeight","antilep_tauscaling"]
        self.lumi = 35.9

        svfit = "SVFIT"
        version = "v2"


        path = "/afs/hephy.at/work/m/mspanring/HephyHiggs/mlFramework/predictions/keras/{0}/".format( channel)
        ext = ".root"

        self.mcSamples = [
            (path + "W_more"+ext,"W",""),
            (path + "Z_more"+ext,"ZTT",Cut("-GENHAD-") ),
            (path + "Z_more"+ext,"ZL", Cut("-GENLEP-") ),
            (path + "Z_more"+ext,"ZJ", Cut("-GENJET-") ),
            (path + "TT_more"+ext,"TTT",Cut("-GENHAD-") ),
            (path + "TT_more"+ext,"TTJ",Cut("!-GENHAD-") ),
            (path + "VV_more"+ext,"VVT",Cut("-GENHAD-") ),
            (path + "VV_more"+ext,"VVJ",Cut("!-GENHAD-") ),
        ]
        self.dataSample = {
            "mt":path + "data_more"+ext,
            "et":path + "data_more"+ext,
            "tt":path + "data_more"+ext
        } 

        self.composition = {
            "mt":{
                "W":["W","VVJ","ZJ"],
                "TT":["TTJ"],
                "QCD":["QCD"],
                "DY":["ZJ"],
                "real":["ZTT","ZL","TTT","VVT"]
            },
            "et":{
                "W":["W","VVJ","ZJ"],
                "TT":["TTJ"],
                "QCD":["QCD"],
                "DY":["ZJ"],
                "real":["ZTT","ZL","TTT","VVT"]
            },
            "tt":{
                "W":["W","VVJ"],
                "TT":["TTJ"],
                "QCD":["QCD"],
                "DY":["ZJ"],
                "real":["ZTT","ZL","TTT","VVT"]
            }        
        }

    def cpHist(self, h, name,title="", reset = True):
        newHist = copy.deepcopy(h)
        if reset: newHist.Reset()
        newHist.SetName(name)
        if title:
            newHist.SetTitle(title)
        else:
            newHist.SetTitle(name)

        return newHist

    def calcFractions(self):
        if not os.path.exists("preliminary_fractions"):
            os.makedirs( "preliminary_fractions" )

        histos = {}

        for sample,name,addcut in self.mcSamples:
            histos[name] = self.fillHisto( sample, self.cut + addcut, name)

        histos["data"]     = self.fillHisto( self.dataSample[self.channel],self.cut, "data_obs", weight = False )

        dummy = self.cpHist( histos["data"], "dummy", ":".join( self.var ) )
        fracs = {}
        for f in ["total","QCD","W","ZTT","ZL","ZJ","TTT","TTJ","VVT","VVJ"]:
            fracs[f] = self.cpHist(dummy, f)
 
        for i in xrange(1, dummy.GetNbinsX() + 1 ):
            for j in xrange(1, dummy.GetNbinsY() + 1 ):

                total = float( histos["data"].GetBinContent( i,j ) )
                part_mc = 0.
                part_other = {}
                for f in fracs:
                    if f == "total" or f == "QCD": continue
                    part_other[f] = histos[f].GetBinContent( i,j )
                    part_mc      += histos[f].GetBinContent( i,j )

                total = max(part_mc, total)
                part_other["QCD"] = total - part_mc

                for f in fracs:
                    if total == 0: continue
                    if f == "total":
                        fracs[f].SetBinContent( i,j, total )
                    else:
                        fracs[f].SetBinContent( i,j, part_other[f] / total )

        comp = {}
        for c,part in self.composition[self.channel].items() :

            for i,p in enumerate( part ):
                if i == 0:
                    comp[c] = self.cpHist( fracs[p], c, reset = False)
                else:
                    comp[c].Add( fracs[p] )

        file = R.TFile("preliminary_fractions/{0}_fractions.root".format( self.channel ), "recreate" )
        file.mkdir("all")
        file.mkdir("fracs")
        file.cd()
        dummy.Write()

        file.cd("all")
        for f in fracs:
            fracs[f].Write()

        file.cd("fracs")
        for c in comp:
            comp[c].Write()      

        file.Close()

        print "written fractions to:", self.channel +"_fractions.root"

    def fillHisto(self, path, cut, name, weight = True):

            tmp =   rp.read_root( paths = path,
                                  where = cut.get(),
                                  columns = self.weights + self.var + ["gen_match_1","gen_match_2","decayMode_1","decayMode_2"] 
                                )

            if weight:
                tmp.eval( "eweight = " + "*".join( self.weights ),  inplace = True )
                tmp["eweight"] *= float(self.lumi)
            else:        
                tmp.eval( "eweight = 1"  , inplace = True )

            tmpHist = R.TH2D(name,name,*(self.binning))
            tmpHist.SetOption("COLZ")
            rn.fill_hist( tmpHist, array = tmp[self.var].values,
                                   weights = tmp["eweight"].values )

            return tmpHist

    def readFractions(self):
        file = R.TFile(self.channel +"_fractions.root", "read" )

    def visualize(self, frac_file = ""):

        contr = ["TT","W","QCD","real"]
        if self.channel == "tt":
            contr.append("DY")

        file = R.TFile( "preliminary_fractions/{0}_fractions.root".format( self.channel ), "read" )


        Hists = { c:file.Get("fracs/"+c) for c in contr   }

        for i in xrange(1, Hists[ contr[0] ].GetNbinsY() + 1 ):

            hists = { c: Hists[c].ProjectionX(c +"x",i,i) for c in Hists }
            dummy = self.cpHist(hists[ contr[0] ], "Fractions")
            stack = R.THStack("stack", "")
            leg = R.TLegend(0.82, 0.5, 0.98, 0.9)
            for c in contr: 
                pl.applyHistStyle( hists[c], c )
                stack.Add( hists[c] )

            for c in contr[::-1]:
                leg.AddEntry( hists[c], c )

            cv = R.TCanvas(str(i)+"cv", str(i)+"cv", 10, 10, 700, 600)
            R.gPad.SetRightMargin(0.2)
            dummy.GetYaxis().SetRangeUser(0,stack.GetMaximum())
            dummy.Draw()
            stack.Draw("same")
            leg.Draw()
            R.gPad.RedrawAxis()
            cv.Print(str(i) + '_fractions.png') 

        file.Close()

class FakeFactor():

    fraction_path = "{0}/default_fractions".format( "/".join( os.path.realpath(__file__).split("/")[:-1] ) )
    ff_config = "{0}/config/default_ff_config.json".format( "/".join( os.path.realpath(__file__).split("/")[:-1] ) )

    def __init__(self, variable, channel, data_file, add_systematics = False):

        self.frac_file = R.TFile( "{0}/{1}_fractions.root".format(self.fraction_path, channel) ,"read" )
        self.channel = channel

        self.fracs = { "QCD":   self.frac_file.Get("fracs/QCD"),
                       "W":     self.frac_file.Get("fracs/W"),
                       "TT":    self.frac_file.Get("fracs/TT"),
                       "DY":    self.frac_file.Get("fracs/DY"),
        }        

        dummy = self.frac_file.Get("dummy")
        self.fracs["px"] = dummy.ProjectionX()
        self.fracs["py"] = dummy.ProjectionY()
        self.frac_var  = dummy.GetTitle().split(":")
        self.frac_isopen = True


        with open(self.ff_config,"r") as FSO:
            config = json.load(FSO)


        self.ff_obj  = R.TFile.Open( config["ff_file"][channel] )
        self.ff = self.ff_obj.Get("ff_comb")
        self.ff_isopen = True

        self.data_file = data_file
        self.variable = variable

        self.inputs = config["inputs"][channel]

        self.uncert_naming = config["uncert_naming"]
        self.uncerts = ["jetFakes"]
        if add_systematics:
            self.uncerts += [ str(u) for u in config["uncerts"][channel] ]


    def __del__(self):
        if self.frac_isopen:
            self.frac_file.Close()

        if self.ff_isopen:
            self.ff.Delete()
            self.ff_obj.Close()

    def addFF(self, row):

        if self.channel == "tt":
            if row["aiso1"]:
                input_list = self.inputs["aiso1"]
            elif row["aiso2"]:
                input_list = self.inputs["aiso2"]
            else:
                return [0.]*len(self.uncerts)
        else:
            input_list = self.inputs

        binx = self.fracs["px"].GetXaxis().FindBin( row[ self.frac_var[0] ] )
        biny = self.fracs["py"].GetXaxis().FindBin( row[ self.frac_var[1] ] )

        frac = { "QCD":   self.fracs["QCD"].GetBinContent(binx, biny),
                 "W":     self.fracs["W"].GetBinContent(binx, biny),
                 "TT":    self.fracs["TT"].GetBinContent(binx, biny),
                 "DY":    self.fracs["DY"].GetBinContent(binx, biny),
        }

        inputs = []
        for v in input_list["vars"]:
            inputs.append( row[v] )
        for f in input_list["frac"]:
            inputs.append( frac[f] )

        ff = []
        for uncert in self.uncerts:

            if uncert == "jetFakes":
                ff_value = self.ff.value( len(inputs),array('d',inputs) ) 
            else:
                ff_value = self.ff.value( len(inputs),array('d',inputs), uncert )

            if  not R.TMath.IsNaN(ff_value):
                ff.append(ff_value)
            else:
                ff.append(0.0)
       

        return ff

    def calc(self, binning, cut ):

        cut = cut.switchTo("-ANTIISO-")
        if self.channel != "tt":
            
            data_content = rp.read_root( paths = self.data_file,
                                         where = cut.get(),
                                         columns =  self.inputs["vars"] + [self.variable] + self.frac_var  ) 

        else:

            inputs = list( set( self.inputs["aiso1"]["vars"] + self.inputs["aiso2"]["vars"] ) )

            for iso in ["VTight","Tight","Loose","VLoose"]:
                inputs.append( "by{0}IsolationMVArun2v1DBoldDMwLT_1".format(iso) )
                inputs.append( "by{0}IsolationMVArun2v1DBoldDMwLT_2".format(iso) )

            data_content = rp.read_root( paths = self.data_file,
                                         where = cut.get(),
                                         columns =inputs+ [self.variable] + self.frac_var )

            data_content.eval(" aiso1 = {0} ".format( Cut("-ANTIISO1-","tt").getForDF() ), inplace = True  )
            data_content.eval(" aiso2 = {0} ".format( Cut("-ANTIISO2-","tt").getForDF() ), inplace = True  )


        ff_weights = []
        for _, row in data_content.iterrows():
            result = self.addFF(row)
            # if not result: continue
            ff_weights.append( self.addFF(row) )

        ff_weights = DataFrame(ff_weights)


        if self.channel == "tt":
            ff_weights *= 0.5

        FFHistos = {}
        for i,uncert in enumerate(self.uncerts):

            if not uncert == "jetFakes":
                name = self.convertSystematicName(uncert)
            else:
                name = uncert

            FFHistos[name] = R.TH1D(name,name,*(binning) )
            rn.fill_hist( FFHistos[name], array = data_content[self.variable].values,
                          weights = ff_weights[i].values )

        norm_factors = {}
        for name, hist in FFHistos.items():
            if name == "jetFakes": continue
            norm_factors[name] =  FFHistos["jetFakes"].Integral() / hist.Integral()

            hist.Scale( norm_factors[name] )


        if norm_factors: FFHistos["jetFakes_norm"] = self.getNormUncertainty(norm_factors)

        return FFHistos

    def convertSystematicName(self,name):

        if "ff_w_syst" in name or "ff_tt_syst" in name:
            if not self.channel == "tt":
                uncert_name = "jetFakes_" + self.uncert_naming[name].format(channel = "")
            else:
                uncert_name = "jetFakes_" + self.uncert_naming[name].format(channel = "_"+self.channel )
                uncert_name = uncert_name.replace("_ff_tt","_ff_ttbar")
        else:
            uncert_name = "jetFakes_" + self.uncert_naming[name].format(channel = "_"+self.channel )
        return uncert_name

    def getNormUncertainty(self, norm_factors ):
        ff_norm = R.TH1D("jetFakes_norm","jetFakes_norm",4,-0.5,3.5 )

        norms = { "statUp":0.,"statDown":0.,"systUp":0.,"systDown":0. }
        for name, factor in norm_factors.items():
            if "syst" in name: key  = "syst"
            else:              key  = "stat"
            if factor > 1:     key += "Up"
            else:              key += "Down"

            norms[key] = math.sqrt( norms[key]**2 + (1. - factor)**2  )

        ff_norm.SetBinContent(1, norms["statUp"])
        ff_norm.SetBinContent(2, norms["statDown"])
        ff_norm.SetBinContent(3, norms["systUp"])
        ff_norm.SetBinContent(4, norms["systDown"])

        return ff_norm    



if __name__ == '__main__':
    main()


