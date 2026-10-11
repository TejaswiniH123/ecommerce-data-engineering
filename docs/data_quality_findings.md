\# Data Quality Findings — Olist E-Commerce Dataset



\## 1. Dataset Overview



The project uses the Olist Brazilian E-Commerce Public Dataset. The source data contains customer, order, order-item, payment, product, seller, and review records.



\## 2. Initial Profiling Results



| Table | Source Rows | Key Check |

|---|---:|---|

| Customers | 99,441 | No missing or duplicate customer IDs |

| Orders | 99,441 | No missing or duplicate order IDs |

| Order items | 112,650 | No missing or duplicate (order\_id, order\_item\_id) keys |

| Payments | 103,886 | No missing or duplicate (order\_id, payment\_sequential) keys |

| Products | 32,951 | No missing or duplicate product IDs |

| Sellers | 3,095 | No missing or duplicate seller IDs |

| Reviews | 99,224 | Repeated review IDs detected |



\## 3. Review Data Investigation



\- Total review rows: 99,224.

\- Unique review IDs: 98,410.

\- Review IDs appearing more than once: 789.

\- Extra occurrences beyond the first: 814.

\- Exact duplicate extra rows: 0.

\- Orders with multiple review rows: 547.

\- Orders with multiple distinct review IDs: 547.



\### Decision



Preserve all original review records. Do not deduplicate solely on review\_id or order\_id. Investigate the source's intended review uniqueness rules before selecting the final analytical grain.



\## 4. Missing Values



\- Order lifecycle timestamps are missing for some orders; validate these against order status.

\- Product category and descriptive attributes are missing for some products.

\- Review titles and messages are optional fields and are frequently empty.



Missing values should not automatically cause records to be discarded.



\## 5. Pipeline Quality Principles



1\. Preserve original source files.

2\. Profile data before transformation.

3\. Validate keys, nulls, data types, and business rules.

4\. Record quality failures and their counts.

5\. Never silently delete questionable records.

6\. Keep source-data anomalies distinct from pipeline-generated errors.



\## 6. Limitations



These findings describe the source dataset and do not establish the underlying cause of every anomaly. Further validation is required before enforcing additional business rules.





\## 7. Investigation: Orders Without Order Items



A total of 775 orders have no corresponding records in the `order\_items` table.



\### Distribution by order status



| Order Status | Orders Without Items |

|---|---:|

| Unavailable | 603 |

| Canceled | 164 |

| Created | 5 |

| Invoiced | 2 |

| Shipped | 1 |

| \*\*Total\*\* | \*\*775\*\* |



All 775 orders have at least one associated payment record.



\### Interpretation



Most affected orders are unavailable or canceled. However, the existence of a payment record does not establish whether the payment was successfully captured, refunded, or retained.



\### Decision



\- Preserve all 775 orders and their payment records.

\- Do not fabricate missing order-item records.

\- Exclude orders without item records from item-based sales calculations.

\- Investigate payment amounts and order statuses separately before making financial conclusions.

\- Keep this condition as a documented data-quality warning rather than an automatic pipeline failure.



The investigation identifies the pattern but does not establish the root cause of every affected order.