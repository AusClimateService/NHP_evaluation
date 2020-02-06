
cd /g/data1a/er4/exv563/hydro_projections/code

# for var in rain_day temp_max_day temp_min_day wind solar_exposure_day; do
for var in rain_day; do
	# for gcm in ACCESS1-0 CNRM-CM5 GFDL-ESM2M MIROC5; do
	for gcm in CNRM-CM5 GFDL-ESM2M MIROC5; do
		for timescale in year seas mon; do
		# for timescale in year; do
			for statistic in mean min max std pctl05 pctl10 pctl25 pctl50 pctl75 pctl90 pctl95; do
			#for statistic in mean; do

		        # copy the template to a new file
		        cp postprocessing/ISIMIP_AWAP/climate_inputs/job_evaluation_scores_climate_input_isimip_data_TEMPLATE.pbs PBS_jobs/job_evaluation_scores_climate_input_isimip_data_awap_${var}_${gcm}_${timescale}_${statistic}.pbs
		        wait
		        
		        # replace VAR in the job file
		        sed -i "s/VAR/${var}/g" "PBS_jobs/job_evaluation_scores_climate_input_isimip_data_awap_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        sed -i "s/GCM/${gcm}/g" "PBS_jobs/job_evaluation_scores_climate_input_isimip_data_awap_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        sed -i "s/TIMESCALE/${timescale}/g" "PBS_jobs/job_evaluation_scores_climate_input_isimip_data_awap_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        sed -i "s/STATISTIC/${statistic}/g" "PBS_jobs/job_evaluation_scores_climate_input_isimip_data_awap_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        
		        wait
		        
		        # submit job
		        qsub PBS_jobs/job_evaluation_scores_climate_input_isimip_data_awap_${var}_${gcm}_${timescale}_${statistic}.pbs
		        wait
		    done
	    done
	done
done
