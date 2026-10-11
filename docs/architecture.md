\# Project Architecture



```mermaid

flowchart TD

&#x20;   A\["Olist CSV files"] --> B\["Python ETL"]

&#x20;   B --> C\[("PostgreSQL warehouse")]

&#x20;   B --> D\[("ETL audit log")]

&#x20;   C --> E\["Python data validation"]

&#x20;   C --> F\["dbt staging views"]

&#x20;   F --> G\["Monthly sales mart"]

&#x20;   F --> H\["Category performance mart"]

&#x20;   G --> I\["dbt tests and reconciliation"]

&#x20;   H --> I





Main components

\- Source: Historical Olist e-commerce CSV files.

\- Ingestion: Python scripts load data into PostgreSQL.

\- Audit: ETL run records capture execution status and processing metrics.

\- Quality: Python validation and automated tests check important data rules.

\- Transformation: dbt staging views and analytical tables prepare data for reporting.

\- Analytics: SQL models calculate monthly sales, category performance, and related metrics.

