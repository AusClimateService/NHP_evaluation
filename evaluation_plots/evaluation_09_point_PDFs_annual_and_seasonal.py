import os
# turn off all warnings
import warnings; warnings.simplefilter('ignore')

import pandas as pd


### Functions

# import data evaluation plotting functions
import evaluation as evl


### Parameters
parameters = evl.config.load_config()

# prepare settings
skip_existing = parameters['skip_existing']
data_path_ref = parameters['data_path_processed_ref']
data_path_sim = parameters['data_path_processed_sim']
plot_path = os.path.join(parameters['plot_path'], '09_point_PDFs')
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

mask = parameters['mask_file']
coordinates = parameters['point_locations']


#### Plot all time series - annual and seasonal mean

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
        statistics = ['mean', 'min'] # calculate annual / seasonal mean and minimum
    elif var == 'temp_max_day':
        statistics = ['mean', 'max']
    
    for statistic in statistics:

        df = None

        fn_plot = os.path.join(plot_path, 'point_PDFs_%s_annual_and_seasonal_%s_%s_%s.png' % (var, statistic, year_start, year_end))
        print('Preparing plot: %s' % fn_plot)

        if not os.path.exists(fn_plot) or not skip_existing:
            print('Reading in data')

            df = pd.DataFrame()
            
            for i, location in enumerate(coordinates):

                lat = coordinates[location]['lat']
                lon = coordinates[location]['lon']

                print('- %s' % location)

                temp_df = evl.read_in.prepare_timeseries_for_all_gcms_and_statistics(
                    data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                    gcms=gcms, var=var, name_sim_prefix=name_sim_prefix, name_ref=name_ref, 
                    statistics=[statistic], year_start=year_start, year_end=year_end, mask=mask,
                    var_ref=var, var_sim=var_sim, var_ref_in_nc=var, var_sim_in_nc=var_sim_in_nc, lat=lat, lon=lon)
                
                temp_df['lat'] = lat
                temp_df['lon'] = lon
                temp_df['location'] = location
                df = df.append(temp_df)

            # select only annual, DJF and JJA
            df = df.loc[df['time_scale'].isin(['annual', 'DJF', 'JJA'])]
            df['time_scale'] = pd.Categorical(df['time_scale'], categories=['annual', 'DJF', 'JJA'], ordered=True)
            df['type'] = [x.upper() for x in df['type']]
            
            evl.plotting.plot_distribution(dataframe=df, x=var, var=var, statistic=statistic,
                        hue='type', col='location', row='time_scale', 
                        name_sim_prefix=name_sim_prefix, name_ref=name_ref, fn_plot=fn_plot)

