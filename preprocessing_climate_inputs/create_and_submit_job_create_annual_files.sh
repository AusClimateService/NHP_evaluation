#!/bin/bash

# pr tasmin tasmax sfcWind rsds
VARIABLES=(pr tasmin taxmax sfcWind rsds)

# ACCESS1-0 CNRM-CM5 GFDL-ESM2M MIROC5
GCMS=(ACCESS1-0 CNRM-CM5 GFDL-ESM2M MIROC5)




PBS_JOBS_FOLDER=PBS_jobs
PBS_JOB_TEMPLATE_FILE=job_create_annual_files_TEMPLATE.pbs

# Create output PBS Jobs folder if it doesn't exist
mkdir -p ${PBS_JOBS_FOLDER}

for var in ${VARIABLES[@]}; do
    for gcm in ${GCMS[@]}; do
        job_file_base_name=job_create_annual_files_ISIMIP_awap_${var}_${gcm}
        job_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.pbs
        job_name=${gcm}_${var}_annual_files
        job_output_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.out
        job_error_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.error

        # Create job file from template
        echo "Creating Job ${job_file}"
        cp ${PBS_JOB_TEMPLATE_FILE} ${job_file}
        sed -i "s|xxVARxx|${var}|g" ${job_file}
        sed -i "s|xxMODELxx|${gcm}|g" ${job_file}
        sed -i "s|xxJOB_NAMExx|${job_name}|g" ${job_file}
        sed -i "s|xxJOB_OUTPUT_FILExx|${job_output_file}|g" ${job_file}
        sed -i "s|xxJOB_ERROR_FILExx|${job_error_file}|g" ${job_file}
        
        # submit job
        echo "Submitting Job ${job_file}"
        qsub ${job_file}
        wait
    done
done
