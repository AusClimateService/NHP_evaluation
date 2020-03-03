import os
import sys
import json
# turn off all warnings
import warnings; warnings.simplefilter('ignore')


### Functions

# import data evaluation plotting functions
import evaluation as evl


### Parameters
with open('config.json', 'r') as fp:
    parameters = json.load(fp)

# prepare settings
skip_existing = parameters['skip_existing']
data_path_ref = parameters['data_path_processed_ref']
data_path_sim = parameters['data_path_processed_sim']
plot_path = os.path.join(parameters['plot_path'], '01_maps')
year_start = parameters['evaluation_year_start']
year_end = parameters['evaluation_year_end']
name_sim_prefix = parameters['name_sim_prefix']
name_ref = parameters['name_ref']
gcms = parameters['gcms']
vars = parameters['vars']
ref_vars = parameters['ref_vars']
ref_vars_in_nc = parameters['ref_vars_in_nc']
sim_vars = parameters['sim_vars']
sim_vars_in_nc = parameters['sim_vars_in_nc']

statistics = parameters['bias_maps_statistics']

# read in mask
mask = parameters['mask_file']


#### Plotting

# Reading and preparing data
for gcm in gcms:
    
    name_sim = '%s_%s' % (name_sim_prefix, gcm)
    for var in vars:
        var_sim = sim_vars[var]
        var_sim_in_nc = sim_vars_in_nc[var]
        var_ref = ref_vars[var]
        var_ref_in_nc = ref_vars_in_nc[var]
        
        for statistic in statistics:
                            
            fn_plot = os.path.join(plot_path, 'bias_annual_seasonal_%s_%s_%s_%s_%s_%s.png' % (name_ref, name_sim, var, statistic, year_start, year_end))
            print('Preparing plot: %s' % fn_plot)
            
            if not os.path.exists(fn_plot) or not skip_existing:
                datasets = evl.read_in.read_in_xarray_data_for_one_gcm(
                    data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                    gcm=gcm, var=var, name_sim=name_sim, name_ref=name_ref,
                    statistic=statistic, year_start=year_start, year_end=year_end,
                    mask=mask, var_ref=var_ref, var_sim=var_sim, var_ref_in_nc=var_ref_in_nc, 
                    var_sim_in_nc=var_sim_in_nc, time_scales = ['annual', 'seasonal'], verbose=True)

                # testing
                # print(datasets)
                
                if datasets is not None:
                    fig = evl.plotting.plot_bias(datasets=datasets, name_ref=name_ref, name_sim=name_sim,
                                        fn_plot=fn_plot, var=var, statistic=statistic,
                                        year_start=year_start, year_end=year_end)
                    
                    

