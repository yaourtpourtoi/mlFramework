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

Cut.cutfile = "utils/cuts.json"

def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='channel', help='Decay channel' ,choices = ['mt','et','tt'], default = 'mt')
    parser.add_argument('-p', dest='plot',    help='Plot fractions' , action = "store_true")
    args = parser.parse_args()

    # Frac = Fractions(args.channel, ["pt_2","njets"], [ (9, array("d",[20,30,35,40,45,50,80,90,100,200] ) ) , (3, array("d",[-0.5,0.5,1.5,15]) )  ] )
    Frac = Fractions(args.channel, ["m_vis","njets"], [ (30,0,300 ) , (3, array("d",[-0.5,0.5,1.5,15]) )  ] )
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

        # self.weights = ["puweight","stitchedWeight","trk_sf","genweight","effweight","topWeight_run1","zPtReweightWeight","antilep_tauscaling"]
        self.weights = "puweight * xsec * 1000 * genNEventsWeight * trk_sf * reco_sf * genweight * antilep_tauscaling * idisoweight_1 * singleTriggerSFLeg1"
        if channel == "tt": self.weights += "*xTriggerSFLeg1*xTriggerSFLeg2"
        # self.lumi = 35.9
        self.lumi = 41.860

        svfit = "SVFIT"
        version = "v2"


        # path = "/afs/hephy.at/work/m/mspanring/HephyHiggs/mlFramework/predictions/keras/{0}/".format( channel)
        path = "/data/higgs/data_2017/v3/{0}-NOMINAL_ntuple_".format( channel)
        ext = ".root"

        # self.mcSamples = [
        #     (path + "W_more"+ext,"W",""),
        #     (path + "Z_more"+ext,"ZTT",Cut("-GENHAD-") ),
        #     (path + "Z_more"+ext,"ZL", Cut("-GENLEP-") ),
        #     (path + "Z_more"+ext,"ZJ", Cut("-GENJET-") ),
        #     (path + "TT_more"+ext,"TTT",Cut("-GENHAD-") ),
        #     (path + "TT_more"+ext,"TTJ",Cut("!-GENHAD-") ),
        #     (path + "VV_more"+ext,"VVT",Cut("-GENHAD-") ),
        #     (path + "VV_more"+ext,"VVJ",Cut("!-GENHAD-") ),
        # ]
        # self.dataSample = {
        #     "mt":path + "data_more"+ext,
        #     "et":path + "data_more"+ext,
        #     "tt":path + "data_more"+ext
        # }

        self.mcSamples = [
            (path + "WJets.root","W",""),
            (path + "DY.root","ZTT",Cut("-GENHAD-") ),
            (path + "DY.root","ZL", Cut("-GENLEP-") ),
            (path + "DY.root","ZJ", Cut("-GENJET-") ),
            (path + "TT.root","TTT",Cut("-GENHAD-") ),
            (path + "TT.root","TTJ",Cut("!-GENHAD-") ),
            (path + "VV.root","VVT",Cut("-GENHAD-") ),
            (path + "VV.root","VVJ",Cut("!-GENHAD-") ),
        ]
        self.dataSample = path + "Data.root"


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
                "W":["W","VVJ","ZJ"],
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

        histos["data"]     = self.fillHisto( self.dataSample,self.cut, "data_obs", weight = False )

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

    def applySF(self, df, process):
        with open("scalefactors.json","r") as FSO:
            sfs = json.load(FSO)

        apply_sf= "eweight"
        for sf in sfs:
            if process in sfs[sf][self.channel]["on"] or "all" in sfs[sf][self.channel]["on"]:
                apl = sfs[sf][self.channel]["apply"] 
                if apl: apply_sf += "*{0}".format(apl)

        df.eval("eweight = {0}".format( apply_sf ), inplace = True )

    def fillHisto(self, path, cut, name, weight = True):

        add_weights = ["puweight","xsec","genNEventsWeight","trk_sf","reco_sf","genweight","antilep_tauscaling","idisoweight_1","singleTriggerSFLeg1","xTriggerSFLeg1","xTriggerSFLeg2","zPtReweightWeight","topWeight_run1","pt_1","pt_2"]

        tmpHist = R.TH2D(name,name,*( self.binning ))

        if not os.path.exists(path):
            print "Warning", path
            return tmpHist

        tmp =   rp.read_root( paths = path,
                              where = cut.get(),
                              columns = add_weights + self.var+ ["gen_match_1","gen_match_2","decayMode_1","decayMode_2","pt_2","NUP"] 
                            )

        if weight:

            weights = self.weights
            if name in ["W"]:
                weights = weights.replace("xsec*1000*genNEventsWeight*","((NUP == 0)*0.79056 + (NUP == 1)*0.15036 + (NUP == 2)*0.30714 + (NUP == 3)*0.05558 + (NUP == 4)*0.05227)*")
            if name in ["ZL","ZTT","ZJ","DY"]:
                weights = weights.replace("xsec*1000*genNEventsWeight*","zPtReweightWeight*((NUP == 0)*0.05913 + (NUP == 1)*0.01017 + (NUP == 2)*0.02150 + (NUP == 3)*0.01351 + (NUP == 4)*0.00922)*")                
            tmp.eval( "eweight = " + weights ,  inplace = True )
            if name in ["TTT","TTJ"]:
                tmp.eval( "eweight = eweight*topWeight_run1",  inplace = True )
            
            tmp["eweight"] *= float(self.lumi)
            self.applySF(tmp, name)
        else:        
            tmp.eval( "eweight = 1"  , inplace = True )

        #dictionary
        tmpHist.SetOption("COLZ")
        rn.fill_hist( tmpHist, array = tmp[self.var].values,
                               weights = tmp["eweight"].values )

        return tmpHist

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
            cv.Print(str(i) +'_'+self.channel+ '_fractions.png') 

        file.Close()

class FakeFactor():

    fraction_path = "{0}/default_fractions".format( "/".join( os.path.realpath(__file__).split("/")[:-1] ) )
    ff_config = "{0}/config/default_ff_config.json".format( "/".join( os.path.realpath(__file__).split("/")[:-1] ) )

    def __init__(self, channel, data_file):

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
            self.config = json.load(FSO)


        self.ff_obj  = R.TFile.Open( self.config["ff_file"][channel] )
        self.ff = self.ff_obj.Get("ff_comb")
        self.ff_isopen = True

        self.data_file = data_file

        self.inputs = self.config["inputs"][channel]

        self.uncert_naming = self.config["uncert_naming"]
        self.uncerts = ["jetFakes"]


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
                 # "DY":    self.fracs["DY"].GetBinContent(binx, biny),
        }

        input_vars = []
        input_fracs = []
        for v in input_list["vars"]:
            input_vars.append( row[v] )
        for f in input_list["frac"]:
            input_fracs.append( frac[f] )

        # tf = frac["QCD"] + frac["W"] + frac["TT"]
        # # inputs += [tf, 0. ,0.]
        # # inputs += [0., tf, 0.]
        # inputs += [0., 0. ,tf]

        ff = []
        for uncert in self.uncerts:

            if uncert == "jetFakes":
                ff_value = self.ff.value( len(input_vars+input_fracs),array('d',input_vars+input_fracs) )
            elif uncert == "jetFakes_QCD":
                ff_value = self.ff.value( len(input_vars)+3, array('d',input_vars+[frac["QCD"],0.,0.]) )
            elif uncert == "jetFakes_W":
                ff_value = self.ff.value( len(input_vars)+3, array('d',input_vars+[0.,frac["W"],0.]) )
            elif uncert == "jetFakes_TT":
                ff_value = self.ff.value( len(input_vars)+3, array('d',input_vars+[0.,0.,frac["TT"]]) )                                
            else:
                ff_value = self.ff.value( len(input_vars+input_fracs),array('d',input_vars+input_fracs), uncert )

            if  not R.TMath.IsNaN(ff_value):
                ff.append(ff_value)
            else:
                ff.append(0.0)
       

        return ff

    def calc(self, variable, cut, add_systematics = True, debug = False ):

        if add_systematics:
            self.uncerts += [ str(u) for u in self.config["uncerts"][self.channel] ]
        if debug:
            self.uncerts += ["jetFakes_W","jetFakes_TT","jetFakes_QCD"]

        cut = cut.switchTo("-ANTIISO-")
        if self.channel != "tt":
            
            data_content = rp.read_root( paths = self.data_file,
                                         where = cut.get(),
                                         columns =  self.inputs["vars"] + variable.getBranches(for_df = True) + self.frac_var  ) 

        else:

            inputs = list( set( self.inputs["aiso1"]["vars"] + self.inputs["aiso2"]["vars"] ) )

            for iso in ["VTight","Tight","Loose","VLoose"]:
                inputs.append( "by{0}IsolationMVArun2017v2DBoldDMwLT2017_1".format(iso) )
                inputs.append( "by{0}IsolationMVArun2017v2DBoldDMwLT2017_2".format(iso) )

            data_content = rp.read_root( paths = self.data_file,
                                         where = cut.get(),
                                         columns =inputs+ variable.getBranches(for_df = True) + self.frac_var )

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

            if not "jetFakes" in uncert:
                name = self.convertSystematicName(uncert)
            else:
                name = uncert

            if variable.is2D():
                FFHistos[name] = R.TH2D(name+"2D",name+"2D",*( variable.bins() ))
            else:
                FFHistos[name] = R.TH1D(name,name,*( variable.bins() ))

            rn.fill_hist( FFHistos[name], array = data_content[variable.getBranches()].values,
                          weights = ff_weights[i].values )

            FFHistos[name] = self.unroll2D(FFHistos[name])

        norm_factors = {}
        for name, hist in FFHistos.items():
            if "jetFakes" in name: continue
            norm_factors[name] =  FFHistos["jetFakes"].Integral() / hist.Integral()

            hist.Scale( norm_factors[name] )


        if norm_factors: FFHistos["jetFakes_norm"] = self.getNormUncertainty(norm_factors)

        return FFHistos

    def unroll2D(self, th):
        if type(th) is R.TH1D: return th

        bins = th.GetNbinsX()*th.GetNbinsY()
        name = th.GetName().replace("2D","")
        unrolled = R.TH1D(name,name, *(bins,0,bins) )
        unrolled.Sumw2(True)

        for i,y in  enumerate( xrange(1,th.GetNbinsY()+1) ):
            for x in xrange(1,th.GetNbinsX()+1):
                offset = i*th.GetNbinsX()

                unrolled.SetBinContent( x+offset, th.GetBinContent(x,y) )
                unrolled.SetBinError( x+offset, th.GetBinError(x,y) )

        return unrolled

    def convertSystematicName(self,name):

        if "ff_w_syst" in name or "ff_tt_syst" in name:
            if not self.channel == "tt":
                uncert_name = "jetFakes_" + self.uncert_naming[name].format(channel = "")
            else:
                uncert_name = "jetFakes_" + self.uncert_naming[name].format(channel = "_"+self.channel )
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


