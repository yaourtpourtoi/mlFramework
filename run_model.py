from Reader import Reader
import copy
import pandas as pd
import numpy as np
import json
import sys
import os
from glob import glob
import argparse
import pickle
import subprocess as sp
import multiprocessing as mp
import keras

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='channel', help='Decay channel' ,choices = ['mt','et','tt','em'], default = 'mt')
    parser.add_argument('-m', dest='model',   help='ML model to use' ,choices = ['keras','xgb'],  default = 'keras')
    parser.add_argument('-t', dest='train',   help='Train new model' , action='store_true')
    parser.add_argument('-s', dest='short',   help='Do !!NOT!! predict shapes' , action='store_true')
    parser.add_argument('-d', dest='datacard',  help='Only produce Datacard' , action='store_true')
    parser.add_argument('-e', dest='era',  help='Era' , choices=["2016","2017","2018"], required = True)
    parser.add_argument('--add_nominal', dest='add_nom',  help='Add nominal samples to prediction', action='store_true' )    
    args = parser.parse_args()

    print("---------------------------")
    print("Era: ", args.era)
    print("Running over {0} samples".format(args.channel))
    print("Using {0}".format(args.model), keras.__version__)
    if args.train:
        print("Training new model")
    if args.short:
        print("Not predicting shape templates.")
    print("---------------------------")

        
    run(samples = "conf/global_config_{0}_{1}.json".format(args.channel,args.era),
        channel=args.channel,
        era = args.era,
        use = args.model,
        train = args.train,
        short = args.short,
        datacard = args.datacard,
        add_nominal = args.add_nom
          )

def run(samples,channel, era, use, train,short, datacard = False, add_nominal=False ):

    if use == "xgb":
        from XGBModel import XGBObject as modelObject
        parameters = "conf/parameters_xgb.json"

    if use == "keras":
        from KerasModel import KerasObject as modelObject
        parameters = "conf/parameters_keras.json"


    read = Reader(channel = channel,
                  config_file = samples,
                  folds=2,
                  era = era)

    target_names = read.config["target_names"]
    variables = read.config["variables"]

    models_folder = era + "/models"
    if not os.path.exists(models_folder):
        os.makedirs(models_folder)

    modelname = "{0}/{1}.{2}".format(models_folder,channel,use)
    scaler = None

    if train:
        print("Training new model")
        print("Loading Training set")
        trainSet = read.getSamplesForTraining()

        # print("Fit Scaler to training set...", end=' ')
        # scaler = trainScaler(trainSet, variables )
        # 
        # print(" done. Dumping for later.")
        # with open("{0}/StandardScaler.{1}.pkl".format(models_folder,channel), 'wb') as FSO:
        #     pickle.dump(scaler, FSO , 2)
        # scaler = [scaler, scaler] # Hotfix since KIT uses 2 scalers
        # 
        # trainSet = applyScaler(scaler, trainSet, variables)
        
        for i, train_df in enumerate(trainSet):
            if np.sum(train_df.isna()).sum() != 0:
                nan_columns = train_df.columns[(np.sum(train_df.isna())) != 0].values
                print('\n\n**********')
                print(f'trainSet[{i}] has {np.sum(train_df.isna()).sum()} NaNs in columns: {nan_columns}')
                print('Will drop them all\n')
                train_df.dropna(inplace=True)
                print('**********\n\n')

        model = modelObject( parameter_file = parameters,
                             variables=variables,
                             target_names = target_names )
        model.train( trainSet )
        model.save(modelname)

    elif not datacard:
        # TODO: Maybe not needed to check. Just load what is there
        if os.path.exists("{0}/StandardScaler.{1}.pkl".format(models_folder,channel) ):
            print("Loading Scaler")
            scaler = []
            if glob("{0}/{1}_*_keras_preprocessing.pickle".format(models_folder,channel)) :
                with open( "{0}/{1}_fold0_keras_preprocessing.pickle".format(models_folder,channel), "rb" ) as FSO:
                    scaler.append( pickle.load( FSO ) )

                with open( "{0}/{1}_fold1_keras_preprocessing.pickle".format(models_folder,channel), "rb" ) as FSO:
                    scaler.append( pickle.load( FSO ) )
            else:
                with open( "{0}/StandardScaler.{1}.pkl".format(models_folder,channel), "rb" ) as FSO:
                    tmp = pickle.load( FSO )
                    scaler = [tmp,tmp]


        print("Loading model and predicting.")
        model = modelObject( filename = modelname )
        read.variables = model.variables
        variables = model.variables

    if not datacard:
        outpath = read.config["outpath"] + "/predictions_" + era
        if not os.path.exists(outpath):
            os.mkdir(outpath)                
        files = glob(outpath + '/*.root')
        print(f'\nDeleting root files in {outpath}\n')
        for f in files:
            os.remove(f)
            
        predictions = {}
        print("Predicting samples")
        if add_nominal:
            print("Predicting Nominal")
            for sample, sampleConfig in read.get(what = "nominal", for_prediction = True):
                sandbox(channel, model, scaler, sample, variables, "nom_" + sampleConfig["histname"], outpath ,sampleConfig, read.modifyDF )


        for sample, sampleConfig in read.get(what = "full", add_jec = not short, for_prediction = True):
            if "data" in sampleConfig["histname"]:
                sandbox(channel, model, scaler, sample, variables, "NOMINAL_ntuple_Data", outpath, sampleConfig, read.modifyDF)
            elif "full" in sampleConfig["histname"]:
                sandbox(channel, model, scaler, sample, variables,  "NOMINAL_ntuple_" + sampleConfig["histname"].split("_")[0], outpath, sampleConfig, read.modifyDF )
            else:
                splName = sampleConfig["histname"].split("_")
                sandbox(channel, model, scaler, sample, variables,  "_".join(splName[1:])+"_ntuple_" + sampleConfig["histname"].split("_")[0], outpath, sampleConfig, read.modifyDF )

        if not short:
            print("Predicting shapes")
            for sample, sampleConfig in read.get(what = "tes", for_prediction = True):
                sandbox(channel, model, scaler, sample, variables, sampleConfig["histname"], outpath ,sampleConfig, read.modifyDF )



    if "hephy.at" in os.environ["HOME"]:
        from Tools.Datacard.produce import Datacard, makePlot
        from Tools.CutObject.CutObject import Cut
        from Tools.FakeFactor.FakeFactor import FakeFactor

        Datacard.use_config = era + "/datacard_conf"
        D = Datacard(channel=channel,
                     variable="predicted_prob",
                     era=era,
                     real_est="mc",
                     add_systematics = not short,
                     debug=True,
                     use_cutfile = "conf/cuts_{0}.json".format(era))

        FakeFactor.fractions = "{0}/datacard_conf/fractions/htt_ff_fractions_{0}.root".format(era) 

        D.create(era+"/"+use)
        makePlot(channel, "ML", era+"/"+use, era, era+"/plots")

def sandbox(channel, model, scaler, sample, variables, outname, outpath, config = None, modify = None):
    # needed because of memory management
    # iterate over chunks of sample and do splitting on the fly
    first = True
    if sample is None:
        print(f'\nSandbox for sample: {config["histname"]} and tree: {config["tree_name"]} is None. Skipping.\n')
        return
    for i, part in enumerate(sample):
        if config['select'] != "None": # "None" is defined in cuts_{era}.json 
            part.query(config['select'], inplace=True) # sample is iterator - can't filter events in _getDF() so implement it here
            
        # This is awful. Try to figure out a better way to add stuff to generator.
        
        if np.sum(part.isna()).sum() != 0:
            nan_columns = part.columns[(np.sum(part.isna())) != 0].values
            drop_nan_columns = config["drop_nan_columns"]
            print('\n**********')
            print(f'Sample {config["histname"]} has in {i}th chunk {np.sum(part.isna()).sum()} NaNs in columns: {nan_columns}')
            if any(elem in nan_columns for elem in drop_nan_columns):    
                print(f'Will drop them for {drop_nan_columns}\n')
                part.dropna(subset=drop_nan_columns, inplace=True)
            else:
                print(f'\nLeaving them, dropping is set only for {drop_nan_columns}')
            print('**********\n')
            
        if modify:
            modify(part, config)

        part["THU"] = 1 # Add dummy
        # Carefull!! Check if splitting is done the same for training. This is the KIT splitting
        folds = [part.query( "abs(evt % 2) != 0 " ).reset_index(drop=True), part.query( "abs(evt % 2) == 0 " ).reset_index(drop=True) ]
        predictions = pd.concat(model.predict( [fold[variables] for fold in folds] ), axis=0)
        folds = pd.concat(folds, axis=0)
        df = pd.concat([folds, predictions], axis=1).reset_index()
        
        outfile_name = "{0}/{1}-{2}.root".format(outpath, channel, outname)
        df.to_root(outfile_name, key=config['tree_name'], mode = 'a')

        # print('pt_1 = ', folds[0].pt_1[0])
        # print('pt_1 = ', folds[1].pt_1[0])
        # addPrediction(channel, model.predict( [fold[variables] for fold in folds] ), folds, outname, config['tree_name'], outpath, new = first )
        
        folds.drop(folds.index, inplace=True)
        # folds[0].drop(folds[0].index, inplace=True)
        # folds[1].drop(folds[1].index, inplace=True)
        part.drop(part.index, inplace=True)

        first = False
    del sample

def addPrediction(channel, prediction, df, sample, tree_name, outpath, new = True):
    outfile_name = "{0}/{1}-{2}.root".format(outpath, channel, sample)
    print(len(df))
    print(list(df[0].pt_1))
        
    for i in range( len(df) ):
        for c in prediction[i].columns.values.tolist():
            df[i][c] =  prediction[i][c]
            
        # if i == 0 and new: mode = "w"
        # else: mode = "a"
        # df[i].to_root("{0}/{1}-{2}.root".format("predictions",channel, sample), key="TauCheck", mode = mode)
        df[i].to_root(outfile_name, key=tree_name, mode = 'a')
        prediction[i].drop(prediction[i].index, inplace = True)

def trainScaler(folds, variables):
    from sklearn.preprocessing import StandardScaler

    total = pd.concat( folds, ignore_index = True ).reset_index(drop=True)
    Scaler = StandardScaler()
    Scaler.fit( total[ variables ] )


    return Scaler

def applyScaler(scaler, folds, variables):
    if not scaler: return folds
    newFolds = copy.deepcopy(folds)
    for i,fold in enumerate(newFolds):
        fold[variables] = scaler[i].transform( fold[variables] )
    return newFolds


if __name__ == '__main__':
    main()
