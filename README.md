\# E-Commerce Data Engineering Platform



An end-to-end data engineering project that ingests e-commerce CSV data, loads it into PostgreSQL, performs data-quality validation, supports incremental loading, and builds analytical data marts using dbt.



\## Project Overview



This project uses the public Brazilian E-Commerce dataset from Olist to demonstrate a practical data engineering workflow, from raw files to analytics-ready data.



\*\*Project goals\*\*

\- Build a reproducible Python-based ETL pipeline.

\- Load relational data into PostgreSQL with appropriate keys and relationships.

\- Implement full-refresh and incremental loading patterns.

\- Track pipeline execution through an ETL audit log.

\- Validate data quality using Python and automated tests.

\- Transform warehouse data into analytical models using dbt.

\- Reconcile analytical metrics against source tables.



\## Technology Stack



\- \*\*Language:\*\* Python

\- \*\*Database:\*\* PostgreSQL 18

\- \*\*SQL transformations:\*\* dbt Core and dbt-postgres

\- \*\*Data testing:\*\* pytest and dbt data tests

\- \*\*Database connectivity:\*\* psycopg2

\- \*\*Configuration:\*\* python-dotenv

\- \*\*Version control:\*\* Git



The project runs locally without Docker.



\## Architecture



```text

Olist CSV Dataset

&#x20;       |

&#x20;       v

Raw CSV Files

&#x20;       |

&#x20;       v

Python ETL Pipeline

&#x20;       |

&#x20;       v

PostgreSQL Data Warehouse

&#x20;       |

&#x20;       +----------------------+

&#x20;       |                      |

&#x20;       v                      v

Data Quality Validation   ETL Audit Log

&#x20;       |

&#x20;       v

dbt Staging Models

&#x20;       |

&#x20;       v

dbt Analytical Marts

&#x20;       |

&#x20;       +----------------------+

&#x20;       |                      |

&#x20;       v                      v

Monthly Sales          Category Performance

&#x20;       |

&#x20;       v

Data Tests and Reconciliation

```



\## Data Source



Dataset: \[Brazilian E-Commerce Public Dataset by Olist](https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce)



The dataset contains historical Brazilian e-commerce orders and related customer, product, seller, payment, review, and order-item records.



The source data covers approximately 2016–2018 and is not live transaction data.



Download the dataset from Kaggle and place the extracted CSV files in `data/raw/`. Do not commit the raw dataset to this repository.



Review the dataset's licence and attribution requirements before redistributing data or derived materials.



\## Project Structure



```text

ecommerce-data-engineering/

├── config/

├── data/

│   ├── raw/

│   ├── processed/

│   ├── rejected/

│   ├── incoming/

│   └── archive/

├── docs/

│   └── data\_quality\_findings.md

├── ecommerce\_analytics/

│   ├── models/

│   │   ├── staging/

│   │   └── marts/

│   ├── tests/

│   └── dbt\_project.yml

├── logs/

├── sql/

├── src/

├── tests/

├── .gitignore

├── requirements.txt

└── README.md

```



\## Core Features



\### 1. Python ETL



\- Loads CSV data into PostgreSQL.

\- Supports full-refresh loading and selected incremental loaders.

\- Uses database transactions for the full-refresh pipeline.

\- Tracks execution status and row-count metrics in an ETL audit table.

\- Provides separate scripts for validation and warehouse-count verification.



\*\*Important:\*\* The full-refresh pipeline truncates and reloads warehouse tables. Run it only when a full reload is intended.



\### 2. Data Quality



Python validation checks include:

\- Expected row counts.

\- Foreign-key relationship integrity.

\- Invalid review scores.

\- Negative item prices, freight values, and payment values.

\- Orders without order items.

\- Repeated review identifiers.



Repeated review IDs are investigated rather than automatically deduplicated, because multiple records can represent distinct source records.



\### 3. PostgreSQL Warehouse



The warehouse contains customer, order, product, seller, order-item, payment, review, and category-translation tables.



Primary keys, composite keys, and foreign-key constraints protect relational integrity.



\### 4. Incremental Loading and Auditability



Incremental loaders support customer loading, order upserts, and order-item loading.



The ETL audit log records pipeline status and execution metrics, including input, inserted, updated, and unchanged row counts where supported.



\### 5. dbt Transformations



The dbt project includes five staging models:



\- `stg\_orders`

\- `stg\_customers`

\- `stg\_order\_items`

\- `stg\_products`

\- `stg\_product\_category\_translation`



It also includes two analytical marts:



\- `monthly\_sales`

\- `category\_performance`



The staging models are views, while the analytical marts are tables.



\### 6. Data Testing and Reconciliation



The project uses Python tests and dbt data tests to check data quality.



The monthly and category sales marts have been reconciled against the underlying PostgreSQL tables.



\## Business Metrics



\### Monthly Sales



The `monthly\_sales` mart reports:

\- Delivered orders containing items.

\- Total order items.

\- Item gross sales.

\- Freight.

\- Item gross sales plus freight.

\- Average order value, calculated as item gross sales divided by delivered orders containing items.



\### Category Performance



The `category\_performance` mart reports:

\- Category-level item counts.

\- Distinct delivered orders per category.

\- Item gross sales.

\- Percentage share of total item gross sales.



Item gross sales exclude freight. Orders without items are not assigned fabricated item revenue.



\## Verified Results



Results from the current local run:



| Metric | Result |

|---|---:|

| Customer records | 99,441 |

| Order records | 99,441 |

| Product records | 32,951 |

| Seller records | 3,095 |

| Order-item records | 112,650 |

| Payment records | 103,886 |

| Review records | 99,224 |

| dbt models | 7 |

| dbt data tests | 23 passed |

| Monthly sales periods | 23 |

| Monthly mart item gross sales | BRL 13,221,498.11 |

| Category mart item gross sales | BRL 13,221,498.11 |



These are results from the current local dataset and are not live business metrics.



\## Local Setup



\### Prerequisites



\- Windows with PowerShell, or an equivalent environment.

\- Python 3.11.

\- PostgreSQL 18.

\- Git.



\### 1. Clone the repository



```powershell

git clone <YOUR\_GITHUB\_REPOSITORY\_URL>

cd ecommerce-data-engineering

```



\### 2. Create and activate a virtual environment



```powershell

python -m venv .venv

.\\.venv\\Scripts\\Activate.ps1

```



\### 3. Install dependencies



```powershell

python -m pip install --upgrade pip

pip install -r requirements.txt

```



\### 4. Configure environment variables



Create a local `.env` file with your PostgreSQL connection settings:



```text

PGHOST=localhost

PGPORT=5432

PGDATABASE=ecommerce\_dw

PGUSER=postgres

PGPASSWORD=<YOUR\_LOCAL\_PASSWORD>

```



Never commit `.env` or expose database credentials.



\### 5. Prepare PostgreSQL



Create the `ecommerce\_dw` database and apply the SQL schema scripts in the order required by the project. Obtain the dataset separately and place the CSV files in `data/raw/`.



Review the Python ETL scripts and database configuration before running any loader. The full-refresh loader replaces existing warehouse table contents.



\### 6. Run validation and tests



Activate the virtual environment, configure the database, and run the applicable project scripts and automated tests.



For Python tests:



```powershell

python -m pytest -v

```



For dbt, first ensure your local `.env` variables are loaded into the process environment and that `profiles.yml` is configured:



```powershell

dbt debug --project-dir .\\ecommerce\_analytics

dbt parse --project-dir .\\ecommerce\_analytics

dbt run --project-dir .\\ecommerce\_analytics

dbt test --project-dir .\\ecommerce\_analytics

```



Generate and serve dbt documentation:



```powershell

dbt docs generate --project-dir .\\ecommerce\_analytics

dbt docs serve --project-dir .\\ecommerce\_analytics

```



\## Limitations and Future Improvements



\- The source dataset is historical, not a real-time feed.

\- Incremental processing currently focuses on selected entities rather than a complete CDC implementation.

\- The source dataset does not provide a dedicated refunds table, so net revenue after refunds is not calculated.

\- Automated scheduling and production deployment can be added later.

\- Further improvements could include a BI dashboard, more comprehensive integration tests, and cloud deployment.