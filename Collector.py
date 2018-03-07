import numpy as np
import ROOT as R
import os
import sys
import copy
import json
import root_numpy as rn
import root_pandas as rp

def main():
    from Reader import Reader
    from Plotter import Plotter
    if len(sys.argv) == 2:
        var = sys.argv[1]
    else:
        var = "pred_prob"

    read = Reader("et","conf/scale_samples.json", 2)
    C = Collector("et","htt_et.inputs-sm-13TeV-ML.root", read.config["target_names"] )
    C.createDC(var,True)
    C.DCfile.Close()
    plot = Plotter( "htt_et.inputs-sm-13TeV-ML.root", naming = read.processes )
    plot.makePlots()
    plot.combineImages( )

class Collector():

    def __init__(self, channel, filename="", target_names={}):
        self.channel = channel
        self.DCfile = None

        if filename:
            self.DCfile =  R.TFile(filename,"RECREATE")

        if target_names:
            self.target_names = {int(k):v for k,v in target_names.items()}
            for name in self.target_names.values():
                self.DCfile.mkdir( self.d(name) )

        with open("conf/reweighting.json","r") as FSO:
            self.reweight = json.load(FSO)

        self.binning = {
        "pred_prob":(21,0,1.05),
        "eta_1": (30,-3,3),
        "iso_1": (100,0,1),
        "iso_2": (100,0,1),
        "eta_2": (50,-2.3,2.3),
        "pt_1": (100,20,220),
        "pt_2": (100,20,220),
        "jpt_1": (100,-10,220),
        "jpt_2": (100,-10,220),
        "jm_1": (100,-10,100),
        "jm_2": (100,-10,100),
        "jphi_1": (100,-10,5),
        "jphi_2": (100,-10,5),
        "bpt_1": (100,-10,220),
        "bpt_2": (100,-10,220),
        "bcsv_1": (100,0,1),
        "bcsv_2": (100,0,1),
        "beta_1": (100,-10,2.5),
        "beta_2": (100,-10,2.5),
        "njets": (12,0,12),
        "nbtag": (12,0,12),
        "mt_1": (100,0,100),
        "mt_2": (100,0,150),
        "pt_tt": (100,0,150),
        "m_sv": (100,0,300),
        "m_vis": (30,0,300),
        "mjj": (100,-10,150),
        "met": (100,0,150),
        "dzeta": (100,-100,150)
        }

    def __del__(self):
        if self.DCfile:
            self.DCfile.Close()

    def d(self, target):
        return "_".join([self.channel, target]) 

    def addPrediction(self, prediction, df, sample):
        for i in xrange( len(df) ):

            df[i]["pred_prob"] =  prediction[i]["predicted_prob"]
            df[i]["pred_class"] = prediction[i]["predicted_class"]
            if sample == "ZTT":
                df[i]["event_weight"] *= 0.95
            if i == 0: mode = "w"
            else: mode = "a"
            df[i].to_root("predictions/{0}/{1}.root".format(self.channel, sample), key="TauCheck", mode = mode)

    def createDC(self, var, writeAll = True, abs_path = ""):
        if not self.DCfile:
            print "Where should I write?"
            return

        path = "predictions/{0}/".format(self.channel)
        if abs_path: path = "/".join([abs_path,path])
        files = os.listdir( path )

        shapes   = [ path+s for s in files if "_CMS_" in s]
        looseMC =  [ path+s for s in files if "_more" in s or "estimate" in s]
        nominal  = [ path+s for s in files if not "_CMS_" in s and not "_more" in s and not "estimate" in s]

        print looseMC
        print nominal

        self.writeTemplates(var, nominal, writeAll)
        self.estimateQCD(var, looseMC)
        if writeAll:
            self.writeTemplates(var, shapes)



    def writeTemplates(self, var, templates, reweight = False):
        for template in templates:
            histname = template.split("/")[-1].replace(".root","")
            templ_content = rp.read_root( paths = template )

            classes = np.unique( templ_content["pred_class"] )
            for c in classes:

                tmpCont = templ_content.query( "pred_class == {0}".format(int(c)) )
                tmpHist = R.TH1D(histname,histname,*self.binning[var])
                rn.fill_hist( tmpHist, array = tmpCont[var].values,
                              weights = tmpCont["event_weight"].values )
                self.DCfile.cd( self.d( self.target_names[int(c)] ) )
                tmpHist.Write()

                if reweight:
                    for rw in self.reweight:
                        rwname = rw.replace("reweight",histname).replace("CHAN",self.channel).replace("CAT", self.target_names[int(c)] )
                        tmpHist = R.TH1D(rwname,rwname,*self.binning[var])
                        rn.fill_hist( tmpHist, array = tmpCont[var].values,
                                      weights = tmpCont.eval( self.reweight[rw] ).values )
                        tmpHist.Write()

    def getWscale(self):
        for region in ["","_ss"]:
            templ_content = rp.read_root( paths = "W"+region,
                                          where = "mt_1 > 80" )

            tmpHist = R.TH1D("Wscale"+region,"Wscale"+region,*self.binning[var])
            rn.fill_hist( tmpHist, array = templ_content[var].values,
                          weights = templ_content["event_weight"].values )

    def estimateQCD(self, var, looseMC):

        if self.channel != "tt":

            for c,t in self.target_names.items():
                
                tmpQCD = R.TH1D("QCD","QCD",*self.binning[var])

                for i,template in enumerate(looseMC):

                    tmpHist = R.TH1D("QCD"+str(i), "QCD"+str(i), *self.binning[var])
                    templ_content = rp.read_root( paths  = template,
                                                  where = "pred_class == {0}".format(int(c)) )

                    rn.fill_hist( tmpHist, array = templ_content[var].values,
                                  weights = templ_content["event_weight"].values )

                    if "estimate" in template: tmpQCD.Add(tmpHist)
                    else:                  tmpQCD.Add(tmpHist, -1)

                self.DCfile.cd( self.d( t ) )
                for rw in ["QCD_WSFUncert_{chan}_{cat}_13TeVUp","QCD_WSFUncert_{chan}_{cat}_13TeVDown"]:
                    tmp = copy.deepcopy( tmpQCD )
                    tmp.SetName(rw.format( chan = self.channel, cat = t ))
                    tmp.Write()
                tmpQCD.Write()
        else:
            for c,t in self.target_names.items():

                tmpQCD = R.TH1D("QCD","QCD",*self.binning[var])

                for i,template in enumerate(looseMC):
                    if not "estimate" in template: continue

                    templ_content = rp.read_root( paths  = template,
                                                  where = "pred_class == {0}".format(int(c)) )

                    rn.fill_hist( tmpQCD, array = templ_content[var].values )

                    tmpQCD.Scale( 0.239 )

                self.DCfile.cd( self.d( t ) )
                for rw in ["QCD_WSFUncert_{chan}_{cat}_13TeVUp","QCD_WSFUncert_{chan}_{cat}_13TeVDown"]:
                    tmp = copy.deepcopy( tmpQCD )
                    tmp.SetName(rw.format( chan = self.channel, cat = t ))
                    tmp.Write()
                tmpQCD.Write()


if __name__ == '__main__':
    main()

