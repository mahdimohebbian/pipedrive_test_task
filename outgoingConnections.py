import dask.dataframe as ddf
import requests
import multiprocessing
from dotenv import load_dotenv
import os


class PipedriveDashboard:
    def __init__(self,aggregated_df,num_of_parallel_process):
        self.url_base = "https://api.pipedrive.com/v1"
        #Split DataFrame into smaller pieces for parallel processing
        self.smaller_dfs = self.split_dataframe(aggregated_df.compute(), num_of_parallel_process)
        self.num_of_parallel_process = num_of_parallel_process
        
    def split_dataframe(self,df, n):
        chunk_size = len(df) // n
        smaller_dfs = []
        for i in range(n - 1):
            start = i * chunk_size
            end = (i + 1) * chunk_size
            smaller_dfs.append(df.iloc[start:end])
        
        smaller_dfs.append(df.iloc[(n - 1) * chunk_size:])
        
        return smaller_dfs
    
    def process_deals_in_parallel(self):
        #Multiprocessing with limited number of parallel processes
        with multiprocessing.Pool(processes=self.num_of_parallel_process) as pool:
            pool.map(self.dealCheck, self.smaller_dfs)

    def updateDeal(self,id, new_body):
        url = f"{self.url_base}/deals/{id}"
        response = requests.put(url=url, data=new_body, params={"api_token": os.getenv('PIPEDRIVE_API_KEY')})
        return response.json()["success"]
        

    def createDeal(self,payload):
        url = f"{self.url_base}/deals"
        response = requests.post(url=url, data=payload, params={"api_token": os.getenv('PIPEDRIVE_API_KEY')})
        return response.json()["success"]


    def dealCheck(self,aggregated_df):
        url = f"{self.url_base}/deals"    
        start = 0
        data = []
        while True:
            all_deal_data = requests.get(url, params={"api_token": os.getenv('PIPEDRIVE_API_KEY'), "limit": 100, "start": start}, headers={"Content-Type": "application/json"}).json()
            if all_deal_data["data"] is not None:
                data.extend(all_deal_data["data"])
            
            if all_deal_data["additional_data"]["pagination"]["more_items_in_collection"] == False:
                break
            start = all_deal_data["additional_data"]["pagination"]["next_start"]
        
        for i,row in aggregated_df.iterrows():
            found = False
            
            for item in data:
                if row["internal_id"] == item["ab39ab4f525e7490e14cb5c78e41cc25aeb08a79"]:
                    found = True
                    if row["amount"] != item["value"]:
                        result = self.updateDeal(item["id"], {"value": row["amount"]})
                        if result:
                            print(f'Deal ID {item["id"]} updated.')
                        else:
                            print(f'Deal ID {item["id"]} update failed.')
                    break
                
            if not found:
                payload = {
                    "title": f'{row["last_name"]}{row["first_name"]}',
                    "value": f'{row["amount"]}',
                    "ab39ab4f525e7490e14cb5c78e41cc25aeb08a79": f'{row["internal_id"]}'
                }
                result = self.createDeal(payload)
                if result:
                    print(f'Deal named :{row["last_name"]}{row["first_name"]} created.')
                else:
                    print(f'Deal creation failed.')


    def cleanDeals(self):
        url = f"{self.url_base}/deals"
        start = 0
        data = []
        while True:
            all_deal_data = requests.get(url, params={"api_token": os.getenv('PIPEDRIVE_API_KEY'), "limit": 100, "start": start}, headers={"Content-Type": "application/json"}).json()
            data.extend(all_deal_data["data"])
            
            if all_deal_data["additional_data"]["pagination"]["more_items_in_collection"] == False:
                break
            start = all_deal_data["additional_data"]["pagination"]["next_start"]
        
        ids = [str(item["id"]) for item in data]
        ids = ",".join(ids)
        
        res = requests.delete(url=url, params={"api_token": os.getenv('PIPEDRIVE_API_KEY'), "ids": ids}, headers={"Content-Type": "application/json"})
        if res.json()["success"]:
            print("Deals are cleaned out.")
            return True
        else:
            print(res.json())
            return False