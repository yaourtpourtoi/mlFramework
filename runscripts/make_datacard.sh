ERA=$1
CHANNEL=$2

eval `scramv1 runtime -sh`
export PYTHONPATH=$HOME/.local/lib/python2.7/site-packages:$PYTHONPATH
python run_model.py -c ${CHANNEL} -s -e ${ERA}
