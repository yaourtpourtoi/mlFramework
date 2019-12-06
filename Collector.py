import numpy as np
import ROOT as R
import os
import sys
import shutil
import copy
import json
import root_numpy as rn
import root_pandas as rp
from array import array
from utils.CutObject import Cut
from utils.VarObject import Var
from utils.FakeFactor import FakeFactor
Cut.cutfile = "conf/cuts.json"
FakeFactor.ff_config = "conf/ff_config.json"
FakeFactor.fraction_path = "fractions"


def main():
    from Reader import Reader
    from Plotter import Plotter
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='channel', help='Decay channel' ,choices = ['mt','et','tt'], default = 'mt')
    parser.add_argument('-v', dest='var',   help='Variable to collect' , default = 'pred_prob')
    parser.add_argument('-a', dest='all',   help='Also write shape templates' , action = 'store_true')
    parser.add_argument('-m', dest='model',   help='Use predictions from model' ,default = 'keras')
    args = parser.parse_args()

    print("---------------------------------")
    print("Collecting {0} events".format(args.channel))
    print("Using prediction from {0}".format(args.model))
    print("Writing {0} to datacard".format( args.var ))
    if args.all:
        print("Add systematic templates in datacard")
    print("---------------------------------")

    read = Reader(channel=args.channel,
                  config_file = "conf/global_config_2017.json",
                  folds = 2)

    C = Collector(channel = args.channel,
                  var_name = args.var,
                  target_names = read.config["target_names"],
                  path = args.model,
                  rebin = False )

    C.createDC(args.all)

    P = Plotter( channel = args.channel,
                 naming = read.processes,
                 path = args.model )

    P.makePlots()
    # P.combineImages( )

class Collector():

    def __init__(self, channel, var_name, target_names={}, path = "", recreate = False, rebin = False):
        self.channel = channel

        self.rebin = rebin
        self.predictionPath = "/".join(["predictions",path, channel])

        if recreate and os.path.exists(self.predictionPath ):
            print("Replacing predictions in {0} {1}".format(channel, path))
            shutil.rmtree( self.predictionPath  )

        if not os.path.exists(self.predictionPath ):
            os.makedirs(self.predictionPath )

        if not os.path.exists(path):
            os.mkdir(path)

        if path:  self.filename = "/".join([path, "htt_"+channel+".inputs-sm-13TeV-ML.root"])
        else:     self.filename = "htt_"+channel+".inputs-sm-13TeV-ML.root"

        if target_names:  self.target_names = {int(k):v for k,v in list(target_names.items())}
        else:             self.target_names = target_names

        self.createDCFile()

        with open("conf/reweighting.json","r") as FSO:
            self.systematics = json.load(FSO)

        self.var = Var( var_name )
        if rebin and var_name == "pred_prob":
            self.var.binning = {"def": (8, array("d", [0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0] ) ), 
                                "ggh": (100,0.2, 1.0  ),
                                "qqh": (100,0.2, 1.0  )}

        self.stxs1_cuts = {
            "ggH125":{
                "":                 "",
                "_0J":               "& njets == 0",
                "_1J_PTH_0_60":      "& njets == 1 & pt_tt > 0 & pt_tt < 60",
                "_1J_PTH_60_120":    "& njets == 1 & pt_tt > 60 & pt_tt < 120",
                "_1J_PTH_120_200":   "& njets == 1 & pt_tt > 120 & pt_tt < 200",
                "_1J_PTH_GT200":     "& njets == 1 & pt_tt > 200",
                "_GE2J_PTH_0_60":    "& njets >= 2 & pt_tt > 0 & pt_tt < 60",
                "_GE2J_PTH_60_120":  "& njets >= 2 & pt_tt > 60 & pt_tt < 120",
                "_GE2J_PTH_120_200": "& njets >= 2 & pt_tt > 120 & pt_tt < 200",
                "_GE2J_PTH_GT200":   "& njets >= 2 & pt_tt > 200",
                "_VBFTOPO_JET3":     "& njets >= 2 & pt_tt < 200 & mjj > 400 & jdeta > 2.8",
                "_VBFTOPO_JET3VETO": "& njets >= 2 & pt_tt < 200 & mjj > 400 & jdeta > 2.8"
            },
            "qqH125":{
                "":"",
                "_VBFTOPO_JET3":     "& njets >= 2 & pt_tt > 0 & pt_tt < 25 & jpt_1 > 0 & jpt_1 < 200 & mjj > 400 & jdeta > 2.8",
                "_VBFTOPO_JET3VETO": "& njets >= 2 & pt_tt >= 25 & jpt_1 > 0 & jpt_1 < 200 & mjj > 400 & jdeta > 2.8",
                "_VH2JET":           "& njets >= 2 & jpt_1 > 0 & jpt_1 < 200 & mjj > 60 & mjj < 120",
                "_REST":             "& njets >= 2 & jpt_1 > 0 & jpt_1 < 200", 
                "_PTJET1_GT200":     "& jpt_1 > 200" 
            } 

        }

    def __del__(self):
        if self.DCfile and not self.FileClosed:
            self.DCfile.Close()

    def createDCFile(self):
        self.FileClosed = False
        self.DCfile =  R.TFile(self.filename,"RECREATE")

        for name in list(self.target_names.values()):
            self.DCfile.mkdir( self.d(name) )

    def d(self, target):
        return "_".join([self.channel, target]) 

    def applySF(self,df, process):
        with open("conf/scalefactors.json","r") as FSO:
            sfs = json.load(FSO)

        apply_sf= "event_weight"
        for sf in sfs:
            if process in sfs[sf][self.channel]["on"] or "all" in sfs[sf][self.channel]["on"]:
                apl = sfs[sf][self.channel]["apply"] 
                if apl: apply_sf += "*{0}".format(apl)

        df.eval("event_weight = {0}".format( apply_sf ), inplace = True )

    def addPrediction(self, prediction, df, sample):
        for i in range( len(df) ):

            df[i]["pred_prob"] =  prediction[i]["predicted_prob"]
            df[i]["pred_class"] = prediction[i]["predicted_class"]
            self.applySF(df[i], sample)

            if i == 0: mode = "w"
            else: mode = "a"
            df[i].to_root("{0}/{1}.root".format(self.predictionPath, sample), key="TauCheck", mode = mode)

    def createDC(self, writeAll = True, abs_path = ""):
        if not self.DCfile or self.FileClosed:
            print("Where should I write?")
            return


        path = self.predictionPath + "/"
        if abs_path: path = "/".join([abs_path,path])
        files = os.listdir( path )

        shapes   = [ path+s for s in files if "_CMS_" in s]
        looseMC  = [ path+s for s in files if not "_CMS_" in s and ("_more" in s or "estimate" in s) ]
        nominal  = [ path+s for s in files if not "_CMS_" in s and not "_more" in s and not "estimate" in s]


        self.writeTemplates( nominal, writeAll)
        self.estimateQCD( looseMC, writeAll)
        if writeAll:
            self.writeTemplates( shapes)

        self.DCfile.Close()
        self.FileClosed = True

        if self.rebin:
            print("Start rebinning")
            self.setRebinning()
            self.createDCFile()

            self.writeTemplates( nominal, writeAll)
            self.estimateQCD( looseMC, writeAll)
            if writeAll:
                self.writeTemplates( shapes)

            self.DCfile.Close()
            self.FileClosed = True




    def setRebinning(self):
        DC = R.TFile( self.filename, "READ" )

        Dirs = {"ggh": DC.Get(self.channel + "_ggh"), "qqh":DC.Get(self.channel + "_qqh") }

        sig = ["ggH125", "qqH125"]
        bkg = ["TTT","TTJ","ZTT","ZL","ZJ","VVT","VVJ","W","QCD","EWKZ"]

        Hists = {}
        for Dir in Dirs:
            Hists[Dir] = {"s":R.TList(),"b":R.TList()}
            for hist in Dirs[Dir].GetListOfKeys():
                hname = hist.GetName()

                if hname in sig:
                    Hists[Dir]["s"].Add( copy.deepcopy( Dirs[Dir].Get( hname )  ) )
                elif hname in bkg:
                    Hists[Dir]["b"].Add( copy.deepcopy( Dirs[Dir].Get( hname )  ) )

            for h in ["s","b"]:
                tmp = copy.deepcopy( Hists[Dir][h][0] )
                tmp.Reset()
                tmp.Merge( Hists[Dir][h] )
                Hists[Dir][h] = copy.deepcopy( tmp ) 

            self.binning["pred_prob"][Dir] = rebin( Hists[Dir]["s"], Hists[Dir]["b"] )

        DC.Close()


    def writeTemplates(self, templates, add_systematics = False):
        print("Write Templates")

        for template in templates:
            histname = template.split("/")[-1].replace(".root","")
            templ_content = rp.read_root( paths = template )
            if self.var.name == "pred_prob":
                templ_content[self.var.name].replace(1.0,0.9999, inplace = True)

            classes = np.unique( templ_content["pred_class"] )
            for c in classes:

                if histname == "ggH125" or histname  == "qqH125":
                    for stxs1 in self.stxs1_cuts[histname]:
                        name = histname.replace("125",stxs1 + "125")
                        cut = "pred_class == {0}{1}".format(int(c), self.stxs1_cuts[histname][stxs1] )
                        self.fillHistos(templ_content, name, c, cut, add_systematics)
                else:
                    cut = "pred_class == {0} ".format(int(c) )
                    self.fillHistos(templ_content, histname, c, cut, add_systematics)

                # tmpCont = templ_content.query(  )

                # tmpHist = R.TH1D(histname,histname,*binning )
                # tmpHist.GetXaxis().SetTitle( self.var.name )
                # tmpHist.Sumw2()
                # rn.fill_hist( tmpHist, array = tmpCont[self.var.name].values,
                #               weights = tmpCont["event_weight"].values )

                # self.DCfile.cd( self.d( self.target_names[int(c)] ) )

                # tmpHist.Write()

                # if add_systematics:
                #     for rw in self.systematics:
                #         rwname = rw.replace("reweight",histname).replace("CHAN",self.channel).replace("CAT", self.target_names[int(c)] )
                #         tmpHist = R.TH1D(rwname,rwname,*binning)
                #         rn.fill_hist( tmpHist, array = tmpCont[self.var.name].values,
                #                       weights = tmpCont.eval( self.systematics[rw] ).values )
                #         tmpHist.Write()

    def fillHistos(self, content, histname, cat, cut,add_systematics):

        binning = self.var.bins( int(cat) )
        tmpCont = content.query( cut )

        tmpHist = R.TH1D(histname,histname,*binning )
        tmpHist.GetXaxis().SetTitle( self.var.name )
        tmpHist.Sumw2()
        rn.fill_hist( tmpHist, array = tmpCont[self.var.name].values,
                      weights = tmpCont["event_weight"].values )

        self.DCfile.cd( self.d( self.target_names[int(cat)] ) )

        tmpHist.Write()

        if add_systematics:
            for rw in self.systematics:
                rwname = rw.replace("reweight",histname).replace("CHAN",self.channel).replace("CAT", self.target_names[int(cat)] )
                tmpHist = R.TH1D(rwname,rwname,*binning)
                rn.fill_hist( tmpHist, array = tmpCont[self.var.name].values,
                              weights = tmpCont.eval( self.systematics[rw] ).values )
                tmpHist.Write()

    def estimateQCD(self, looseMC, add_systematics = False):

        print("Estimating Jet Fakes")
        for i,template in enumerate(looseMC):
            if not "data" in template: continue
            FF = FakeFactor( self.channel, data_file = template )

            for c,t in list(self.target_names.items()):
                binning = self.var.bins( t )
                ff_select = Cut("pred_class == {0} && -OS- && -ANTIISO- ".format( int(c) ), self.channel)
                FFHistos = FF.calc( self.var, ff_select, add_systematics )

                self.DCfile.cd( self.d( t ) )


                for name,FFHist in list(FFHistos.items()):
                    FFHist.Write()
                    FFHist.Delete()
                    

        print("Estimating QCD")
        if self.channel != "tt":

            for c,t in list(self.target_names.items()):
                binning = self.var.bins( t )

                tmpQCD = R.TH1D("QCD","QCD",*binning)

                for i,template in enumerate(looseMC):
                    if "data" in template: continue 

                    tmpHist = R.TH1D("QCD"+str(i), "QCD"+str(i), *binning)
                    tmpHist.Sumw2()
                    templ_content = rp.read_root( paths  = template,
                                                  where =  Cut("pred_class == {0} && -SS- && -ISO-".format( int(c) ), self.channel).get() 
                                                )

                    if self.var.name == "pred_prob":
                        templ_content[self.var.name].replace(1.0,0.9999, inplace = True)

                    rn.fill_hist( tmpHist, array = templ_content[self.var.name].values,
                                  weights = templ_content["event_weight"].values )

                    if "estimate" in template: tmpQCD.Add(tmpHist)
                    else:                  tmpQCD.Add(tmpHist, -1)

                self.DCfile.cd( self.d( t ) )
                if add_systematics:
                    for rw in ["QCD_WSFUncert_{chan}_{cat}_13TeVUp","QCD_WSFUncert_{chan}_{cat}_13TeVDown"]:
                        rwname = rw.format( chan = self.channel, cat = t )
                        tmp = copy.deepcopy( tmpQCD )
                        tmp.SetName(rwname)
                        tmp.Write()

                tmpQCD.Write()
        else:

            for c,t in list(self.target_names.items()):

                binning = self.var.bins( t )

                tmpHists = { "-ISO-":    {"-SS-": R.TH1D("ssiso"+t,"ssiso"+t,*binning),   "-OS-": R.TH1D("osiso"+t,"osiso"+t,*binning)},
                             "-ANTIISO2-":{"-SS-": R.TH1D("ssaiso"+t,"ssaiso"+t,*binning), "-OS-": R.TH1D("osaiso"+t,"osaiso"+t,*binning)} 
                            }

                for i,template in enumerate(looseMC):

                    for iso in tmpHists:
                        for sign in tmpHists[iso]:
                            if sign == "-SS-" and "estimate" in template: continue
                            if sign == "-OS-":
                                if "data" in template: continue
                                if iso == "-ISO-" and "estimate" in template: continue

                            tmpHist =  R.TH1D(sign+str(i)+iso, sign+str(i)+iso, *binning)
                            try:
                                templ_content = rp.read_root( paths  = template,
                                                              where = Cut("pred_class == {0} && {1} && {2}".format( int(c), iso, sign ), self.channel).get()
                                                            )
                            except IndexError:
                                pass
                            rn.fill_hist( tmpHist, array = templ_content[self.var.name].values,
                                          weights = templ_content["event_weight"].values )

                            if "data" in template or "estimate" in template: addV = 1
                            else: addV = -1
                            tmpHists[iso][sign].Add(tmpHist, addV)

                tmpHists["-ANTIISO2-"]["-OS-"].Scale( tmpHists["-ISO-"]["-SS-"].Integral() / float(tmpHists["-ANTIISO2-"]["-SS-"].Integral() ) )
                tmpHists["-ANTIISO2-"]["-OS-"].SetName("QCD")

                self.DCfile.cd( self.d( t ) )
                if add_systematics:
                    for rw in ["QCD_WSFUncert_{chan}_{cat}_13TeVUp","QCD_WSFUncert_{chan}_{cat}_13TeVDown"]:
                        rwname = rw.format( chan = self.channel, cat = t )
                        tmp = copy.deepcopy( tmpHists["-ANTIISO2-"]["-OS-"] )
                        tmp.SetName(rwname)
                        tmp.Write()
                tmpHists["-ANTIISO2-"]["-OS-"].Write()



def rebin(m_sig, m_bg):
    #    const float RELSTATMAX=0.5
    RELSTATMAX=float(0.2)
    BINC=float(1.4)

    bin_edge = np.array([])
    
    nedges = int( m_sig.GetNbinsX()+1 ) #edges=bins+1
    bin_edge = [ float( m_sig.GetBinLowEdge( nedges ) ) ]

    bprev=0
    b=0
    s=0
    serr2=0
    berr2=0
    for i in reversed(range(1,nedges-1)): #loop over bin edges


        s += m_sig.GetBinContent(i)
        serr2 += m_sig.GetBinError(i)**2

        b += m_bg.GetBinContent(i)
        berr2 += m_bg.GetBinError(i)**2

        # t_edge=m_sig.GetBinLowEdge( i )
        #check if this is a new edge
        if ( b<1e-3 ): continue #if b is negativ or 0 or very small, continue
        if ( (np.sqrt(berr2)/b)>RELSTATMAX ): continue #if the rel stat unc on the background is >X%, continue
        if ( b<bprev*BINC ): continue #more b than bin to the right (previous bin)


        # if ( t_edge<0.8 ):
        #     if ( bin_edge[-1]-t_edge < 0.05 ): continue
        # if ( t_edge<0.6 ):
        #     if ( bin_edge[-1]-t_edge < 0.10 ): continue
        # if ( t_edge<0.4 ):
        #     if ( bin_edge[-1]-t_edge < 0.20 ): continue

        #we have a new edge!
        bin_edge.append( m_sig.GetBinLowEdge( i ) )
       
        bprev=b
        b=0
        s=0
        serr2=0
        berr2=0

    if bin_edge[-1] > 0.2: bin_edge[-1] = 0.2
    # bin_edge.append( 0.2 )

    bin_edge = array("d",bin_edge[::-1])

    return ( len(bin_edge)-1, bin_edge )





if __name__ == '__main__':
    main()
