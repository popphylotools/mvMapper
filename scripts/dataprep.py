#!/usr/bin/env python
# coding: utf-8

"""
This script is used to synthesise a single webapp_input.csv with data of interest pulled from the various dapc tables
as well as from a separately included localities.csv

The dapc data includes the keys and loadings from 'ind.coord.csv'; the a priori group (grp) and
model predicted group (assign) from their respective csv's; and the corresponding posterior probabilities
for the 'grp' and 'assign' columns from 'posterior.csv'.

The localities.csv must include at least a 'key', 'lat', and 'lng' column, but can include any additional metadata.
"""

import os
import pandas as pd

data_directory = "./data/"


"""read in csv's from dapc analysis in R"""
# create a dict of short names and their respective .csv files
fns = {fn.strip().split(".csv")[0]: fn for fn in os.listdir(data_directory) if
       fn in ["assign.csv", "eig.csv", "ind.coord.csv", "posterior.csv", "grp.csv"]}

# create a dict of short names and dataframes sourced from the above .csv files
dfs = {n: pd.read_csv(data_directory + fn) for n, fn in fns.items()}


"""Make key's consistent across all dataframes"""
# for each dataframe
for n, df in dfs.items():
    # rename 0th column to key
    df.rename(columns={df.columns[0]: 'key'}, inplace=True)
    # treat keys as strings even if numeric
    df.key = df.key.apply(str)


"""extract posterior probabilities for a priori group (grp) and model predicted group (assign)"""
# create dataframe with better column names 
posterior = dfs["posterior"].rename(columns=lambda x: x.split(".")[-1] if "posterior." in x else x)

# join in the model predicted groups for each individual from the assign column of the assign dataframe
posterior = posterior.join(dfs["assign"]["assign"].apply(str))

# create a 'posterior_assign' column from the column corresponding to each individual's model predicted group
posterior["posterior_assign"] = posterior.apply(lambda row: row.loc[row["assign"]], axis=1)

# join in the a priori groups for each individual from the grp column of the grp dataframe
posterior = posterior.join(dfs["grp"]["grp"].apply(str))

# create a 'posterior_grp' column from the column corresponding to each individual's a priori group
posterior["posterior_grp"] = posterior.apply(lambda row: row.loc[row["grp"]], axis=1)


"""append posterior probabilities to principle components"""
# copy loadings df but with better column names.
df = dfs["ind.coord"].rename(columns=lambda x: x.split(".")[-1] if "ind.coord." in x else x)

# append the 'assign' and 'grp' columns from their respective df's as well as the two newly synthesised
# columns created in the 'posterior' df above.
df = df.join([dfs["assign"]["assign"], dfs["grp"]["grp"],
              posterior["posterior_assign"], posterior["posterior_grp"]])


"""append location information"""
# pull location data into a csv
loc_df = pd.read_csv(data_directory + "localities.csv")

# be sure to treat key as a string even if it's numeric
loc_df.key = loc_df.key.apply(str)

# join location data to working dataframe 'df'
df = df.merge(loc_df, on="key", how="left")


"""clean up nulls"""
df = df.applymap(lambda x: "NaN" if pd.isnull(x) else x)


"""output"""
df.to_csv(data_directory + "webapp_input.csv", index=False)
