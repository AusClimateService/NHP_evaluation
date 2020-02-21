# Evaluation
A set of scripts that generate various plots for the purposes of evaluating GCMs.

Scripts are broadly broken up into two types of scripts; Preprocessing, and Plotting.



## Preprocessing
These scripts need to be run first, and generate evaluation metrics which are then used by the Plotting Scripts.

## Plotting
These scripts take the preprocessed data as inputs, as well as reference data, to generate various plots.



# Intended Usage
The intention is for only one person to run the scripts at any one time.

The Preprocessing step generates data into shared folders. This is intentional, as preprocessing only needs to be done when something changes (e.g. there is a new GCM, or the reference model changes), and therefore only needs to be run occasionally.

The situation is similar for Plotting scripts.