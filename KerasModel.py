import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser
import numpy as np
from pandas import DataFrame,concat
import json
np.random.seed(0)
from sklearn.preprocessing import StandardScaler
import conf.keras_models as keras_models
from keras.callbacks import EarlyStopping, ModelCheckpoint
from keras.models import load_model as lm
from keras.utils.np_utils import to_categorical
from collections import deque
import cPickle

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
        with open(filename, 'rb') as FSO:
            tmp_dict = cPickle.load(FSO)

        print "Loading model from: " + filename 
        self.__dict__.clear()
        self.__dict__.update(tmp_dict)

    def save(self, filename):
        with open(filename, 'wb') as FSO:
            cPickle.dump(self.__dict__, FSO, 2)


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

        # N_classes = len( np.unique( train["target"].values ) )

        # writing targets in keras readable shape
        y_train = to_categorical( train["target"].values )
        y_test  = to_categorical( test["target"].values )

        N_classes = len(y_train[0])

        scaler = StandardScaler()
        x_train = scaler.fit_transform( train[self.variables].values )

        model_impl = getattr(keras_models, self.params["name"])
        model = model_impl(len(self.variables), N_classes)
        model.summary()
        class_weights = self.getClassWeights(train)
        model.fit(
            x_train,
            y_train,
            sample_weight=train["train_weight"].values,
            validation_data=(test[self.variables].values, y_test, test["train_weight"].values),
            batch_size=self.params["batch_size"],
            nb_epoch=self.params["epochs"],
            shuffle=True,
            class_weight = class_weights,
            callbacks=[EarlyStopping(patience=self.params["early_stopping"])])

        return model

    def getClassWeights(self,train):
        classes = np.unique(train["target"])
        class_weights = {}
        for c in classes:
            class_weights[c] = 1000 / train.query( "target == {0} ".format(c) )["event_weight"].sum()
            class_weights[c] = 0.0
        return class_weights

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

        if self.target_names: prediction.rename( columns = self.target_names, inplace=True  )

        summary = DataFrame( test["hist_name"] )
        summary["weight"] =  test["event_weight"]
        summary["predicted_class"] = prediction.idxmax(axis=1)
        summary["predicted_prob" ] = prediction.max(axis=1)
        for c in test:
            if "reweight" in c: summary[c] = test[c]

        return summary

