import os
import sys
import json
# turn off all warnings
import warnings; warnings.simplefilter('ignore')

import pandas as pd
import xarray as xr


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
plot_path = os.path.join(parameters['plot_path'], '06b_NRM_region_PDFs_spatial_correlation')
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

# read in mask
mask = parameters['mask_file']

# region mask
region_file = parameters['region_file']
region_var = parameters['region_var']
region_meta_data = parameters['region_meta_data']
region_meta_data_id_column = parameters['region_meta_data_id_column']
region_meta_data_label_column = parameters['region_meta_data_label_column']
region_ids = parameters['region_codes_to_use']


#### Plot all time series - annual and seasonal mean

# read in the region mask and the AWRA mask

regions, region_codes = evl.read_in.read_region_mask(region_file, region_var, region_meta_data, 
                                             region_meta_data_id_column, region_meta_data_label_column)
if mask is not None and type(mask) == str:
    mask = xr.open_dataset(mask)
    mask = evl.helpers.standardise_dimension_names(mask)
    mask = mask['mask'] == 1

# Reading and preparing data
for var in vars:
    
    print(var)
    
    var_sim = sim_vars[var]
    var_sim_in_nc = sim_vars_in_nc[var]
    var_ref = ref_vars[var]
    var_ref_in_nc = ref_vars_in_nc[var]
    
    if var in ['rain_day', 'wind', 'solar_exposure_day']:
        statistics = ['mean']
    elif var == 'temp_min_day':
        statistics = ['mean', 'min']
    elif var == 'temp_max_day':
        statistics = ['mean', 'max']
    
    for statistic in statistics:

        df = None

        fn_plot = os.path.join(plot_path, 'NRM_region_PDF_spatial_correlation_%s_annual_and_seasonal_%s_%s_%s.png' % (var, statistic, year_start, year_end))
        print('Preparing plot: %s' % fn_plot)

        if not os.path.exists(fn_plot) or not skip_existing:
            print('Reading in data')

            df = pd.DataFrame()

            for region_id in region_ids:
                
                if region_id == 'AU':
                    region = 'Australia'
                    mask_temp = mask
                else:
                    region = region_codes.loc[region_codes['region_id'] == region_id, 'label'].values[0]
                    # extract the new mask: for each region
                    mask_temp = (mask & (regions == region_id))

                print('- %s' % region)

                temp_df = evl.read_in.prepare_mean_field_for_all_gcms_and_statistics(
                    data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                    gcms=gcms, var=var, name_sim_prefix=name_sim_prefix, name_ref=name_ref,
                    statistics=[statistic], year_start=year_start, year_end=year_end, mask=mask_temp, 
                    var_ref=var_ref, var_sim=var_sim, var_ref_in_nc=var_ref_in_nc, var_sim_in_nc=var_sim_in_nc)
                
                temp_df['region'] = region
                
                # reshape the table and put simulation and reference data in two columns to be able to plot them against each other
                temp_ref = temp_df.loc[temp_df['type'] == name_ref].copy()
                temp_ref = temp_ref.rename({var: name_ref}, axis=1)
                temp_ref = temp_ref.drop('type', axis=1)

                temp_sim = temp_df.loc[temp_df['type'] != name_ref].copy()
                temp_sim = temp_sim.rename({var: name_sim_prefix}, axis=1)

                # merge the two so that each grid cell has one observation, but all of the GCM data
                temp_df = temp_ref.merge(temp_sim, on=['time_scale', 'statistic', 'lat', 'lon', 'region'], how='outer')
                temp_df = temp_df.dropna()

                df = df.append(temp_df)

            # select only annual, DJF and JJA
            df = df.loc[df['time_scale'].isin(['annual', 'DJF', 'JJA'])]
            df['time_scale'] = pd.Categorical(df['time_scale'], categories=['annual', 'DJF', 'JJA'], ordered=True)
            df['region'] = pd.Categorical(df['region'], categories=df['region'].unique(), ordered=True)
            df['type'] = [x.upper() for x in df['type']]
            
            evl.plotting.plot_spatial_correlation(dataframe=df, x=name_sim_prefix, y=name_ref, var=var, 
                                         statistic=statistic, hue='type', col='region', row='time_scale', 
                                         name_sim_prefix=name_sim_prefix, name_ref=name_ref, fn_plot=fn_plot)

