import os

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
