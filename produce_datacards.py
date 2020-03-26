from ROOT import TH1D, TFile, gROOT
import uproot

import os
import numpy as np
import pandas as pd
# import modin.pandas as pd
import seaborn as sns
from matplotlib import pyplot as plt


def create_folders(path_to_datacard, category_names, channel, DM_name, year):
    if not os.path.exists(path_to_datacard):
        os.mkdir(path_to_datacard)
    for category_name in category_names:
        dir_name = f'{channel}_{DM_name}_{category_name}_{year}'
        if dir_name not in os.listdir(path_to_datacard):
            os.mkdir(f'{path_to_datacard}/{dir_name}')
            
            
path = '/nfs/dust/cms/user/rasp/storage/cardinia/2018/OutputDNN/March18/predictions_2018'
path_to_datacard = '/nfs/dust/cms/user/filatovo/HTT/CMSSW_10_2_16/src/mlFramework/my_first_datacard'

### used in naming of folders in the datacard, as follows:
### {channel}_{DM_name}_{category_name}_{year}
year = '2018'
channel = 'mt'

sample_to_filename = {
                      'data_obs': 'mt-NOMINAL_ntuple_data.root',
                      'DY' : 'mt-NOMINAL_ntuple_DY.root',
                      'EMB': 'mt-NOMINAL_ntuple_EMB.root',
#                       'ST' : 'mt-NOMINAL_ntuple_ST.root',
                      'TT' : 'mt-NOMINAL_ntuple_TT.root',
                      'VV' : 'mt-NOMINAL_ntuple_VV.root',
                      'W'  : 'mt-NOMINAL_ntuple_W.root',
                      'ggH': 'mt-NOMINAL_ntuple_ggH125.root',
                      'qqH': 'mt-NOMINAL_ntuple_qqH125.root',
                     }
                     
tree_name = 'TauCheck'
branches = [ # if a cut/weight is applied, corresponding variable should be included here
            'predicted_class', 'predicted_prob', 'acotautau_refitbs_00', 'acotautau_refitbs_01',
            'weight', 'gen_sm_htt125', 'gen_ps_htt125', 'gen_mm_htt125', 'ff_mva',
            'gen_match_1', 'gen_match_2',
            'dmMVA_2', 'pt_1', 'eta_1', 'pt_2', 'm_vis', 'puppimt_1', 'os', 'byMediumDeepTau2017v2p1VSjet_2', 'byVVVLooseDeepTau2017v2p1VSjet_2',
            'IP_signif_RefitV_with_BS_1', 'IP_signif_RefitV_with_BS_2',
           ]            
            
target_to_category = {
                        0.: 'sig',
                        1.: 'ztt',
                        2.: 'fakes'
                     }
                     
                     
DM_var = 'dmMVA_2'
DM_to_name = { # the others are ignored
              -99.: 'inclusive', # -99 and 'inclusive' are used internally in the code
                0.: 'mupi',
                1.: 'murho',
#                 2.: 'mua1pi0',
                10.:'mua1',
#                 11.:'mu11'
              }

category_to_DM = {
                    'sig': ['mupi', 'murho', 'mua1'],
                    'ztt': ['inclusive'], # should be a list
                    'fakes': ['inclusive']
              }
              
              
category_to_observables = {
                            'sig': ['predicted_prob', 'CP_angle'],
                            'ztt': ['predicted_prob'],
                            'fakes': ['predicted_prob'],
                          }

DM_to_CP_angle = {
                    'mupi': 'acotautau_refitbs_00',
                    'murho': 'acotautau_refitbs_01',
                    'mua1': 'acotautau_refitbs_01',
#                     'mua1pi0': 'acotautau_refitbs_01',
#                     'mu11': 'acotautau_refitbs_01',
                }
                
observable_to_bins = { # specify edges
                       'predicted_prob': {
                                         'sig': [0.0, 0.5, 0.7, 0.8, 1.0],
                                         'ztt'  : [0.0, 0.5, 0.7, 0.8, 1.0],
                                         'fakes': [0, 0.5, 1.],
                                        },
                       'acotautau_refitbs_00': dict.fromkeys(target_to_category.values(), np.linspace(0, 2*np.pi, 8)), 
                       'acotautau_refitbs_01': dict.fromkeys(target_to_category.values(), np.linspace(0, 2*np.pi, 8)), 
                     }

gen_match_selection = '(gen_match_1 == 4 & gen_match_2 == 5)'
is_not_genjet = '(gen_match_2 != 6)'
process_to_samples = { # 'process_name': ([list of input_tuple_names], 'process_specific_selection')
                        'data_obs': (['data_obs'], None), 
                        'ZTT': (['DY'], gen_match_selection),
                        'EMB': (['EMB'], gen_match_selection), 
                        'ZLL': (['DY'], f'not {gen_match_selection}'),
#                         'ST' : (['ST'], None), 
                        'TT' : (['TT'], None), 
                        'VV' : (['VV'], None), 
                        'W'  : (['W' ], None), 
                        'ggH': (['ggH'], None), 
                        'qqH': (['qqH'], None), 
#                         'EWK': (['W', 'ST'], None),
}

process_to_subprocess = {
                           'ggH': ['sm_htt125', 'ps_htt125', 'mm_htt125'],
                           'qqH': ['sm_htt125', 'ps_htt125', 'mm_htt125'],
                        }
                        
process_to_weight = dict.fromkeys(process_to_samples.keys(), ['weight']) # apply weight to all the processes
subprocess_to_weight = {
                          'sm_htt125': ['gen_sm_htt125'],
                          'ps_htt125': ['gen_ps_htt125'],
                          'mm_htt125': ['gen_mm_htt125'],
                       }

FF_weight = 'ff_mva'
## it should be either ZTT or embedded!
processes_for_FF = {'data_obs', 'EMB', 'ZLL', 'VV', 'TT', 'W'}



common_cuts  = '(pt_1 > 21) & (pt_2 > 20) & (os > 0.5) & (puppimt_1 < 50) & (m_vis > 40) & (abs(eta_1) < 2.1)'
DM_to_cut = {
                'mupi' : 'IP_signif_RefitV_with_BS_1 > 1.5 & IP_signif_RefitV_with_BS_2 > 1.5',
                'murho': 'IP_signif_RefitV_with_BS_1 > 1.5',
                'mua1' : 'IP_signif_RefitV_with_BS_1 > 1.5',
                'inclusive': 'IP_signif_RefitV_with_BS_1 > 1.5',
#                 'mua1pi0' : 'IP_signif_RefitV_with_BS_1 > 1.5',
#                 'mu11' : 'IP_signif_RefitV_with_BS_1 > 1.5',
}

FF_cuts_SR = 'byMediumDeepTau2017v2p1VSjet_2 > 0.5'
FF_cuts_AR = 'byMediumDeepTau2017v2p1VSjet_2 < 0.5 & byVVVLooseDeepTau2017v2p1VSjet_2 > 0.5'

category_to_cuts = {}      
process_to_cuts = {
                    'EMB': f'(weight < 1000) & {is_not_genjet}',
                    'ZTT': is_not_genjet,
                    'ZLL': is_not_genjet,
#                     'ST' : f'not {gen_match_selection} & {is_not_genjet}',
                    'TT' : f'not {gen_match_selection} & {is_not_genjet}',
                    'W'  : f'not {gen_match_selection} & {is_not_genjet}',
                    'VV' : f'not {gen_match_selection} & {is_not_genjet}',
                }
subprocess_to_cuts = {}


print("\n\n---- Loading files")

sample_to_dataframe = {}
for sample, sample_filename in sample_to_filename.items():
    print(f'     > {sample_filename}')
    data_tree = uproot.open(f'{path}/{sample_filename}')[tree_name]
    dataframe = data_tree.pandas.df(branches) 
    sample_to_dataframe[sample] = dataframe
    
print("---- Constructing bigboy")    
bigboy = pd.concat(sample_to_dataframe, axis=0).reset_index()
bigboy.rename(columns={'level_0':'input_tuple', 'entry': 'event_id'}, inplace=True)


# think of a smarter and faster way of doing this
# use cython?

print("---- Setting processes")    
bigboy['process'] = None
for process_name, (sample_names, selection) in process_to_samples.items(): 
    print(f'     > {process_name}')   
    mask = np.isin(bigboy['input_tuple'], sample_names)
    if selection:
        mask &= bigboy.eval(selection)
    bigboy.loc[mask, 'process'] = process_name
    
print("---- Setting indices")        
# can we do w/o it? takes time
bigboy.set_index('input_tuple', append=True, inplace=True)
bigboy.set_index('process', append=True, inplace=True)
bigboy.set_index('event_id', append=True, inplace=True)
bigboy = bigboy.droplevel(level=0)
# bigboy = bigboy.reorder_levels(['input_tuple', 'process', 'event_id'])


def make_datacard(data, observable_names, cuts, weight_names, category_name, process_name, subprocess_name, save=False):    
    bins = [observable_to_bins[observable][category_name] for observable in observable_names]
    if cuts:
        data = data.query(cuts)
    weights = data[weight_names].prod(axis=1) if weight_names is not None else None    
    if len(observable_names) == 1:
        bins = bins[0]
        x = data[observable_names].values.ravel()
        H_array, xedges = np.histogram(x, bins=bins, weights=weights)
#         H_array = np.insert(H_array, 0, 0)
#         H_array = np.append(H_array, 0)
#         H = MyTH1(bins[0], bins[1], H_array) 
    elif len(observable_names) == 2:
        x = data[observable_names[0]]
        y = data[observable_names[1]]
        H_array, xedges, yedges = np.histogram2d(x, y, bins=bins, weights=weights)
        H_array = H_array.ravel()
        xedges = np.linspace(0, H_array.size, H_array.size+1)
#         H_array = np.insert(H.ravel(), 0, 0)
#         H_array = np.append(H_array, 0)
#         H = MyTH1(0, H_array.size, H_array)
    else:
        print(f'Can\'t make a datacard for >2D data for {category_name}:{process}:{subprocess_name} process')
        return
    if save:
        hist_name = f'{process_name}_{subprocess_name}' if subprocess_name else process_name
        file_name = f'{path_to_datacard}/{channel}_{DM_name}_{category_name}_{year}/{hist_name}.root'
#         output_file = uproot.recreate(f'{path_to_datacard}/{channel}_{DM_name}_{category_name}_{year}/{hist_name}.root')
#         output_file[hist_name] = H   
#         hfile = gROOT.FindObject(file_name)
#         if hfile:
#             hfile.Close()
        hfile = TFile(file_name, 'RECREATE')
        hist = TH1D(hist_name, hist_name, len(xedges)-1, np.asarray(xedges, 'd'))
        for i, x in enumerate(H_array, start=1):
            hist.SetBinContent(i, x)
        hist.Write()
        hfile.Write()
        hfile.Close()
    return H_array


# use groupby() parallelization!

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
                    if subprocess_name in subprocess_to_cuts:
                        subprocess_cuts_SR = process_cuts_SR + ' & ' + subprocess_to_cuts[subprocess_name]
                    else:
                        subprocess_cuts_SR = process_cuts_SR
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
    #         output_file = uproot.recreate(f'{path_to_datacard}/{channel}_{DM_name}_{category_name}_{year}/{hist_name}.root')
    #         output_file[hist_name] = H   
    #         hfile = gROOT.FindObject(file_name)
    #         if hfile:
    #             hfile.Close()

        for i, x in enumerate(fakes_datacard, start=1):
            hist.SetBinContent(i, x)
        hist.Write()
        hfile.Write()
        hfile.Close()
