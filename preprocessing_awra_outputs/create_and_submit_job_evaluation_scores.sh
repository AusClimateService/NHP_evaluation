
cd /g/data1a/er4/exv563/hydro_projections/code

for var in sm etot qtot; do
# for var in sm; do
	for gcm in GFDL-ESM2M; do
		# for timescale in year mon; do
		for timescale in seas; do
			for statistic in mean min max std pctl05 pctl10 pctl25 pctl50 pctl75 pctl90 pctl95; do
			#for statistic in pctl05; do

		        # copy the template to a new file
		        cp postprocessing/ISIMIP_original/awra_outputs/job_evaluation_scores_awra_output_isimip_data_TEMPLATE.pbs PBS_jobs/job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}.pbs 
		        wait
		        
		        # replace VAR in the job file
		        sed -i "s/VAR/${var}/g" "PBS_jobs/job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        sed -i "s/GCM/${gcm}/g" "PBS_jobs/job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        sed -i "s/TIMESCALE/${timescale}/g" "PBS_jobs/job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        sed -i "s/STATISTIC/${statistic}/g" "PBS_jobs/job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}.pbs"
		        
		        wait
		        
		        # submit job
		        qsub PBS_jobs/job_evaluation_scores_awra_output_isimip_data_${var}_${gcm}_${timescale}_${statistic}.pbs
		        wait
		    done
	    done
	done
done
