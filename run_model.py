from Reader import Reader
from Plotter import Plotter 
from Collector import Collector
import json
import sys
import argparse

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='channel', help='Decay channel' ,choices = ['mt','et','tt'], default = 'mt')
    parser.add_argument('-m', dest='model',   help='ML model to use' ,choices = ['keras','xgb'],  default = 'keras')
    parser.add_argument('-t', dest='task',   help='Train new model' , action='store_true')
    args = parser.parse_args()
        
    run(samples = "conf/scale_samples.json",
        channel=args.channel,
        use = args.model,
        task = args.task
          )

def run(samples,channel, use, task, preprocess_chain = []):

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
    
    if task:
        print "Training new model"
        print "Loading simulation"
        tmp = read.getSamplesForTraining()
        model = modelObject( parameters, read.config["variables"], target_names = target_names )
        model.train( tmp )
        model.save(".".join([channel, use]))

    else:
        print "Loading model and predicting."
        model = modelObject( filename = ".".join([channel, use]) )

    where = ""
    coll = Collector( channel, outfile, target_names )
    print "Predicting simulation"
    for tmp, sample in read.get(what = "nominal"):
        pred =  model.predict( tmp, where )
        coll.addPrediction(pred, tmp, sample)
        
    print "Adding looser samples to predictions"
    for tmp, sample in read.get(what = "more"):
        pred =  model.predict( tmp, where )
        coll.addPrediction(pred, tmp, sample)
        
    print "Predicting data"
    for tmp, sample in read.get(what = "data"):
        pred =  model.predict( tmp, where )
        coll.addPrediction(pred, tmp, sample)
        
    print "Predicting TES shapes"
    for tmp, sample in read.get(what = "tes"):
      pred =  model.predict( tmp, where )
      coll.addPrediction(pred, tmp, sample)

    print "Predicting JES shapes"
    for tmp, sample in read.get(what = "jec"):
      pred =  model.predict( tmp, where )
      coll.addPrediction(pred, tmp, sample)   

    coll.createDC("pred_prob",True)
    coll.DCfile.Close()
    plot = Plotter( outfile, naming = read.processes )
    plot.makePlots()
    plot.combineImages( )


if __name__ == '__main__':
    main()
