
# coding: utf-8

# In[ ]:

import os

import pandas as pd
import numpy as np

data_directory = "../data/"


# In[ ]:

# read in csv's from dapc analisis in R
fns = {fn.strip().split(".csv")[0]:fn for fn in os.listdir(data_directory) if fn in ["assign.csv", "eig.csv", "ind.coord.csv", "posterior.csv", "grp.csv"]}
dfs = {n:pd.read_csv(data_directory + fn) for n,fn in fns.items()}

# rename 0th column to key
for n,df in dfs.items():
    df.rename(columns={df.columns[0]: 'key'}, inplace=True)

# extract posterior probabilities for a priori group (grp) and model predicted group (assign)
posterior = dfs["posterior"].rename(columns=lambda x: x.split(".")[-1] if "posterior." in x else x)
posterior = posterior.join(dfs["assign"]["assign"])
posterior["posterior_assign"] = posterior.apply(lambda row: row[row["assign"]], axis=1)
posterior = posterior.join(dfs["grp"]["grp"])
posterior["posterior_grp"] = posterior.apply(lambda row: row[row["grp"]], axis=1)

# append posterior probabilities to principle components 
df = dfs["ind.coord"].rename(columns=lambda x: x.split(".")[-1] if "ind.coord." in x else x)
df = df.join([dfs["assign"]["assign"], dfs["grp"]["grp"],
              posterior["posterior_assign"], posterior["posterior_grp"]])


# In[ ]:

# append location information
loc_df = pd.read_csv(data_directory + "location.csv")
df = df.merge(loc_df, on="key", how="left")


# In[ ]:

# clean up nulls
df = df.applymap(lambda x: "NaN" if pd.isnull(x) else x)

# output
df.to_csv(data_directory + "webapp_data.csv", index=False)

