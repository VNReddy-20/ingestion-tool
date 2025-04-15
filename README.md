# Bidirectional ClickHouse & Flat File Data Ingestion Tool
This is a web-based application for bidirectional data ingestion between ClickHouse and Flat File (CSV). It supports JWT authentication for ClickHouse, allows column selection, and reports the number of records processed. The app includes a simple UI for configuring connections, selecting tables/columns, previewing data, and executing ingestion.
## Features

Bidirectional data flow: ClickHouse to Flat File and Flat File to ClickHouse.
UI for selecting source (ClickHouse or Flat File) and target.
ClickHouse connection with JWT token authentication.
Flat File (CSV) upload and processing.
Schema discovery and column selection.
Data preview (first 100 records).
Record count reporting after ingestion.
Basic error handling for connection, authentication, and ingestion.

## Prerequisites

Python 3.8+
Docker (for running ClickHouse locally)
ClickHouse instance (local or cloud) with example datasets (e.g., uk_price_paid)

## Setup Instructions

### Clone the Repository
git clone <your-repo-url>
cd ingestion-tool


### Set Up Virtual Environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


### Install Dependencies
pip install -r requirements.txt


### Set Up ClickHouse (Local)

Run ClickHouse using Docker:
docker run -d -p 8123:8123 -p 9000:9000 --name clickhouse clickhouse/clickhouse-server


Create a user with JWT token:
docker exec -it clickhouse clickhouse-client
CREATE USER test_user IDENTIFIED WITH plaintext_password BY 'your_jwt_token';
GRANT ALL ON *.* TO test_user;


Load example dataset (e.g., uk_price_paid):
CREATE DATABASE test_db;
CREATE TABLE test_db.uk_price_paid (
    price UInt32,
    date DateTime,
    postcode1 String,
    postcode2 String,
    type String,
    is_new UInt8,
    tenure String,
    paon String,
    saon String,
    street String,
    locality String,
    city String,
    district String,
    county String,
    ppd_category String,
    record_status String
) ENGINE = MergeTree ORDER BY date;
INSERT INTO test_db.uk_price_paid SELECT * FROM s3('https://clickhouse-public-datasets.s3.amazonaws.com/uk_price_paid/price_paid.csv', 'CSVWithNames');




### Create Uploads Folder
mkdir Uploads



## Running the Application

### Start the Flask App
python app.py


### Access the UI

Open your browser and go to http://localhost:5000.



## Configuration

### ClickHouse Source:

Host: localhost (for local Docker)
Port: 8123 (HTTP) or 8443 (HTTPS if configured)
Database: test_db
User: test_user
JWT Token: your_jwt_token


### Flat File Source:

Upload a CSV file (e.g., sample.csv).

Example CSV content:
id,name,age
1,Alice,25
2,Bob,30
3,Charlie,35





## Usage

Select source (ClickHouse or Flat File).
Enter connection details or upload a CSV file.
Click Connect to fetch tables.
Select a table and load columns.
Check desired columns and click Preview to see the first 100 records.
Select target (ClickHouse or Flat File).
Click Start Ingestion to transfer data.
View the result (record count or error message).

## Testing

### Test Case 1: ClickHouse to Flat File
Source: ClickHouse, table uk_price_paid, select columns price, city.
Target: Flat File.
Verify: CSV file (output_uk_price_paid.csv) created in Uploads with correct data and record count.


### Test Case 2: Flat File to ClickHouse
Source: Upload sample.csv, select columns name, age.
Target: ClickHouse, new table sample.
Verify: Table created in ClickHouse with correct data and record count.


### Test Case 3: Connection Failure
Enter invalid ClickHouse credentials.
Verify: Error message displayed in UI.


### Test Case 4: Data Preview
Select source and columns, click Preview.
Verify: First 100 records displayed in table.



## Notes

Flat File output is saved in the Uploads folder.
ClickHouse tables created from Flat Files use String type for simplicity.
Ensure ClickHouse is accessible and JWT token is valid.
CSV files must have headers.
