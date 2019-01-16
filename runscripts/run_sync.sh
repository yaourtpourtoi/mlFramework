ERA=$1
CHANNEL=$2

eval `scramv1 runtime -sh`
export PYTHONPATH=$HOME/.local/lib/python2.7/site-packages:$PYTHONPATH

cd ..

python run_model.py -c ${CHANNEL} -s -e ${ERA}
cp ${ERA}/keras/htt_${CHANNEL}.inputs-sm-Run2016-ML.root /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/HephyHiggs/synchronisation/
cd /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/HephyHiggs/synchronisation
python compareDatacards.py htt_${CHANNEL}.inputs-sm-Run2016-ML.root /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/HephyHiggs/synchronisation/SM-ML-2017/KIT/htt_${CHANNEL}.inputs-sm-Run2016-ML.root -f -t V,K ; mv *pdf ~/www/
