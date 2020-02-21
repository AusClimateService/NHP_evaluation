# This script calculates evaluation metrics at different time scales from an AWRA simulation
# relative to a reference AWRA simulation. The files are subsequently used for
# plotting verification metrics.
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
# Date: 07/03/2019

# load required netcdf modules
module load netcdf/4.7.1 cdo/1.7.2 nco/4.7.7


# read in variable
var=$1
ref_start_year=$2
ref_end_year=$3
path_awra_run=$4 # simulation to evaluate
path_awra_ref=$5 # reference simulation
out_path=$6
timescales=$7
statistics=$8
name_sim=$9 # name for the simulation, used to create file names
name_ref=${10} # name for the historical reference, used to create file names

echo ${var} ${ref_start_year} ${ref_end_year} ${path_awra_run} ${path_awra_ref} ${out_path} ${timescales} ${statistics} ${name_sim} ${name_ref}

#timescales="year seas mon"
#statistics="mean min max std pctl05 pctl10 pctl50 pctl90 pctl95"


# prepare output paths
statistics_path=${out_path}/annual_statistics
bias_path=${out_path}/bias
mkdir -p ${statistics_path}
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
        
        # prepare temp folder
        temp_path=${out_path}/temp_${var}_${timescale}${statistic}_${name_sim}_${name_ref}
        mkdir -p ${temp_path}
        

        for sim_ref in ${name_sim} ${name_ref}; do
        
            # if no simulation or reference dataset was given, skip it
            if [ ${sim_ref} == "NONE" ] || [ ${sim_ref} == "" ]; then
                continue;
            fi
            
            fn_merged=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_merged.nc
            
            cdo_fun=${timescale}${statistic}
            if [ ! -f ${fn_merged} ]; then
            
                # Calculate statistic for each year separately (less memory use)
                echo 'Calculate values for each year separately (less memory use)'
                for (( year=ref_start_year;year<=ref_end_year;year++ )); do
                    echo '- ' ${year}
                    
                    fn_year=${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                    
                    # if file hasn't been created before, calculate it
                    if [ ! -f ${fn_year} ]; then
                    
                        if [ ${sim_ref} == ${name_sim} ]; then
                            input_path=${path_awra_run}
                        elif [ ${sim_ref} == ${name_ref} ]; then
                            input_path=${path_awra_ref}
                        fi
                        input_file=${input_path}/${var}_${year}.nc
                        
                        if [ ${timescale} != 'seas' ]; then
                            # if variable is "sm" and sm file not there, then calculate sm from s0 and ss first
                            if [ ${var} == 'sm' ] && [ ! -f ${input_path}/${var}_${year}.nc ]; then
                                cdo add ${input_path}/s0_${year}.nc ${input_path}/ss_${year}.nc ${temp_path}/${sim_ref}_sm_${year}.nc
                                ncrename -v .s0,sm ${temp_path}/${sim_ref}_sm_${year}.nc
                                ncatted -a long_name,sm,o,c,sm ${temp_path}/${sim_ref}_sm_${year}.nc
                                ncatted -a standard_name,sm,o,c,sm ${temp_path}/${sim_ref}_sm_${year}.nc
                                input_file=${temp_path}/${sim_ref}_${var}_${year}.nc
                                wait
                            fi
                        
                        # if calculating seasonal aggregates, read in year before as well (for DJF season) and 
                        # select 01/01/year-1 up to 30/11/year to calculate the seasonal statistics
                        elif [ ${timescale} == 'seas' ]; then
                        
                            let year_before=${year}-1
                            
                            if [ ${var} != 'sm' ]; then
                                cdo mergetime ${input_path}/${var}_${year_before}.nc ${input_path}/${var}_${year}.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                                wait
                                
                                cdo seldate,"${year_before}-12-01","${year}-11-30" ${temp_path}/${sim_ref}_${var}_${year}.nc ${temp_path}/${sim_ref}_${var}_${year}_2.nc
                                wait
                                mv ${temp_path}/${sim_ref}_${var}_${year}_2.nc ${temp_path}/${sim_ref}_${var}_${year}.nc
                                input_file=${temp_path}/${sim_ref}_${var}_${year}.nc
                                
                            elif [ ${var} == 'sm' ]; then
                                # add s0 and ss together
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
                             fi
                        fi
                        wait
                        
                        echo ${input_file}
                        
                        # start calculation
                        if [ ${statistic:0:4} != 'pctl' ]; then # not a percentile
                            # statistics for simulation and reference
                            cdo ${cdo_fun} ${input_file} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                        else # percentiles
                            pctl=${statistic:4:2}
                            cdo_fun=${timescale}pctl
                            cdo -L ${timescale}pctl,${pctl} ${input_file} -${timescale}min ${input_file} -${timescale}max ${input_file} ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                        fi # percentile?
                        wait
                        
                        
                        mv ${temp_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc ${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_${year}.nc
                        wait
                    fi # fn_year exists?
                done

                # Merge all years
                echo 'Merge all years'
                cdo mergetime ${statistics_path}/${sim_ref}_${var}_${timescale}${statistic}_*.nc ${temp_path}/${sim_ref}_merged.nc
                wait
                cdo selyear,${ref_start_year}/${ref_end_year} ${temp_path}/${sim_ref}_merged.nc ${fn_merged}
                rm ${temp_path}/${sim_ref}_merged.nc
                wait
                # The following isn't necessary anymore if everything worked fine before, but somehow it didn't
                if [ ${var} == 'sm' ]; then
                    ncrename -v .s0,sm ${fn_merged}
                    ncatted -a long_name,'sm',o,c,sm ${fn_merged}
                    ncatted -a standard_name,'sm',o,c,sm ${fn_merged}
                fi
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
         
        # Calculate biases
        
        # if no simulation or reference dataset was given, skip it
        if [ ${name_ref} != "NONE" ] && [ ${name_ref} != ""  ]; then
            
            echo 'Calculate biases'
            sim_mean=${out_path}/${name_sim}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            ref_mean=${out_path}/${name_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            sim_std=${out_path}/${name_sim}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
            ref_std=${out_path}/${name_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
            bias_abs=${bias_path}/bias_abs_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_rel=${bias_path}/bias_rel_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_std=${bias_path}/bias_std_rel_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            
            cdo sub ${sim_mean} ${ref_mean} ${bias_abs}
            cdo div ${bias_abs} ${ref_mean} ${bias_rel}
            cdo sub ${sim_std} ${ref_std} ${temp_path}/bias_std.nc
            cdo div ${temp_path}/bias_std.nc ${ref_std} ${bias_std}
            
        fi
        
        rm -r ${temp_path}
    done
done




################################################################################
# 2) Zonal means
################################################################################

# This step calculates the latitudinal means - overall, for each season and month.

echo '2) Zonal means'
 
#timescales="year seas mon"
#statistics="mean min max std pctl05 pctl10 pctl50 pctl90 pctl95"

for timescale in ${timescales}; do
    for statistic in ${statistics}; do
    
        echo 'Statistic: ' ${timescale} ${statistic}
        echo '- calculate zonal means'
        
        # prepare temp folder
        temp_path=${out_path}/temp_${timescale}${statistic}
        mkdir -p ${temp_path}
        
        for sim_ref in ${name_sim} ${name_ref}; do
        
            # if no simulation or reference dataset was given, skip it
            if [ ${sim_ref} == "NONE" ] || [ ${sim_ref} == "" ]; then
                continue;
            fi

            # File names for the gridded data
            fn_mean=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_mean.nc
            fn_std=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_std.nc
            
            # File name for the output data
            fn_mean_zonal=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_zonal_mean.nc
            fn_std_zonal=${out_path}/${sim_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_zonal_std.nc
            
            # Calculate the zonal mean
            cdo zonmean ${fn_mean} ${fn_mean_zonal}
            cdo zonmean ${fn_std} ${fn_std_zonal}
        done
        
        # Calculate the bias in zonal means
        
        # if no simulation or reference dataset was given, skip it
        if [ ${name_ref} != "NONE" ] && [ ${name_ref} != ""  ]; then
        
            echo '- calculate the bias in zonal means'
            sim_mean=${out_path}/${name_sim}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_zonal_mean.nc
            ref_mean=${out_path}/${name_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_zonal_mean.nc
            sim_std=${out_path}/${name_sim}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_zonal_std.nc
            ref_std=${out_path}/${name_ref}_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}_zonal_std.nc
            bias_abs=${bias_path}/bias_abs_zonal_mean_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_rel=${bias_path}/bias_rel_zonal_mean_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            bias_std=${bias_path}/bias_std_rel_zonal_mean_${var}_${timescale}${statistic}_${ref_start_year}_${ref_end_year}.nc
            
            # subtract reference from simulation and then multiply with -1, so that all information from reference is retained (units, long_name etc.)
            cdo -L mulc,-1 -sub ${ref_mean} ${sim_mean} ${bias_abs}
            cdo div ${bias_abs} ${ref_mean} ${bias_rel}
            cdo -L mulc,-1 -sub ${ref_std} ${sim_std} ${temp_path}/bias_std.nc
            cdo div ${temp_path}/bias_std.nc ${ref_std} ${bias_std}
            
        fi
        
        rm -r ${temp_path}
    done
done


