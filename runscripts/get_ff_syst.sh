#!/bin/bash

dir="./"

if [ $# -gt 0 ]; then
    dir=$1
fi

chans=( mt et tt)
echo "ff_norm_stat"
for chan in  ${chans[@]} ; do 
	f=${dir}htt_${chan}.inputs-sm-13TeV-ML.root

	if [ ${chan} = "mt" ]; then
		cat=( ggh qqh w ztt tt ss zll misc inclusive  )
		lbl=( 1 2 11 12 13 14 15 16 100)
	fi

	if [ ${chan} = "et" ]; then
		cat=( ggh qqh w ztt tt ss zll misc inclusive  )
		lbl=( 1 2 11 12 13 14 15 16 100)
	fi

	if [ ${chan} = "tt" ]; then
		cat=( ggh qqh ztt misc noniso inclusive )
		lbl=( 1 2 12 16 17 100 )
	fi

	itr=0

	for c in ${cat[@]}; do
		# echo ${c}
	    # root -l $f <<<"${chan}_${c}->cd(); cout << \"({\\\"$chan\\\"}, {${lbl[$itr]}}, \" << 1+round(1000*(jetFakes_norm->GetBinContent(1)/2.828427+jetFakes_norm->GetBinContent(2)/2.828427 ))/1000  << \") // ${c}\"  << endl;" | grep "({"
	    root -l $f <<<"${chan}_${c}->cd(); cout << \"({\\\"$chan\\\"}, {${lbl[$itr]}}, \" << 1+round(1000*(jetFakes_norm->GetBinContent(1)/2+jetFakes_norm->GetBinContent(2)/2))/1000    << \") // ${c}\"  << endl;" | grep "({"
	    let itr=$itr+1
	done
	echo ""
done

echo "ff_norm_syst"
for chan in  ${chans[@]} ; do 
	f=${dir}htt_${chan}.inputs-sm-13TeV-ML.root

	if [ ${chan} = "mt" ]; then
		cat=( ggh qqh w ztt tt ss zll misc inclusive  )
		lbl=( 1 2 11 12 13 14 15 16 100)
	fi

	if [ ${chan} = "et" ]; then
		cat=( ggh qqh w ztt tt ss zll misc inclusive  )
		lbl=( 1 2 11 12 13 14 15 16 100)
	fi

	if [ ${chan} = "tt" ]; then
		cat=( ggh qqh ztt misc noniso inclusive )
		lbl=( 1 2 12 16 17 100 )
	fi

	itr=0

	for c in ${cat[@]}; do
		# echo ${c}
	    # root -l $f <<<"${chan}_${c}->cd(); cout << \"({\\\"$chan\\\"}, {${lbl[$itr]}}, \" << 1+round(1000*(jetFakes_norm->GetBinContent(3)/2.828427+jetFakes_norm->GetBinContent(4)/2.828427 ))/1000 << \") //${c}\" << endl;" | grep "({"
	    root -l $f <<<"${chan}_${c}->cd(); cout << \"({\\\"$chan\\\"}, {${lbl[$itr]}}, \" <<  1+round(1000*(jetFakes_norm->GetBinContent(3)/2+jetFakes_norm->GetBinContent(4)/2))/1000     << \") //${c}\" << endl;" | grep "({"
	    let itr=$itr+1
	done
	echo
done


