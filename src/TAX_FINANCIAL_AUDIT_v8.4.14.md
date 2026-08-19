# Tax & Financial Integrity Audit v8.4.15

- Monetary arithmetic is normalized to Decimal(0.01) with ROUND_HALF_UP.
- Tax-period validation rejects end <= start.
- Duplicate tax reports for the same user/type/period are prevented in application code and by a unique DB index.
- NPD quarterly calculation no longer subtracts expenses/deductions from the tax base.
- Accounting transaction creation rejects non-RUB transactions to prevent mixed-currency aggregation in the tax engine.
- Calculator responses no longer convert money to binary floating point.
- Transaction amount has a DB positive-value constraint.

## Important scope note
Tax rules vary by taxpayer status, counterparty type, region, period and applicable law. The application must not present the calculator as an official FNS determination. Actual filing/submission must use verified current FNS integrations and current statutory rules.
