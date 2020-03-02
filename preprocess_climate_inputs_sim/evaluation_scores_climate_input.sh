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

# Set bash script to fail on first error
set -e
# Trap each command and log it to output (except ECHO)
trap '! [[ "$BASH_COMMAND" =~ (echo|for|\[) ]] && \
cmd=`eval echo "$BASH_COMMAND" 2>/dev/null` && echo [$(date "+%Y%m%d %H:%M:%S")] $cmd' DEBUG


# load required netcdf modules
module load netcdf/4.7.1 cdo/1.7.2 nco/4.7.7


# read in variable
var_sim=$1 # name of climate variable in dataset to evaluate
var_ref=$2 # name of climate variable in reference dataset
ref_start_year=$3
ref_end_year=$4
path_climate_data=$5 # climate data to evaluate
path_statistics_ref=$6 # Statistics of reference dataset
out_path_sim=$7
timescales=$8
statistics=${9}
name_sim=${10} # name for the climate data to evaluate, used to create file names
name_ref=${11} # name for the historical reference, used to create file names
unit_conv_factor=${12} # multiply the simulation unit with this conversion factor to get unit of reference dataset
unit_conv_add=${13} # add this number to the simulation unit to get unit of reference dataset

echo "##### Script Ran With" ${var_sim} ${var_ref} ${ref_start_year} ${ref_end_year} ${path_climate_data} ${path_statistics_ref} ${out_path_sim} ${timescales} ${statistics} ${name_sim} ${name_ref} ${unit_conv_factor} ${unit_conv_add}


# create bias path
bias_path=${out_path_sim}/bias_${name_ref}
echo "##### Creating output folder for bias data" ${bias_path}
mkdir -p ${bias_path}
                
for timescale in ${timescales}; do
    for statistic in ${statistics}; do
        echo '##### Statistic to calculate:' ${timescale} ${statistic}
        
        sim_ref=${name_sim}
        var=${var_sim}
        out_path=${out_path_sim}

        echo '##### Processing' ${sim_ref}

        fn_merged=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_merged.nc
        if [ -f ${fn_merged} ]; then
            echo '##### Merged File already exists. Skipping' ${fn_merged}
        else
            echo '##### Creating Merged File' ${fn_merged}

            # prepare paths for annual statistics
            statistics_path=${out_path}/annual_statistics
            mkdir -p ${statistics_path}

            # prepare temp folder
            temp_path=${out_path}/temp_${var}_${timescale}${statistic}_${sim_ref}
            mkdir -p ${temp_path}

            # Calculate statistic for each year separately (less memory use)
            echo '##### Calculate values for each year separately (less memory use)'
            for (( year=ref_start_year;year<=ref_end_year;year++ )); do
                echo '- ' ${year}
                
                fn_year=${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                if [ -f ${fn_year} ]; then
                    echo '##### Statistic file already exists. Skipping' ${fn_year}
                else
                    echo '##### Creating statistic file' ${fn_year}
                    input_path=${path_climate_data}
                    input_file=${input_path}/${var}*${year}.nc
                    
                    ##########################################################
                    
                    # if calculating seasonal aggregates, read in year before as well (for DJF season) and 
                    # select 01/12/year-1 up to 30/11/year to calculate the seasonal statistics
                    if [ ${timescale} == 'seas' ]; then
                        echo '##### Read in previous year for seasonal statistic'
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
                        echo '##### Calculate Statistic' ${statistic}
                        cdo_fun=${timescale}${statistic}
                        cdo ${cdo_fun} ${input_file} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                    else # percentiles
                        echo '##### Calculate Percentile Statistic' ${statistic}
                        pctl=${statistic:4:2}
                        cdo_fun=${timescale}pctl,${pctl}
                        cdo -L ${cdo_fun} ${input_file} -${timescale}min ${input_file} -${timescale}max ${input_file} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                    fi # percentile?
                    wait
                    
                    ##########################################################
                    
                    # UNIT CONVERSIONS
                    if [ ${unit_conv_factor} != '1' ]; then
                        echo '##### Applying Unit Conversion Factor' ${unit_conv_factor}
                        cdo mulc,${unit_conv_factor} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc
                        wait
                        mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                        wait
                    fi
                    
                    if [ ${unit_conv_add} != '0' ]; then
                        echo '##### Applying Unit Conversion Offset' ${unit_conv_add}
                        cdo addc,${unit_conv_add} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc
                        wait
                        mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}_unit.nc ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                        wait
                    fi
                    mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${fn_year}
                fi # fn_year exists?
            done # for each year

            # Merge all years
            echo '##### Merge all years'
            cdo mergetime ${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_*.nc ${temp_path}/${sim_ref}_merged.nc
            wait
            cdo selyear,${ref_start_year}/${ref_end_year} ${temp_path}/${sim_ref}_merged.nc ${fn_merged}
            wait
            rm -r ${temp_path}
        fi # fn_merge exists?

        # Calculate overall statistics from annual statistics
        # - for annual: calculate overall mean/min/max from annual means: timmean
        # - for seasonal, monthly: calculate mean/min/max for each season/month: yseasmean, ymonmean
        
        # Prepare file names
        fn_mean=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
        fn_std=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc

        # Calculate mean and standard deviation over reference period
        echo '##### Calculate mean and standard deviation over reference period'
        if [ ${timescale} == 'year' ]; then
            cdo_fun=tim
        else
            cdo_fun=y${timescale}
        fi
        cdo ${cdo_fun}mean ${fn_merged} ${fn_mean}
        cdo ${cdo_fun}std ${fn_merged} ${fn_std}
        wait

        # Calculate biases
        # if no simulation or reference dataset was given, skip it
        if [ ${name_ref} != "NONE" ] && [ ${name_ref} != ""  ]; then
            echo '##### Calculate biases'

            temp_path=${out_path_sim}/temp_bias_${var_sim}_${timescale}${statistic}_${name_sim}
            mkdir -p ${temp_path}

            sim_mean=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            sim_std=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
            ref_mean=${path_statistics_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            ref_std=${path_statistics_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
            bias_abs=${bias_path}/bias_abs_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_rel=${bias_path}/bias_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_std=${bias_path}/bias_std_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            
            # subtract reference from simulation and then multiply with -1, so that all information from reference is retained (units, long_name etc.)
            cdo -L mulc,-1 -sub ${ref_mean} ${sim_mean} ${bias_abs}
            wait
            cdo div ${bias_abs} ${ref_mean} ${bias_rel}

            cdo -L mulc,-1 -sub ${ref_std} ${sim_std} ${temp_path}/bias_std.nc
            wait
            cdo div ${temp_path}/bias_std.nc ${ref_std} ${bias_std}

            wait
            rm -r ${temp_path}
        fi
    done
done

echo '##### Completed'
