import os
import sys
import json
import glob
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
path_daily_ref = parameters['path_daily_ref']
path_daily_sim = parameters['path_daily_sim']
plot_path = os.path.join(parameters['plot_path'], '05_animations')
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

animation_daily_start = parameters['animation_daily_start']
animation_daily_end = parameters['animation_daily_end']
animation_daily_years_read_in = parameters['animation_daily_years_read_in']
save_awap_animations = parameters['animation_create_ref_animations']

mask = parameters['mask_file']


### Create all plots - daily data

#### 1) GCM data - daily

path_daily = path_daily_sim

for gcm in gcms:
    for var in vars:
        var_sim = sim_vars[var]
        var_sim_in_nc = sim_vars_in_nc[var]
        print('GCM: %s, var: %s' % (gcm, var_sim))
        
        fn_anim = os.path.join(plot_path, 'animations_daily_%s_%s_%s_%s_%s.gif' % (name_sim_prefix, gcm, var_sim,
                                                                                   animation_daily_start, animation_daily_end))
        
        if os.path.exists(fn_anim):
            print('Animation created before. Skipping.')
            continue
            
        print('- read in data')
        files = os.path.join(path_daily, gcm, 'historical', '*%s*.nc' % (var_sim))
        print(files)
        ds = evl.read_in.read_in_data_for_animations(files=files, start_date=animation_daily_start,
                                         end_date=animation_daily_end, var_in_nc=var_sim_in_nc)
        
        # Create animation
        print('- create animation')
        evl.plotting.create_animation(ds, fn_anim, fps=6)


#### 2) AWAP data - daily

if save_awap_animations:
    
    path_daily = path_daily_ref

    for gcm in gcms:
        for var in vars:
            var_ref = ref_vars[var]
            var_ref_in_nc = ref_vars_in_nc[var]
            print('GCM: %s, var: %s' % (gcm, var_ref))

            fn_anim = os.path.join(plot_path, 'animations_daily_%s_%s_%s_%s.gif' % (name_ref, var_ref,
                                                                                       animation_daily_start,
                                                                                       animation_daily_end))

            if os.path.exists(fn_anim):
                print('Animation created before. Skipping.')
                continue

            print('- read in data')
            files = [glob.glob(os.path.join(path_daily_ref, var_ref, '*%s*%s*.nc' % (var_ref, x))) for x in animation_daily_years_read_in]

            ds = evl.read_in.read_in_data_for_animations(files=files, start_date=animation_daily_start,
                                             end_date=animation_daily_end, var_in_nc=var_ref_in_nc)

            # Create animation
            print('- create animation')
            evl.plotting.create_animation(ds, fn_anim, fps=6)


### Create all plots - annual data

#### 1) GCM data - annual (mean)

for gcm in gcms:
    for var in vars:
        var_sim = sim_vars[var]
        var_sim_in_nc = sim_vars_in_nc[var]
        print('GCM: %s, var: %s' % (gcm, var_sim))
        
        fn_anim = os.path.join(plot_path, 'animations_annual_%s_%s_%s_%s_%s.gif' % (name_sim_prefix, gcm, var_sim,
                                                                                   year_start, year_end))
        
        if os.path.exists(fn_anim):
            print('Animation created before. Skipping.')
            continue
            
        print('- read in data')
        files = os.path.join(data_path_ref, gcm,  '%s_%s_%s_yearmean_*_merged.nc' % (name_sim_prefix, gcm, var_sim))
        
        print(files)
        ds = evl.read_in.read_in_data_for_animations(files=files, start_date=year_start,
                                         end_date=year_end, var_in_nc=var_sim_in_nc)
        
        # Create animation
        print('- create animation')
        evl.plotting.create_animation(ds, fn_anim, fps=2)


#### 2) AWAP data - annual

if save_awap_animations:
    
    for var in vars:
        var_ref = ref_vars[var]
        var_ref_in_nc = ref_vars_in_nc[var]
        print('var: %s' % var_ref)

        fn_anim = os.path.join(plot_path, 'animations_annual_%s_%s_%s_%s.gif' % (name_ref, var_ref,
                                                                                   year_start,
                                                                                   year_end))

        if os.path.exists(fn_anim):
            print('Animation created before. Skipping.')
            continue

        print('- read in data')
        files = os.path.join(data_path_sim, '%s_%s_yearmean_*_merged.nc' % (name_ref, var))
        
        ds = evl.read_in.read_in_data_for_animations(files=files, start_date=year_start,
                                         end_date=year_end, var_in_nc=var_ref_in_nc)

        # Create animation
        print('- create animation')
        evl.plotting.create_animation(ds, fn_anim, fps=2)

