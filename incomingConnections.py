import dask.dataframe as ddf
import requests
import multiprocessing
from dotenv import load_dotenv
import os

class SharedFiles:
    def __init__(self,customers_url,orders_url,payments_url):
        self.customers_url = customers_url
        self.orders_url = orders_url
        self.payments_url = payments_url
        
    def data_transfer(self):
        #Using Dask instead of Pandas for memory efficiency (Dask can operate within disk in case the incoming data was larger than the memory)
        aggregated_df = ddf.read_csv(self.customers_url)
        aggregated_df = aggregated_df.merge(ddf.read_csv(self.orders_url), how="inner", left_on="id", right_on="user_id")
        aggregated_df = aggregated_df.merge(ddf.read_csv(self.payments_url), how="inner", left_on="id_y", right_on="order_id")
        aggregated_df = aggregated_df.drop(columns=["id_x", "id_y"])
        aggregated_df = aggregated_df.rename(columns={"id": "payment_id"})
        
        return aggregated_df
