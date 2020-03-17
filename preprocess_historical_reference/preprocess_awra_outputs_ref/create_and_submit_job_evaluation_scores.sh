#!/bin/bash

# sm etot qtot
VARIABLES=(sm e0 etot qtot)

# ACCESS1-0 CNRM-CM5 GFDL-ESM2M MIROC5
GCMS=(ACCESS1-0 CNRM-CM5 GFDL-ESM2M MIROC5)

# year seas mon
TIMESCALES=(year seas mon)

# mean_or_sum min max std pctl05 pctl10 pctl25 pctl50 pctl75 pctl90 pctl95
STATISTICS=(mean_or_sum min max std pctl05 pctl10 pctl25 pctl50 pctl75 pctl90 pctl95)
# mean_or_sum will be replaced below by 'mean' or 'sum' depending on the variable

PBS_JOBS_FOLDER=PBS_jobs
PBS_JOB_TEMPLATE_FILE=job_evaluation_scores_awra_output_isimip_data_TEMPLATE.pbs

# Create output PBS Jobs folder if it doesn't exist
mkdir -p ${PBS_JOBS_FOLDER}

# Generate and run all jobs
for var in ${VARIABLES[@]}; do
    for gcm in ${GCMS[@]}; do
        for timescale in ${TIMESCALES[@]}; do
            for statistic in ${STATISTICS[@]}; do

                if [ ${statistic} == 'mean_or_sum' ]; then
                case ${var} in
                    qtot|e0|etot)
                        statistic=sum
                        ;;
                    sm)
                        statistic=mean
                        ;;
                esac
                fi

                job_file_base_name=job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}
                job_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.pbs
                job_name=isimip_outputs_${gcm}_${var}_${timescale}_${statistic}_evaluation_scores_awra_output
                job_output_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.out
                job_error_file=${PBS_JOBS_FOLDER}/${job_file_base_name}.error
                
                # Create job file from template
                echo "Creating Job ${job_file}"
                cp ${PBS_JOB_TEMPLATE_FILE} ${job_file}
                sed -i "s|xxVARxx|${var}|g" ${job_file}
                sed -i "s|xxGCMxx|${gcm}|g" ${job_file}
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
done
