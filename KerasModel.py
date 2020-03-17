import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True  # disable ROOT internal argument parser
import numpy as np
import pandas as pd
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
            print(e)
            self.params = []

        if target_names: self.target_names = target_names



    def load(self, filename):
        with open(filename + ".dict", 'rb') as FSO:
            tmp_dict = json.load(FSO)

        print(("Loading model from: " + filename)) 
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

        for i in range( len(samples) ):
            test = samples[0]
            train = [ samples[1] ]

            for j in range(2, len(samples) ):
                train.append( samples[j] )
            
            train = pd.concat(train , ignore_index=True).reset_index(drop=True)

            self.models.append( self.trainSingle( train, test ) )
            samples.rotate(-1)

        print("Finished training!")


    def trainSingle(self, train, test):


        # writing targets in keras readable shape
        best = str(int(time.time()))
        y_train = to_categorical( train["target"].values )
        y_test  = to_categorical( test["target"].values )

        N_classes = len(y_train[0])

        model_impl = getattr(keras_models, self.params["name"])
        model = model_impl(len(self.variables), N_classes)
        model.summary()
        history = model.fit(
            train[self.variables].values,
            y_train,
            sample_weight=train["train_weight"].values,
            validation_split = 0.1,
            # validation_data=(test[self.variables].values, y_test, test["train_weight"].values),
            batch_size=self.params["batch_size"],
            epochs=self.params["epochs"],
            shuffle=True,
            callbacks=[EarlyStopping(patience=self.params["early_stopping"]), ModelCheckpoint( best + ".model", save_best_only=True, verbose = 1) ])

        import matplotlib as mpl
        mpl.use('Agg')
        import matplotlib.pyplot as plt

        print("plotting training")
        epochs = range(1, len(history.history["loss"]) + 1)
        plt.plot(epochs, history.history["loss"], lw=3, label="Training loss")
        plt.plot(epochs, history.history["val_loss"], lw=3, label="Validation loss")
        plt.xlabel("Epoch")
        plt.ylabel("Loss")
        plt.legend()
        if not os.path.exists("plots"):
            os.mkdir("plots")
        plt.savefig("plots/fold_{0}_loss.png".format(best), bbox_inches="tight")


        print("Reloading best model")
        model = lm(best + ".model")
        os.remove( best + ".model" )

        return model

    def predict(self, samples, where=""):

        predictions = []
        if type(samples) is list:
            samples_deque = deque(samples)

        for i in range( len(samples_deque) ):
            predictions.append( self.testSingle( samples_deque[0], i ) )
            samples_deque.rotate(-1)

        # samples[0].drop(samples[0].index, inplace = True)
        # samples[1].drop(samples[1].index, inplace = True)

        return predictions


    def testSingle(self, test,fold ):

        prediction = self.models[fold].predict(test[self.variables].values)
        prediction_dict = {}
        for i in prediction.shape[1]: 
            prediction_dict[f'predicted_prob_{i}'] = prediction[:, i]
        prediction_dict['predicted_class'] = np.argmax(prediction, axis=1)
        prediction_dict['predicted_prob'] = np.max(prediction, axis=1)
        return pd.DataFrame(dtype = float, data = prediction_dict )
