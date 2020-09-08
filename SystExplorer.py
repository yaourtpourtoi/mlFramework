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
        directories = self._process_names(self.data_file.keys()) # can use allkeys() to go recursively
        for dir_name in directories:
            print(dir_name) 
            
    def print_category_content(self, category_name):
        template_names = self._process_names(self.data_file[category_name].keys())
        for template_name in template_names:
            print(template_name) 

    def print_category_summary(self, category_name):
        samples = set()
        systematics = set()
        template_names = self._process_names(self.data_file[category_name].keys())
        for template_name in template_names:
            if 'Up' not in template_name and 'Down' not in template_name:
                samples.add(template_name)
            else:
                num_splits = 3 if 'htt125' in template_name else 1  
                num_joints = 3 if 'htt125' in template_name else 1       
                systematic_name = template_name.split('_', maxsplit=num_splits)[-1]
                systematic_name = re.sub('Up$', '', systematic_name)
                systematic_name = re.sub('Down$', '', systematic_name)
                systematics.add(systematic_name)
        print(f'found these samples in {category_name} category:')
        [print(f'      * {sample}') for sample in sorted(samples)]
        print(f'\nand these systematics:')
        [print(f'      * {systematic}') for systematic in sorted(systematics)]
    
            
    def _process_names(self, names):
        cleaned_names = []
        for name in names: # can use allkeys() to go recursively
            cleaned_name = name.decode("utf-8") # convert bytes into str
            cleaned_name = cleaned_name.split(';')[0] # remove from ; up to the end
            cleaned_names.append(cleaned_name)
        return cleaned_names
            
    def set_central_tree(self, tree_name):
        self.tree_central = self.data_file[tree_name]
        
    # TODO: systematic_name might not relate to the dataframe attributes. 
    # Merge (set trees) with (set dataframes)? lacks flexibility in loading though
    def _set_updown_trees(self):
        self.tree_up = self.data_file[self.systematic_name + 'Up']
        self.tree_down = self.data_file[self.systematic_name + 'Down']

    def set_templates(self, channel, decay_mode, category, sample, year, systematic_name, template_folder_name = None):
        self.channel = channel
        self.decay_mode = decay_mode
        self.category = category
        self.sample = sample
        self.year = year
        self.systematic_name = systematic_name
        self.systematic_type = 'datacard'
        
        if template_folder_name is not None:
            if self.decay_mode is not None:
                self.template_folder_name = f'{self.channel}_{self.decay_mode}_{self.category}_{self.year}'
            else:
                self.template_folder_name = f'{self.channel}_{self.category}_{self.year}'
        else:
            self.template_folder_name = template_folder_name
            
        self._set_central_template()
        self._set_updown_templates()
        
    def _set_central_template(self):
        self.template_central = self.data_file[f'{self.template_folder_name}/{self.sample}']

    def _set_updown_templates(self):
        self.template_up = self.data_file[f'{self.template_folder_name}/{self.sample}_{self.systematic_name}Up']
        self.template_down = self.data_file[f'{self.template_folder_name}/{self.sample}_{self.systematic_name}Down']
    
    def set_dataframes(self, variables, systematic_name, systematic_type, weights=None, cut=None):
        # picking just branches of interest speeds loading
        self.applied_cuts = []
        self.systematic_name = systematic_name
        self.systematic_type = systematic_type
        branches = variables + weights if weights else variables
        if cut:
            cut_pruned = re.sub('[\s()\[\]]', '', cut)
            cut_branches = [re.split('\s|>|<|=|!', s)[0] for s in re.split('&|\|', cut_pruned)]
            branches = branches + cut_branches
        branches = list(set(branches))
        
        if self.systematic_type == 'tree':
            self.data_central = self.tree_central.pandas.df(branches)
            self._set_updown_trees()
            self.data_up = self.tree_up.pandas.df(branches)
            self.data_down = self.tree_down.pandas.df(branches)
        elif self.systematic_type == 'weight':
            self.data_central = self.tree_central.pandas.df(branches + [systematic_name + 'Up', systematic_name + 'Down'])
            self.data_up = self.data_central.copy()
            self.data_down = self.data_central.copy()
        else:
            print('systematic type should be either tree or weight to set dataframes: will do nothing. \nFor a \"datacard\" option please use set_templates() method.')
        
        if (self.systematic_type == 'tree' or self.systematic_type == 'weight'):
            if cut:
                self._filter_dataframes(cut)   
            if weights:
                self.weights = self.data_central[weights].prod(axis=1)
                self.weights_up = self.data_up[weights].prod(axis=1)
                self.weights_down = self.data_down[weights].prod(axis=1)
            else:
                self.weights = np.ones(self.data_central.shape[0])
                self.weights_up = np.ones(self.data_up.shape[0])
                self.weights_down = np.ones(self.data_down.shape[0])
        else:
            print('can apply weights only to \"tree\" and \"weight\" options!')

        if self.systematic_type == 'weight':
            self.weights_up *= self.data_central[f'{systematic_name}Up']
            self.weights_down *= self.data_central[f'{systematic_name}Down']

        
    def _filter_dataframes(self, cut):
        self.data_central.query(cut, inplace=True)
        self.data_up.query(cut, inplace=True)
        self.data_down.query(cut, inplace=True)
        self.applied_cuts.append(cut) 

    def plot_var_shifts(self, var_name=None, var_range=None, nbins=None, out_plots_path='./', verbose=False, save_plot=True):
        if verbose:  
            if self.systematic_type != 'datacard': 
                print(f'\n\nLooking into systematic: {self.systematic_name}\nplotting up/down shifts for variable: {var_name}\n\n')
            else:
                print(f'\n\nLooking into systematic: {self.systematic_name}\nplotting up/down shifts for {self.sample} template in category: {self.template_folder_name}\n\n')
                
        plt.figure(figsize=(15,10))
        plt.xlabel(var_name, size=20)
        plt.xticks(size=15)
        plt.yticks(size=15)
        plt.title(self.systematic_name, size=25)
        
        if self.systematic_type == 'tree' or self.systematic_type == 'weight':
            weights_central = self.weights
            weights_up = self.weights_up
            weights_down = self.weights_down
            data_central = self.data_central[var_name]
            data_up = self.data_up[var_name]
            data_down = self.data_down[var_name]              
            plt.hist(data_central, label='central', range=var_range, bins=nbins, weights = weights_central, histtype='step', linewidth=5, alpha=0.7, color='black')
            plt.hist(data_up, label='up', range=var_range, bins=nbins, weights = weights_up, histtype='step', linewidth=5, alpha=.7, color='tan')
            plt.hist(data_down, label='down', range=var_range, bins=nbins, weights = weights_down, histtype='step', linewidth=5, alpha=.7, color='steelblue')        
            plt.legend(fontsize=15)
            plot_name = var_name
        elif self.systematic_type == 'datacard':
            edges = self.template_central.edges
            x = [0] + [edges[i] + (edges[i+1] - edges[i])/2 for i in range(edges.shape[0] - 1)] # add (0,0) point to see variations better
            y = np.insert(self.template_central.values, 0, 0)
            y_up = np.insert(self.template_up.values, 0, 0)
            y_down = np.insert(self.template_down.values, 0, 0)
            plt.plot(x, y, label = 'central', color='black', marker='o', markersize=20, linestyle=':', fillstyle='none', linewidth=2)
            plt.plot(x, y_up, label = 'up', color='tan', marker='o', markersize=20, linestyle=':', fillstyle='none', linewidth=2)
            plt.plot(x, y_down, label = 'down', color='steelblue', marker='o', markersize=20, linestyle=':', fillstyle='none', linewidth=2)
            # plt.hlines(0.98, var_range[0], var_range[1], linestyles='dotted', colors='steelblue', linewidths=5) # can be used to imitate histogram look
            plt.legend(fontsize=15)
            plot_name = self.sample
        
        if save_plot:
            if not os.path.exists(f'{out_plots_path}/{self.systematic_name}/'):
                os.mkdir(f'{out_plots_path}/{self.systematic_name}/')           
            path = f'{out_plots_path}/{self.systematic_name}'            
            if self.systematic_type == 'datacard':
                if not os.path.exists(f'{path}/{self.category}_{self.year}'):
                    os.mkdir(f'{path}/{self.category}_{self.year}')   
                path = f'{path}/{self.category}_{self.year}'
                if not os.path.exists(f'{path}/{self.decay_mode}'):
                    os.mkdir(f'{path}/{self.decay_mode}')   
                path = f'{path}/{self.decay_mode}'                             
            plt.savefig(f'{path}/{plot_name}.pdf')
        if not verbose:
            plt.close()
            
    def plot_var_ratio_shifts(self, var_name=None, var_range=None, nbins=None, normalise=False, out_plots_path='./', verbose=False, save_plot=True):
        if verbose:  
            if self.systematic_type != 'datacard': 
                print(f'\n\nLooking into systematic: {self.systematic_name}\nplotting up(down)/central ratio for variable: {var_name}\n\n')
            else:
                print(f'\n\nLooking into systematic: {self.systematic_name}\nplotting up(down)/central ratio for {self.sample} template in category: {self.template_folder_name}\n\n')
    
        if self.systematic_type == 'tree' or self.systematic_type == 'weight':
            weights_central = self.weights
            weights_up = self.weights_up
            weights_down = self.weights_down
            data_central = self.data_central[var_name]
            data_up = self.data_up[var_name]
            data_down = self.data_down[var_name]              

            counts, edges, _ = plt.hist(data_central, label='central', range=var_range, bins=nbins, weights=weights_central, histtype='step', alpha=0.7, color='black')
            counts_up, _, _ = plt.hist(data_up, label='up', range=var_range, bins=nbins, weights = weights_up, histtype='step', linewidth=5, alpha=1., color='tan')
            counts_down, edges_down, _ = plt.hist(data_down, label='down', range=var_range, bins=nbins, weights = weights_down, histtype='step', linewidth=5, alpha=1., color='steelblue') 
            plot_name = var_name    
            plt.close()
        if self.systematic_type == 'datacard':
            counts = self.template_central.values
            edges = self.template_central.edges
            counts_up = self.template_up.values
            counts_down = self.template_down.values
            plot_name = self.sample
        
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
        x_min = var_range[0] if self.systematic_type != 'datacard' else edges[0]
        x_max = var_range[1] if self.systematic_type != 'datacard' else edges[-1]
        plt.hlines(1., x_min, x_max, linestyles='dashed', colors='grey', linewidths=5)
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
            path = f'{out_plots_path}/{self.systematic_name}'            
            if self.systematic_type == 'datacard':
                if not os.path.exists(f'{path}/{self.category}_{self.year}'):
                    os.mkdir(f'{path}/{self.category}_{self.year}')   
                path = f'{path}/{self.category}_{self.year}'
                if not os.path.exists(f'{path}/{self.decay_mode}'):
                    os.mkdir(f'{path}/{self.decay_mode}')   
                path = f'{path}/{self.decay_mode}'                             
            plt.savefig(f'{path}/ratio_{plot_name}.pdf')
        if not verbose:
            plt.close()

    def print_mean_variance_shifts(self, var_name):
        print(f'Mean, Variance for {var_name}:\n')
        print(f'central: {self.data_central[var_name].mean(), self.data_central[var_name].var()}')
        print(f'up: {self.data_up[var_name].mean(), self.data_up[var_name].var()}')
        print(f'down: {self.data_down[var_name].mean(), self.data_down[var_name].var()}')
