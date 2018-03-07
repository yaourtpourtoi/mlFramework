import xgboost as xgb
from json import load
from pandas import DataFrame, concat
from numpy import unique
from collections import deque
import cPickle

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
                    params = load(FSO)
                self.params = params
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

        N_classes = len( unique( samples[0]["target"].values ) )
        
        if N_classes > 2:
            self.params = self.params["multiclass"]
            self.params["num_class"] = N_classes    
        else:
            self.params = self.params["binary"]

        for i in xrange( len(samples) ):
            test = samples[0]
            train = [ samples[1] ]

            for j in xrange(2, len(samples) ):
                train.append( samples[j] )
            
            train = concat(train , ignore_index=True).reset_index(drop=True)

            self.models.append( self.trainSingle( train, test ) )
            samples.rotate(-1)

        print "Finished training!"


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
        return bst

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


    def testSingle(self, test, fold):

        devents = xgb.DMatrix( test[ self.variables ].values )
        prediction = DataFrame( self.models[fold].predict( devents ) )

        if self.target_names:
            self.target_names = {int(k):v for k,v in self.target_names.items()}
            prediction.rename( columns = self.target_names, inplace=True  )

        summary = DataFrame( test["hist_name"] )
        summary["weight"] =          test["event_weight"]
        summary["var"] =             test["jpt_1"]
        summary["predicted_class"] = prediction.idxmax(axis=1)
        summary["predicted_prob" ] = prediction.max(axis=1)
        for c in test:
            if "reweight" in c: summary[c] = test[c]

        return summary



if __name__ == '__main__':
    main()