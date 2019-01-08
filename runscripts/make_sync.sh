ERA=$1
CHANNEL=$2

eval `scramv1 runtime -sh`
export PYTHONPATH=$HOME/.local/lib/python2.7/site-packages:$PYTHONPATH
python run_model.py -c ${CHANNEL} -s -e ${ERA}
cd /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/HephyHiggs/synchronisation
python compareDatacards.py /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/mlFramework/${ERA}/keras/htt_${CHANNEL}.inputs-sm-Run${ERA}-ML.root /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/HephyHiggs/synchronisation/181220_kit_ml/htt_${CHANNEL}.inputs-sm-Run${ERA}-ML.root -f -t Vienna,KIT ;mv *pdf ~/www/
