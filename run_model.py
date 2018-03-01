from Reader import Reader
from Plotter import Plotter 
from Collector import Collector
import numpy as np
import json
import sys

def main():

    if len(sys.argv) > 1:
        use = sys.argv[1]
    else:
        use = "xgb"
        
    run(samples = "conf/scale_samples.json",
        channel="mt",
        use = use,
          )

def run(samples,channel, use, preprocess_chain = []):

    if use == "xgb":
        from XGBModel import XGBObject as modelObject
        parameters = "conf/parameters_xgb.json"

    if use == "keras":
        from KerasModel import KerasObject as modelObject
        parameters = "conf/parameters_keras.json"

    folds = 2
    outfile = "htt_"+channel+".inputs-sm-13TeV-ML.root"
    read = Reader(channel,samples, folds)
    target_names = read.config["target_names"]

    coll = Collector( channel, outfile, folds, target_names )
    plot = Plotter( outfile, naming = read.processes )

    
    print "Loading simulation"
    tmp = read.getSamplesForTraining()
    showWeights(tmp[0])
    showWeights(tmp[1])
    model = modelObject( parameters, read.config["variables"], target_names = target_names )
    model.train( tmp )
    # model.save("model." + use)

    # model = modelObject( filename = "model."+use )

    where = ""
    print "Predicting simulation"
    for tmp in read.get("nominal"):
        pred =  model.predict( tmp, where )
        coll.writePrediction( pred )

    print "Adding same sign to predictions"
    for tmp in read.get("samesign"):
        pred =  model.predict( tmp, where )
        coll.writePrediction( pred )

    print "Predicting data"
    for tmp in read.get("data"):
        pred =  model.predict( tmp, where )
        coll.writePrediction( pred )

    # print "Predicting TES shapes"
    # for tmp in read.get("tes"):
    #   pred =  model.predict( tmp, where )
    #   coll.writePrediction( pred )

    # print "Predicting JES shapes"
    # for tmp in read.get("jec"):
    #   pred =  model.predict( tmp, where )
    #   coll.writePrediction( pred )    

    coll.combineFolds()
    plot.makePlots()
    plot.combineImages( )
def showWeights(data):

    a = data.query("hist_name == 'ZTT'")
    print "ZTT", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'ZL'")
    print "ZL", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'ZJ'")
    print "ZJ", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'TTT'")
    print "TTT",a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'TTJ'")
    print "TTJ", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'VVT'")
    print "VVT", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'VVJ'")
    print "VVJ", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'W'")
    print "W", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'ggH125'")
    print "ggH125", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'qqH125'")
    print "qqH125", a["train_weight"].iloc[0], len(a)

    a = data.query("hist_name == 'data_ss'")
    print "data_ss", a["train_weight"].iloc[0], len(a)



if __name__ == '__main__':
    main()
