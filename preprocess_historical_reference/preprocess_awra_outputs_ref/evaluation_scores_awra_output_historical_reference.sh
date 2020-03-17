# This script calculates one evaluation metric at one time scale from AWRA data for the
# historical reference data (AWRA v6.1). The files are subsequently used for
# plotting verification metrics.
#
# The structure of the script assumes the following file name pattern:
# VARNAME_YEAR.nc (for example: etot_2001.nc) - one file for each year and variable.
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
var_ref=$1
ref_start_year=$2
ref_end_year=$3
path_awra_ref=$4 # reference simulation
out_path_ref=$5
timescale=$6
statistic=$7
name_ref=$8 # name for the historical reference, used to create file names
temp_path_ref=$9 # path for temporary files (usually the same as the output path, but on scratch)

echo '##### Script ran with' ${var} ${ref_start_year} ${ref_end_year} ${path_awra_ref} ${out_path} ${timescale} ${statistic} ${name_ref} ${temp_path_ref}

echo '##### Statistic to calculate:' ${timescale} ${statistic}

sim_ref=${name_ref}
var=${var_ref}
out_path=${out_path_ref}

# Prepare temp foler
temp_path=${temp_path_ref}/temp_${var}_${timescale}${statistic}_${sim_ref}
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
            
            input_path=${path_awra_ref}
            input_file=${input_path}/${var}_${year}.nc
            
            ##########################################################
            
            # if calculating seasonal aggregates, read in year before as well (for DJF season) and 
            # select 01/12/year-1 up to 30/11/year to calculate the seasonal statistics
            if [ ${timescale} == 'seas' ]; then

                echo '##### Read in previous year for seasonal statistic'
                let year_before=${year}-1
                
                # if it is sm, then add s0 and ss first
                if [ ${var} == 'sm' ]; then

                    echo '##### Add s0 and ss first, then combine both years'
                    cdo mergetime ${input_path}/s0_${year_before}.nc ${input_path}/s0_${year}.nc ${temp_path}/${sim_ref}_s0_${year}.nc
                    wait
                    cdo mergetime ${input_path}/ss_${year_before}.nc ${input_path}/ss_${year}.nc ${temp_path}/${sim_ref}_ss_${year}.nc
                    wait
                    cdo add ${temp_path}/${sim_ref}_s0_${year}.nc ${temp_path}/${sim_ref}_ss_${year}.nc ${temp_path}/${sim_ref}_sm_${year}.nc
                    wait
                    cdo seldate,"${year_before}-12-01","${year}-11-30" ${temp_path}/${sim_ref}_sm_${year}.nc ${temp_path}/${sim_ref}_sm_${year}_2.nc
                    wait
                    mv ${temp_path}/${sim_ref}_sm_${year}_2.nc ${temp_path}/${sim_ref}_sm_${year}.nc
                    input_file=${temp_path}/${sim_ref}_${var}_${year}.nc

                elif [ ${var} != 'sm' ]; then

                    cdo mergetime ${input_path}/${var}_${year_before}.nc ${input_path}/${var}_${year}.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                    wait
                    cdo seldate,"${year_before}-12-01","${year}-11-30" ${temp_path}/${sim_ref}_${var}_${year}.nc ${temp_path}/${sim_ref}_${var}_${year}_2.nc
                    wait
                    mv ${temp_path}/${sim_ref}_${var}_${year}_2.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                    input_file=${temp_path}/${sim_ref}_${var}_${year}.nc

                 fi

            elif [ ${timescale} != 'seas' ]; then

                # if variable is "sm" and sm file not there, then calculate sm from s0 and ss first
                if [ ${var} == 'sm' ] && [ ! -f ${input_path}/${var}_${year}.nc ]; then

                    cdo add ${input_path}/s0_${year}.nc ${input_path}/ss_${year}.nc ${temp_path}/${sim_ref}_sm_${year}.nc
                    wait
                    ncrename -v s0,sm ${temp_path}/${sim_ref}_sm_${year}.nc
                    wait
                    ncatted -a long_name,sm,o,c,sm ${temp_path}/${sim_ref}_sm_${year}.nc
                    wait
                    ncatted -a standard_name,sm,o,c,sm ${temp_path}/${sim_ref}_sm_${year}.nc
                    input_file=${temp_path}/${sim_ref}_${var}_${year}.nc
                    wait

                fi
            fi
            wait
            
            echo ${input_file}
            
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

            mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${fn_year}
        fi # fn_year exists?
    done # for eacg year

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

    # The following isn't necessary anymore if everything worked fine before, but somehow it didn't always
    if [ ${var} == 'sm' ]; then
        ncrename -v .s0,sm ${fn_merged}
        ncatted -a long_name,'sm',o,c,sm ${fn_merged}
        ncatted -a standard_name,'sm',o,c,sm ${fn_merged}
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
    echo 'Calculate mean over reference period'
    cdo ${cdo_fun}mean ${fn_merged} ${fn_mean}
fi

if [ ! -f ${fn_std} ]; then
    echo 'Calculate standard deviation over reference period'
    cdo ${cdo_fun}std ${fn_merged} ${fn_std}
fi

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

# Remove the temporary path
rm -r ${temp_path}

echo '##### Completed'
