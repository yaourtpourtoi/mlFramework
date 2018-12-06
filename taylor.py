import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser

import argparse
from array import array
import yaml
import pickle
import numpy as np
import os
import sys
from glob import glob
import cPickle
import copy

import matplotlib as mpl
mpl.use('Agg')
mpl.rcParams['font.size'] = 16
import matplotlib.pyplot as plt
from matplotlib import cm

from keras.models import load_model
import tensorflow as tf

from tensorflow_derivative.tensorflow_derivative.inputs import Inputs
from tensorflow_derivative.tensorflow_derivative.outputs import Outputs
from tensorflow_derivative.tensorflow_derivative.derivatives import Derivatives
from Reader import Reader


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-c', dest='channel', help='Decay channel' ,choices = ['mt','et','tt','em'], default = 'mt')
    parser.add_argument('-e', dest='era',  help='Era' , choices=["2016","2017"], required = True)
    args = parser.parse_args()



        
    run(samples = "conf/global_config_{0}_{1}.json".format(args.channel,args.era),
        channel=args.channel,
        era = args.era,

          )

def run(samples,channel, era ):

    use = "keras"
    from KerasModel import KerasObject as modelObject
    parameters = "conf/parameters_keras.json"


    read = Reader(channel = channel,
                  config_file = samples,
                  folds=2,
                  era = era)

    target_names = read.config["target_names"]
    variables = read.config["variables"]
    models_folder = era + "/models"

    modelname = "{0}/{1}.{2}".format(models_folder,channel,use)



    if os.path.exists("{0}/StandardScaler.{1}.pkl".format(models_folder,channel) ):
        print "Loading Scaler"
        scaler = []
        if glob("{0}/{1}_*_keras_preprocessing.pickle".format(models_folder,channel)) :
            with open( "{0}/{1}_fold0_keras_preprocessing.pickle".format(models_folder,channel), "rb" ) as FSO:
                scaler.append( cPickle.load( FSO ) )

            with open( "{0}/{1}_fold1_keras_preprocessing.pickle".format(models_folder,channel), "rb" ) as FSO:
                scaler.append( cPickle.load( FSO ) )
        else:
            with open( "{0}/StandardScaler.{1}.pkl".format(models_folder,channel), "rb" ) as FSO:
                tmp = cPickle.load( FSO )
                scaler = [tmp,tmp]

    model = modelObject( filename = modelname )

    print "Loading Training set"
    response =  model.predict(  applyScaler( scaler, read.getSamplesForTraining(), variables ) )
    print response


def applyScaler(scaler, folds, variables):
    if not scaler: return folds
    newFolds = copy.deepcopy(folds)
    for i,fold in enumerate(newFolds):
        fold[variables] = scaler[i].transform( fold[variables] )
    return newFolds

if __name__ == '__main__':
    main()