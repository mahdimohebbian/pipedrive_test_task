# README
# Test task for Data Platform Engineer
This application is written in Python programming language (version 3.10).

## Code flow in summary
- The source of data in the current scenario are 3 different csv files in a github repository.
- Incoming data are imported as [Dask][DaskLink_url] data frames instead of Python native Pandas data frame. (for memory efficiency)
- Data from 3 different sources are joined together in a unified single data frame containing all of the necessary data.
- Required transformation will be applied to the data frame at this stage. 
-- _The hypothetical data transformation scenario: if the payment of a deal is in "completed" status and the payment is above 2000 Euros, there will be a 20% additional compensation award added to the payment value._
- The data is filtered, cleaned and ready to be deployed to Pipedrive dashboard (via Pipedrive API).
- The data is split into equal pieces and each piece will be processed and transferred to Pipedrive dashboard on a separate parallel process (for time efficiency).

## Requirements
The project does not require any particular python dependencies or even Python installed.<br />
This project is containerized using Docker and by executing the `deploy.sh` bash script you can activate the "deal synchronization" task. The only requirement is to grant execution permission to `deploy.sh` file, have a Docker engine running and have a copy of the .env file available in the project root folder according to the following :<br />
```bash
application/
│
├── __pycache__/
├── .env
├── app.py
├── deploy.sh
├── Dockerfile
├── incomingConnections.py
├── outgoingConnections.py
├── README.md
└── equirements.txt
```
the content of `.env` file should include `PIPEDRIVE_API_KEY` and `PARALLEL_PROCESS_NUMBER`.<br />
example :
```bash
PIPEDRIVE_API_KEY=************************
PARALLEL_PROCESS_NUMBER=4
```
## Some notes regarding the additional questions section

- **Scenarios with 100K or 1 million deals:**
At this rate the chance of memory shortage is lower than having run time efficiency issues. A normal sequential process will take a long time to process and transfer all the data.<br />
The best solution for moderately large data (like 1 million rows) is to distribute the process among all available CPUs on the host machine in order to process the data in parallel as it is implemented in the current project. (faster execution)<br />
But on excessively large data (100 millions and more) the best solution are distributed system data processing tools such as Apache Spark (EMR on AWS) to distribute the data among different worker nodes for processing and transfer.<br />

- **Source  pluggable capabilities:**
The current project architecture consist of three main sectors:<br />
1- incoming data pipe (**BLOCK 1**)<br />
2- data transformation (**BLOCK 2**)<br />
3- outgoing data pipe (**BLOCK 3**)<br />
In the current source code the connection between block 1 and 2 is where the CSV files are received and converted into a Dask dataframe, and the connection between block 2 and 3 is where the transformed dataframe was sent to pipedrive dashboard using API calls.<br />
Essentially a new incoming data pipe block would have to receive the data from its original source (HTTP request, S3, AWS DynamoDB or etc) and convert the data into a dask data frame and **pass it** to the next block (block 2).
With the same logic a new outgoing data pipe would also have to **accept** the data as a dask data frame and perform the necessary transformation to transfer the data from data frame to the destination (Postgres database, another S3 bucket, different API endpoints and etc.)<br />

- **Containerised solution:**
The current solution is indeed containerised and can be triggered directly from CLI with minimum requirements on certain interval (daily, weekly or even hourly). From personal experience this solution can also be implemented along Apache Airflow for orchestration and scheduling (triggering the `deploy.sh` script on the server in certain intervals) or implementing the same logic in an AWS lambda function (serverless solution) where we can specify scheduled trigger to start up the task on certain intervals and schedules.

[DaskLink_url]: <https://docs.dask.org/en/stable>