
cd /g/data1/er4/exv563/hydro_projections/code

# for var in pr tasmin tasmax sfcWind rsds; do
for var in pr; do
    # for gcm in ACCESS1-0 CNRM-CM5 GFDL-ESM2M MIROC5; do
    for gcm in CNRM-CM5 GFDL-ESM2M MIROC5; do

        # copy the template to a new file
        cp postprocessing/ISIMIP_AWAP/climate_inputs/job_create_annual_files_TEMPLATE.pbs PBS_jobs/job_create_annual_files_ISIMIP_awap_${var}_${gcm}.pbs
        wait
        
        # replace VAR in the job file
        sed -i "s/VAR/${var}/g" "PBS_jobs/job_create_annual_files_ISIMIP_awap_${var}_${gcm}.pbs"
        wait
        sed -i "s/MODEL/${gcm}/g" "PBS_jobs/job_create_annual_files_ISIMIP_awap_${var}_${gcm}.pbs"
        wait
        
        # submit job
        qsub PBS_jobs/job_create_annual_files_ISIMIP_awap_${var}_${gcm}.pbs
        wait
        
    done
done
