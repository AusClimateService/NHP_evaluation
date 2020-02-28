#!/bin/bash

# rain_day temp_max_day temp_min_day wind solar_exposure_day
VARIABLES=(rain_day temp_max_day temp_min_day wind solar_exposure_day)

#year seas mon
TIMESCALES=(year seas mon)

#mean min max std pctl05 pctl10 pctl25 pctl50 pctl75 pctl90 pctl95
STATISTICS=(mean min max std pctl05 pctl10 pctl25 pctl50 pctl75 pctl90 pctl95)




PBS_JOBS_FOLDER=PBS_jobs
PBS_JOB_TEMPLATE_FILE=job_evaluation_scores_climate_input_awap_TEMPLATE.pbs

# Create output PBS Jobs folder if it doesn't exist
mkdir -p ${PBS_JOBS_FOLDER}

for var in ${VARIABLES[@]}; do
    for timescale in ${TIMESCALES[@]}; do
        for statistic in ${STATISTICS[@]}; do
            job_file_base_name=job_evaluation_scores_climate_input_awap_${var}_${timescale}_${statistic}
            job_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.pbs
            job_name=awap_inputs_${gcm}_${var}_${timescale}_${statistic}_evaluation_scores
            job_output_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.out
            job_error_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.error
            
            # Create job file from template
            echo "Creating Job ${job_file}"
            cp ${PBS_JOB_TEMPLATE_FILE} ${job_file}
            sed -i "s|xxVARxx|${var}|g" ${job_file}
            sed -i "s|xxTIMESCALExx|${timescale}|g" ${job_file}
            sed -i "s|xxSTATISTICxx|${statistic}|g" ${job_file}
            sed -i "s|xxJOB_NAMExx|${job_name}|g" ${job_file}
            sed -i "s|xxJOB_OUTPUT_FILExx|${job_output_file}|g" ${job_file}
            sed -i "s|xxJOB_ERROR_FILExx|${job_error_file}|g" ${job_file}
            wait
            
            # submit job
            echo "Submitting Job ${job_file}"
            qsub ${job_file}
            wait
        done
    done
done
