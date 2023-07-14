# find church-owned lots in SF, based on ReportAll's county data
import pandas as pd

df = pd.read_csv("SF_reportall.csv", skiprows=2, low_memory=False)
churches = df[df["land_use_code"] == "Churches,Convents,Rectories"]
church_owners = churches["owner"]
church_owned = df[df["owner"].isin(church_owners)]
church_owned.to_csv("church_owned_SF.csv", index=False)
church_owned_count = church_owned["owner"].value_counts()
church_owned_count.to_csv("church_owners_total_count.csv")
