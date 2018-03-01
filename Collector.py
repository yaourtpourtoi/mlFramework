import numpy as np
import ROOT as R
import subprocess as sp
import shlex
import os
import copy
import pandas
import json
import root_numpy as rn
from math import sqrt

class Collector():

    def __init__(self, channel, filename, folds, target_names):
        self.target_names = target_names.values()
        self.file = []
        self.closed = False
        self.folds = folds
        self.channel = channel
        self.filename = filename.replace(".root","")
        self.hist_binning = (21,0.,1.05)
        self.avail_hist = []

        for i in xrange(self.folds):
            self.file.append( R.TFile(self.filename + "fold{0}.root".format(i),"RECREATE") )

            for name in self.target_names:
                self.file[i].mkdir( self.d(name) )

    def __del__(self):
        if not self.closed:
            print "Wait!!! I need to close the root-files!"
            for i in xrange(self.folds):
                self.file[i].Close()
            print "Done."

    def d(self, target):
        return "_".join([self.channel, target])       

    def writePrediction(self, prediction):

        for i in xrange( self.folds ):
            tmpQCD = {}
            for pred in self.target_names:
                self.file[i].cd(self.d(pred))
                tmpQCD[pred] = R.TH1D( "QCD", "QCD" , *self.hist_binning )
                for hist_name in  np.unique( prediction[i]["hist_name"].apply(str) ):

                    tmp = prediction[i].query( "hist_name == '{0}' & predicted_class == '{1}'".format(hist_name,pred) )

                    weights = [ (hist_name,"weight") ] 
                    if not "_CMS_" in hist_name:
                        for c in tmp: 
                            if "reweight" in c: weights.append( (c.replace("reweight",hist_name), c ) )

                    for hname,weight in weights:
                        tmpHist = R.TH1D( hname, hname , *self.hist_binning )
                        tmpHist.Sumw2(True)
                        rn.fill_hist( tmpHist, array = tmp["predicted_prob"].values,
                                               weights = tmp[weight].values )

                        tmpHist.Write()

                

    def estimateQCD(self):
        for i in xrange( self.folds ):
            for key in self.file[i].GetListOfKeys():
                self.file[i].cd( key.GetName() )
                TDir = self.file[i].Get( key.GetName() )
                hists = [ t.GetName() for t  in TDir.GetListOfKeys() ]

                tmpQCD = copy.deepcopy( TDir.Get( "data_ss" ) )
                tmpQCD.SetName("QCD")
                for a in ["Z_samesign","TT_samesign","VV_samesign","W_samesign"]:
                    tmp = copy.deepcopy( TDir.Get( a ) )
                    tmpQCD.Add( tmp, -1 )
                tmpQCD.Write()



    def combineFolds(self, keep_folds = True):
        self.estimateQCD()
        for i in xrange(self.folds):
            self.file[i].Close()    
        self.closed = True

        inlist = [self.filename + "fold{0}.root".format(i) for i in xrange(self.folds)]
        outfile = self.filename + ".root"
        cmd = shlex.split( "hadd -f {outfile} {inlist}".format( outfile = outfile, 
                                                                inlist=" ".join(inlist) ) )
        p = sp.Popen( cmd )
        p.communicate()

        if not keep_folds:
            for f in inlist:
                os.remove(f)
