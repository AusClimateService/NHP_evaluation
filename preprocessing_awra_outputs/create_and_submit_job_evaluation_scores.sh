#!/bin/bash

PBS_JOBS_FOLDER=PBS_jobs
PBS_JOB_TEMPLATE_FILE=job_evaluation_scores_awra_output_isimip_data_TEMPLATE.pbs


VARIABLES=(sm etot qtot)
GCMS=(GFDL-ESM2M)
TIMESCALES=(seas)
STATISTICS=(mean min max std pctl05 pctl10 pctl25 pctl50 pctl75 pctl90 pctl95)


# Create output PBS Jobs folder if it doesn't exist
mkdir -p ${PBS_JOBS_FOLDER}

# Generate all JOBS
for var in ${VARIABLES[@]}; do
    for gcm in ${GCMS[@]}; do
        for timescale in ${TIMESCALES[@]}; do
            for statistic in ${STATISTICS[@]}; do

                job_file=${PBS_JOBS_FOLDER}/job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}.pbs
                cp ${PBS_JOB_TEMPLATE_FILE} ${job_file}
                
                # replace template text in the job file
                sed -i "s/VAR/${var}/g" ${job_file}
                sed -i "s/GCM/${gcm}/g" ${job_file}
                sed -i "s/TIMESCALE/${timescale}/g" ${job_file}
                sed -i "s/STATISTIC/${statistic}/g" ${job_file}
                wait
                
                # submit job
                qsub ${job_file}
                wait
            done
        done
    done
done
