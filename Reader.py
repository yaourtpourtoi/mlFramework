import json
import pandas
import root_pandas as rp
import os
import sys
import yaml


def main():

    SR = Reader("mt","conf/scale_samples.json",2)

    print "For testing"
    # for i in SR.get(what = "nominal"):
    #     print i[0]["train_weight"][0]
    data = SR.getSamplesForTraining()
    a = data[0].query("hist_name == 'ZTT'")
    print "ZTT", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'ZL'")
    print "ZL", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'ZJ'")
    print "ZJ", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'TTT'")
    print "TTT",a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'TTJ'")
    print "TTJ", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'VVT'")
    print "VVT", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'VVJ'")
    print "VVJ", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'W'")
    print "W", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'ggH125'")
    print "ggH125", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'qqH125'")
    print "qqH125", a["train_weight"].iloc[0]

    a = data[0].query("hist_name == 'data_ss'")
    print "data_ss", a["train_weight"].iloc[0]


class Reader():

    def __init__(self, channel,config_file, folds):
        self.itersamples = []
        self.idx = 0

        self.channel = channel
        self.trainReweighting = ""
        self.folds = folds
        self.processes = []
        self.config = self.__flattenConfig(config_file)
        with open("conf/hist_names.json","r") as FSO:
            self.hist_names = json.load(FSO)

        with open("conf/reweighting.json","r") as FSO:
            self.reweight = json.load(FSO)

    def __iter__(self):
        return self

    def next(self):
        try:
            sample = self.itersamples[ self.idx ]
            self.idx += 1
            return self.loadForMe( sample )
        except IndexError as e:
            raise StopIteration


    def __flattenConfig(self,config_file):
        '''
        Read dataset configuration file and flatten the return object to the current use case.
        '''
        try:
            with open(config_file,"r") as FSO:
                config = json.load(FSO)
        except ValueError as e:
            print e
            print "Check {0}. Probably a ',' ".format(config_file)
            sys.exit(0)

        config["channel"] = self.channel
        self.trainReweighting = config["train_weight"] 

        config["global_selection"] = config["global_selection"][self.channel]
        config["path"] = "{path}/ntuples_{version}/{channel}/ntuples_{useSV}_merged".format( **config )
        config["target_names"] = {int(k):v for k,v in config["target_names"].items()}

        for sample in config["samples"]:
            
            self.processes.append(sample)

            if type(config["samples"][sample]["name"] ) is dict:
                sample_name = config["samples"][sample]["name"][ self.channel ]
            else:
                sample_name = config["samples"][sample]["name"]

            config["samples"][sample]["name"]    = "{path}/{name}_{channel}_{version}.root".format(name = sample_name, **config)
            config["samples"][sample]["select"] += " && {global_selection}".format(**config)
            
            if sample != "data" and sample != "data_ss":
                config["samples"][sample]["shapes"]  = self.__getShapePaths( config["samples"][sample]["name"] )
                if type(config["samples"][sample]["event_weight"]) is list:
                    config["addvar"] = list( set( config["addvar"] + config["samples"][sample]["event_weight"] ) )

        return config


    def getSamplesForTraining(self):
        self.setNominalSamples()
        samples = []
        for sample in self:
            samples.append(sample)
        print "Combining for training"
        return self.combineFolds(samples)

    def setNominalSamples(self):
        self.itersamples = []
        self.idx = 0
        for sample in self.config["samples"]:
            if sample == "data" or "samesign" in sample: continue

            tmp = self.__getCommonSettings(sample)

            tmp["path"] = self.config["samples"][sample]["name"] 
            tmp["hist_name"   ] = sample
            tmp["reweight"    ] = True
            tmp["rename"      ] = {}

            self.itersamples.append( tmp )

        return self

    def setSameSignSamples(self):
        self.itersamples = []
        self.idx = 0
        for sample in self.config["samples"]:
            if not "samesign" in sample: continue

            tmp = self.__getCommonSettings(sample)

            tmp["path"] = self.config["samples"][sample]["name"] 
            tmp["hist_name"   ] = sample
            tmp["reweight"    ] = True
            tmp["rename"      ] = {}

            self.itersamples.append( tmp )

        return self

    def setDataSample(self):
        self.itersamples = []
        self.idx = 0

        tmp = self.__getCommonSettings("data")

        tmp["path"] = self.config["samples"]["data"]["name"] 
        tmp["hist_name"   ] = "data_obs"
        tmp["reweight"    ] = False
        tmp["rename"      ] = {}

        self.itersamples.append( tmp )

        return self

    def setTESSamples(self):
        self.itersamples = []
        self.idx = 0
        for sample in self.config["samples"]:
            if sample == "data" or sample == "data_ss" or "samesign" in sample: continue

            for shape in self.config["samples"][sample]["shapes"]:
                if "JEC" in shape: continue

                tmp = self.__getCommonSettings(sample)

                tmp["path"] = self.config["samples"][sample]["shapes"][shape] 
                tmp["hist_name"   ] = sample + self.hist_names[shape]
                tmp["reweight"    ] = False
                tmp["rename"      ] = {}

                self.itersamples.append( tmp )

        return self

    def setJECSamples(self):
        self.itersamples = []
        self.idx = 0
        for sample in self.config["samples"]:
            if sample == "data" or sample == "data_ss" or "samesign" in sample: continue

            for shape in self.config["samples"][sample]["shapes"]:
                if not "JEC" in shape: continue

                tmp = self.__getCommonSettings(sample)

                tmp["path"] = self.config["samples"][sample]["shapes"][shape] 
                tmp["hist_name"   ] = sample + self.hist_names[shape]
                tmp["reweight"    ] = False
                tmp["rename"      ] = self.__getRenaming( shape.replace("JEC","") )

                self.itersamples.append( tmp )

        return self


    def loadForMe(self, sample_info):

        DF = self.__getDF(sample_path = sample_info["path"], 
                          select = sample_info["select"])

        DF.eval( "event_weight = " + sample_info["event_weight"], inplace = True  )

        DF["hist_name"] = sample_info["hist_name"]
        DF["target"] = sample_info["target"]

        if not self.trainReweighting:
            DF["train_weight"] = 1.0
        else:
            DF["train_weight"] = self.__getTrainWeight(DF, scale = sample_info["train_weight_scale"] )

        if sample_info["reweight"]:
            self.__addReweightWeights(DF)

        if sample_info["rename"]:
            DF.rename(columns = sample_info["rename"], inplace = True)


        return self.__getFolds( DF )



    def combineFolds(self, samples):

        folds = [ [fold] for fold in samples[0] ]
        for sample in samples[1:]:
            for i in xrange(len(folds)):
                folds[i].append( sample[i] )

        for i,fold in enumerate(folds):  
            folds[i] = pandas.concat( fold, ignore_index=True).sample(frac=1., random_state = 41).reset_index(drop=True)
            # if self.trainReweighting == "normalize_xsec":
            #     folds[i]["train_weight"] /= folds[i]["event_weight"].sum()
        return folds

    def get(self, what):
        if what == "nominal"  : return self.setNominalSamples()
        if what == "samesign" : return self.setSameSignSamples()
        if what == "data"     : return self.setDataSample()
        if what == "tes"      : return self.setTESSamples()
        if what == "jec"      : return self.setJECSamples()


    def __getShapePaths(self, sample):

        shapes = {"T0Up":"","T0Down":"","T1Up":"","T1Down":"","T10Up":"","T10Down":"","JECUp":sample,"JECDown":sample}

        for shape in shapes:
            shape_path = sample.replace(".root","_{0}.root".format(shape) )
            if os.path.exists( shape_path ):
                shapes[shape] = shape_path
            else:
                shapes[shape] = sample

        return shapes

    def __getCommonSettings(self, sample):

        settings = {}
        settings["event_weight"] = self.__getEventWeight(sample)
        settings["target"      ] = self.config["samples"][sample]["target"]
        settings["select"      ] = self.config["samples"][sample]["select"]
        settings["train_weight_scale"] = self.config["samples"][sample]["train_weight_scale"]
        
        return settings


    def __getEventWeight(self, sample):
        if type( self.config["samples"][sample]["event_weight"] ) is list:
            return "*".join( self.config["samples"][sample]["event_weight"] + [ str(self.config["lumi"]) ] )

        if type( self.config["samples"][sample]["event_weight"] ) is float:
            return str( self.config["samples"][sample]["event_weight"] )

        else:
            return 1.0

    def __getTrainWeight(self, DF, scale):
        if self.trainReweighting == "normalize_evt":
            evts = len(DF)
            if evts > 0: return 10000 / float(evts)

        elif self.trainReweighting == "normalize_xsec":
            return DF["event_weight"].abs() * scale

        elif self.trainReweighting == "use_scale":
            return scale

        else:
            return 1.0

    def __getRenaming(self, corr):

        tmp =[]
        for nom in ["mjj","jdeta","njets","jpt"]:
            if not nom == "jpt": tmp+= [(nom, nom+corr),(nom+corr, nom) ]
            else : tmp += [ (nom + "_1", nom+corr+ "_1"),(nom+corr+ "_1", nom+ "_1"),
                            (nom + "_2", nom+corr+ "_2"),(nom+corr+ "_2", nom+ "_2") ]

        return dict( tmp )

    def __addReweightWeights(self, DF):

        for rw in self.reweight:
            DF[rw] = DF.eval( self.reweight[rw] )

    def __getFolds(self, df):

        if self.folds != 2: raise NotImplementedError("Only implemented two folds so far!!!")
        folds = []

        folds.append( df.query( "fileEntry % 2 != 0 " ).reset_index(drop=True) )
        folds.append( df.query( "fileEntry % 2 == 0 " ).reset_index(drop=True) )

        return folds

    def __getDF( self, sample_path, select ):

        branches = set( self.config["variables"] + self.config["addvar"] )
        print "loading ", sample_path.split("/")[-1]
        tmp = rp.read_root( paths = sample_path,
                             where = select,
                             columns = branches)   

        tmp.replace(-10,-10, inplace = True)
        return tmp

if __name__ == '__main__':
    main()