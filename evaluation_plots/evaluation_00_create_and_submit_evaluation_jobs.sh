# This script creates one PBS job script for every python script and submits the job.
# All scripts use the same config file ("config.json") that is in the folder.
# TODO: Probably better to pass the location of the config file as an argument to the python function
# (at the moment, it assumes that it is in the same folder as the python functions.)

# Author: Elisabeth Vogel, elisabeth.vogel@bom.gov.au
# Date: 19/09/2019


PBS_JOBS_FOLDER=PBS_jobs
PBS_JOB_TEMPLATE_FILE=evaluation_jobs_TEMPLATE.pbs

# create a folder for the PBS jobs
mkdir -p ${PBS_JOBS_FOLDER}


create_job_and_submit() {
    local script_to_run=$1
    local num_cpus=$2
    local memory_required=$3

    local job_file_basename=job_${script_to_run%.py}
    local job_file=${PBS_JOBS_FOLDER}/${job_file_basename}.pbs
    local job_output_file=${PBS_JOBS_FOLDER}/${job_file_basename}.out
    local job_error_file=${PBS_JOBS_FOLDER}/${job_file_basename}.error

    echo "Creating Job ${job_file}"
    cp ${PBS_JOB_TEMPLATE_FILE} ${job_file}
    sed -i "s|xxSCRIPT_FILExx|${script_to_run}|g" ${job_file}
    sed -i "s|xxJOB_NAMExx|${script_to_run}|g" ${job_file}
    sed -i "s|xxNUM_CPUSxx|${num_cpus}|g" ${job_file}
    sed -i "s|xxMEMORYxx|${memory_required}|g" ${job_file}
    sed -i "s|xxJOB_OUTPUT_FILExx|${job_output_file}|g" ${job_file}
    sed -i "s|xxJOB_ERROR_FILExx|${job_error_file}|g" ${job_file}

    echo "Submitting Job ${job_file}"
    qsub ${job_file}
    wait
}



# 1
cpus=4
memory=16gb
python_script='evaluation_01a_bias_maps.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 2
cpus=4
memory=16gb
python_script='evaluation_01b_bias_lag1_correlation.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 3
cpus=4
memory=16gb
python_script='evaluation_01c_bias_trend.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 4
cpus=4
memory=8gb
python_script='evaluation_02_climatologies.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 5
cpus=4
memory=32gb
python_script='evaluation_03a_PDFs_spatial_variability.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 6
cpus=4
memory=32gb
python_script='evaluation_03b_CDFs_spatial_variability.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 7
cpus=4
memory=16gb
python_script='evaluation_04_spatial_correlation.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 8
cpus=4
memory=8gb
python_script='evaluation_05a_PDFs_temporal_variability.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 9
cpus=4
memory=8gb
python_script='evaluation_05b_CDFs_temporal_variability.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 10
cpus=4
memory=8gb
python_script='evaluation_06a_point_PDFs.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 11
cpus=4
memory=8gb
python_script='evaluation_06b_point_CDFs.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}

# 12
cpus=4
memory=8gb
python_script='evaluation_07_point_Fourier_diagrams.py'
create_job_and_submit "${python_script}" ${cpus} ${memory}
