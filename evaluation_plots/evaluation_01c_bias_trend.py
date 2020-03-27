import os
import sys
import json
import numpy as np
import xarray as xr
# turn off all warnings
import warnings; warnings.simplefilter('ignore')


### Functions

# import data evaluation plotting functions
sys.path.append('/g/data/er4/exv563/hydro_projections/code/functions')
import evaluation as evl


### Parameters
with open('config.json', 'r') as fp:
    parameters = json.load(fp)

# prepare settings
skip_existing = parameters['skip_existing']
data_path_ref = parameters['data_path_processed_ref']
data_path_sim = parameters['data_path_processed_sim']
plot_path = os.path.join(parameters['plot_path'], '01_maps')
year_start = parameters['trend_year_start']
year_end = parameters['trend_year_end']
name_sim_prefix = parameters['name_sim_prefix']
name_ref = parameters['name_ref']
gcms = parameters['gcms']
vars = parameters['vars']
units = parameters['units']
ref_vars = parameters['ref_vars']
ref_vars_in_nc = parameters['ref_vars_in_nc']
sim_vars = parameters['sim_vars']
sim_vars_in_nc = parameters['sim_vars_in_nc']

statistics = parameters['bias_maps_statistics']
seasons = parameters['seasons']

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

    # prepare the geographic extent
    mask_df = mask_temp.where(mask_temp==1).to_dataframe(name='mask').dropna().reset_index()
    coordinates=dict(llcrnrlat=np.min(mask_df['lat'])-0.2,
                     urcrnrlat=np.max(mask_df['lat'])+0.2,
                     llcrnrlon=np.min(mask_df['lon'])-0.2,
                     urcrnrlon=np.max(mask_df['lon'])+0.2)

    print('- %s' % region_str)

    for gcm in gcms:

        name_sim = '%s_%s' % (name_sim_prefix, gcm)

        for var in vars:
            var_sim = sim_vars[var]
            var_sim_in_nc = sim_vars_in_nc[var]
            var_ref = ref_vars[var]
            var_ref_in_nc = ref_vars_in_nc[var]

            for statistic in statistics[var]:

                fn_plot = os.path.join(plot_path, region_code, 'bias_trend_abs_%s_%s_%s_trend_%s_%s_%s_ALL-SEASONS.png' % (name_ref.upper(), name_sim.upper(), var_sim,
                                                                                                                  year_start, year_end, region_code))

                print('Preparing plot: %s' % fn_plot)

                if not os.path.exists(fn_plot) or not skip_existing:
                    datasets = evl.read_in.read_in_xarray_data_for_one_gcm(
                        data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                        gcm=gcm, var=var, name_sim=name_sim, name_ref=name_ref,
                        statistic=statistic, year_start=year_start, year_end=year_end,
                        mask=mask_temp, var_ref=var_ref, var_sim=var_sim, var_ref_in_nc=var_ref_in_nc, 
                        var_sim_in_nc=var_sim_in_nc, time_scales = ['annual', 'seasonal'], verbose=True,
                        read_in_bias_types=['bias_trend_abs'])                    

                    if datasets is not None:
                        fig = evl.plotting.plot_bias_trend(datasets=datasets, name_ref=name_ref, name_sim=name_sim,
                                                    fn_plot=fn_plot, var=var, unit=units[var],
                                                     statistic=statistic, time_scales=seasons,
                                                    year_start=year_start, year_end=year_end,
                                                    coordinates=coordinates, region=region_str)



