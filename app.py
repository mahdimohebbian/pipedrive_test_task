import dask.dataframe as ddf
import requests
import multiprocessing
from dotenv import load_dotenv
import os
from outgoingConnections import PipedriveDashboard
from incomingConnections import SharedFiles
import logging


# a custom function to delete all existing deals for test and development.
def cleanDeals():
    url = f"https://api.pipedrive.com/v1/deals"
    start = 0
    data = []
    while True:
        all_deal_data = requests.get(url, params={"api_token": os.getenv('PIPEDRIVE_API_KEY'), "limit": 200, "start": start}, headers={"Content-Type": "application/json"}).json()
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
    

if __name__ == "__main__":
    
    logging.basicConfig(level=logging.INFO)
    load_dotenv()
    num_of_parallel_process = int(os.getenv('PARALLEL_PROCESS_NUMBER'))
    
    #--------------------- uncomment the following lines to clear the deals on Pipedrive dashboard.
    # try :
    #     cleanDeals()
    #     exit()
    # except:
    #     exit() # for situation where the dashboard is already empty
    #---------------------
    
    # BLOCK 1
    customers_url = "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/main/seeds/raw_customers.csv"
    orders_url = "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/main/seeds/raw_orders.csv"
    payments_url = "https://raw.githubusercontent.com/dbt-labs/jaffle-shop-classic/main/seeds/raw_payments.csv"
    
    
    try :
        files_source = SharedFiles(customers_url,orders_url,payments_url)
        aggregated_df = files_source.data_transfer()
    except Exception as ex:
        logging.error(f"data ingestion failed: {ex.__str__()}")
        exit()
    logging.info("Data ingestion, successful.")
    
    
    #BLOCK 2
    #creating a custom internal_id by combining user_id, order_id, and payment_id
    try :
        aggregated_df["internal_id"] = (aggregated_df["user_id"].astype(str) + "." +aggregated_df["order_id"].astype(str) + "."+aggregated_df["payment_id"].astype(str))

        #setting a hypothetical payment amount threshold of 2000 where "completed" orders above this threshold would receive 20% additional value to the original amount as compensation.
        condition = ( aggregated_df["amount"] > 2000 ) & ( aggregated_df["status"] == "completed" )
        aggregated_df["amount"] = aggregated_df["amount"].where(~condition, aggregated_df["amount"]*1.2)
    except Exception as ex:
        logging.error(f"Data transformation failed: {ex.__str__()}")
        exit()
    logging.info("Data transformation, successful")
    
    
    # BLOCK 3
    #splitting up the aggregated data frame into equal smaller pieces for parallel processing of each batch to save time. (processing time efficiency)
    try :
        pipedrive_connector = PipedriveDashboard(aggregated_df,num_of_parallel_process)
        pipedrive_connector.process_deals_in_parallel()
    except Exception as ex:
        logging.error(f"Data transfer to destination failed: {ex.__str__()}")
        exit()
    
    logging.info("Data transfer to destination, successful")
