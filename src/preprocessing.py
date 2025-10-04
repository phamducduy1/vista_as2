"""
This file contains a class that will preprocess the "data/raw_data" files and output it to "data/processed_data"
"""

import pandas as pd
import numpy as np
from typing import Dict
from models import DataManager
import re
import os


class Preprocess:
    """
    Data preprocessing for the dataset.
    Implements some data preprocessing features.
    """

    def __init__(self, data_manager: DataManager) -> None:
        """
        Initialise the Preprocess with an DataManager instance

        Args:
            data_manager: DataManager instance for data access
        """
        self.dm = data_manager
        self.processed_data = {}

    @staticmethod
    def _to_float(val):
        if val == "Missing":
            return None
        return float(val)

    @staticmethod
    def _find_avg_yearly(val):
        """
        Find the yearly average of grouped income group.

        Args:
            val (str): income group that comes in format "$1,500-$1,749 ($78,000-$90,999)"

        Returns:
            int: A single value that is the mean of the values in the bracket "()"
        """
        if pd.isna(val):
            return None

        text = str(val)

        # Handle "or more" case eg. $8,000 or more ($416,000 or more)
        if "or more" in text:
            return 450000

        match = re.search(r"\(\$([\d,]+)-\$([\d,]+)\)", text)
        if match:
            low = int(match.group(1).replace(",", ""))
            high = int(match.group(2).replace(",", ""))
            avg = int((low + high) / 2)
            return avg

        return None

    @staticmethod
    def _personal_income(text: str):
        """Find category for personal income"""
        # nil income for negative income, let it be 0
        if "Negative income" == text:
            return 0
        if text == "Nil income":
            return None
        if "or more" in text:
            return 200000

        match = re.search(r"\(\$([\d,]+)-\$([\d,]+)\)", text)
        if match:
            low = int(match.group(1).replace(",", ""))
            high = int(match.group(2).replace(",", ""))
            avg = int((low + high) / 2)
            return avg

        return None

    @staticmethod
    def _categorise_melbourne_zone(subregion: str) -> str:
        """Categorise Melbourne zones."""
        if pd.isna(subregion):
            return "Unknown"
        subregion = str(subregion)
        if "Inner" in subregion:
            return "Inner"
        elif "Middle" in subregion:
            return "Middle"
        elif "Outer" in subregion:
            return "Outer"
        elif "Melbourne" not in subregion:
            return "Regional"
        else:
            return "Other"

    @staticmethod
    def _convert_age_to_decade(age_str: str) -> str:
        """Convert 5-years groups into 10-years groups"""
        if age_str == "100+":
            return "100+"
        start_age_str = age_str.split("->")[0]
        start_age = int(start_age_str)

        decade_start = (start_age // 10) * 10
        decade_end = decade_start + 9

        return f"{decade_start}->{decade_end}"

    def _categorise_emp_status(self, row) -> str:
        """Categorise employment status."""
        if row["fulltimework"] == "Yes":
            return "Full-time"
        elif row["parttimework"] == "Yes":
            return "Part-time"
        elif row["casualwork"] == "Yes":
            return "Casual"
        elif row["studying"] != "No Study":
            return "Student"
        elif row["activities"] == "Retired":
            return "Retired"
        else:
            return "Not Working"

    @staticmethod
    def _categorise_life_stage(row) -> str:
        """Categorise life stage based on age and activity."""
        age = row["age_decade"]
        if age in ["0-10", "10-20"]:
            return "Youth"
        elif row["studying"] != "No Study":
            return "Student"
        elif row["anywork"] == "Yes" and age in ["20-30", "30-40", "40-50", "50-60"]:
            return "Working Adult"
        elif row["activities"] == "Retired" or age in [
            "60-70",
            "70-80",
            "80-90",
            "90+",
        ]:
            return "Retired/Senior"
        else:
            return "Other"

    @staticmethod
    def _categorise_licence_freedom(row) -> str:
        car_licence_status = row["carlicence"]
        mbike_licence_status = row["mbikelicence"]
        other_licence_status = row["otherlicence"]
        if (
            car_licence_status == "Full Licence"
            or mbike_licence_status == "Yes"
            or other_licence_status == "Yes"
        ):
            return "Full"
        elif car_licence_status in [
            "Red Probationary Licence",
            "Green Probationary Licence",
            "Learners Permit",
        ]:
            return "Limited"
        return "None"

    @staticmethod
    def _categorise_car_licence_freedom(status: str) -> str:
        if status == "Full Licence":
            return "Full"
        elif status == "No Licence":
            return "None"
        else:
            return "Limited"

    @staticmethod
    def _categorise_trip_purpose(purp) -> str:
        """Categorised trip purposes into more general categories"""
        if pd.isna(purp):
            return "Unknown"

        mandatory = ["Work Related", "Education"]
        maintenance = [
            "Buy Something",
            "Personal Business",
            "Pick-up or Deliver Something",
            "Pick-up or Drop-off Someone",
            "Accompany Someone",
        ]
        discretionary = ["Social", "Recreational"]
        if purp == "At Home":
            return "Home"
        elif purp in mandatory:
            return "Mandatory"
        elif purp in maintenance:
            return "Maintenance"
        elif purp == discretionary:
            return "Discretionary"
        else:
            return "Other"

    @staticmethod
    def _categorise_trip_mode(mode) -> str:
        """Categorise transport modes into more general categories"""
        if pd.isna(mode):
            return "Unknown"

        public = ["Public Bus", "School Bus", "Train", "Tram"]
        private = [
            "Vehicle Driver",
            "Vehicle Passenger",
            "Motorcycle",
            "Taxi",
            "Rideshare Service",
        ]
        active = [
            "Walking",
            "Bicycle",
            "Running/jogging",
            "Mobility Scooter",
            "e-Scooter",
        ]

        if mode in public:
            return "Public"
        elif mode in private:
            return "Private"
        elif mode in active:
            return "Active"
        else:
            return "Other"

    def get_unique_values(self, dataset: str, column: str) -> pd.Series:
        """
        Get unique values from a specific column in a dataset.
        Args:
            dataset (str): Name of the dataset (e.g., 'households', 'persons').
            column (str): Column name to extract unique values from.

        Returns:
            List: A list of unique values from the specified column.
        """
        data = self.processed_data[dataset]
        if column in data.columns:
            return data[column].value_counts()
        else:
            raise ValueError(f"Column {column} not found in dataset {dataset}.")

    def prep_households(self) -> pd.DataFrame:
        """
        Preprocess the households data with income conversion and missing value handling.
        Create household_income column, fill missing values with median income.
        Add feature columns to the data
        Returns:
            pd.DataFrame: Preprocessed households DataFrame
        """

        households = self.dm.households.copy()

        # Create household_income column and fill missing values with mean income
        hhinc_group = households["hhinc_group"]
        hhinc_group = hhinc_group.apply(self._find_avg_yearly)
        mean_yearly = hhinc_group.mean()
        hhinc_group = hhinc_group.fillna(mean_yearly)
        households["household_income"] = hhinc_group

        # Create income bracket, binning based on socioeconomic status
        # Categorised into 6 groups: ['Low', 'Lower-middle', 'Middle', 'Upper-middle', 'High', 'Very high']
        households["income_bracket"] = pd.cut(
            households["household_income"],
            bins=[0, 25000, 50000, 100000, 150000, 250000, float("inf")],
            labels=[
                "Low (0 - 25000]",
                "Lower-middle (25000 - 50000]",
                "Middle (50000 - 100000]",
                "Upper-middle (100000 - 150000]",
                "High (150000 - 250000]",
                "Very high (250000+)",
            ],
        )

        # Categorised by vehicle per person in household. There is no household with hhsize = 0
        households["vehicle_per_person"] = (
            households["totalvehs"] / households["hhsize"]
        )

        # Categorised by vehicle availability
        households["vehicle_availability"] = pd.cut(
            households["vehicle_per_person"],
            bins=[-0.1, 0.5, 1, 1.5, float("inf")],
            labels=["Limited", "Moderate", "Adequate", "Abundant"],
        )

        # Categorised based on household types ['has_young_children', 'has_teenagers']
        households["has_young_children"] = households["youngestgroup_5"].apply(
            lambda x: 1 if x in ["0->4", "5->9"] else 0
        )
        households["has_teenagers"] = households["youngestgroup_5"].apply(
            lambda x: 1 if x in ["10->14", "15->20"] else 0
        )

        # Categorised by hosuehold size
        households["household_size_category"] = pd.cut(
            households["hhsize"],
            bins=[0, 1, 2, 4, 6, 10],
            labels=[
                "Single (0 - 1]",
                "Couple (1 - 2]",
                "Small family (2 - 4]",
                "Large family (4 - 6]",
                "Extended family (6 - 10]",
            ],
        )

        # Categorised by region: City or Regional area
        households["is_city"] = households["homeregion_ASGS"].apply(
            lambda x: 1 if "Melbourne" in str(x) else 0
        )

        # Categorised by zones: Inner, Middle, Outer
        households["zone"] = households["homesubregion_ASGS"].apply(
            self._categorise_melbourne_zone
        )

        self.processed_data["households"] = households
        print(f"Household preprocessing complete. Shape: {households.shape}")
        return households

    def prep_persons(self) -> pd.DataFrame:
        """
        Preprocess the persons data with age grouping by decades and WFH categorisation
        Returns:
            pd.DataFrame: Preprocessed households DataFrame
        """
        persons = self.dm.persons.copy()

        # Convert 5-years age group into decades
        persons["age_decade"] = persons["agegroup"].apply(self._convert_age_to_decade)
        # Counting the total number of WFH days
        wfh_columns = [
            "wfhmon",
            "wfhtue",
            "wfhwed",
            "wfhthu",
            "wfhfri",
            "wfhsat",
            "wfhsun",
        ]
        # Convert from 'Yes' to 1, 'No' or 'Not in Workforce' to 0
        for col in wfh_columns:
            persons[col] = persons[col].apply(lambda x: 1 if x == "Yes" else 0)

        persons["total_wfh_days"] = persons[wfh_columns].sum(axis=1)

        # Categorised by WFH days:
        # Never (0 days),
        # Occasional (1–2 days),
        # Frequent (3–5 days)
        # Always (6–7 days).
        persons["wfh_category"] = pd.cut(
            persons["total_wfh_days"],
            bins=[-0.1, 0.1, 2.1, 5.1, 7.1],
            labels=["Never", "Occasional", "Frequent", "Always"],
        )

        # Categorised by employment status
        persons["employment_status"] = persons.apply(
            self._categorise_emp_status, axis=1
        )

        # Categorised by life stage
        persons["life_stage"] = persons.apply(self._categorise_life_stage, axis=1)

        # Categorised by personal income and fill missing values with mean
        persons["personal_income"] = persons["persinc"].apply(self._personal_income)
        mean_personal_income = int(persons["personal_income"].mean())
        persons["personal_income"] = persons["personal_income"].fillna(
            mean_personal_income
        )

        # Categorised by percentile
        persons["income_percentile"] = pd.qcut(
            persons["personal_income"],
            q=[0, 0.25, 0.5, 0.75, 1.0],
            labels=["Bottom 25%", "25-50%", "50-75%", "Top 25%"],
        )

        # Categorised by car licence
        persons["car_mobility"] = persons["carlicence"].apply(
            self._categorise_car_licence_freedom
        )

        # Categorised by licence, or degree of freedom
        persons["mobility"] = persons.apply(self._categorise_licence_freedom, axis=1)

        self.processed_data["persons"] = persons
        return persons

    def prep_trips(self) -> pd.DataFrame:
        """
        Preprocess trip data with temporal, modal, and purpose categorisation

        Returns:
            pd.DataFrame: Preprocessed trips DataFrame
        """

        trips = self.dm.trips.copy()

        # Normalise from Minutes from midnight to Hours
        trips["start_hour"] = trips["startime"] / 60
        trips["arr_hour"] = trips["arrtime"] / 60

        # Categorised by peak hours:
        trips["is_morning_peak"] = trips["start_hour"].apply(
            lambda x: 1 if 7 <= x <= 9 else 0
        )
        trips["is_evening_peak"] = trips["start_hour"].apply(
            lambda x: 1 if 17 <= x <= 19 else 0
        )
        trips["is_peak_hour"] = trips["is_morning_peak"] | trips["is_morning_peak"]

        # Categorised by time of day:
        trips["time_of_day"] = pd.cut(
            trips["arr_hour"],
            bins=[0, 6, 9, 12, 15, 19, 22, 24],
            labels=[
                "Early Morning (0-6]",
                "Morning Peak (6-9]",
                "Late Morning (9-12]",
                "Afternoon (12-15]",
                "Evening Peak (15-19]",
                "Evening (19-22]",
                "Late Night (22-24",
            ],
        )

        # Convert dsitance into floats, and fill in missing values with median distance
        trips["cumdist"] = trips["cumdist"].apply(self._to_float)
        median_distance = trips["cumdist"].median()
        trips["cumdist"] = trips["cumdist"].fillna(median_distance)

        # Categorised by trip distance
        trips["distance_category"] = pd.cut(
            trips["cumdist"],
            bins=[0, 10, 20, 40, float("inf")],
            labels=[
                "Short (0-10]",
                "Medium (10-20]",
                "Long (20-40]",
                "Very Long (40+)",
            ],
        )

        # Categorised by trip purpose
        trips["purpose_category"] = trips["destpurp1"].apply(
            self._categorise_trip_purpose
        )

        # CAtegorised by mode of transport
        trips["mode_category"] = trips["linkmode"].apply(self._categorise_trip_mode)

        # Convert into numerical values
        trips["travtime"] = trips["travtime"].apply(self._to_float)

        # Categorised by trip duration
        trips["duration_category"] = pd.cut(
            trips["travtime"],
            bins=[0, 10, 20, 40, float("inf")],
            labels=[
                "Short (0-10]",
                "Medium (10-20]",
                "Long (20-40]",
                "Very Long (40+)",
            ],
        )

        self.processed_data["trips"] = trips
        return trips

    def prep_journeys(self) -> Dict[str, pd.DataFrame]:
        """
        Preprocess journey to work and journey to education data.

        Returns:
            Dict[str, pd.DataFrame]: a Dict where 'Work' represents journey_to_work data
            and 'Education' key represents journey_to_education data
        """

        jtw = self.dm.journey_work.copy()
        jte = self.dm.journey_education.copy()

        jtw["journey_type"] = "Work"
        jte["journey_type"] = "Education"

        for journey, type in [(jtw, "Work"), (jte, "Education")]:
            # Convert travel time from minutes to hours
            journey["journey_travel_hours"] = (
                pd.to_numeric(journey["journey_travel_time"], errors="coerce") / 60
            )

            # Categorised journey by number of stops (complexity)
            columns_name = [f"mainmode_desc_{i:02d}" for i in range(1, 16)]
            journey["num_stops"] = journey[columns_name].notna().sum(axis=1)

            journey["journey_complexity"] = pd.cut(
                journey["num_stops"],
                bins=[0, 1, 2, 3, 15],
                labels=["One-Stage", "Two-Stage", "Three-Stage", "Complex"],
            )

            # Categorised by journey distance and clean data
            # there are some negatve values in journey_to_work data. set to 0
            journey["jdist"] = pd.to_numeric(
                journey["journey_distance"], errors="coerce"
            )
            journey["jdist"] = journey["jdist"].apply(lambda x: 0 if x < 0 else x)

            journey["journey_distance_category"] = pd.cut(
                journey["jdist"],
                bins=[0, 10, 20, 40, float("inf")],
                labels=[
                    "Short (0-10]",
                    "Medium (10-20]",
                    "Long (20-40]",
                    "Very Long (40+)",
                ],
            )

            # Convert time from minutes to hours
            journey["start_hour"] = journey["start_time"] / 60
            journey["end_hour"] = journey["end_time"] / 60

            journey["starts_in_peak_hour"] = journey["start_hour"].apply(
                lambda x: 1 if (7 <= x <= 9) or (17 <= x <= 19) else 0
            )

        self.processed_data["journey_work"] = jtw
        self.processed_data["journey_education"] = jte
        return {"Work": jtw, "Education": jte}

    def prep_person_trip(self) -> pd.DataFrame:
        """
        Calculate trips metrics and merge with persons table
        """

        if "persons" not in self.processed_data:
            self.prep_persons()
        if "trips" not in self.processed_data:
            self.prep_trips

        persons = self.processed_data["persons"]
        trips = self.processed_data["trips"]

        # Calculate travelling summary for each person
        trip_summary = (
            trips.groupby("persid")
            .agg(
                {
                    "tripid": "count",
                    "cumdist": "sum",
                    "travtime": "sum",
                    "is_peak_hour": "sum",
                }
            )
            .rename(
                columns={
                    "tripid": "total_trips",
                    "cumdist": "total_distance",
                    "travtime": "total_travel_time",
                    "is_peak_hour": "total_peak_hour_trips",
                }
            )
        )

        # Summarised by purpose, either work or education.
        work_trips = (
            trips[trips["destpurp1"] == "Work Related"]
            .groupby("persid")["tripid"]
            .count()
        )
        edu_trips = (
            trips[trips["destpurp1"] == "Education"].groupby("persid")["tripid"].count()
        )

        trip_summary["work_trips"] = work_trips
        trip_summary["edu_trips"] = edu_trips
        trip_summary.fillna(0, inplace=True)

        # Some Ratios
        trip_summary["peak_hour_ratio"] = (
            trip_summary["total_peak_hour_trips"] / trip_summary["total_trips"]
        )
        trip_summary["avg_trip_distance"] = (
            trip_summary["total_distance"] / trip_summary["total_trips"]
        )
        trip_summary["avg_trip_duration"] = (
            trip_summary["total_travel_time"] / trip_summary["total_trips"]
        )
        # for people who don't have any trips
        trip_summary = trip_summary.replace([np.inf, -np.inf], 0)
        trip_summary.fillna(0, inplace=True)

        person_trips = pd.merge(
            persons, trip_summary, left_on="persid", right_index=True, how="left"
        )

        trip_metric_cols = trip_summary.columns.tolist()
        person_trips[trip_metric_cols] = person_trips[trip_metric_cols].fillna(0)

        self.processed_data["persons_trips_summary"] = person_trips

        return person_trips

    def create_combined_dataset(self) -> pd.DataFrame:
        """
        Create a master dataset by combining hosueholds, persons, and trips.
        """

        if "households" not in self.processed_data:
            self.prep_households()
        if "persons_trips_summary" not in self.processed_data:
            self.prep_person_trip()

        households = self.processed_data["households"]
        person_trips = self.processed_data["persons_trips_summary"]

        # Features to include in the merged table
        hh_features = [
            "hhid",
            "household_income",
            "income_bracket",
            "vehicle_per_person",
            "vehicle_availability",
            "household_size_category",
            "is_city",
            "zone",
            "has_young_children",
            "has_teenagers",
        ]

        df = pd.merge(person_trips, households[hh_features], on="hhid", how="left")

        self.processed_data["master"] = df
        return df

    def create_compare_dataset(self) -> Dict[str, pd.DataFrame]:
        """
        Create a dataset for comparision between journey_to_work and journey_to_education
        """

        if "trips" not in self.processed_data:
            self.prep_trips()
        if "master" not in self.processed_data:
            self.create_combined_dataset()

        trips = self.processed_data["trips"]
        master = self.processed_data["master"]

        work_trips = trips[trips["destpurp1"] == "Work Related"].copy()
        edu_trips = trips[trips["destpurp1"] == "Education"].copy()

        master_work_cols = [
            "persid",
            "hhid",
            "age_decade",
            "sex",
            "wfh_category",
            "household_income",
            "vehicle_availability",
            "zone",
        ]

        master_edu_cols = [
            "persid",
            "hhid",
            "age_decade",
            "sex",
            "life_stage",
            "household_income",
            "vehicle_availability",
            "zone",
        ]

        work_trips = pd.merge(
            work_trips, master[master_work_cols], on="persid", how="left"
        )
        edu_trips = pd.merge(
            edu_trips, master[master_edu_cols], on="persid", how="left"
        )

        compare_data = {
            "work_trips": work_trips,
            "education_trips": edu_trips
        }

        #
        self.processed_data.update(compare_data)
        return compare_data

    def save_processed_data(self):
        """
        Save preprocessed data into the "data/processed_data' folder
        """

        cur_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(cur_dir, "data/processed_data") + os.sep

        os.makedirs(self.data_path, exist_ok=True)

        for name, df in self.processed_data.items():
            file_path = self.data_path + name + "_processed.csv"
            df.to_csv(file_path, index=False)
            print(f"Saved {name} to {file_path}")
    


def main():
    print("preprocessing.py")

    dm = DataManager()
    preprocessor = Preprocess(dm)
    households = preprocessor.prep_households()
    persons = preprocessor.prep_persons()
    trips = preprocessor.prep_trips()
    journeys = preprocessor.prep_journeys()
    person_trips = preprocessor.prep_person_trip()
    master = preprocessor.create_combined_dataset()
    compare_data = preprocessor.create_compare_dataset()

    print(households.head())
    print(persons.head())
    print(trips.head())
    print(journeys["Work"])
    print(journeys["Education"])
    print(person_trips.head())
    print(master.head())
    print(compare_data['work_trips'].head())
    print(compare_data['education_trips'].head())

    preprocessor.save_processed_data()