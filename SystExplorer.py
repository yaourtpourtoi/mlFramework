import uproot
from matplotlib import pyplot as plt 
import numpy as np
import os
import re

class SystExplorer(object):
    """docstring for SystExplorer."""

    def __init__(self, path_to_data):
        super(SystExplorer, self).__init__()
        self.data_file = uproot.open(path_to_data)
        self.applied_cuts = []
        
    def print_file_content(self):
        for dir_item_name in self.data_file.keys(): # can use allkeys() to go recursively
            dir_item_name = str(dir_item_name).split('\'', 1)[-1] # remove from the beginning up to \ 
            dir_item_name = dir_item_name.split(';')[0] # remove from ; up to the end
            print(dir_item_name) 
            
    def set_central_tree(self, tree_name):
        self.tree_central = self.data_file[tree_name]
        
    # TODO: systematic_name might not relate to the dataframe attributes. 
    # Merge (set trees) with (set dataframes)? lacks flexibility in loading though
    def _set_updown_trees(self):
        self.tree_up = self.data_file[self.systematic_name + 'Up']
        self.tree_down = self.data_file[self.systematic_name + 'Down']
    
    def set_dataframes(self, variables, systematic_name, systematic_type, weights=None, cut=None):
        # picking just branches of interest speeds loading
        self.applied_cuts = []
        self.systematic_name = systematic_name
        self.systematic_type = systematic_type
        branches = variables + weights if weights else variables
        if cut:
            cut_pruned = re.sub('[\s()\[\]]', '', cut)
            cut_branches = [re.split('\s|>|<|=', s)[0] for s in re.split('&|\|', cut_pruned)]
            branches += cut_branches
        if self.systematic_type == 'tree':
            self.data_central = self.tree_central.pandas.df(branches)
            self._set_updown_trees()
            self.data_up = self.tree_up.pandas.df(branches)
            self.data_down = self.tree_down.pandas.df(branches)
            if cut:
                self._filter_dataframes(cut)   
        elif self.systematic_type == 'weight':
            self.data_central = self.tree_central.pandas.df(branches + [systematic_name + 'Up', systematic_name + 'Down'])
            if cut:
                self._filter_dataframes(cut)   
            self.weight_up = self.data_central[f'{systematic_name}Up']
            self.weight_down = self.data_central[f'{systematic_name}Down']
        else:
            print('systematic type should be either tree or weight: will do nothing')
        
        if weights:
            self.weights = self.data_central[weights].prod(axis=1)
        else:
            self.weights = np.ones(self.data_central.shape[0])
            
        
    def _filter_dataframes(self, cut):
        self.data_central.query(cut, inplace=True)
        if self.systematic_type == 'tree':
            self.data_up.query(cut, inplace=True)
            self.data_down.query(cut, inplace=True)
        self.applied_cuts.append(cut) 

    def plot_var_shifts(self, var_name, var_range, nbins, out_plots_path='./', verbose=False, save_plot=True):
        if var_name not in self.data_central.columns:
            print(f'Can\'t find variable {var_name} in data_central' )
            raise  
        if verbose:   
            print(f'\n\nLooking into systematic: {self.systematic_name}\nplotting up/down shifts for variable: {var_name}\n\n')

        plt.figure(figsize=(15,10))
        plt.xlabel(var_name, size=20)
        plt.xticks(size=15)
        plt.yticks(size=15)
        plt.title(self.systematic_name, size=25)
        
        plt.hist(self.data_central[var_name], label='central', range=var_range, bins=nbins, weights = self.weights, histtype='step', linewidth=5, alpha=0.7, color='black')
        if self.systematic_type == 'weight':
            weights_up = self.weights * self.weight_up
            weights_down = self.weights * self.weight_down
            plt.hist(self.data_central[var_name], label='up', range=var_range, bins=nbins, weights = weights_up, histtype='step', linewidth=5, alpha=0.7, color='tan')
            plt.hist(self.data_central[var_name], label='down', range=var_range, bins=nbins, weights = weights_down, histtype='step', linewidth=5, alpha=0.7, color='steelblue')
        if self.systematic_type == 'tree':
            weights_up = self.weights
            weights_down = self.weights
            plt.hist(self.data_up[var_name], label='up', range=var_range, bins=nbins, weights = weights_up, histtype='step', linewidth=5, alpha=1., color='tan')
            plt.hist(self.data_down[var_name], label='down', range=var_range, bins=nbins, weights = weights_down, histtype='step', linewidth=5, alpha=1., color='steelblue')        
        plt.legend(fontsize=15)
        
        if save_plot:
            if not os.path.exists(f'{out_plots_path}/{self.systematic_name}/'):
                os.mkdir(f'{out_plots_path}/{self.systematic_name}/')            
            plt.savefig(f'{out_plots_path}/{self.systematic_name}/{var_name}.pdf')
        if not verbose:
            plt.close()
            
    def plot_var_ratio_shifts(self, var_name, var_range, nbins, normalise=False, out_plots_path='./', verbose=False, save_plot=True):
        if var_name not in self.data_central.columns:
            print(f'Can\'t find variable {var_name} in data_central' )
            raise     
        if verbose:    
            print(f'\n\nLooking into systematic: {self.systematic_name}\nplotting up(down)/central ratio for variable: {var_name}\n\n')
    
        counts, edges, _ = plt.hist(self.data_central[var_name], label='central', range=var_range, bins=nbins, weights=self.weights, histtype='step', alpha=0.7, color='black')
        if self.systematic_type == 'weight':
            weights_up = self.weights * self.weight_up
            weights_down = self.weights * self.weight_down
            counts_up, edges_up, _ = plt.hist(self.data_central[var_name], label='up', range=var_range, bins=nbins, weights = weights_up, histtype='step', linewidth=5, alpha=0.7, color='tan')
            counts_down, edges_down, _ = plt.hist(self.data_central[var_name], label='down', range=var_range, bins=nbins, weights = weights_down, histtype='step', linewidth=5, alpha=0.7, color='steelblue')
        if self.systematic_type == 'tree':
            weights_up = self.weights
            weights_down = self.weights
            counts_up, edges_up, _ = plt.hist(self.data_up[var_name], label='up', range=var_range, bins=nbins, weights = weights_up, histtype='step', linewidth=5, alpha=1., color='tan')
            counts_down, edges_down, _ = plt.hist(self.data_down[var_name], label='down', range=var_range, bins=nbins, weights = weights_down, histtype='step', linewidth=5, alpha=1., color='steelblue')        
        plt.close()
        
        if normalise:
            counts = counts/np.sum(counts)
            counts_up = counts_up/np.sum(counts_up)
            counts_down = counts_down/np.sum(counts_down)
        ratio_up = counts_up / counts
        ratio_down = counts_down / counts
        central_edges = [edges[i] + (edges[i+1] - edges[i])/2 for i in range(edges.shape[0] - 1)]

        plt.figure(figsize=(15,10))
        plt.plot(central_edges, ratio_up, color='tan', marker='o', linestyle='None', markersize=15, label='up')
        plt.plot(central_edges, ratio_down, color='steelblue', marker='o', linestyle='None', markersize=15, label='down')
        # plt.hlines(0.98, var_range[0], var_range[1], linestyles='dotted', colors='steelblue', linewidths=5)
        # plt.hlines(1.02, var_range[0], var_range[1], linestyles='dotted', colors='steelblue', linewidths=5)
        plt.hlines(1., var_range[0], var_range[1], linestyles='dashed', colors='grey', linewidths=5)
        #     plt.ylim(0.95, 1.05)
        plt.xlabel(var_name, size=20)
        plt.ylabel("{up, down} / central", size=20)
        plt.xticks(size=15)
        plt.yticks(size=15)
        plt.title(self.systematic_name, size=25)
        plt.legend(fontsize=15)
        
        if save_plot:
            if not os.path.exists(f'{out_plots_path}/{self.systematic_name}/'):
                os.mkdir(f'{out_plots_path}/{self.systematic_name}/')            
            plt.savefig(f'{out_plots_path}/{self.systematic_name}/ratio_{var_name}.pdf')
        if not verbose:
            plt.close()

    def print_mean_variance_shifts(self, var_name):
        print(f'Mean, Variance for {var_name}:\n')
        print(f'central: {self.data_central[var_name].mean(), self.data_central[var_name].var()}')
        print(f'up: {self.data_up[var_name].mean(), self.data_up[var_name].var()}')
        print(f'down: {self.data_down[var_name].mean(), self.data_down[var_name].var()}')
