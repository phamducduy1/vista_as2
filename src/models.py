"""
This file contains a model for data storage and data accessing.
"""


import pandas as pd
from typing import Optional, Dict, List, Tuple
import os
import re


class DataManager:
    """
    Manages the loading and caching of dataset files.
    Uses lazy loading and selective merging for memory efficiency.
    """

    def __init__(self):
        cur_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(cur_dir, "data/raw_data") + os.sep

        self._households = None
        self._persons = None
        self._trips = None
        self._stops = None
        self._journey_work = None
        self._journey_education = None

        self._cache = {}

        self.dataset_info = {
            "households": {"file": "households.csv", "id": "hhid"},
            "persons": {"file": "persons.csv", "id": "persid"},
            "trips": {"file": "trips.csv", "id": "tripid"},
            "stops": {"file": "stops.csv", "id": "stopid"},
            "journey_work": {
                "file": "journey_to_work.csv",
                "id": "persid"
            },
            "journey_education": {
                "file": "journey_to_education.csv",
                "id": "persid"
            },
        }

    @property
    def households(self) -> pd.DataFrame:
        """Lazy load households data."""
        if self._households is None:
            print("Loading households data...")
            self._households = pd.read_csv(
                self.data_path + self.dataset_info["households"]["file"]
            )
            print(f"Loaded {len(self._households)} households records.")
        return self._households

    @property
    def persons(self) -> pd.DataFrame:
        """Lazy load persons data."""
        if self._persons is None:
            print("Loading persons data...")
            self._persons = pd.read_csv(
                self.data_path + self.dataset_info["persons"]["file"]
            )
            print(f"Loaded {len(self._persons)} persons records.")
        return self._persons

    @property
    def trips(self) -> pd.DataFrame:
        """Lazy load trips data."""
        if self._trips is None:
            print("Loading trips data...")
            self._trips = pd.read_csv(
                self.data_path + self.dataset_info["trips"]["file"]
            )
            print(f"Loaded {len(self._trips)} trips records.")
        return self._trips

    @property
    def stops(self) -> pd.DataFrame:
        """Lazy load stops data."""
        if self._stops is None:
            print("Loading stops data...")
            self._stops = pd.read_csv(
                self.data_path + self.dataset_info["stops"]["file"]
            )
            print(f"Loaded {len(self._stops)} stops records.")
        return self._stops

    @property
    def journey_work(self) -> pd.DataFrame:
        """Lazy load journey to work data."""
        if self._journey_work is None:
            print("Loading journey to work data...")
            self._journey_work = pd.read_csv(
                self.data_path + self.dataset_info["journey_work"]["file"]
            )
            print(f"Loaded {len(self._journey_work)} journey to work records.")
        return self._journey_work

    @property
    def journey_education(self) -> pd.DataFrame:
        """Lazy load journey to education data."""
        if self._journey_education is None:
            print("Loading journey to education data...")
            self._journey_education = pd.read_csv(
                self.data_path + self.dataset_info["journey_education"]["file"]
            )
            print(
                f"Loaded {len(self._journey_education)} journey to education records."
            )
        return self._journey_education

    def load_columns(self, dataset: str, columns: List[str]) -> pd.DataFrame:
        """
        Load specific columns from a dataset to save memory.
        Args:
            dataset (str): Name of the dataset (e.g., 'households', 'persons').
            columns (List[str]): List of columns to load.

        Returns:
            pd.DataFrame: DataFrame containing only the specified columns.
        """
        if dataset not in self.dataset_info:
            raise ValueError(f"Dataset {dataset} not recognized.")

        file_path = self.data_path + self.dataset_info[dataset]["file"]
        print(f"Loading columns {columns} from {dataset}...")
        df = pd.read_csv(file_path, usecols=columns)
        print(f"Loaded {len(df)} records from {dataset} with columns {columns}.")
        return df

    def get_work_trips(
        self, include_person_data: bool = False, include_household_data: bool = False
    ) -> pd.DataFrame:
        """
        Get trips related to work journeys, with optional merging of person and household data.
        Args:
            include_person_data (bool): Whether to merge person data.
            include_household_data (bool): Whether to merge household data.

        Returns:
            pd.DataFrame: DataFrame of work-related trips.
        """
        cache_key = f"work_trips_{include_person_data}_{include_household_data}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        work_trips = self.trips[self.trips["destpurp1"] == "Work Related"].copy()
        if include_person_data:
            person_cols = [
                "persid",
                "agegroup",
                "sex",
                "carlicence",
                "anywork",
                "emptype",
                "anzsco1",
                "anzsco2",
                "anzsic1",
                "anzsic2",
                "persinc",
                "anywfh",
            ]
            work_trips = pd.merge(
                work_trips, self.persons[person_cols], on="persid", how="left"
            )

        if include_household_data:
            if "hhid" not in work_trips.columns:
                work_trips = pd.merge(
                    work_trips,
                    self.persons[["persid", "hhid"]],
                    on="persid",
                    how="left",
                )

            household_cols = [
                "hhid",
                "hhinc_group",
                "totalvehs",
                "totalbikes",
                "hhsize",
                "dwelltype",
                "owndwell",
                "homelga",
                "homesubregion_ASGS",
                "homeregion_ASGS",
            ]

            work_trips = pd.merge(
                work_trips, self.households[household_cols], on="hhid", how="left"
            )

        self._cache[cache_key] = work_trips
        return work_trips

    def get_education_trips(
        self, include_person_data: bool = False, include_household_data: bool = False
    ) -> pd.DataFrame:
        """
        Get education related journeys, with optional merging of person and household data.
        Args:
            include_person_data (bool): Whether to merge person data.
            include_household_data (bool): Whether to merge household data.

        Returns:
            pd.DataFrame: DataFrame of education related trips.
        """
        cache_key = f"education_trips_{include_person_data}_{include_household_data}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        education_trips = self.trips[self.trips["destpurp1"] == "Education"].copy()

        # Person data columns to be included
        if include_person_data:
            person_cols = [
                "persid",
                "agegroup",
                "sex",
                "studying",
                "mainact",
                "carlicence",
                "relationship",
            ]
            education_trips = pd.merge(
                education_trips, self.persons[person_cols], on="persid", how="left"
            )

        if include_household_data:
            if "hhid" not in education_trips.columns:
                education_trips = pd.merge(
                    education_trips,
                    self.persons[["persid", ["hhid"]]],
                    on="persid",
                    how="left",
                )

            household_cols = [
                "hhid",
                "hhinc_group",
                "totalvehs",
                "totalbikes",
                "hhsize",
                "dwelltype",
                "owndwell",
                "homelga",
                "youngestgroup_5",
                "aveagegroup_5",
                "oldestgroup_5",
            ]

            education_trips = pd.merge(
                education_trips, self.households[household_cols], on="hhid", how="left"
            )

        self._cache[cache_key] = education_trips
        return education_trips

    def get_journey_dict(self) -> Dict[str, pd.DataFrame]:
        """
        Get journey to work and education data merged with person data.
        Args: 
            None

        Returns:
            Dictionary with 'work' and 'education' keys for their respective Dataframe
        """
        cache_key = "journey_dict"
        if cache_key in self._cache:
            return self._cache[cache_key]

        result = {
            "work": self.journey_work.copy(),
            "education": self.journey_education.copy(),
        }

        result["work"] = pd.merge(
            result["work"],
            self.persons[["persid", "agegroup", "sex", "hhid"]],
            on="persid",
            how="left",
        )
        result["education"] = pd.merge(
            result["education"],
            self.persons[["persid", "agegroup", "sex", "hhid"]],
            on="persid",
            how="left",
        )

        self._cache[cache_key] = result

        return result

    def get_spatial_data(self, trip_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get spatial data from stops dataset.
        Args:
            trip_type (Optional[str]): Filter by trip type ('work' or 'education').

        Returns:
            pd.DataFrame: DataFrame containing spatial data.
        """
        # Select relevant columns for spatial data (location data)
        spatial_cols = ['tripid', 'origlga', 'destlga', 'origplace1', 'origplace2',
                       'destplace1', 'destplace2', 'cumdist', 'destpurp1']
        
        spatial_data = self.stops[spatial_cols].copy()
        if trip_type == "work":
            spatial_data = spatial_data[spatial_data["destpurp1"] == "Work Related"]
        elif trip_type == "education":
            spatial_data = spatial_data[spatial_data["destpurp1"] == "Education"]

        return spatial_data

    def get_temporal_data(self, trip_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get temporal data from trips dataset.
        Args:
            trip_type (Optional[str]): Filter by trip type ('work' or 'education').

        Returns:
            pd.DataFrame: DataFrame containing temporal data.
        """
        # Select relevant columns for temporal data(time data)
        temporal_cols = ['tripid', 'startime', 'arrtime', 'travtime', 'triptime',
                        'starthour', 'arrhour', 'duration', 'dayType', 'destpurp1']

        temporal_data = self.trips[temporal_cols].copy()
        if trip_type == "work":
            temporal_data = temporal_data[temporal_data["destpurp1"] == "Work Related"]
        elif trip_type == "education":
            temporal_data = temporal_data[temporal_data["destpurp1"] == "Education"]

        return temporal_data

    def get_modal_data(self, trip_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get modal data from trips dataset, including multi-model information.
        Args:
            trip_type (Optional[str]): Filter by trip type ('work' or 'education').
        Returns:
            pd.DataFrame: DataFrame containing modal data.
        """
        # Select relevant columns for modal data (mode of transport)
        modes = [f"mode{i}" for i in range(1, 10)]
        times = [f"time{i}" for i in range(1, 10)]
        dists = [f"dist{i}" for i in range(1, 10)]
        
        modal_cols = ['tripid', 'linkmode', 'destpurp1'] + modes + times + dists

        modal_data = self.trips[modal_cols].copy()

        if trip_type == "work":
            modal_data = modal_data[modal_data["destpurp1"] == "Work Related"]
        elif trip_type == "education":
            modal_data = modal_data[modal_data["destpurp1"] == "Education"]

        # Add multi-modal information - count non-null modes
        existing_mode_cols = [col for col in modes if col in modal_data.columns]
        modal_data['is_multimodal'] = modal_data[existing_mode_cols].notna().sum(axis=1) > 1
        modal_data['num_modes'] = modal_data[existing_mode_cols].notna().sum(axis=1)

        return modal_data

    def get_stop_data(self, trip_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get stop-level data for further analysis.
        Args:
            trip_type (Optional[str]): Filter by trip type ('work' or 'education').
        Returns:
            pd.DataFrame: DataFrame containing stop data.
        """
        # Select relevant columns for stop data (stop-level details)
        stop_cols = ['stopid', 'hhid', 'persid', 'tripid', 'stopno',
            'origplace1', 'origplace2', 'destplace1', 'destplace2',
            'origlga', 'destlga', 'mainmode', 'destpurp1',
            'startime', 'arrtime', 'deptime', 'travtime', 'vistadist', 'duration']
        stop_data = self.stops[stop_cols].copy()

        if trip_type == "work":
            stop_data = stop_data[stop_data["destpurp1"] == "Work Related"]
        elif trip_type == "education":
            stop_data = stop_data[stop_data["destpurp1"] == "Education"]

        return stop_data
    
    def get_journey_segments(self, journey_type: Optional[str] = None) -> pd.DataFrame:
        """
        Get journey segments data for detailed trip analysis.
        Args:
            journey_type (Optional[str]): Filter by journey type ('work' or 'education').
        Returns:
            pd.DataFrame: DataFrame containing journey segments data.
        """
        if journey_type == "work":
            journey_df = self.journey_work.copy()
        else:
            journey_df = self.journey_education.copy()

        segments = []

        for idx, row in journey_df.iterrows():
            journey_id = row['jtwid'] if journey_type == 'work' else row['jteid']

            for i in range(1, 16):
                mode_col = f'mainmode_desc_{i:02d}'
                time_col = f'travtime_{i:02d}'
                dist_col = f'vistadist_{i}'
                start_col = f'starttime_{i:02d}'
                arr_col = f'arrtime_{i:02d}'

                if pd.notna(row.get(mode_col)):
                    segments.append({
                        'journey_id': journey_id,
                        'persid': row['persid'],
                        'hhid': row['hhid'],
                        'segment_no': i,
                        'mode': row.get(mode_col),
                        'travel_time': row.get(time_col),
                        'distance': row.get(dist_col),
                        'start_time': row.get(start_col),
                        'arrival_time': row.get(arr_col),
                        'journey_type': journey_type,
                        'main_journey_mode': row.get('main_journey_mode'), 
                        'journey_travel_time': row.get('journey_travel_time')
                    })
        return pd.DataFrame(segments)
    
    def get_unique_values(self, dataset: str, column: str) -> pd.Series:
        """
        Get unique values from a specific column in a dataset.
        Args:
            dataset (str): Name of the dataset (e.g., 'households', 'persons').
            column (str): Column name to extract unique values from.

        Returns:
            List: A list of unique values from the specified column.
        """

        data = getattr(self, dataset)
        if column in data.columns:
            return data[column].value_counts()
        else:
            raise ValueError(f"Column {column} not found in dataset {dataset}.")

def main():
    data_manager = DataManager()
    households = data_manager.households
    unique_income_values = data_manager.get_unique_values('journey_education', 'journey_distance')
    print(unique_income_values)
