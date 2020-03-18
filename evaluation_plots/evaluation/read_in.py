# Read in and data pre-processing functions for the evaluation library.

# Author: Elisabeth Vogel, elisabeth.vogel@bom.gov.au
# Date: 19/09/2019

# Import libraries
import os
import glob

import pandas as pd
import xarray as xr
import numpy as np

from evaluation.helpers import *


# Read in a regional mask and the related metadata file.
def read_region_mask(region_file, region_var, region_meta_data_file, region_meta_data_id_column, region_meta_data_label_column, code_column='code'):
    """
    This function reads in a region mask (nc file) with a given variable name for the region IDs (region_var).
    It also reads in a metadata file with an ID column and metadata column and returns both
    the xarray data array and the metadata DataFrame.
    """

    # read in region mask
    regions = xr.open_dataset(region_file)
    regions = standardise_dimension_names(regions)

    # round the lat lon values (otherwise can't combine with other data)
    regions.lat.values = np.round(regions.lat.values, 3)
    regions.lon.values = np.round(regions.lon.values, 3)

    regions = regions[region_var]

    # read in region codes
    region_codes = pd.read_csv(region_meta_data_file, keep_default_na=False)
    region_codes = region_codes[[region_meta_data_id_column, region_meta_data_label_column, code_column]]
    region_codes = region_codes.rename({region_meta_data_id_column:'region_id'}, axis=1)
    region_codes = region_codes.rename({region_meta_data_label_column:'label'}, axis=1)

    return regions, region_codes


# Function to read in daily / monthly / annual data for creating an animation.
def read_in_data_for_animations(files, start_date, end_date, var_in_nc):

    """
    This function reads in files for creating an animation.
    """

    # Open data
    ds = xr.open_mfdataset(files)

    ds = ds.sel(time=slice(str(start_date), str(end_date)))

    # Load
    ds = ds.load()

    # Standardise dimension names
    ds = standardise_dimension_names(ds)
    ds = ds[var_in_nc]

    return ds


# Function: Read in bias maps as xarray dataset for one GCM and variable.
def read_in_xarray_data_for_one_gcm(data_path_ref, data_path_sim, gcm, var, name_sim, name_ref,
                                    statistic, year_start, year_end, mask=None,
                                    var_ref=None, var_sim=None, var_ref_in_nc=None, var_sim_in_nc=None,
                                    time_scales = ['annual', 'seasonal', 'monthly'],
                                    read_in_bias_types=['bias_abs', 'bias_rel', 'bias_lag1corr'],
                                    verbose=True):

    """
    This functions reads in the 30-year mean (annual, seasonal and/or monthly) and the bias and returns them
    as xarray datasets to be plotted in bias maps.
    It reads in the data for one GCM and variable - for both the simulation and reference dataset.
    """
    
    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim

    # prepare output dictionary of the following shape:
    # datasets[TIMESCALE][NAME_REF/NAME_SIM] # TIMESCALE: annual,seasonal,monthly; # NAME_REF/NAME_SIM: e.g. awap, isimip_NorESM1-M
    # each item is an xarray dataset

    datasets = dict()
    for time_scale in time_scales:
        
        datasets[time_scale] = dict() # create a new dictionary, for "bias_abs", "bias_rel", "bias_lag1corr"
        time_scale_str = dict(annual='year', seasonal='seas', monthly='mon')[time_scale]
    
        # read in reference data
        if name_ref is not None:

            # read in mean values
            fn = os.path.join(data_path_ref, '%s_%s_%s%s_%s_%s_mean.nc' % (name_ref, var_ref, time_scale_str, statistic, year_start, year_end))
            if verbose: print(fn)
            datasets[time_scale][name_ref] = xr.open_dataset(fn).load()
            
            # if time_scale is seasonal or monthly, aggregate data, so that the dimension name changes to
            # season or month instead of dates (values will be the same)
            if time_scale == 'seasonal':
                datasets[time_scale][name_ref] = datasets[time_scale][name_ref].groupby('time.season').mean(dim='time')
            elif time_scale == 'monthly':
                datasets[time_scale][name_ref] = datasets[time_scale][name_ref].groupby('time.month').mean(dim='time')

            # read in lag1 correlation (if applicable)
            fn = os.path.join(data_path_ref, '%s_%s_%s%s_%s_%s_lag1corr.nc' % (name_ref, var_ref, time_scale_str, statistic, year_start, year_end))
            if os.path.exists(fn):
                if verbose: print(fn)
                datasets[time_scale][name_ref + '_lag1corr'] = xr.open_dataset(fn).load()


        # read in simulation data
        if name_sim is not None:

            # read in mean values
            fn = os.path.join(data_path_sim, gcm, '%s_%s_%s%s_%s_%s_mean.nc' % (name_sim, var_sim, time_scale_str, statistic, year_start, year_end))
            if verbose: print(fn)
            datasets[time_scale][name_sim] = xr.open_dataset(fn).load()
            
            # if time_scale is seasonal or monthly, aggregate data, so that the dimension name changes to
            # season or month (values will be the same)
            if time_scale == 'seasonal':
                datasets[time_scale][name_sim] = datasets[time_scale][name_sim].groupby('time.season').mean(dim='time')
            elif time_scale == 'monthly':
                datasets[time_scale][name_sim] = datasets[time_scale][name_sim].groupby('time.month').mean(dim='time')

            # read inlag1 correlation (if applicable)
            fn = os.path.join(data_path_sim, gcm, '%s_%s_%s%s_%s_%s_lag1corr.nc' % (name_sim, var_sim, time_scale_str, statistic, year_start, year_end))
            if os.path.exists(fn):
                if verbose: print(fn)
                datasets[time_scale][name_sim + '_lag1corr'] = xr.open_dataset(fn).load()

        # read in absolute / relative bias or bias in lag1corr
        if read_in_bias_types is not None:
            for bias_type in read_in_bias_types:
                fn = os.path.join(data_path_sim, gcm, 'bias_%s' % name_ref, '%s_%s_%s%s_%s_%s.nc' % (bias_type, var, time_scale_str, statistic, year_start, year_end))
                if verbose: print(fn)
                datasets[time_scale][bias_type] = xr.open_dataset(fn).load()
                
                if bias_type in ['bias_abs', 'bias_rel']:
                    # if time_scale is seasonal or monthly, aggregate data, so that the dimension name changes to
                    # season or month (values will be the same)
                    # this does not apply to the bias in lag1 correlation, because there is only one bias value
                    if time_scale == 'seasonal':
                        datasets[time_scale][bias_type] = datasets[time_scale][bias_type].groupby('time.season').mean(dim='time')
                    elif time_scale == 'monthly':
                        datasets[time_scale][bias_type] = datasets[time_scale][bias_type].groupby('time.month').mean(dim='time')

    # standardise dimension and variable names and apply AWRA mask
    for key1 in datasets.keys():
        for key2 in datasets[key1].keys():
            # remove time bnds
            if 'time_bnds' in datasets[key1][key2].variables:
                datasets[key1][key2] = datasets[key1][key2].drop('time_bnds')
            # rename variables
            datasets[key1][key2] = rename_variable_in_ds(datasets[key1][key2], var_ref_in_nc, var)
            datasets[key1][key2] = rename_variable_in_ds(datasets[key1][key2], var_sim_in_nc, var)
            # standardise lat/lon
            datasets[key1][key2] = standardise_dimension_names(datasets[key1][key2])
            # apply mask to all data
            datasets[key1][key2] = apply_mask(datasets[key1][key2], mask)
            # round lat/lon
            datasets[key1][key2] = standardise_latlon(datasets[key1][key2])
    
    return datasets



    
# Function: Prepare dataframes of bias maps for creating boxplots, for all GCMs.
def prepare_dataframes_for_all_gcms_and_statistics(data_path_ref, data_path_sim, gcms, var, name_sim_prefix, name_ref, 
                                                   statistics, year_start, year_end, mask=None,
                                                   time_scales = ['annual', 'seasonal', 'monthly'],
                                                   var_ref=None, var_sim=None, var_ref_in_nc=None, 
                                                   var_sim_in_nc=None,
                                                   verbose=False):

    """
    This functions reads in the 30-year mean (annual, seasonal and/or monthly) and the bias, converts them into dataframes and combines all of the
    data to be plotted in boxplots.
    """
    
    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim
        
    if type(statistics) == str:
        statistics = [statistics]

    # prepare output dataframe with the following columns: ['type', 'time_scale', 'statistic', 'lat', 'lon', var]
    # type: e.g. 'awap', 'isimip'
    # time_scale: e.g. 'annual'
    # statistic: e.g. 'mean', 'min', 'pctl90'
    # lat, lon: coordinates
    # var: e.g. 'pr'

    df = pd.DataFrame()

    for statistic in statistics:
        if verbose: print(statistic)
        for time_scale in time_scales:
            
            # First: read in reference (historical AWRA run)

            # read in reference data
            datasets = read_in_xarray_data_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                      gcm=None, var=var, name_sim=None, name_ref=name_ref,
                                                      statistic=statistic, year_start=year_start, 
                                                      year_end=year_end, mask=mask,
                                                      var_ref=var_ref, var_sim=None, var_ref_in_nc=var_ref_in_nc,
                                                      var_sim_in_nc=None, time_scales=[time_scale],
                                                      read_in_bias_types=None)
            
            temp = datasets[time_scale][name_ref].to_dataframe().reset_index()
            temp['type'] = name_ref
            temp['statistic'] = statistic
            
            # add time scale (for annual, it's just annual, for season it is the name of the season, for month it's
            # the name of each month)
            if time_scale == 'annual':
                temp['time_scale'] = 'annual'
            elif time_scale == 'seasonal':
                temp['time_scale'] = temp['season']
            elif time_scale == 'monthly':
                temp['time_scale'] = [calendar.month_abbr[x] for x in temp['month']]
                
            df = df.append(temp[['type', 'time_scale', 'statistic', 'lat', 'lon', var]])
            

            # loop through gcms and read in data:
            for gcm in gcms:
                name_sim = '%s_%s' % (name_sim_prefix, gcm)
                datasets = read_in_xarray_data_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                      gcm=gcm, var=var, name_sim=name_sim, name_ref=None,
                                                      statistic=statistic, year_start=year_start, 
                                                      year_end=year_end, mask=mask,
                                                      var_ref=None, var_sim=var_sim, var_ref_in_nc=None,
                                                      var_sim_in_nc=var_sim_in_nc, time_scales=[time_scale],
                                                      read_in_bias_types=None)

                temp = datasets[time_scale][name_sim].to_dataframe().reset_index()
                temp['type'] = name_sim
                temp['statistic'] = statistic
                                      
                # add time scale (for annual, it's just annual, for season it is the name of the season, for month it's
                # the name of each month)
                if time_scale == 'annual':
                    temp['time_scale'] = 'annual'
                elif time_scale == 'seasonal':
                    temp['time_scale'] = temp['season']
                elif time_scale == 'monthly':
                    temp['time_scale'] = [calendar.month_abbr[x] for x in temp['month']]
                                          
                df = df.append(temp[['type', 'time_scale', 'statistic', 'lat', 'lon', var]])
        
    return df



# Read in time series of monthly, seasonal or annual values to be plotted in time series plots, for one GCM.
def read_in_timeseries_for_one_gcm(data_path_ref, data_path_sim, gcm, var, name_sim, name_ref, statistic, year_start, year_end, mask=None,
                 var_ref=None, var_sim=None, var_ref_in_nc=None, var_sim_in_nc=None, 
                                   read_in_bias_types=['bias_abs', 'bias_rel'], 
                                   time_scales=['annual', 'seasonal', 'monthly'], load=True,
                                   verbose=False, lat=None, lon=None):
    """
    This functions reads in in time series of monthly, seasonal or annual values and returns them as xarray datasets to be plotted in time series plots.
    It reads in the data for one GCM and variable - for both the simulation and reference.
    """
    
    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim
    
    # prepare output dictionary of the following shape:
    # datasets[TIMESCALE][NAME_REF/NAME_SIM] # TIMESCALE: annual,seasonal,monthly; # NAME_REF/NAME_SIM: e.g. awap, isimip_NorESM1-M
    # each item is an xarray dataset

    datasets = dict()
    for time_scale in time_scales:
        datasets[time_scale] = dict()
    
    for time_scale in time_scales:
        
        time_scale_str = dict(annual='year', seasonal='seas', monthly='mon')[time_scale]
        
        # read in reference data
        if name_ref is not None:
            fn = os.path.join(data_path_ref, '%s_%s_%s%s_%s_%s_merged.nc' % (name_ref, var_ref, time_scale_str, 
                                                                              statistic, year_start, year_end))
            if verbose: print(fn)
            datasets[time_scale][name_ref] = xr.open_dataset(fn)


        # read in simulation data
        if name_sim is not None:
            fn = os.path.join(data_path_sim, gcm, '%s_%s_%s%s_%s_%s_merged.nc' % (name_sim, var_sim, time_scale_str,
                                                                              statistic, year_start, year_end))
            if verbose: print(fn)
            datasets[time_scale][name_sim] = xr.open_dataset(fn)
        
    # standardise dimension and variable names and apply AWRA mask
    for key1 in datasets.keys():
        for key2 in datasets[key1].keys():
            
            # remove time bnds
            if 'time_bnds' in datasets[key1][key2].variables:
                datasets[key1][key2] = datasets[key1][key2].drop('time_bnds')
            # rename variables
            datasets[key1][key2] = rename_variable_in_ds(datasets[key1][key2], var_ref_in_nc, var)
            datasets[key1][key2] = rename_variable_in_ds(datasets[key1][key2], var_sim_in_nc, var)
            
            # standardise lat/lon
            datasets[key1][key2] = standardise_dimension_names(datasets[key1][key2])
            # round lat/lon
            datasets[key1][key2] = standardise_latlon(datasets[key1][key2])

            # read in lat / lon coordinate, if applicable
            if lat is not None and lon is not None:
                datasets[key1][key2] = datasets[key1][key2].sel(lat=lat, lon=lon, method='nearest')
            
            # load data (before mask seems to be faster)
            if load:
                datasets[key1][key2] = datasets[key1][key2].load()
            
            # apply mask to all data
            datasets[key1][key2] = apply_mask(datasets[key1][key2], mask)
    
    return datasets





# Read in time series of monthly, seasonal or annual values to be plotted in time series plots, for one GCM.
def read_in_mean_field_for_one_gcm(data_path_ref, data_path_sim, gcm, var, name_sim, name_ref, statistic, year_start, year_end, mask=None,
                                   var_ref=None, var_sim=None, var_ref_in_nc=None, var_sim_in_nc=None, 
                                   time_scales=['annual', 'seasonal', 'monthly'], load=True,
                                   verbose=False, lat=None, lon=None):
    """
    This functions reads in the monthly, seasonal or annual mean and returns them as xarray datasets to be plotted in time series plots.
    It reads in the data for one GCM and variable - for both the simulation and reference.
    """
    
    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim
    
    # prepare output dictionary of the following shape:
    # datasets[TIMESCALE][NAME_REF/NAME_SIM] # TIMESCALE: annual,seasonal,monthly; # NAME_REF/NAME_SIM: e.g. awap, isimip_NorESM1-M
    # each item is an xarray dataset

    datasets = dict()
    for time_scale in time_scales:
        datasets[time_scale] = dict()
    
    for time_scale in time_scales:
        
        time_scale_str = dict(annual='year', seasonal='seas', monthly='mon')[time_scale]
        
        # read in reference data
        if name_ref is not None:
            fn = os.path.join(data_path_ref, '%s_%s_%s%s_%s_%s_mean.nc' % (name_ref, var_ref, time_scale_str, 
                                                                              statistic, year_start, year_end))
            if verbose: print(fn)
            datasets[time_scale][name_ref] = xr.open_dataset(fn)


        # read in simulation data
        if name_sim is not None:
            fn = os.path.join(data_path_sim, gcm, '%s_%s_%s%s_%s_%s_mean.nc' % (name_sim, var_sim, time_scale_str,
                                                                              statistic, year_start, year_end))
            if verbose: print(fn)
            datasets[time_scale][name_sim] = xr.open_dataset(fn)
        
    # standardise dimension and variable names and apply AWRA mask
    for key1 in datasets.keys():
        for key2 in datasets[key1].keys():
            
            # remove time bnds
            if 'time_bnds' in datasets[key1][key2].variables:
                datasets[key1][key2] = datasets[key1][key2].drop('time_bnds')
            # rename variables
            datasets[key1][key2] = rename_variable_in_ds(datasets[key1][key2], var_ref_in_nc, var)
            datasets[key1][key2] = rename_variable_in_ds(datasets[key1][key2], var_sim_in_nc, var)
            
            # standardise lat/lon
            datasets[key1][key2] = standardise_dimension_names(datasets[key1][key2])
            # round lat/lon
            datasets[key1][key2] = standardise_latlon(datasets[key1][key2])

            # read in lat / lon coordinate, if applicable
            if lat is not None and lon is not None:
                datasets[key1][key2] = datasets[key1][key2].sel(lat=lat, lon=lon, method='nearest')
            
            # load data (before mask seems to be faster)
            if load:
                datasets[key1][key2] = datasets[key1][key2].load()
            
            # apply mask to all data
            datasets[key1][key2] = apply_mask(datasets[key1][key2], mask)
    
    return datasets




# Read in the monthly time series and calculate climatologies to be plotted in climatology plots.
def prepare_climatologies_for_all_gcms_and_statistics(data_path_ref, data_path_sim, gcms, variables, name_sim_prefix, name_ref, 
                                                   statistics, year_start, year_end, mask=None,
                                                   ref_vars=None, sim_vars=None, ref_vars_in_nc=None, 
                                                   sim_vars_in_nc=None, verbose=False):

    """
    This function reads in monthly time series and calculates the spatial mean for each month
    of the year. The spatial mean is calculated after applying a mask, so for regional climatologies, pass a regional mask.
    The function returns a dataframe with the following columns: ['type', 'statistic', 'month', 'var', 'value']
    The plotting function used to plot the climatology groups the data by month and plots the climatology and uncertainty bands.
    """
        
    if type(statistics) == str:
        statistics = [statistics]
    
    # Prepare a dataframe for the outputs. The final dataframe has the following columns: ['type', 'statistic', 'month', 'var', 'value']
    df = pd.DataFrame()

    for var in variables:
        
        var_ref = ref_vars[var]
        var_sim = sim_vars[var]
        var_ref_in_nc = ref_vars_in_nc[var]
        var_sim_in_nc = sim_vars_in_nc[var]
        
        for statistic in statistics:
            if verbose: print(statistic)
            # First: read in reference (historical AWRA run)

            # read in reference data - mothly data
            datasets = read_in_timeseries_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                      gcm=None, var=var, name_sim=None, name_ref=name_ref,
                                                      statistic=statistic, year_start=year_start, year_end=year_end, mask=mask,
                                                      var_ref=var_ref, var_sim=None, var_ref_in_nc=var_ref_in_nc, var_sim_in_nc=None, 
                                                      read_in_bias_types=None, time_scales=['monthly'], load=True)

            # calculate the spatial mean for each time step
            temp = datasets['monthly'][name_ref].groupby('time').mean()
            temp['month'] = temp['time.month'] # add month variable
            temp = temp.to_dataframe().reset_index()
            temp['type'] = name_ref
            temp['statistic'] = statistic
            temp['var'] = var
            temp['value'] = temp[var]
                        
            df = df.append(temp[['type', 'statistic', 'month', 'var', 'value']])

            # loop through gcms and read in data:
            for gcm in gcms:
                name_sim = '%s_%s' % (name_sim_prefix, gcm)
                datasets = read_in_timeseries_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                      gcm=gcm, var=var, name_sim=name_sim, name_ref=None,
                                                      statistic=statistic, year_start=year_start, year_end=year_end, mask=mask,
                                                      var_ref=None, var_sim=var_sim, var_ref_in_nc=None, var_sim_in_nc=var_sim_in_nc, 
                                                      read_in_bias_types=None, time_scales=['monthly'], load=True)
                
                # calculate the spatial mean for each time step
                temp = datasets['monthly'][name_sim].groupby('time').mean()
                temp['month'] = temp['time.month'] # add month variable
                temp = temp.to_dataframe().reset_index()
                temp['type'] = name_sim
                temp['statistic'] = statistic
                temp['var'] = var
                temp['value'] = temp[var]
                df = df.append(temp[['type', 'statistic', 'month', 'var', 'value']])
            
    return df


# Read in time series of monthly, seasonal or annual time series to be plotted in time series plots, for all GCMs.
# This function calculates the spatial mean for each time step (i.e. combining all lat/lons into one mean value).
def prepare_timeseries_for_all_gcms_and_statistics(data_path_ref, data_path_sim, gcms, var, name_sim_prefix, name_ref, 
                                                   statistics, year_start, year_end, mask=None,
                                                   var_ref=None, var_sim=None, var_ref_in_nc=None, 
                                                   var_sim_in_nc=None, lat=None, lon=None, verbose=False):

    """
    # This function reads in time series of monthly, seasonal or annual time series to be plotted in time series plots, for all GCMs.
    # It calculates the spatial mean for each time step (i.e. combining all lat/lons into one mean value).
    # The mean calculation is done after applying a mask, so for regional means pass a mask for the region.
    # Returns a dataframe with the following columns:
    # Columns: ['type', 'time_scale', 'statistic', 'time', var, 'year', 'month', 'season']
    """
    
    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim
        
    if type(statistics) == str:
        statistics = [statistics]
    
    df = pd.DataFrame()

    for statistic in statistics:
        if verbose: print(statistic)
        # First: read in reference (historical AWRA run)

        # read in reference data - annual
        datasets = read_in_timeseries_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                  gcm=None, var=var, name_sim=None,
                                                  name_ref=name_ref, statistic=statistic, year_start=year_start,
                                                  year_end=year_end, mask=mask,
                                                  var_ref=var_ref, var_sim=None, var_ref_in_nc=var_ref_in_nc,
                                                  var_sim_in_nc=None, read_in_bias_types=None, 
                                                  time_scales=['annual', 'seasonal'], lat=lat, lon=lon)
        
        # calculate the mean for each time step
        temp = datasets['annual'][name_ref].groupby('time').mean()
        temp = temp.to_dataframe().reset_index()
        temp['type'] = name_ref
        temp['time_scale'] = 'annual'
        temp['statistic'] = statistic
        df = df.append(temp[['type', 'time_scale', 'statistic', 'time', var]])

        # read in reference data - seasonal
        temp = datasets['seasonal'][name_ref].groupby('time').mean()
        temp = temp.to_dataframe().reset_index()
        temp['type'] = name_ref
        temp['statistic'] = statistic
        temp['time_scale'] = 'seasonal'
        temp['statistic'] = statistic
        df = df.append(temp[['type', 'time_scale', 'statistic', 'time', var]])

        # loop through gcms and read in data:
        for gcm in gcms:
            name_sim = '%s_%s' % (name_sim_prefix, gcm)
            datasets = read_in_timeseries_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                  gcm=gcm, var=var, name_sim=name_sim,
                                                  name_ref=None, statistic=statistic, year_start=year_start,
                                                  year_end=year_end, mask=mask,
                                                  var_ref=None, var_sim=var_sim, var_ref_in_nc=None,
                                                  var_sim_in_nc=var_sim_in_nc, read_in_bias_types=None, 
                                                  time_scales=['annual', 'seasonal'], lat=lat, lon=lon)
            
            # calculate the mean for each time step
            temp = datasets['annual'][name_sim].groupby('time').mean()
            temp = temp.to_dataframe().reset_index()
            temp['type'] = name_sim
            temp['time_scale'] = 'annual'
            temp['statistic'] = statistic
            df = df.append(temp[['type', 'time_scale', 'statistic', 'time', var]])

            # calculate the mean for each time step
            temp = datasets['seasonal'][name_sim].groupby('time').mean()
            temp = temp.to_dataframe().reset_index()
            temp['type'] = name_sim
            temp['statistic'] = statistic
            temp['time_scale'] = 'seasonal'
            temp['statistic'] = statistic
            df = df.append(temp[['type', 'time_scale', 'statistic', 'time', var]])
    
    df['year'] = [x.year for x in df['time']]
    df['month'] = [x.month for x in df['time']]
    month_to_season = ['DJF','DJF','MAM','MAM','MAM','JJA','JJA','JJA','SON','SON','SON','DJF']
    df['season'] = [month_to_season[x-1] for x in df['month']]
    df['time_scale'][df['time_scale'] == 'seasonal'] = df['season'][df['time_scale'] == 'seasonal']

    return df



# Read in time series of monthly, seasonal or annual time series to be plotted in time series plots, for all GCMs.
# This function calculates the temporal mean for all grid cells (i.e. combining all time steps into one mean value).
def prepare_mean_field_for_all_gcms_and_statistics(data_path_ref, data_path_sim, gcms, var, name_sim_prefix, name_ref, 
                                                   statistics, year_start, year_end, mask=None,
                                                   var_ref=None, var_sim=None, var_ref_in_nc=None, 
                                                   var_sim_in_nc=None, lat=None, lon=None, verbose=False):

    """
    # This function reads in time series of monthly, seasonal or annual time series to be plotted in time series plots, for all GCMs.
    # It calculates the temporal mean for all grid cells (i.e. combining all time steps into one mean value).
    # The mean calculation is done after applying a mask, so for regional means pass a mask for the region.
    # Returns a dataframe with the following columns:
    # Columns: ['type', 'time_scale', 'statistic', 'lat', 'lon', var]
    """
    
    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim
        
    if type(statistics) == str:
        statistics = [statistics]
    
    df = pd.DataFrame()

    for statistic in statistics:
        # First: read in reference (historical AWRA run)

        # read in reference data - annual, seasonal
        datasets = read_in_mean_field_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                  gcm=None, var=var, name_sim=None,
                                                  name_ref=name_ref, statistic=statistic, year_start=year_start,
                                                  year_end=year_end, mask=mask,
                                                  var_ref=var_ref, var_sim=None, var_ref_in_nc=var_ref_in_nc,
                                                  var_sim_in_nc=None, time_scales=['annual', 'seasonal'],
                                                  lat=lat, lon=lon, verbose=verbose)
        
        # calculate the mean over time
        temp = datasets['annual'][name_ref].mean(dim='time') # calculate the time mean, for each grid cell
        temp = temp.to_dataframe().reset_index()
        temp['type'] = name_ref
        temp['time_scale'] = 'annual'
        temp['statistic'] = statistic
        df = df.append(temp[['type', 'time_scale', 'statistic', 'lat', 'lon', var]])

        # calculate the mean over time
        temp = datasets['seasonal'][name_ref].groupby('time.season').mean(dim='time')
        temp = temp.to_dataframe().reset_index()
        temp['type'] = name_ref
        temp['statistic'] = statistic
        temp['time_scale'] = temp['season']
        temp['statistic'] = statistic
        df = df.append(temp[['type', 'time_scale', 'statistic', 'lat', 'lon', var]])

        # loop through gcms and read in data:
        for gcm in gcms:
            name_sim = '%s_%s' % (name_sim_prefix, gcm)
            datasets = read_in_mean_field_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                  gcm=gcm, var=var, name_sim=name_sim,
                                                  name_ref=None, statistic=statistic, year_start=year_start,
                                                  year_end=year_end, mask=mask,
                                                  var_ref=None, var_sim=var_sim, var_ref_in_nc=None,
                                                  var_sim_in_nc=var_sim_in_nc, time_scales=['annual', 'seasonal'],
                                                  lat=lat, lon=lon, verbose=verbose)
            
            # calculate the mean over time
            temp = datasets['annual'][name_sim].mean(dim='time')
            temp = temp.to_dataframe().reset_index()
            temp['type'] = name_sim
            temp['time_scale'] = 'annual'
            temp['statistic'] = statistic
            df = df.append(temp[['type', 'time_scale', 'statistic', 'lat', 'lon', var]])

            # calculate the mean over time
            temp = datasets['seasonal'][name_sim].groupby('time.season').mean(dim='time')
            temp = temp.to_dataframe().reset_index()
            temp['type'] = name_sim
            temp['statistic'] = statistic
            temp['time_scale'] = temp['season']
            temp['statistic'] = statistic
            df = df.append(temp[['type', 'time_scale', 'statistic', 'lat', 'lon', var]])
    return df




# Read in time series of monthly, seasonal or annual time series to be plotted in time series plots, for all GCMs, without
# spatial or temporal aggregation.
def prepare_spatiotemporal_data_for_all_gcms_and_statistics(data_path_ref, data_path_sim, gcms, var, name_sim_prefix, name_ref, 
                                                   statistics, year_start, year_end, mask=None,
                                                   var_ref=None, var_sim=None, var_ref_in_nc=None, 
                                                   var_sim_in_nc=None, lat=None, lon=None):
    
    """
    # This function reads in time series of monthly, seasonal or annual time series to be plotted in time series plots, for all GCMs.
    # Returns a dataframe with the following columns:
    # Columns: ['type', 'time_scale', 'statistic', 'time', 'lat', 'lon', var, 'year', 'month', 'season']
    """

    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim
        
    if type(statistics) == str:
        statistics = [statistics]
    

    
    df = pd.DataFrame()

    for statistic in statistics:
        # First: read in reference (historical AWRA run)

        # read in reference data - annual
        datasets = read_in_timeseries_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                  gcm=None, var=var, name_sim=None,
                                                  name_ref=name_ref, statistic=statistic, year_start=year_start,
                                                  year_end=year_end, mask=mask,
                                                  var_ref=var_ref, var_sim=None, var_ref_in_nc=var_ref_in_nc,
                                                  var_sim_in_nc=None, read_in_bias_types=None, 
                                                  time_scales=['annual', 'seasonal'], lat=lat, lon=lon)
        
        # calculate the mean for each time step
        temp = datasets['annual'][name_ref]
        temp = temp.to_dataframe().reset_index()
        temp['type'] = name_ref
        temp['time_scale'] = 'annual'
        temp['statistic'] = statistic
        df = df.append(temp[['type', 'time_scale', 'statistic', 'time', 'lat', 'lon', var]])

        # read in reference data - seasonal
        temp = datasets['seasonal'][name_ref]
        temp = temp.to_dataframe().reset_index()
        temp['type'] = name_ref
        temp['statistic'] = statistic
        temp['time_scale'] = 'seasonal'
        temp['statistic'] = statistic
        df = df.append(temp[['type', 'time_scale', 'statistic', 'time', 'lat', 'lon', var]])

        # loop through gcms and read in data:
        for gcm in gcms:
            name_sim = '%s_%s' % (name_sim_prefix, gcm)
            datasets = read_in_timeseries_for_one_gcm(data_path_ref=data_path_ref, data_path_sim=data_path_sim,
                                                  gcm=gcm, var=var, name_sim=name_sim,
                                                  name_ref=None, statistic=statistic, year_start=year_start,
                                                  year_end=year_end, mask=mask,
                                                  var_ref=None, var_sim=var_sim, var_ref_in_nc=None,
                                                  var_sim_in_nc=var_sim_in_nc, read_in_bias_types=None, 
                                                  time_scales=['annual', 'seasonal'], lat=lat, lon=lon)
            
            # calculate the mean for each time step
            temp = datasets['annual'][name_sim]
            temp = temp.to_dataframe().reset_index()
            temp['type'] = name_sim
            temp['time_scale'] = 'annual'
            temp['statistic'] = statistic
            df = df.append(temp[['type', 'time_scale', 'statistic', 'time', 'lat', 'lon', var]])

            # calculate the mean for each time step
            temp = datasets['seasonal'][name_sim]
            temp = temp.to_dataframe().reset_index()
            temp['type'] = name_sim
            temp['statistic'] = statistic
            temp['time_scale'] = 'seasonal'
            temp['statistic'] = statistic
            df = df.append(temp[['type', 'time_scale', 'statistic', 'time', 'lat', 'lon', var]])
    
    df['year'] = [x.year for x in df['time']]
    df['month'] = [x.month for x in df['time']]
    month_to_season = ['DJF','DJF','MAM','MAM','MAM','JJA','JJA','JJA','SON','SON','SON','DJF']
    df['season'] = [month_to_season[x-1] for x in df['month']]
    df['time_scale'][df['time_scale'] == 'seasonal'] = df['season'][df['time_scale'] == 'seasonal']

    return df




# Read in daily time series to be plotted in time series plots, for a given lat/lon coordinate - for all GCMs.
def prepare_daily_timeseries_for_all_gcms(data_path_sim, data_path_ref, gcms, var, name_sim_prefix, name_ref,
                                           year_start, year_end, lat=None, lon=None,
                                           var_ref=None, var_sim=None, var_ref_in_nc=None,
                                           var_sim_in_nc=None):

    """
    # This function reads in daily time series for one lat/lon coordinate for all GCMs, to be plotted in time series plots.
    # Returns a dataframe with the following columns:
    # Columns: ['type', 'time_scale', 'time', 'lat', 'lon', var]
    """
    
    # set default values
    if var_ref is None: var_ref=var
    if var_sim is None: var_sim=var
    if var_ref_in_nc is None: var_ref_in_nc=var_ref
    if var_sim_in_nc is None: var_sim_in_nc=var_sim
    
    df = pd.DataFrame()
    
    # Read in reference data
    data_path_ref_temp = data_path_ref.replace('#VAR#', var_ref) # replace VAR placeholder, if applicable    
    years_to_read_in = np.arange(year_start, year_end+1) # can't just merge all files together, because there is an issue with latitudes after 2017
    files = [glob.glob(os.path.join(data_path_ref_temp, '*%s*%s*.nc' % (var_ref, x))) for x in years_to_read_in]
    temp = xr.open_mfdataset(files)
    
    # Standardise dimension names
    temp = standardise_dimension_names(temp)
    temp = temp.rename({var_ref_in_nc:var})
        
    # extract time and coordinates
    temp = temp.sel(time=slice(str(year_start), str(year_end)))
    temp = temp.sel(lat=lat, lon=lon, method='nearest')
    temp = temp.load()
    
    # create a dataframe
    temp = temp.to_dataframe().reset_index()
    temp['type'] = name_ref
    temp['time_scale'] = 'daily'
    
    df = df.append(temp[['type', 'time_scale', 'time', 'lat', 'lon', var]])
    
    
    # Read in GCM data
    for gcm in gcms:
        
        name_sim = '%s_%s' % (name_sim_prefix, gcm)
        data_path_sim_temp = data_path_sim.replace('#GCM#', gcm).replace('#VAR#', var_sim)
        files = os.path.join(data_path_sim_temp, '*%s*.nc' % (var_sim))
        
        # Open data
        temp = xr.open_mfdataset(files)
        
        # Standardise dimension names
        temp = standardise_dimension_names(temp)
        temp = temp.rename({var_sim_in_nc:var})

        # extract time and coordinates
        temp = temp.sel(time=slice(str(year_start), str(year_end)))
        temp = temp.sel(lat=lat, lon=lon, method='nearest')
        temp = temp.load()
        
        # Do unit adjustments (only needed for GCMs)
        if var in ['temp_max_day', 'temp_min_day']:
            print('Unit conversion: K --> degC')
            temp[var].values = temp[var].values - 273.15 # K --> degC
        if var == 'rain_day':
            print('Unit conversion: mm/s --> mm/day')
            temp[var].values = temp[var].values * 60 * 60 * 24 # mm/s --> mm/day

        # create a dataframe
        temp = temp.to_dataframe().reset_index()
        temp['type'] = name_sim
        temp['time_scale'] = 'daily'
        
        df = df.append(temp[['type', 'time_scale', 'time', 'lat', 'lon', var]])

    return df
