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
    target_values = read.config["target_values"]

    outputs = [ i for k,i in target_names.items() ]
    outputs.remove("none")

    inputs = Inputs(read.config["variables"])
    models_folder = era + "/models"

    modelname = "{0}/{1}.{2}".format(models_folder,channel,use)


    if os.path.exists("{0}/StandardScaler.{1}.pkl".format(models_folder,channel) ):
        print "Loading Scaler"
        scaler = []
        #KIT uses 2 scalers. 
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
    model_tensorflow = model.getTensorflowModels( inputs.placeholders, 0 )
    outputs = Outputs(model_tensorflow, outputs )


    # print "Loading Training set"
    # response =  model.predict(  applyScaler( scaler, read.getSamplesForTraining(), inputs.names ) )

    sess = tf.Session()
    sess.run(tf.global_variables_initializer())

    # Get operations for first-order derivatives
    deriv_ops = getOperations(inputs, outputs)

    print "Loading Training set"
    values_preprocessed = applyScaler( scaler, read.getSamplesForTraining(), inputs.names )

    mean_abs_deriv = {}
    for class_ in outputs.names:

        class_preprocessed = values_preprocessed[0].query("target == {0}".format(target_values[class_]) )

        deriv_class = []

        for _, row in class_preprocessed[inputs.names].iterrows():
            values = np.array(row.values).reshape(1, len(inputs.names))
            deriv_values = sess.run(
                deriv_ops[class_],
                feed_dict={
                    inputs.placeholders: values
                })
            deriv_class.append( np.squeeze(deriv_values) )


        print class_, len(deriv_class), len(class_preprocessed["event_weight"].values)

        mean_abs_deriv[class_] = np.average( np.abs(deriv_class), weights=class_preprocessed["event_weight"].values, axis=0)

    plot(mean_abs_deriv, inputs, outputs)


def plot(derivatives, inputs,outputs, normalize = False):
    matrix = np.vstack([derivatives[class_] for class_ in outputs.names])
    if normalize:
        for i_class, class_ in enumerate(outputs.names):
            matrix[i_class, :] = matrix[i_class, :] / np.sum(
                matrix[i_class, :])

    # Plotting
    plt.figure(0, figsize=(len(inputs.names), len(outputs.names)))
    axis = plt.gca()
    for i in range(matrix.shape[0]):
        for j in range(matrix.shape[1]):
            axis.text(
                j + 0.5,
                i + 0.5,
                '{:.2f}'.format(matrix[i, j]),
                ha='center',
                va='center')
    q = plt.pcolormesh(matrix, cmap='Wistia')
    #cbar = plt.colorbar(q)
    #cbar.set_label("mean(abs(Taylor coefficients))", rotation=270, labelpad=20)
    plt.xticks(
        np.array(range(len(inputs.names))) + 0.5, inputs.names, rotation='vertical')
    plt.yticks(
        np.array(range(len(outputs.names))) + 0.5, outputs.names, rotation='horizontal')
    plt.xlim(0, len(inputs.names ))
    plt.ylim(0, len(outputs.names ))
    output_path = os.path.join("2016/plots",
                               "fold0_keras_taylor_1D")
    plt.savefig(output_path+".png", bbox_inches='tight')
    plt.savefig(output_path+".pdf", bbox_inches='tight')

def getOperations(inputs, outputs):
    # Get operations for first-order derivatives
    deriv_ops = {}
    derivatives = Derivatives(inputs, outputs)
    for class_ in outputs.names:
        deriv_ops[class_] = []
        for variable in inputs.names:
            deriv_ops[class_].append(derivatives.get(class_, [variable]))

    return deriv_ops
def applyScaler(scaler, folds, variables):
    if not scaler: return folds
    newFolds = copy.deepcopy(folds)
    for i,fold in enumerate(newFolds):
        fold[variables] = scaler[i].transform( fold[variables] )
    return newFolds

if __name__ == '__main__':
    main()