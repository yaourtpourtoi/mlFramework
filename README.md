## Setup for XGBoost and Keras

1) Source softwarestack from LCG (always needed) 

        source /cvmfs/sft.cern.ch/lcg/views/LCG_92/x86_64-slc6-gcc62-opt/setup.sh
 
2) Install xgboost and root_pands (only needed once)

       pip install --user xgboost
       pip install --user root_pandas
 
3) Add local python packages to PYTHONPATH ( best to add to ~/.profile )

       export PYTHONPATH=$HOME/.local/lib/python2.7/site-packages:$PYTHONPATH

