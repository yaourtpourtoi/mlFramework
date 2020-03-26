from ROOT import TH1D, TFile, gROOT
import uproot

import os
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt

from datacards_cfg import *


if not os.path.exists('bigboy_feather'):
    print("\n\n---- Loading dataframes")
    sample_to_dataframe = {}
    for sample, sample_filename in sample_to_filename.items():
        print(f'     > {sample_filename}')
        data_tree = uproot.open(f'{path}/{sample_filename}')[tree_name]
        dataframe = data_tree.pandas.df(branches) 
        dataframe['input_tuple'] = sample
        sample_to_dataframe[sample] = dataframe
        
    print("\n---- Constructing bigboy")    
    bigboy = pd.concat(sample_to_dataframe, axis=0, ignore_index=True)
    bigboy.to_feather('bigboy_feather')
    
bigboy = pd.read_feather('bigboy_feather')
print("\n---- Setting processes")    
bigboy['process'] = None
for process_name, (sample_names, selection) in process_to_samples.items(): 
    print(f'     > {process_name}')   
    mask = np.isin(bigboy['input_tuple'], sample_names)
    if selection:
        mask &= bigboy.eval(selection)
    bigboy.loc[mask, 'process'] = process_name

################################################################################
    
def make_datacard(data, observable_names, cuts, weight_names, category_name, process_name, subprocess_name, save=False):    
    bins = [observable_to_bins[observable][category_name] for observable in observable_names]
    if cuts:
        data = data.query(cuts)
    weights = data[weight_names].prod(axis=1) if weight_names is not None else None    
    if len(observable_names) == 1:
        bins = bins[0]
        x = data[observable_names].values.ravel()
        H_array, xedges = np.histogram(x, bins=bins, weights=weights)
    elif len(observable_names) == 2:
        x = data[observable_names[0]]
        y = data[observable_names[1]]
        H_array, xedges, yedges = np.histogram2d(x, y, bins=bins, weights=weights)
        H_array = H_array.ravel()
        xedges = np.linspace(0, H_array.size, H_array.size+1)
    else:
        print(f'Can\'t make a datacard for >2D data for {category_name}:{process}:{subprocess_name} process')
        return
    if save:
        hist_name = f'{process_name}_{subprocess_name}' if subprocess_name else process_name
        file_name = f'{path_to_datacard}/{channel}_{DM_name}_{category_name}_{year}/{hist_name}.root'
        hfile = TFile(file_name, 'RECREATE')
        hist = TH1D(hist_name, hist_name, len(xedges)-1, np.asarray(xedges, 'd'))
        for i, x in enumerate(H_array, start=1):
            hist.SetBinContent(i, x)
        hist.Write()
        hfile.Write()
        hfile.Close()
    return H_array
    
################################################################################

FF_datacards = {}

# categories
categories = bigboy.groupby('predicted_class')
for category_target, category in categories:
    category_name = target_to_category[category_target]   
    category_cuts = common_cuts
    if category_name in category_to_cuts:
        category_cuts += ' & ' + category_to_cuts[category_name]   

    # DMs   
    if category_to_DM[category_name] == ['inclusive']:
        DMs = [(-99, category)]
    else:
        DMs = category.groupby(DM_var)
    for DM_number, DM in DMs:
        if DM_number not in DM_to_name: continue
        DM_name = DM_to_name[DM_number]
        if DM_name not in category_to_DM[category_name]: continue
       
        print('\n\n'+ '*'*30)
        print(' '* 9 + f'{category_name}: {DM_name}')
        print('*'*30)
        create_folders(path_to_datacard, target_to_category.values(), channel, DM_name, year)
        observables = category_to_observables[category_name]  
        if 'CP_angle' in observables:
            observables = np.char.replace(observables, 'CP_angle', DM_to_CP_angle[DM_name]).tolist()
        category_DM_cuts = category_cuts
        if DM_name in DM_to_cut:
            category_DM_cuts += ' & ' + DM_to_cut[DM_name]
            
        # processes
        processes = DM.groupby('process')
        for process_name, process_data in processes:
            print(f'\n---> Producing datacard for {category_name}: {process_name}')
            process_cuts = category_DM_cuts
            if process_name in process_to_cuts:
                process_cuts += ' & ' + process_to_cuts[process_name]
                
            process_cuts_SR = process_cuts + ' & ' + FF_cuts_SR
            process_cuts_AR = process_cuts + ' & ' + FF_cuts_AR
            process_weights = process_to_weight[process_name]
            process_weights_FF = process_weights + [FF_weight]
            if process_name not in process_to_subprocess:
                make_datacard(process_data, observables, process_cuts_SR, process_weights, category_name, process_name, subprocess_name=None, save=True)
                if process_name in processes_for_FF:
                    FF_datacard = make_datacard(process_data, observables, process_cuts_AR, process_weights_FF, category_name, process_name, subprocess_name=None, save=False)
                    FF_datacards[process_name] = FF_datacard
            else:
                for subprocess_name in process_to_subprocess[process_name]:
                    print(f'      > subprocess: {subprocess_name}')
                    subprocess_cuts_SR = process_cuts_SR
                    if subprocess_name in subprocess_to_cuts:
                        subprocess_cuts_SR += ' & ' + subprocess_to_cuts[subprocess_name]                        
                    subprocess_weights = process_weights + subprocess_to_weight[subprocess_name]
                    make_datacard(process_data, observables, subprocess_cuts_SR, subprocess_weights, category_name, process_name, subprocess_name, save=True)

        # fakes
        print(f'\n---> Producing datacard for {category_name}: fakes')
        fakes_datacard = FF_datacards.pop('data_obs')
        for datacard in FF_datacards.values():
            fakes_datacard -= datacard

        hist_name = 'fakes'
        file_name = f'{path_to_datacard}/{channel}_{DM_name}_{category_name}_{year}/fakes.root'
        hfile = TFile(file_name, 'RECREATE')

        if(any(fakes_datacard) < 0):
            print(f'Careful! Got negative values in fakes template for {category_name}:{process_name}')
        if len(observables) == 1:
            bins = [observable_to_bins[observable][category_name] for observable in observables]   
            bins = bins[0]
            hist = TH1D(hist_name, hist_name, len(bins)-1, np.asarray(bins, 'd'))
        elif len(observables) == 2:
            hist = TH1D(hist_name, hist_name, fakes_datacard.size, 0, fakes_datacard.size)   
        for i, x in enumerate(fakes_datacard, start=1):
            hist.SetBinContent(i, x)
        hist.Write()
        hfile.Write()
        hfile.Close()
