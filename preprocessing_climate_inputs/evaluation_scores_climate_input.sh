# This script calculates evaluation metrics at different time scales from climate input data
# relative to a reference climate dataset. The files are subsequently used for
# plotting verification metrics.
#
# The structure of the script assumes the following file name pattern:
# VARNAME_YEAR.nc (for example: pr_2001.nc) - one file for each year and variable
# Other folder and file name patterns can be implemented manually in the code.
#
#
# The following indicators are calculated at annual, seasonal and monthly time scale.
# The script calculates these for both datasets and the bias (absolute, relative) in both.
#
#
# Indicators and names

# Gridded statistics:
# - mean: 
# - min: min
# - max: max
# - std: std
# - quantiles: pctl05, pctl10, pctl50, pctl90, pctl95
#
#
# Zonal statistics
# - latitude mean: zonmean
# - latitude min: zonmin
# - latitude max: zonmax
# - latitude std: zonstd

# Author: Elisabeth Vogel, elisabeth.vogel@bom.gov.au
# Date: 26/03/2019

# load required netcdf modules
module load netcdf cdo nco


# read in variable
var_sim=$1 # name of climate variable in dataset to evaluate
var_ref=$2 # name of climate variable in reference dataset
ref_start_year=$3
ref_end_year=$4
path_climate_data=$5 # climate data to evaluate
path_climate_ref=$6 # reference climate data (e.g. AWAP)
out_path_sim=$7
out_path_ref=$8
timescales=$9
statistics=${10}
name_sim=${11} # name for the climate data to evaluate, used to create file names
name_ref=${12} # name for the historical reference, used to create file names
unit_conv_factor=${13} # multiply the simulation unit with this conversion factor to get unit of reference dataset
unit_conv_add=${14} # add this number to the simulation unit to get unit of reference dataset

echo ${var_sim} ${var_ref} ${ref_start_year} ${ref_end_year} ${path_climate_data} ${path_climate_ref} ${out_path} ${timescales} ${statistics} ${name_sim} ${name_ref} ${unit_conv_factor} ${unit_conv_add}

#timescales="year seas mon"
#statistics="mean min max std pctl05 pctl10 pctl50 pctl90 pctl95"

# create bias path
echo ${out_path_sim}
bias_path=${out_path_sim}/bias_${name_ref}
mkdir -p ${bias_path}
                
################################################################################
# 1) Bias in annual, seasonal and monthly statistics
################################################################################

echo '1) Bias in annual, seasonal and monthly statistics'

# Steps:
# - Calculate the annual, seasonal and monthly mean for each year
# - Calculate overall mean over reference period
# - Calculate biases (absolute and relative)

#timescales="year seas mon"
#statistics="mean min max std pctl05 pctl10 pctl50 pctl90 pctl95"

for timescale in ${timescales}; do
    for statistic in ${statistics}; do
    
        echo 'Statistic to calculate: ' ${timescale} ${statistic}
        
        for sim_ref in ${name_sim} ${name_ref}; do
        
            # if no simulation or reference dataset was given, skip it
            if [ ${sim_ref} == "NONE" ] || [ ${sim_ref} == "" ]; then
                continue;
            fi
        
            if [ ${sim_ref} == ${name_sim} ]; then
                var=${var_sim}
                out_path=${out_path_sim}
            elif [ ${sim_ref} == ${name_ref} ]; then
                var=${var_ref}
                out_path=${out_path_ref}
            fi
            
            # prepare paths for annual statistics
            statistics_path=${out_path}/annual_statistics
            mkdir -p ${statistics_path}
            
            # prepare temp folder
            temp_path=${out_path}/temp_${var_sim}_${timescale}${statistic}_${name_sim}_${name_ref}
            mkdir -p ${temp_path}
            
            fn_merged=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_merged.nc
            
            cdo_fun=${timescale}${statistic}
            if [ ! -f ${fn_merged} ]; then
            
                # Calculate statistic for each year separately (less memory use)
                echo 'Calculate values for each year separately (less memory use)'
                for (( year=ref_start_year;year<=ref_end_year;year++ )); do
                    echo '- ' ${year}                  
                    
                    fn_year=${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                    echo ${fn_year}
                    # if file hasn't been created before, calculate it
                    if [ ! -f ${fn_year} ]; then
                    
                        # ADJUST THESE ACCORDING TO THE ACTUAL FOLDER AND FILE NAME PATTERN
                        if [ ${sim_ref} == ${name_sim} ]; then
                            input_path=${path_climate_data}
                        elif [ ${sim_ref} == ${name_ref} ]; then
                            input_path=${path_climate_ref}/${var}
                        fi
                        
                        input_file=${input_path}/${var}*${year}.nc
                        
                        ##########################################################
                        
                        # if calculating seasonal aggregates, read in year before as well (for DJF season) and 
                        # select 01/01/year-1 up to 30/11/year to calculate the seasonal statistics
                        if [ ${timescale} == 'seas' ]; then
                        
                            let year_before=${year}-1
                            
                            cdo mergetime ${input_path}/${var}*${year_before}.nc ${input_path}/${var}*${year}.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                            wait
                            
                            cdo seldate,"${year_before}-12-01","${year}-11-30" ${temp_path}/${sim_ref}_${var}_${year}.nc ${temp_path}/${sim_ref}_${var}_${year}_2.nc
                            wait
                            mv ${temp_path}/${sim_ref}_${var}_${year}_2.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                            input_file=${temp_path}/${sim_ref}_${var}_${year}.nc
                            
                        fi
                                

                        ##########################################################
                        
                        # start calculation
                        
                        if [ ${statistic:0:4} != 'pctl' ]; then # not a percentile
                            # statistics for simulation and reference
                            
                            # testing
                            echo "cdo ${cdo_fun} ${input_file} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc"
                            cdo ${cdo_fun} ${input_file} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                        else # percentiles
                            pctl=${statistic:4:2}
                            cdo_fun=${timescale}pctl
                            cdo -L ${timescale}pctl,${pctl} ${input_file} -${timescale}min ${input_file} -${timescale}max ${input_file} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                        fi # percentile?
                        wait
                        
                        ##########################################################
                        
                        # UNIT CONVERSIONS
                        
                        if [ ${sim_ref} == ${name_sim} ]; then
                        
                            if [ ${unit_conv_factor} != '1' ]; then
                                cdo mulc,${unit_conv_factor} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc
                                wait
                                mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                                wait
                            fi
                            
                            if [ ${unit_conv_add} != '0' ]; then
                                cdo addc,${unit_conv_add} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc
                                wait
                                mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                                wait
                            fi
                        fi
                        mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${fn_year}
                         
                     fi # fn_year exists?
                     
                done

                # Merge all years
                echo 'Merge all years'
                cdo mergetime ${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_*.nc ${temp_path}/${sim_ref}_merged.nc
                wait
                cdo selyear,${ref_start_year}/${ref_end_year} ${temp_path}/${sim_ref}_merged.nc ${fn_merged}
                rm ${temp_path}/${sim_ref}_merged.nc
                wait
               
            fi # fn_merge exists?

            # Calculate overall statistics from annual statistics
            # - for annual: calculate overall mean/min/max from annual means: timmean
            # - for seasonal, monthly: calculate mean/min/max for each season/month: yseasmean, ymonmean
            
            if [ ${timescale} == 'year' ]; then
                cdo_fun=tim
            else
                cdo_fun=y${timescale}
            fi
            
            # Prepare file names
            fn_mean=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            fn_std=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc

            # Calculate mean and standard deviation over reference period
            echo 'Calculate mean and standard deviation over reference period'
            cdo ${cdo_fun}mean ${fn_merged} ${fn_mean}
            cdo ${cdo_fun}std ${fn_merged} ${fn_std}
            
        done # sim_ref
        var='' # empty variable, just to be safe
         
        # Calculate biases
        
        # if no simulation or reference dataset was given, skip it
        if [ ${name_ref} != "NONE" ] && [ ${name_ref} != ""  ]; then
        
            echo 'Calculate biases'
            sim_mean=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            ref_mean=${out_path_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            sim_std=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
            ref_std=${out_path_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
            bias_abs=${bias_path}/bias_abs_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_rel=${bias_path}/bias_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_std=${bias_path}/bias_std_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            
            # subtract reference from simulation and then multiply with -1, so that all information from reference is retained (units, long_name etc.)
            cdo -L mulc,-1 -sub ${ref_mean} ${sim_mean} ${bias_abs}
            cdo div ${bias_abs} ${ref_mean} ${bias_rel}
            cdo -L mulc,-1 -sub ${ref_std} ${sim_std} ${temp_path}/bias_std.nc
            cdo div ${temp_path}/bias_std.nc ${ref_std} ${bias_std}
            
        fi
        
        rm -r ${temp_path}
    done
done

