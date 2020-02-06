# This script creates one PBS job script for every python script and submits the job. All scripts use the same config file that is in the folder.
# TODO: Probably better to pass the location of the config file as an argument to the python function (at the moment, it assumes that it
# is in the same path as the python functions.)

# Author: Elisabeth Vogel, elisabeth.vogel@bom.gov.au
# Date: 19/09/2019

# find the location of this script
current_path="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
echo ${current_path}
cd ${current_path}

# create a folder for the PBS jobs
PBS_path=${current_path}/PBS_jobs
mkdir -p ${PBS_path}

# 1
cpus=4
memory=16
python_script='evaluation_01_bias_annual_and_seasonal_per_gcm.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs" # using +, to be able to replace path names
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs" # using +, to be able to replace path names
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 2
cpus=4
memory=8
python_script='evaluation_02_boxplots_annual_and_seasonal_bias.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 3
cpus=4
memory=8
python_script='evaluation_03_timeseries_annual_and_seasonal.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 4
cpus=4
memory=8
python_script='evaluation_04_climatologies.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 5
cpus=4
memory=16
python_script='evaluation_05_animations.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 6
cpus=4
memory=8
python_script='evaluation_06a_NRM_regions_PDFs_spatial_variability.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

python_script='evaluation_06b_NRM_regions_spatial_correlation.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 7
cpus=4
memory=8
python_script='evaluation_07_NRM_regions_PDFs-temporal_variability.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 8 - to do

# 9
cpus=4
memory=8
python_script='evaluation_09_point_PDFs_annual_and_seasonal.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs

# 10
cpus=4
memory=8
python_script='evaluation_10_point_Fourier_diagrams.py'
cp evaluation_jobs_TEMPLATE.pbs PBS_jobs/evaluation_jobs_${python_script%.py}.pbs
wait
sed -i "s/SCRIPTNAME/${python_script}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/CPUS/${cpus}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s/MEMORY/${memory}/g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+PBSPATH+${PBS_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
sed -i "s+SCRIPTPATH+${current_path}+g" "PBS_jobs/evaluation_jobs_${python_script%.py}.pbs"
wait
qsub PBS_jobs/evaluation_jobs_${python_script%.py}.pbs




