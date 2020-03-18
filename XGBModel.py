import xgboost as xgb
import json
import pandas as pd 
from numpy import unique
from collections import deque


def main():
    obj = XGBObject()

class XGBObject():

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
                self.params = params
        except Warning as e:
            print(e)
            self.params = []

        if target_names: self.target_names = target_names



    def load(self, filename):
        with open(filename + ".dict", 'rb') as FSO:
            tmp_dict = json.load(FSO)

        print("Loading model from: " + filename) 
        self.__dict__.clear()
        self.__dict__.update(tmp_dict)


        self.models = []
        for model in tmp_dict["models"]:
            self.models.append( xgb.Booster({'nthread':8}) ) 
            self.models[-1].load_model(model)


    def save(self, filename):
        placeholders = []
        tmp_models = []
        for i,model in enumerate(self.models):
            modelname = filename + ".fold{0}".format(i)
            model.save_model( modelname )
            tmp_models.append(model)
            placeholders.append( modelname )
        self.models = placeholders

        with open(filename + ".dict", 'wb') as FSO:
            json.dump(self.__dict__, FSO)

        self.models = tmp_models


    def train(self, samples):

        if type(samples) is list:
            samples = deque(samples)

        N_classes = len( unique( samples[0]["target"].values ) )
        
        if N_classes > 2:
            self.params = self.params["multiclass"]
            self.params["num_class"] = N_classes    
        else:
            self.params = self.params["binary"]

        for i in range( len(samples) ):
            test = samples[0]
            train = [ samples[1] ]

            for j in range(2, len(samples) ):
                train.append( samples[j] )
            
            train = pd.concat(train , ignore_index=True).reset_index(drop=True)

            self.models.append( self.trainSingle( train, test ) )
            samples.rotate(-1)

        print("Finished training!")


    def trainSingle(self, train, test ):

        dtrain = xgb.DMatrix(  train[self.variables].values,
                               label=train['target'].values,
                               missing=-10.0,
                               weight=train['train_weight'].values )

        dtest = xgb.DMatrix( test[self.variables].values,
                             label=test['target'].values,
                             missing=-10.0,
                             weight=test['train_weight'].values )

        bst = xgb.train(params = self.params,
                        dtrain=dtrain,
                        num_boost_round=self.params["n_estimators"],
                        verbose_eval=2,
                        evals = [(dtest,"test")],
                        early_stopping_rounds = self.params["early_stopping"]
                        )
        print(bst.attributes())
        return bst

    def predict(self, samples, where=""):

        predictions = []
        if type(samples) is list:
            samples = deque(samples)

        for i in range( len(samples) ):
            test = samples[0]
            if where: test  = test.query( where ).reset_index(drop=True)

            predictions.append( self.testSingle( test, i ) )
            samples.rotate(-1)

        return predictions

    def testSingle(self, test, fold):
        devents = xgb.DMatrix(test[self.variables])
        bst = self.models[fold]
        prediction = bst.predict(devents)  #, num_iteration=bst.best_iteration
        prediction_dict = {}
        for i in range(prediction.shape[1]): 
            prediction_dict[f'predicted_prob_{i}'] = prediction[:, i]
        prediction_dict['predicted_class'] = np.argmax(prediction, axis=1)
        prediction_dict['predicted_prob'] = np.max(prediction, axis=1)
        return pd.DataFrame(dtype = float, data = prediction_dict )

if __name__ == '__main__':
    main()
