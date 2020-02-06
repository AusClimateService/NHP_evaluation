import os
import sys
import json
# turn off all warnings
import warnings; warnings.simplefilter('ignore')


### Functions

# import data evaluation plotting functions
# sys.path.append('/g/data1a/er4/exv563/hydro_projections/code/functions')
import evaluation as evl


### Parameters
with open('config.json', 'r') as fp:
    parameters = json.load(fp)

# prepare settings
skip_existing = parameters['skip_existing']
data_path_ref = parameters['data_path_processed_ref']
data_path_sim = parameters['data_path_processed_sim']
plot_path = os.path.join(parameters['plot_path'], '04_climatologies')
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

statistics = parameters['climatologies_statistics']

# read in mask
mask = parameters['mask_file']


#### Create all plots

# Reading and preparing data
for statistic in statistics:        
    print(statistic)

    df = None
    fn_plot = os.path.join(plot_path, 'climatologies_%s_%s_%s.png' % (statistic, year_start, year_end))
    print('Preparing plot: %s' % fn_plot)
    
    if not os.path.exists(fn_plot) or not skip_existing:
        
        # read in data
        print('Reading in data')
        df = evl.read_in.prepare_climatologies_for_all_gcms_and_statistics(
            data_path_ref=data_path_ref, data_path_sim=data_path_sim,
            gcms=gcms, variables=vars, name_sim_prefix=name_sim_prefix, name_ref=name_ref,
            statistics=[statistic], year_start=year_start, year_end=year_end, mask=mask,
            ref_vars=ref_vars, sim_vars=sim_vars, ref_vars_in_nc=ref_vars_in_nc, sim_vars_in_nc=sim_vars_in_nc)
        
        # plot data
        print('Plotting')
        evl.plotting.plot_climatologies(dataframe=df, x='month', y='value', var='var',name_sim_prefix=name_sim_prefix,
                               name_ref=name_ref, fn_plot=fn_plot)
        

