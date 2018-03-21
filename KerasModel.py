import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser
import numpy as np
from pandas import DataFrame,concat
import json
np.random.seed(0)
import conf.keras_models as keras_models
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import load_model as lm
from keras.utils.np_utils import to_categorical
from collections import deque
import time
import os

class KerasObject():

    def __init__(self, parameter_file = "", variables=[], target_names = {}, filename = "" ):

        self.variables = variables
        self.models = []

        try:
            if filename: self.load(filename)
            elif not parameter_file or not variables:
                raise Warning("Warning! Object not defined. Load from file or set 'params' and 'variables'")
            else:
                with open(parameter_file,"r") as FSO:
                    params = json.load(FSO)
                self.params = params["model"]
        except Warning as e:
            print e
            self.params = []

        if target_names: self.target_names = target_names



    def load(self, filename):
        with open(filename + ".dict", 'rb') as FSO:
            tmp_dict = json.load(FSO)

        print "Loading model from: " + filename 
        self.__dict__.clear()
        self.__dict__.update(tmp_dict)

        self.models = []
        for model in tmp_dict["models"]:
            self.models.append( lm(model) )

    def save(self, filename):
        placeholders = []
        tmp_models = []
        for i,model in enumerate(self.models):
            modelname = filename + ".fold{0}".format(i)
            model.save( modelname )
            tmp_models.append(model)
            placeholders.append( modelname )
        self.models = placeholders

        with open(filename + ".dict", 'wb') as FSO:
            json.dump(self.__dict__, FSO)

        self.models = tmp_models


    def train(self, samples):

        if type(samples) is list:
            samples = deque(samples)

        for i in xrange( len(samples) ):
            test = samples[0]
            train = [ samples[1] ]

            for j in xrange(2, len(samples) ):
                train.append( samples[j] )
            
            train = concat(train , ignore_index=True).reset_index(drop=True)

            self.models.append( self.trainSingle( train, test ) )
            samples.rotate(-1)

        print "Finished training!"


    def trainSingle(self, train, test):


        # writing targets in keras readable shape
        best = str(int(time.time()))
        y_train = to_categorical( train["target"].values )
        y_test  = to_categorical( test["target"].values )

        N_classes = len(y_train[0])

        model_impl = getattr(keras_models, self.params["name"])
        model = model_impl(len(self.variables), N_classes)
        model.summary()
        model.fit(
            train[self.variables].values,
            y_train,
            sample_weight=train["train_weight"].values,
            # validation_split = 0.25,
            validation_data=(test[self.variables].values, y_test, test["train_weight"].values),
            batch_size=self.params["batch_size"],
            epochs=self.params["epochs"],
            shuffle=False,
            callbacks=[EarlyStopping(patience=self.params["early_stopping"]), ModelCheckpoint( best + ".model", save_best_only=True, verbose = 1) ])

        print "Reloading best model"
        model = lm(best + ".model")
        os.remove( best + ".model" )

        return model

    def predict(self, samples, where=""):

        predictions = []
        if type(samples) is list:
            samples = deque(samples)

        for i in xrange( len(samples) ):
            test = samples[0]
            if where: test  = test.query( where ).reset_index(drop=True)

            predictions.append( self.testSingle( test, i ) )
            samples.rotate(-1)

        return predictions


    def testSingle(self, test,fold ):

        prediction = DataFrame( self.models[fold].predict(test[self.variables].values) )

        return DataFrame(dtype = float, data = {"predicted_class":prediction.idxmax(axis=1).values,
                                 "predicted_prob": prediction.max(axis=1).values } )

