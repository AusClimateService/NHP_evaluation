import os
import sys
import json
# turn off all warnings
import warnings; warnings.simplefilter('ignore')

import pandas as pd
import xarray as xr


### Functions
import evaluation as evl

### Parameters
parameters = evl.config.load_config()


# prepare settings
skip_existing = parameters['skip_existing']
data_path_ref = parameters['data_path_processed_ref']
data_path_sim = parameters['data_path_processed_sim']
plot_path = os.path.join(parameters['plot_path'], '06b_CDFs_spatial_variability')
year_start = parameters['evaluation_year_start']
year_end = parameters['evaluation_year_end']
name_sim_prefix = parameters['name_sim_prefix']
name_ref = parameters['name_ref']
gcms = parameters['gcms']
include_all_gcms_plot = parameters['include_all_gcms_plot']
seasons = parameters['seasons']

vars = parameters['vars']
units = parameters['units']
ref_vars = parameters['ref_vars']
ref_vars_in_nc = parameters['ref_vars_in_nc']
sim_vars = parameters['sim_vars']
sim_vars_in_nc = parameters['sim_vars_in_nc']

statistics = parameters['pdf_spatial_statistics']

# read in mask
mask = parameters['mask_file']

# region mask
region_file = parameters['region_file']
region_var = parameters['region_var']
region_meta_data = parameters['region_meta_data']
region_meta_data_id_column = parameters['region_meta_data_id_column']
region_meta_data_label_column = parameters['region_meta_data_label_column']
region_ids = parameters['region_codes_to_use']

#### Plotting

# Reading and preparing data

# read in the region mask and the AWRA mask

regions, region_codes = evl.read_in.read_region_mask(region_file, region_var, region_meta_data, 
                                             region_meta_data_id_column, region_meta_data_label_column)
if mask is not None and type(mask) == str:
    mask = xr.open_dataset(mask)
    mask = evl.helpers.standardise_dimension_names(mask)
    mask = mask['mask'] == 1
    
for region_id in region_ids:
                
    if region_id == 'AU':
        region_str = 'Australia'
        region_code = 'AU'
        mask_temp = mask
    else:
        region_str = region_codes.loc[region_codes['region_id'] == region_id, 'label'].values[0]
        region_code = region_codes.loc[region_codes['region_id'] == region_id, 'code'].values[0]
        # extract the new mask: for each region
        mask_temp = (mask & (regions == region_id))

    print('- %s' % region_str)
    
    for gcm in gcms + ['ALL-GCMS']:
        
        name_sim = '%s_%s' % (name_sim_prefix, gcm)
        if gcm == 'ALL-GCMS':
            if include_all_gcms_plot:
                gcms_temp = gcms # all gcms
            else:
                continue
        else:
            gcms_temp = [gcm] # individual gcm

        for var in vars:

            var_sim = sim_vars[var]
            var_sim_in_nc = sim_vars_in_nc[var]
            var_ref = ref_vars[var]
            var_ref_in_nc = ref_vars_in_nc[var]

            for statistic in statistics[var]:
                
                df = None
                
                fn_plot = os.path.join(plot_path, region_code, 'CDF_spatial_variability_%s_%s_%s_%s_%s_%s_%s_ALL-SEASONS.png' % (name_ref.upper(), 
                                                                                                                     name_sim.upper(), var_sim,
                                                                                                                     statistic, year_start,
                                                                                                                     year_end, region_code))

                print('Preparing plot: %s' % fn_plot)

                if not os.path.exists(fn_plot) or not skip_existing:
                    print('Reading in data')

                    df = pd.DataFrame()

                    
                    df = evl.read_in.prepare_mean_field_for_all_gcms_and_statistics(
                        data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                        gcms=gcms_temp, var=var, name_sim_prefix=name_sim_prefix, name_ref=name_ref,
                        statistics=[statistic], year_start=year_start, year_end=year_end, mask=mask_temp, 
                        var_ref=var_ref, var_sim=var_sim, var_ref_in_nc=var_ref_in_nc, var_sim_in_nc=var_sim_in_nc)

                    df['region'] = region_str

                    # select seasons
                    df = df.loc[df['time_scale'].isin(seasons)]
                    df['time_scale'] = pd.Categorical(df['time_scale'], categories=seasons, ordered=True)
                    df['region'] = pd.Categorical(df['region'], categories=df['region'].unique(), ordered=True)
                    df['type'] = [x.upper() for x in df['type']]

                    # change variable names and values for better plotting using seaborn
                    df = df.rename({'type':'Dataset'}, axis=1)
                    df['Dataset'] = [x.upper() for x in df['Dataset']]
                    
                    evl.plotting.plot_ecdf(dataframe=df, x=var, var=var, statistic=statistic,
                                hue='Dataset', col='time_scale', row='region',
                                name_sim_prefix=name_sim_prefix.upper(),
                                        name_ref=name_ref.upper(), fn_plot=fn_plot)

