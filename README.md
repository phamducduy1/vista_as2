# vista_as2

This project is to answer this question: How do temporal, modal, and spatial characteristics of work-related trips differ from education-related trips, and what household factors are associated with these differences?

## Components  
#### Data: 
The data is provided by the State of Victoria under Creative Commons Attribution 4.0.
State of Victoria. (2025). Victorian Integrated Survey of Travel and Activity (VISTA). Retrieved September 11, 2025 from https://discover.data.vic.gov.au/dataset/victorian-integrated-survey-of-travel-and-activity-vista

#### Graphs and Relevant plots for analysis
Located in the `graphs` folder
#### Instruction of how to do the analysis
Located in the `instruction` folder
## Installation
Located in the 'instruction' folder

### Overview
#### models.py
This file contains the model which is designed for data manipulation and analysis.
#### preprocess.py
This file contains functions for data cleaning and preprocessing.

*** Preprocessing steps include:
1. Handling missing values: 
- Mean imputation for numerical columns: `household_income`, `personal_income`
- Median imputation for numerical columns with outliers (``cumdist``)
- Zero filling:
    - Person with zero trips in `total_trips`
    - wfh days for non-working individuals
2. Reshaping Data
- Aggregation: 
    - Person-level trip summaries from trip-level data
    - Household-level summaries from person and trip-level data
3. Scaling
- Calculated ratios instead of using normalisation/standardisation
4. Encoding Categorical Variables
- Binary Encoding: 
    - wfh days: 'yes'/'no' to 1/0
    - indicators such as `is_peak_hour`, `is_city`, ... to 1/0
- Label encoding: Transforming numerical categories into categorical
- Ordinal Encoding: 
    - Income percentiles, Vehicle availability
5. Discretization (Binning)
- Age groups: Categorizing ages from 5-years intervals to 10-years intervals
- Time of day: Early Morning to Night with 7 categories
- journey complexity: Based on number of stops per journey
- Income brackets, Distance Categories, Duration Categories, WFH categories, household Size categories into custom bins.
- quantile-based binning for `personal_income`
6. Merging Datasets
- Merge using keys (`persid`, `hhid`, `tripid`) to create a comprehensive dataset for analysis.
- Aggregated merges: trip summaries to person-level, person summaries to household-level.
- Selective merged: Merges only relevant columns for analysis.
7. Feature Engineering
- Composite Features:
    - total wfh days
    - household indicators: `has_young_children`, `has_teenagers`
- Derived Metrics:
    - average trip distance and duration
    - `vehicle_per_person` 
- Categorical Features:
    - Employment status categories
    - lifestage categories
    - purpose categories
    - mode categories
    - Zone categories
8. Outlier Detection and Treatment
- Handling non-sensical values: 
    - Negative distances are set to 0
9. Type Conversion
- Ensuring correct data types for analysis:
