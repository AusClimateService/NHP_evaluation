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
path_daily_ref = parameters['path_daily_ref']
path_daily_sim = parameters['path_daily_sim']
plot_path = os.path.join(parameters['plot_path'], '10_point_Fourier_diagrams')
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

fourier_time_aggregations = parameters['fourier_time_aggregations']
coordinates = parameters['point_locations']


#### Plot all time series - annual and seasonal mean

# Reading and preparing data
for var in vars:
    for location in coordinates.keys():
        for timestep in fourier_time_aggregations:
            print(var, location, timestep)
            fn_plot = os.path.join(plot_path, 'point_Fourier_diagrams_frequencies_%s_%s_%s_%s_%s.png' % (timestep, location, var, year_start, year_end))
            if os.path.exists(fn_plot):
                continue
            
            print('Reading in data')

            var_sim = sim_vars[var]
            var_sim_in_nc = sim_vars_in_nc[var]
            var_ref = ref_vars[var]
            var_ref_in_nc = ref_vars_in_nc[var]
            lat = coordinates[location]['lat']
            lon = coordinates[location]['lon']

            df = evl.read_in.prepare_daily_timeseries_for_all_gcms(
                data_path_sim=path_daily_sim, data_path_ref=path_daily_ref, gcms=gcms, var=var, lat=lat, lon=lon, 
                name_sim_prefix=name_sim_prefix, name_ref=name_ref, year_start=year_start, year_end=year_end,
                var_ref=var_ref, var_sim=var_sim, var_ref_in_nc=var_ref_in_nc, var_sim_in_nc=var_sim_in_nc)

            print('Plotting data')

            for plot_type in ['wavelengths', 'frequencies']:
                
                fn_plot = os.path.join(plot_path, 'point_Fourier_diagrams_%s_%s_%s_%s_%s_%s.png' % (plot_type, timestep, location, var, year_start, year_end))
                print('Preparing plot: %s' % fn_plot)

                if not os.path.exists(fn_plot) or not skip_existing:
                    evl.plotting.plot_fourier_transform(dataframe=df, location_name=location, var=var, timestep=timestep,
                                               name_sim_prefix=name_sim_prefix, name_ref=name_ref,
                                               fn_plot=fn_plot, n_top_frequencies=5, x_axis=plot_type)

