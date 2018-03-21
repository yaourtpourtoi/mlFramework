from Reader import Reader
from Plotter import Plotter 
from Collector import Collector
import pandas
import json
import sys
import os
import argparse
import cPickle

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='channel', help='Decay channel' ,choices = ['mt','et','tt'], default = 'mt')
    parser.add_argument('-m', dest='model',   help='ML model to use' ,choices = ['keras','xgb'],  default = 'keras')
    parser.add_argument('-t', dest='train',   help='Train new model' , action='store_true')
    parser.add_argument('-s', dest='short',   help='Do !!NOT!! predict shapes' , action='store_true')
    args = parser.parse_args()

    print "---------------------------"
    print "Running over {0} samples".format(args.channel)
    print "Using {0}".format(args.model)
    if args.train:
        print "Training new model"
    if args.short:
        print "Not predicting shape templates."
    print "---------------------------"

        
    run(samples = "conf/scale_samples.json",
        channel=args.channel,
        use = args.model,
        train = args.train,
        short = args.short
          )

def run(samples,channel, use, train,short, preprocess_chain = []):

    if use == "xgb":
        from XGBModel import XGBObject as modelObject
        parameters = "conf/parameters_xgb.json"

    if use == "keras":
        from KerasModel import KerasObject as modelObject
        parameters = "conf/parameters_keras.json"


    read = Reader(channel = channel,
                  config_file = samples,
                  folds=2)

    target_names = read.config["target_names"]
    variables = read.config["variables"]
    if not os.path.exists("models"):
        os.mkdir("models")

    modelname = "models/{0}.{1}".format(channel,use)
    scaler = None

    if train:
        print "Training new model"
        print "Loading Training set"
        trainSet = read.getSamplesForTraining()

        print "Fit Scaler to training set...",
        scaler = trainScaler(trainSet, variables )

        print " done. Dumping for later."
        with open("models/StandardScaler.{0}.pkl".format(channel), 'wb') as FSO:
            cPickle.dump(scaler, FSO , 2)
        trainSet = applyScaler(scaler, trainSet, variables)

        model = modelObject( parameter_file = parameters,
                             variables=variables,
                             target_names = target_names )
        model.train( trainSet )
        model.save(modelname)

    else:
        
        if os.path.exists("models/StandardScaler.{0}.pkl".format(channel) ):
            print "Loading Scaler"
            with open( "models/StandardScaler.{0}.pkl".format(channel), "rb" ) as FSO:
                scaler = cPickle.load( FSO )

        print "Loading model and predicting."
        model = modelObject( filename = modelname )

    where = ""
    coll = Collector( channel = channel, 
                      target_names = target_names, 
                      path = use, 
                      recreate = False,
                      rebin = False )

    print "Predicting simulation"
    for sample, sampleName in read.get(what = "nominal"):
        pred =  model.predict( applyScaler(scaler, sample, variables), where )
        coll.addPrediction(pred, sample, sampleName)
        
    print "Adding looser samples to predictions"
    for sample, sampleName in read.get(what = "more"):
        pred =  model.predict( applyScaler(scaler, sample, variables), where )
        coll.addPrediction(pred, sample, sampleName)
        
    print "Predicting data"
    for sample, sampleName in read.get(what = "data"):
        pred =  model.predict( applyScaler(scaler, sample, variables), where )
        coll.addPrediction(pred, sample, sampleName)
    
    if not short:
        print "Predicting TES shapes"
        for sample, sampleName in read.get(what = "tes"):
            pred =  model.predict( applyScaler(scaler, sample, variables), where )
            coll.addPrediction(pred, sample, sampleName)

        print "Predicting JES shapes"
        for sample, sampleName in read.get(what = "jec"):
            pred =  model.predict( applyScaler(scaler, sample, variables), where )
            coll.addPrediction(pred, sample, sampleName)   

    coll.createDC(var = "pred_prob",
                  writeAll = True)

    plot = Plotter( channel= channel,
                    naming = read.processes,
                    path = use )

    plot.makePlots()
    plot.combineImages( )


def trainScaler(folds, variables):
    from sklearn.preprocessing import StandardScaler

    total = pandas.concat( folds, ignore_index = True ).reset_index(drop=True)
    Scaler = StandardScaler()
    Scaler.fit( total[ variables ] )


    return Scaler

def applyScaler(scaler, folds, variables):
    if not scaler: return folds
    newFolds = folds
    for fold in newFolds:
        fold[variables] = scaler.transform( fold[variables] )
    return newFolds


if __name__ == '__main__':
    main()
