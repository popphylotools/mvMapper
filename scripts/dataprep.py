#!/usr/bin/env python
# coding: utf-8

import os
import pandas as pd

data_directory = "./data/"


"""read in csv's from dapc analisis in R"""
# create a dict of short names and their respective .csv files
fns = {fn.strip().split(".csv")[0]: fn for fn in os.listdir(data_directory) if
       fn in ["assign.csv", "eig.csv", "ind.coord.csv", "posterior.csv", "grp.csv"]}

# create a dict of short names and dataframes sourced from the above .csv files
dfs = {n: pd.read_csv(data_directory + fn) for n, fn in fns.items()}


"""Make key's consistant across all dataframes"""
# for each dataframe
for n, df in dfs.items():
    # rename 0th column to key
    df.rename(columns={df.columns[0]: 'key'}, inplace=True)
    # treat keys as strings even if numeric
    df.key = df.key.apply(str)


"""extract posterior probabilities for a priori group (grp) and model predicted group (assign)"""
# create dataframe with better column names 
posterior = dfs["posterior"].rename(columns=lambda x: x.split(".")[-1] if "posterior." in x else x)

# join in the model predicted groups for each individule from the assign column of the assign dataframe
posterior = posterior.join(dfs["assign"]["assign"].apply(str))

# create a 'posterior_assign' column from the column corisponding to each individule's model predicted group
posterior["posterior_assign"] = posterior.apply(lambda row: row.loc[row["assign"]], axis=1)

# join in the a priori groups for each individule from the grp column of the grp dataframe
posterior = posterior.join(dfs["grp"]["grp"].apply(str))

# create a 'posterior_grp' column from the column corisponding to each individule's a priori group
posterior["posterior_grp"] = posterior.apply(lambda row: row.loc[row["grp"]], axis=1)


"""append posterior probabilities to principle components"""
# copy loadings df but with better column names.
df = dfs["ind.coord"].rename(columns=lambda x: x.split(".")[-1] if "ind.coord." in x else x)

# append the 'assign' and 'grp' columns from their respecteve df's as well as the two newly synthisised
# columns created in the 'posterior' df above.
df = df.join([dfs["assign"]["assign"], dfs["grp"]["grp"],
              posterior["posterior_assign"], posterior["posterior_grp"]])


"""append location information"""
# pull location data into a csv
loc_df = pd.read_csv(data_directory + "location.csv")

# be sure to treat key as a string even if it's numeric
loc_df.key = loc_df.key.apply(str)

# join location data to working dataframe 'df'
df = df.merge(loc_df, on="key", how="left")


"""clean up nulls"""
df = df.applymap(lambda x: "NaN" if pd.isnull(x) else x)


"""output"""
df.to_csv(data_directory + "webapp_input.csv", index=False)
