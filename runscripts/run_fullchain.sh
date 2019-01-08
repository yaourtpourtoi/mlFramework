ERA=$1
CHANNEL=$2

eval `scramv1 runtime -sh`
export PYTHONPATH=$HOME/.local/lib/python2.7/site-packages:$PYTHONPATH

cd ..

python run_model.py -c ${CHANNEL} -d -e ${ERA}
cd /afs/hephy.at/work/m/mspanring/CMSSW_7_4_7/src/CombineHarvester/HTTSM2017/shapes/Vienna/
cp /afs/hephy.at/work/m/mspanring/CMSSW_9_4_0/src/mlFramework/${ERA}/keras/htt_${CHANNEL}.inputs-sm-Run${ERA}-ML.root .
cd ../..
eval `scramv1 runtime -sh`
sh run_analysis.sh ${ERA} ${CHANNEL}
