# This script calculates one evaluation metric at one time scale from climate input data for the
# historical reference data (AWAP). The files are subsequently used for
# plotting verification metrics.
#
# The structure of the script assumes the following file name pattern:
# VARNAME_YEAR.nc (for example: pr_2001.nc) - one file for each year and variable.
# Other folder and file name patterns can be implemented manually in the code.
#
#
# The time scale can be: annual (year), seasonal (seas), or monthly (mon).
# The statistics can be one of the following:
# - mean: mean
# - sum: sum
# - min: min
# - max: max
# - std: std
# - percentiles: pctl05, pctl10, pctl50, pctl90, pctl95
#
# The steps of the script are:
# 1) Calculate the statistics (e.g. monthly maxima) for each year separately.
# 2) Merge all years together into one file to produce an aggregated time series (e.g. 30 years of monthly maxima).
# 3) Calculate the overall mean climatology, e.g. the 30-year climatology of monthly maxima.
# 4) If the statistic is sum or mean, also calculate the lag-1 auto correlation from the 30-years time series.
# 5) Calculate the biases relative to the reference dataset.

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
path_statistics_ref=$6 # output path of the statistics of reference dataset (previously calculated)
out_path_sim=$7 # output path for the statistics of the dataset to evaluate
timescale=$8
statistic=$9
name_sim=${10} # name for the climate data to evaluate, used to create file names
name_ref=${11} # name for the historical reference, used to create file names
unit_conv_factor=${12} # multiply the simulation unit with this conversion factor to get unit of reference dataset
unit_conv_add=${13} # add this number to the simulation unit to get unit of reference dataset
temp_path=${14} # path for temporary files (usually the same as the output path, but on scratch)

echo "##### Script Ran With" ${var_sim} ${var_ref} ${ref_start_year} ${ref_end_year} ${path_climate_data} ${path_statistics_ref} ${out_path_sim} ${timescale} ${statistic} ${name_sim} ${name_ref} ${unit_conv_factor} ${unit_conv_add} ${temp_path}

echo '##### Statistic to calculate:' ${timescale} ${statistic}

sim_ref=${name_sim}
var=${var_sim}
out_path=${out_path_sim}

# Prepare temp folder
temp_path=${temp_path}/temp_${var}_${timescale}${statistic}_${sim_ref}
mkdir -p ${temp_path}

# Create the aggregated time series (e.g. monthly, seasonal, annual)
fn_merged=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_merged.nc
if [ -f ${fn_merged} ]; then
    echo '##### Merged File already exists. Skipping' ${fn_merged}
else
    echo '##### Creating Merged File' ${fn_merged}

    # Prepare paths for annual statistics - helps to restart a script if only one year
    # failed writing out properly. The annual files can be deleted manually, when they are not 
    # needed anymore.
    statistics_path=${out_path}/annual_statistics
    mkdir -p ${statistics_path}

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
            input_file=${input_path}/${var}*historical*.nc # -> only one file

            # create annual file first (as ISIMIP data is saved as all years in one)
            if [ ${timescale} != 'seas' ]; then
                
                cdo selyear,${year} ${input_file} ${temp_path}/${sim_ref}_${var}_${year}.nc
                wait
                # remove lat_bounds, lon_bounds - these have an extent of zero at the moment, and this results in problems for remapping in CDO
                ncks -C -O -x -v lat_bnds,lon_bnds ${temp_path}/${sim_ref}_${var}_${year}.nc ${temp_path}/${sim_ref}_${var}_${year}_2.nc
                wait
                mv ${temp_path}/${sim_ref}_${var}_${year}_2.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                wait
            
            ##########################################################
            
            # if calculating seasonal aggregates, read in year before as well (for DJF season) and 
            # select 01/01/year-1 up to 30/11/year to calculate the seasonal statistics
            elif [ ${timescale} == 'seas' ]; then
                let year_before=${year}-1
                cdo selyear,${year_before}/${year} ${input_file} ${temp_path}/${sim_ref}_${var}_${year}.nc
                wait
                cdo seldate,"${year_before}-12-01","${year}-11-30" ${temp_path}/${sim_ref}_${var}_${year}.nc ${temp_path}/${sim_ref}_${var}_${year}_2.nc
                wait
                # remove lat_bounds, lon_bounds
                ncks -C -O -x -v lat_bnds,lon_bnds ${temp_path}/${sim_ref}_${var}_${year}_2.nc ${temp_path}/${sim_ref}_${var}_${year}_3.nc
                wait
                mv ${temp_path}/${sim_ref}_${var}_${year}_3.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                wait
            fi

            input_file=${temp_path}/${sim_ref}_${var}_${year}.nc

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

    # Check all years have now been prepared
    n_files=`find ${statistics_path} -type f -name "${sim_ref}_${var}_${timescale}${statistic}_*.nc" -print | wc -l`
    let "n_years = ${ref_end_year} - ${ref_start_year} + 1"

    if (( ${n_files} < ${n_years} )); then
        echo '##### Not all files have been prepared. Skip this calculation.'
        break
    else
        echo '##### Merge all years'
        cdo mergetime ${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_*.nc ${temp_path}/${sim_ref}_merged.nc
        wait
        cdo selyear,${ref_start_year}/${ref_end_year} ${temp_path}/${sim_ref}_merged.nc ${fn_merged}
        wait
    fi

fi # fn_merge exists?

# Calculate overall 30-year mean and standard deviation from annual statistics
# - for annual: calculate overall mean from annual data: timmean
# - for seasonal, monthly: calculate mean for each season/month: yseasmean, ymonmean

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
if [ ! -f ${fn_mean} ]; then
    cdo ${cdo_fun}mean ${fn_merged} ${fn_mean}
fi

if [ ! -f ${fn_std} ]; then
    cdo ${cdo_fun}std ${fn_merged} ${fn_std}
fi
wait


if [ ${statistic} == 'mean' ] | [ ${statistic} == 'sum' ]; then
    echo '##### Calculate the lag-1 auto-correlation'
    # Calculate the lag-1 auto-correlation
    # - only for the mean or sum, not for the percentiles and other statistics
    # Steps:    1) create a temporary dataset where the first time step is removed
    #           2) calculate the correlation between this temporary time series and the original time series (= lag-1 correlation)

    fn_lag_corr=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_lag1corr.nc

    if [ ! -f ${fn_lag_corr} ]; then
        ntimesteps=`cdo ntime ${fn_merged}` # how many time step does the merged file have?
        cdo delete,timestep=1 ${fn_merged} ${temp_path}/${sim_ref}_shift1.nc
        cdo delete,timestep=${ntimesteps} ${fn_merged} ${temp_path}/${sim_ref}_shift2.nc # so both have the same length
        cdo timcor ${temp_path}/${sim_ref}_shift1.nc ${temp_path}/${sim_ref}_shift2.nc ${fn_lag_corr}
    fi
fi


# Calculate biases

# create bias path
bias_path=${out_path_sim}/bias_${name_ref}
echo "##### Creating output folder for bias data" ${bias_path}
mkdir -p ${bias_path}


# if no simulation or reference dataset was given, skip it
if [ ${name_ref} != ''  ] & [ ${path_statistics_ref} != '' ]; then

    ref_merged=${out_path_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_merged.nc
    ref_mean=${out_path_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
    ref_std=${out_path_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
    ref_lag1=${out_path_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_lag1corr.nc

    sim_merged=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_merged.nc
    sim_mean=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
    sim_std=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
    sim_lag1=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_lag1corr.nc

    if [ ! -f ${ref_merged} ]; then
        echo '##### Reference data not created before. Skip calculating biases.'
    else

        echo '##### Calculate biases relative to ' ${name_ref}

        echo '##### Regridding all files to ' ${name_ref} ' grid'
        cdo griddes ${ref_merged} > ${temp_path}/griddes.txt
        # regridding the merged files
        cdo remapnn,${temp_path}/griddes.txt ${sim_merged} ${sim_merged%.nc}_remapped.nc
        mv ${sim_merged%.nc}_remapped.nc ${sim_merged}
        # regridding the mean
        cdo remapnn,${temp_path}/griddes.txt ${sim_mean} ${sim_mean%.nc}_remapped.nc
        mv ${sim_mean%.nc}_remapped.nc ${sim_mean}
        # regridding the standard deviation file
        cdo remapnn,${temp_path}/griddes.txt ${sim_std} ${sim_std%.nc}_remapped.nc
        mv ${sim_std%.nc}_remapped.nc ${sim_std}

        echo '##### Calculate biases'
        bias_abs=${bias_path}/bias_abs_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
        bias_rel=${bias_path}/bias_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
        bias_std=${bias_path}/bias_std_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc

        # subtract reference from simulation and then multiply with -1, so that all information from reference is retained (units, long_name etc.)
        cdo -L mulc,-1 -sub ${ref_mean} ${sim_mean} ${bias_abs}
        cdo div ${bias_abs} ${ref_mean} ${bias_rel}
        cdo -L mulc,-1 -sub ${ref_std} ${sim_std} ${temp_path}/bias_std.nc
        cdo div ${temp_path}/bias_std.nc ${ref_std} ${bias_std}

        # regridding the lag1 auto-correlation file, if applicable
        if [ ${statistic} == 'mean' ] | [ ${statistic} == 'sum' ]; then
            cdo remapnn,${temp_path}/griddes.txt ${sim_lag1} ${sim_lag1%.nc}_remapped.nc
            mv ${sim_lag1%.nc}_remapped.nc ${sim_lag1}

            bias_lag1=${bias_path}/bias_lag1corr_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            cdo -L mulc,-1 -sub ${ref_lag1} ${sim_lag1} ${bias_lag1}
        fi

        sim_mean=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
        sim_std=${out_path_sim}/${name_sim}_${var_sim}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
        ref_mean=${path_statistics_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
        ref_std=${path_statistics_ref}/${name_ref}_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
        bias_abs=${bias_path}/bias_abs_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
        bias_rel=${bias_path}/bias_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
        bias_std=${bias_path}/bias_std_rel_${var_ref}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc

    fi 
fi

wait
rm -r ${temp_path}
echo '##### Completed'
