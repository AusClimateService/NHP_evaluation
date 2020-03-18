# Helper functions for the evaluation plotting library.

# Author: Elisabeth Vogel, elisabeth.vogel@bom.gov.au
# Date: 19/09/2019

# Import libraries
import os
import numpy as np
import xarray as xr



# Function definitions
def standardise_dimension_names(ds):
    """
    This function renames the latitude / longitude coordinates into lat / lon, where applicable, so that
    all xarray datasets use the same coordinate names.
    """
    ds = rename_variable_in_ds(ds, 'latitude', 'lat')
    ds = rename_variable_in_ds(ds, 'longitude', 'lon')
    return(ds)

def standardise_latlon(ds, digits=4):
    """
    This function rounds the latitude / longitude coordinates to the 4th digit, because some dataset
    seem to have strange digits (e.g. 50.00000001 instead of 50.0), which prevents merging of data.
    """
    ds['lat'].values = np.round(ds['lat'].values, digits)
    ds['lon'].values = np.round(ds['lon'].values, digits)
    return(ds)

def rename_variable_in_ds(ds, old_name, new_name):
    """
    This function renames a variable in an xarray dataset.
    """
    dict_temp = dict(zip([old_name], [new_name]))
    if old_name in ds.variables or old_name in ds.dims:
        ds = ds.rename(dict_temp)
    return(ds)

def apply_mask(ds, mask):
    """
    This function applies a mask to to a dataset. Requirement is that both have the same resolution.
    """

    # read in mask, if it's a file name
    if mask is not None and type(mask) == str:
        mask = xr.open_dataset(mask)
        mask = standardise_dimension_names(mask)
        mask = mask['mask'] == 1

    if mask is not None:
        ds = ds.where(mask==1)

    return(ds)

def create_containing_folder(file):
    if not os.path.exists(os.path.dirname(file)):
        os.makedirs(os.path.dirname(file), exist_ok=True)




def get_variable_longname(var):
    long_names = {
        'rain_day': 'Precipitation',
        'temp_min_day': 'Min. temperature',
        'temp_max_day': 'Max. temperature',
        'solar_exposure_day': 'Solar radiation',
        'wind': 'Wind speed',
        'sm': 'Soil moisture',
        'etot': 'Actual ET',
        'e0': 'Potential ET',
        'qtot': 'Runoff'}
    
    return(long_names[var])