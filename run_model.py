from Reader import Reader
from Tools.Datacard.produce import Datacard, makePlot
import copy
import pandas
import json
import sys
import os
import argparse
import cPickle
import subprocess as sp
import multiprocessing as mp

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

        
    run(samples = "conf/global_config_2016.json",
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


        predictions = {}
        print "Predicting samples"
        if add_nominal:
            print "Predicting Nominal"
            for sample, sampleConfig in read.get(what = "nominal", for_prediction = True):
                sandbox(channel, model, scaler, sample, variables, "nom_" + sampleConfig["histname"] ,sampleConfig, read.modifyDF )   


        for sample, sampleConfig in read.get(what = "full", add_jec = not short, for_prediction = True):
            if "data" in sampleConfig["histname"]:
                sandbox(channel, model, scaler, sample, variables, "NOMINAL_ntuple_Data",sampleConfig, read.modifyDF)
            elif "full" in sampleConfig["histname"]:
                sandbox(channel, model, scaler, sample, variables,  "NOMINAL_ntuple_" + sampleConfig["histname"].split("_")[0], sampleConfig, read.modifyDF )
            else:
                splName = sampleConfig["histname"].split("_")
                sandbox(channel, model, scaler, sample, variables,  "_".join(splName[1:])+"_ntuple_" + sampleConfig["histname"].split("_")[0], sampleConfig, read.modifyDF )

        if not short:
            print "Predicting TES shapes"
            for sample, sampleConfig in read.get(what = "tes", for_prediction = True):
                sandbox(channel, model, scaler, sample, variables, sampleConfig["histname"] ,sampleConfig, read.modifyDF )




def sandbox(channel, model, scaler, sample, variables, outname, config = None, modify = None):
    # needed because of memory management
    # iterate over chunks of sample and do splitting on the fly
    first = True
    for part in sample:
        # This is awful. Try to figure out a better way to add stuff to generator.
        if modify:
            modify(part, config)

        part["THU"] = 1 # Add dummy
        folds = [part.query( "evt % 2 != 0 " ).reset_index(drop=True), part.query( "evt % 2 == 0 " ).reset_index(drop=True) ]
        addPrediction(channel, model.predict( applyScaler(scaler, folds, variables) ), folds, outname, new = first )
        
        folds[0].drop(folds[0].index, inplace=True)
        folds[1].drop(folds[1].index, inplace=True)
        part.drop(part.index, inplace=True)

        first = False
    del sample

def addPrediction(channel,prediction, df, sample, new = True):

    for i in xrange( len(df) ):
        for c in prediction[i].columns.values.tolist():
            df[i][c] =  prediction[i][c]
            
        if i == 0 and new: mode = "w"
        else: mode = "a"
        df[i].to_root("{0}/{1}-{2}.root".format("predictions",channel, sample), key="TauCheck", mode = mode)
        prediction[i].drop(prediction[i].index, inplace = True)

def trainScaler(folds, variables):
    from sklearn.preprocessing import StandardScaler

    total = pandas.concat( folds, ignore_index = True ).reset_index(drop=True)
    Scaler = StandardScaler()
    Scaler.fit( total[ variables ] )


    return Scaler

def applyScaler(scaler, folds, variables):
    if not scaler: return folds
    newFolds = copy.deepcopy(folds)
    for fold in newFolds:
        fold[variables] = scaler.transform( fold[variables] )
    return newFolds


if __name__ == '__main__':
    main()
