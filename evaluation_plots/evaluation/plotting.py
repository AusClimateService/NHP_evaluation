# Plotting functions for the evaluation library.

# Author: Elisabeth Vogel, elisabeth.vogel@bom.gov.au
# Date: 19/09/2019

# Import libraries
import numpy as np

import matplotlib.pyplot as plt
import seaborn as sns
import plotnine as pn
from plotnine import *

from mpl_toolkits.basemap import Basemap
import cartopy.crs as ccrs
import cartopy.feature as cfeat
import matplotlib.animation as animation

from evaluation.helpers import *


# Function definitions

# 01) Bias maps #################################################################
# TODO: uses Basemap - change to cartopy
def plot_bias(datasets, name_ref, name_sim, var,
              statistic, year_start, year_end,
              coordinates=dict(llcrnrlat=-44.5,
                         urcrnrlat=-10.7,
                         llcrnrlon=112,
                         urcrnrlon=156.25),
              fn_plot=None, adjust=0.93):

    """
    This function creates a plot with a) the 30-year mean for the historical reference,
    b) the simulated / bias corrected data, c) the absolute/relative bias of both, for
    annual and seasonal values.
    """
    
    # plot absolute bias for temperature, else relative bias
    if var in ['temp_min_day', 'temp_max_day']:
        plot_bias_type = 'bias_abs'
    else:
        plot_bias_type = 'bias_rel'

    # create a map
    map = Basemap(resolution='c', **coordinates)
    types = [name_ref, name_sim, plot_bias_type]
    time_scales = ['annual', 'DJF', 'MAM', 'JJA', 'SON']
   
    # create a figure
    fig, axes = plt.subplots(nrows=len(time_scales), ncols=len(types), figsize=(10,12))

    # loop through columns and rows
    # 3 colums: mean of reference, mean of GCM, bias
    # 5 rows: annual, DJF, MAM, JJA, SON
    for col_idx in range(len(types)):
        for row_idx in range(len(time_scales)):
            
            ds = None # set dataset to plot to Null before reading in new data
            ax = axes[row_idx, col_idx]
            
            type = types[col_idx]
            time_scale = time_scales[row_idx]
            
            # set plotting parameters

            if type in [name_ref, name_sim]:
                vmin = 0
                if var == 'qtot': # maximum values too large, therefore times 0.5
                    vmax = 0.5 * max([float(datasets['annual'][name_ref][var].max()),
                                float(datasets['seasonal'][name_ref][var].max()),
                                float(datasets['annual'][name_sim][var].max()),
                                float(datasets['seasonal'][name_sim][var].max())])
                else:
                    vmax = max([float(datasets['annual'][name_ref][var].max()),
                            float(datasets['seasonal'][name_ref][var].max()),
                            float(datasets['annual'][name_sim][var].max()),
                            float(datasets['seasonal'][name_ref][var].max())])
                            
                vmax = np.ceil(vmax)
                if var in ['temp_min_day', 'temp_max_day', 'solar_exposure_day']:
                    cmap = plt.get_cmap('Reds', 10)
                else:
                    cmap = plt.get_cmap('Blues', 10)
                    
                cmap.set_bad('white')
                cmap.colorbar_extend = True
                legend_title = '%s (abs)pl' % var
                
            elif type == 'bias_abs':
                vmax = dict(temp_min_day=10, temp_max_day=10)[var]
                vmin = -vmax
                
                if var in ['temp_min_day', 'temp_max_day', 'solar_exposure_day']:
                    cmap = plt.get_cmap('RdBu_r', 11)
                else:
                    cmap = plt.get_cmap('RdBu', 11)
                
                cmap.set_under('#addd8e')
                cmap.set_over('#dd1c77')
                cmap.set_bad('white')
                cmap.colorbar_extend = True
                legend_title = 'bias (abs)'
                
            elif type == 'bias_rel':
                vmin = -100
                vmax = 100
        
                if var in ['temp_min_day', 'temp_max_day', 'solar_exposure_day']:
                    cmap = plt.get_cmap('RdBu_r', 11)
                else:
                    cmap = plt.get_cmap('RdBu', 11)
                    
                cmap.set_bad('white')
                cmap.colorbar_extend = True
                legend_title = 'rel. bias (%)'
                
            if type == 'bias_rel':
                levels = [-100,-50,-25,-10,-5,5,10,25,50,100]
                # levels = None
                extend = 'neither'
            else:
                levels = None
                extend = 'max'
                 
                    
            # read in data to plot
            if time_scale == 'annual':
                ds = datasets[time_scale][type].isel(time=0)
            elif time_scale in ['DJF', 'MAM', 'JJA', 'SON']:
                ds = datasets['seasonal'][type].sel(season=time_scale)
            
            # multiply with 100 for relative bias in percent
            if type == 'bias_rel':
                ds[var].values = ds[var].values * 100
                        
            # create plot
            ds[var].plot.pcolormesh(ax=ax, vmin=vmin, vmax=vmax, levels=levels, extend=extend,cmap=cmap, cbar_kwargs={'label':legend_title})
            # ds[var].plot.imshow(ax=ax, vmin=vmin, vmax=vmax, cmap=cmap, cbar_kwargs={'label':legend_title})
            
            # turn off borders
            ax.axis('off')
            
            # add title
            median = np.float(ds[var].median())
            plot_title = [name_ref.upper(), name_sim.upper(), 'rel. bias'][col_idx]
            plot_title = '%s (%s) \nmedian: %.3f' % (plot_title, time_scale, median)
            ax.set_title(plot_title, fontsize=10)
            
            # add map
            map.drawcoastlines(ax=ax, linewidth=0.2)
            map.drawstates(ax=ax, linewidth=0.1)

    plt.tight_layout()
    plt.subplots_adjust(top=adjust)
    x=fig.suptitle('%s (%s), %s vs %s, period: %s-%s' % (get_variable_longname(var), statistic, name_sim.upper(), name_ref.upper(),
                                                         year_start,year_end), fontsize=16)

    if fn_plot is not None:
        create_containing_folder(fn_plot)
        fig.savefig(fn_plot, dpi=300)

    return fig
    

# 02) Boxplots of bias #################################################################
def plot_boxplots(dataframe, x, y, var, name_ref, name_sim_prefix, statistic=None,
                 col='time_scale', row='statistic', showfliers=False,
                 palette='Blues', height=3, aspect=1.2, adjust=0.7,
                 fn_plot=None):
    
    # create plot
    plot = sns.catplot(data=dataframe, kind='box', sharey='row',
                               showfliers=showfliers,
                               x=x, y=var,
                               col=col, row=row,
                               palette=palette, height=height, aspect=aspect)

    # add title
    plt.subplots_adjust(top=adjust)
    if statistic is None:
        statistic_str = 'statistics'
    else:
        statistic_str = statistic
    if showfliers:
        plot_title = '%s (annual and seasonal %s) %s run vs %s' % \
        (get_variable_longname(var), statistic_str, name_sim_prefix.upper(), name_ref.upper())
    else:
        plot_title = '%s (annual and seasonal %s) %s run vs %s\n--note: not showing outliers--' % \
        (get_variable_longname(var), statistic_str, name_sim_prefix.upper(), name_ref.upper())
    if showfliers:
        plot_title = '%s (annual and seasonal statistics) %s run vs %s' % \
        (get_variable_longname(var), name_sim_prefix.upper(), name_ref.upper())
    else:
        plot_title = '%s (annual and seasonal statistics) %s run vs %s\n--note: not showing outliers--' % \
        (get_variable_longname(var), name_sim_prefix.upper(), name_ref.upper())
    x = plt.suptitle(plot_title,fontsize=12)

    # save plot
    if fn_plot is not None:
        create_containing_folder(fn_plot)
        plot.savefig(fn_plot, dpi=300)
        
        

# 03) Australia mean time series #################################################################
def plot_timeseries(dataframe, x, y, var, name_sim_prefix, name_ref, 
                    hue='type', col='time_scale', row='statistic', palette=None, 
                    height=2, aspect=1.5, linewidth=0.8, adjust=0.95,
                    fn_plot=None):
    
    # set defaults
    if palette is None:
        palette = sns.color_palette("rocket_r", len(dataframe[hue].unique()))
        palette.reverse()
        palette[0] = (0,0,0) # set reference to black
    
    # create plot
    plot = sns.relplot(data=dataframe,kind='line', x=x, y=y, hue=hue,
                       palette=palette, col=col, row=row,
                       height=2, aspect=1.5, linewidth=0.8,
                       facet_kws=dict(sharey='row'))
    
    # add title
    plt.subplots_adjust(top=adjust)
    plot_title = '%s (annual and seasonal time series) %s vs %s data' % \
        (get_variable_longname(var), name_sim_prefix.upper(), name_ref.upper())
    x = plt.suptitle(plot_title,fontsize=16)

    # save plot
    if fn_plot is not None:
        create_containing_folder(fn_plot)
        plot.savefig(fn_plot, dpi=300)
        

# 04) Climatologies #################################################################
# Plot mean monthly values (aggregated over Australia or region) and standard deviation around monthly mean.  
def plot_climatologies(dataframe, x, y, var, name_sim_prefix, name_ref,
                    hue='type', col='var', row='statistic',
                    palette=None, height=2, aspect=1.5, linewidth=0.8, 
                    fn_plot=None, adjust=0.85):
    
    # set defaults
    if palette is None:
        palette = sns.color_palette("rocket_r", len(dataframe[hue].unique()))
        palette.reverse()
        palette[0] = (0,0,0) # set reference to black
    
    plot = sns.relplot(data=dataframe, kind='line', x=x, y=y,
                   hue=hue, col=col, row=row,
                   palette=palette, err_style='bars',
                   linewidth=linewidth, err_kws={'linewidth':linewidth-0.3},
                   facet_kws=dict(sharey=False))
        
    plt.subplots_adjust(top=adjust)
    plot_title = 'Climatologies -- %s vs %s data' % (name_sim_prefix.upper(), name_ref.upper())
    x = plt.suptitle(plot_title,fontsize=12)

    if fn_plot is not None:
        create_containing_folder(fn_plot)
        plot.savefig(fn_plot, dpi=300)


# 05) Animations #################################################################
def create_animation(ds, fn_anim, fps=6):

    # helper functions
    def make_figure():
        fig = plt.figure(figsize=(15, 6))
        ax = fig.add_subplot(1, 1, 1, projection=ccrs.PlateCarree())

        # generate a basemap with country borders, oceans and coastlines
        #ax.add_feature(cfeat.LAND)
        #ax.add_feature(cfeat.OCEAN)
        ax.add_feature(cfeat.COASTLINE)
        ax.add_feature(cfeat.BORDERS, linestyle='dotted')
        
        plt.gca().outline_patch.set_visible(False)

        return fig, ax

    def draw(frame, add_colorbar):
        grid = area[frame]
        contour = grid.plot(ax=ax, transform=ccrs.PlateCarree(), cmap='Blues',
                            add_colorbar=add_colorbar, vmin=min_value, vmax=max_value)
        title = u"%s - %s" % (ds.long_name, str(area.time[frame].values)[:19])
        ax.set_title(title)
        return contour


    def init():
        return draw(0, add_colorbar=True)


    def animate(frame):
        return draw(frame, add_colorbar=False)


    fig, ax = make_figure()
    plt.gca().outline_patch.set_visible(False)

    area = ds.sel(lat=slice(-10.5,-44), lon=slice(112.6,154.3)) # select Australia
    frames = area.time.size
    min_value = np.nanmin(area.values)
    max_value = np.nanmax(area.values)

    ani = animation.FuncAnimation(fig, animate, frames, interval=0.01, blit=False,
                                    init_func=init, repeat=False)

    create_containing_folder(fn_anim)
    print('- save animation to: %s' % (fn_anim))
    ani.save(fn_anim, writer='imagemagick', fps=fps)
    plt.close(fig)


#################################################################
# 06a), 07) and 09) PDF plots
def plot_distribution(dataframe, x, var, statistic, name_sim_prefix, name_ref, 
                    hue='type', col='time_scale', row='statistic', palette=None, 
                    height=2, aspect=1.5, linewidth=0.8, 
                    fn_plot=None):
    
    n_row = len(dataframe[row].unique())
    n_col = len(dataframe[col].unique())
    figure_size = (5 * n_row, 2 * n_col)
    
    plot_title = '%s (PDF of annual and seasonal %s),\n%s vs %s data' % (get_variable_longname(var), statistic, name_sim_prefix.upper(), name_ref.upper())
    
    # prepare the string to pass to the facet grid function
    facet_str = '~ %s + %s' % (col, row)
    
    # create plot
    plot = (ggplot(data=dataframe, mapping=aes(x=x, color=hue, fill=hue)) +
                        
            geom_density(size=0.5, alpha=0.2) +
            
            facet_wrap(facet_str, scales='free', ncol=n_col,
                      labeller=labeller(cols=label_value,multi_line=False), dir='v') +
            
        theme(panel_background = element_rect(fill='#f0f0f0'),
           # panel_grid_major = element_line(linetype='dashed', color='white', size=1),
              panel_grid_major = element_blank(),
           panel_grid_minor = element_blank(),
           # axis_ticks = element_blank(),
           panel_border = element_blank(),
           strip_text = element_text(size=9, color='black'),
           strip_background = element_blank(),
           figure_size = figure_size,
           legend_key_size = 20,
           legend_key_width = 20,
           axis_title_y = element_text(size=8),
           axis_text_x = element_text(size=6),
           axis_text_y = element_text(size=7),
           panel_spacing_x = 0.4,
             panel_spacing_y = 0.2) +
                      
            labs(x='', y='density\n', title=plot_title) +
            
        scale_x_continuous(expand=(0,0.1)) +
        scale_y_continuous(expand=(0,0)))
            

    # save plot
    if fn_plot is not None:
        create_containing_folder(fn_plot)
        plot.save(fn_plot, dpi=300)
        
    return plot

#################################################################
# 06b) Scatter plot of simulated / bias corrected data vs historical reference.
def plot_spatial_correlation(dataframe, x, y, var, statistic, name_sim_prefix, name_ref, 
                    hue='type', col='time_scale', row='statistic', palette=None, 
                    height=2, aspect=1.5, linewidth=0.8, 
                    fn_plot=None):
    
    n_row = len(dataframe[row].unique())
    n_col = len(dataframe[col].unique())
    figure_size = (5 * n_row, 2 * n_col)
    
    plot_title = '%s (annual and seasonal %s),\n%s vs %s data' % (get_variable_longname(var), statistic, name_sim_prefix.upper(), name_ref.upper())
    
    # prepare the string to pass to the facet grid function
    facet_str = '~ %s + %s' % (col, row)
    
    # create plot
    plot = (ggplot(data=dataframe, mapping=aes(x=x, y=y, color=hue, fill=hue)) +
                        
            geom_point(size=0.5, alpha=0.5) +
            geom_smooth(method='lm', se=False, size=0.5) +
            
            # add 1:1 line
            geom_abline(intercept=0, slope=1, size=0.5, linetype='dashed') +
            
            facet_wrap(facet_str, scales='free', ncol=n_col,
                      labeller=labeller(cols=label_value,multi_line=False), dir='v') +
            
        theme(panel_background = element_rect(fill='#f0f0f0'),
           # panel_grid_major = element_line(linetype='dashed', color='white', size=1),
              panel_grid_major = element_blank(),
           panel_grid_minor = element_blank(),
           # axis_ticks = element_blank(),
           panel_border = element_blank(),
           strip_text = element_text(size=9, color='black'),
           strip_background = element_blank(),
           figure_size = figure_size,
           legend_key_size = 20,
           legend_key_width = 20,
           axis_title_y = element_text(size=8),
           axis_text_x = element_text(size=6),
           axis_text_y = element_text(size=7),
           panel_spacing_x = 0.4,
             panel_spacing_y = 0.2) +
                      
            labs(x='', y='density\n', title=plot_title) +
            
        scale_x_continuous(expand=(0,0.1)) +
        scale_y_continuous(expand=(0,0)))
            

    # save plot
    if fn_plot is not None:
        create_containing_folder(fn_plot)
        plot.save(fn_plot, dpi=300)
        
    return plot





# 10) Fourier transform #################################################################
# This plot plots the wavelength on the x-axis (instead of the frequency).
def plot_fourier_transform_wavelengths(dataframe, location_name, var, name_sim_prefix, name_ref, timestep='daily',
                           n_top_frequencies=4, fn_plot=None):
    # adapted from: https://plot.ly/matplotlib/fft/
    
    obs_and_gcms = dataframe['type'].unique()
    
    fig, axes = plt.subplots(len(obs_and_gcms), 2, figsize=(15,2.5*len(obs_and_gcms)))
    
    # plot in rows: "type", i.e. AWAP, GCM1, GCM2, etc.
    # plot in columns: left colums - time series, right column - fourier transform
    
    if timestep == 'monthly':
        # calculate monthly from daily
        dataframe = dataframe.set_index('time')
        dataframe = dataframe.groupby(['type', 'lat', 'lon']).resample('1MS')[var].mean()
        dataframe = dataframe.reset_index()
            
    for row in range(len(obs_and_gcms)):
        
        temp = dataframe.loc[dataframe['type'] == obs_and_gcms[row]]

        if timestep == 'daily':
            
            time_length = (temp['time'].max() - temp['time'].min()).days + 1 # in days
            # prepare the frequencies
            frequencies = np.arange(int(time_length / 2)) # only first half, as 2nd half is duplicated in fft output
            wavelengths = time_length / frequencies # in days
            frequencies = frequencies / time_length * 365 # in years, for plotting

        elif timestep == 'monthly':
            
            average_days_in_a_month = 30.4375
            # in months; +1 is because the last month finishes on the 1st
            time_length = int(np.round((temp['time'].max() - temp['time'].min()).days  / average_days_in_a_month + 1)) # in months
            
            # prepare the frequencies
            frequencies = np.arange(int(time_length / 2)) # only first half, as 2nd half is duplicated in fft output
            wavelengths = time_length / frequencies # in months
            frequencies = frequencies / time_length * 365 # in years, for plotting
            
        ts = temp[var]
        time = temp['time']
        
        # calculate the fourier transform
        fourier_transform = np.fft.fft(ts) # fft computing
        fourier_transform = abs(fourier_transform) # absolute values
        fourier_transform = fourier_transform[np.arange(len(frequencies))]
        
        # remove Inf from wavelengts (Frequency = 0 --> mean of the time series)
        fourier_transform = fourier_transform[np.isfinite(wavelengths)]
        wavelengths = wavelengths[np.isfinite(wavelengths)]
    
        # remove those wavelengths that are longer than half the time series       
        selection = wavelengths <= (time_length / 2)
        fourier_transform = fourier_transform[selection]
        wavelengths = wavelengths[selection]
        len_wavelengths = len(wavelengths)
        
        # 1) plot time series
        ax = axes[row,0]
        ax.plot(temp['time'], ts, '#045a8d', linewidth=0.3)
        ax.set_xlabel('Time')
        ax.set_ylabel(get_variable_longname(var))
        ax.set_ylim(0,temp[var].max()*1.1)
        ax.set_title('Time series: %s' % obs_and_gcms[row].upper())

        # 2) plot fourier transform
        ax = axes[row,1]
        if np.isfinite(abs(fourier_transform).max()):
            ax.set_ylim(0,abs(fourier_transform).max()*1.1)
        ax.set_ylabel('Fourier transform')
        
        ax.plot(wavelengths,fourier_transform,'#800026',linewidth=0.3) # plotting the spectrum
        ax.set_title('Fourier diagram: %s' % obs_and_gcms[row].upper())
        ax.set_xlabel('Wave length (years)')
        
        if timestep == 'daily':
            ax.set_xticks(np.arange(0,wavelengths.max()+1,365)) # in years
            ax.set_xticklabels(np.arange(0,int((wavelengths.max()+1)/365),1)); # in years
            
        elif timestep == 'monthly':
            ax.set_xticks(np.arange(0,wavelengths.max()+1,12)) # in years
            ax.set_xticklabels(np.arange(0,int((wavelengths.max()+1)/12),1)); # in years

        # add top wave lengths to the diagram, if applicable
        if n_top_frequencies > 0:           
            
            top_freq = sorted(fourier_transform[np.isfinite(fourier_transform)], reverse=True)[0:n_top_frequencies]   
            top_freq_idx = []
            for x in top_freq:
                top_freq_idx = top_freq_idx + list(np.where(fourier_transform == x)[0])
                
            # testing
            print(top_freq)
            print(top_freq_idx)
            
            # highlight top frequencies using dot points
            ax.scatter(wavelengths[top_freq_idx], fourier_transform[top_freq_idx], color='#800026', s=10)
            
            for i in range(n_top_frequencies):
                
                if i == 0:
                    x = wavelengths.max()*1.06 # outside of the plot
                    y = top_freq[0]
                    ax.text(x=x, y=y,s='Top wave lengths:',fontsize=8,color='#800026')
                    
                # prepare x, y locations of the text
                x = wavelengths.max()*1.06 # outside of the plot
                y = top_freq[0] * (1/(n_top_frequencies+1) * (n_top_frequencies-i)) # decreasing with increasing i

                if timestep == 'daily':
                    string = '- %s days' % int(round(wavelengths[top_freq_idx[i]],0))
                elif timestep == 'monthly':
                    string = '- %s months' % round(wavelengths[top_freq_idx[i]],1)

                ax.text(x=x, y=y,s=string,fontsize=8,color='#800026')
                
        # remove axis labels if row is not the last row
        if row < len(obs_and_gcms)-1:
            axes[row,0].set_xticks([])
            axes[row,1].set_xticks([])
            axes[row,0].set_xticklabels([])
            axes[row,1].set_xticklabels([])
            axes[row,0].set_xlabel('')
            axes[row,1].set_xlabel('')
    
    plot_title = 'Fourier transform for %s (%s) -- %s vs %s data' % (get_variable_longname(var), location_name, name_sim_prefix, name_ref)
    x = plt.suptitle(plot_title,fontsize=12)

    if fn_plot is not None:
        create_containing_folder(fn_plot)
        fig.savefig(fn_plot, dpi=300)


# 10) Fourier transform #################################################################
# This plot plots the frequency on the x-axis (instead of the wavelength).
def plot_fourier_transform_frequencies(dataframe, location_name, var, name_sim_prefix, name_ref, timestep='daily',
                           n_top_frequencies=4, fn_plot=None):
    # adapted from: https://plot.ly/matplotlib/fft/
    
    obs_and_gcms = dataframe['type'].unique()
    
    fig, axes = plt.subplots(len(obs_and_gcms), 2, figsize=(15,2.5*len(obs_and_gcms)))
    
    # plot in rows: "type", i.e. AWAP, GCM1, GCM2, etc.
    # plot in columns: left colums - time series, right column - fourier transform
    
    if timestep == 'monthly':
        # calculate monthly from daily
        dataframe = dataframe.set_index('time')
        dataframe = dataframe.groupby(['type', 'lat', 'lon']).resample('1MS')[var].mean()
        dataframe = dataframe.reset_index()
            
    for row in range(len(obs_and_gcms)):
        
        temp = dataframe.loc[dataframe['type'] == obs_and_gcms[row]]

        if timestep == 'daily':
            
            time_length = (temp['time'].max() - temp['time'].min()).days + 1 # in days
            # prepare the frequencies
            frequencies = np.arange(int(time_length / 2)) # only first half, as 2nd half is duplicated in fft output

        elif timestep == 'monthly':
            
            average_days_in_a_month = 30.4375
            # in months; +1 is because the last month finishes on the 1st
            time_length = int(np.round((temp['time'].max() - temp['time'].min()).days  / average_days_in_a_month + 1)) # in months
            
            # prepare the frequencies
            frequencies = np.arange(int(time_length / 2)) # only first half, as 2nd half is duplicated in fft output
            
            
        ts = temp[var]
        time = temp['time']
        
#         # testing
#         time = temp['time']
#         ts = np.array([200 * np.sin(2*np.pi*x/12) for x in range(time_length)])

        # calculate the fourier transform
        fourier_transform = np.fft.fft(ts) # fft computing
        fourier_transform = abs(fourier_transform) # absolute values
        fourier_transform = fourier_transform[np.arange(len(frequencies))]
    
        # remove those wavelengths that are longer than half the time series       
        selection = frequencies > 2
        frequencies = frequencies[selection]
        fourier_transform = fourier_transform[selection]
        
        # calculate frequencies as per year, for plotting
        if timestep == 'daily':
            frequencies = frequencies / time_length * 365 # in years
        elif timestep == 'monthly':
            frequencies = frequencies / time_length * 12 # in years
        
        # 1) plot time series
        ax = axes[row,0]
        ax.plot(temp['time'], ts, '#045a8d', linewidth=0.3)
        ax.set_xlabel('Time')
        ax.set_ylabel(get_variable_longname(var))
        ax.set_ylim(0,temp[var].max()*1.1)
        ax.set_title('Time series: %s' % obs_and_gcms[row].upper())

        # 2) plot fourier transform
        ax = axes[row,1]
        ax.set_ylim(0,abs(fourier_transform).max()*1.1)
        ax.set_ylabel('Fourier transform')

        ax.plot(frequencies,fourier_transform,'#800026',linewidth=0.3) # plotting the spectrum
        ax.set_xlabel('Frequency (year-1)')
        ax.set_title('Fourier diagram: %s' % obs_and_gcms[row].upper())
         
        # add top frequencies to the diagram, if applicable
        if n_top_frequencies > 0:           
            
            top_freq = sorted(fourier_transform, reverse=True)[0:n_top_frequencies]   
            top_freq_idx = []
            for x in top_freq:
                top_freq_idx = top_freq_idx + list(np.where(fourier_transform == x)[0])
            
            # highlight top frequencies using dot points
            ax.scatter(frequencies[top_freq_idx], fourier_transform[top_freq_idx], color='#800026', s=10)
            
            for i in range(n_top_frequencies):
                
                if i == 0:
                    x = frequencies.max()*1.06 # outside of the plot
                    y = top_freq[0]
                    ax.text(x=x, y=y,s='Top frequencies:',fontsize=8,color='#800026')
                    
                # prepare x, y locations of the text
                x = frequencies.max()*1.06 # outside of the plot
                y = top_freq[0] * (1/(n_top_frequencies+1) * (n_top_frequencies-i)) # decreasing with increasing i
                string = '- %s / year' % round(frequencies[top_freq_idx[i]],2)
                ax.text(x=x, y=y,s=string,fontsize=8,color='#800026')
                
        # remove axis labels if row is not the last row
        if row < len(obs_and_gcms)-1:
            axes[row,0].set_xticks([])
            axes[row,1].set_xticks([])
            axes[row,0].set_xticklabels([])
            axes[row,1].set_xticklabels([])
            axes[row,0].set_xlabel('')
            axes[row,1].set_xlabel('')
    
    plot_title = 'Fourier transform for %s (%s) -- %s vs %s data' % (get_variable_longname(var), location_name, name_sim_prefix.upper(), name_ref.upper())
    x = plt.suptitle(plot_title,fontsize=12)

    if fn_plot is not None:
        create_containing_folder(fn_plot)
        fig.savefig(fn_plot, dpi=300)


# 10) Fourier transform #################################################################
# Wrapper function to call the fourier transform plotting function, either using frequencies or wavelengths as x-axis.
def plot_fourier_transform(dataframe, location_name, var, name_sim_prefix, name_ref, timestep='daily',
                           n_top_frequencies=4, fn_plot=None, x_axis='frequencies'):
    if x_axis == 'frequencies':
        plot_fourier_transform_frequencies(dataframe, location_name, var, name_sim_prefix, name_ref, timestep,
                           n_top_frequencies, fn_plot)
    elif x_axis == 'wavelengths':
        plot_fourier_transform_wavelengths(dataframe, location_name, var, name_sim_prefix, name_ref, timestep,
                           n_top_frequencies, fn_plot)
