# SQLite Cache Queries

This guide provides common SQL queries to inspect and manage the `market_analysis.db` used by the caching layer.

## Accessing the Database

You can use the `sqlite3` CLI tool to run these queries:

```bash
sqlite3 market_analysis.db
```

## Common Queries

### 1. View All Cached Entries
List all entries stored in the cache.
```sql
SELECT id, tool_name, cache_key, datetime(created_at, 'unixepoch', 'localtime') as created_at_local 
FROM api_cache;
```

### 2. View Graph-Level Analysis Results
These are the full results returned to the user, cached after intent analysis.
```sql
SELECT cache_key, response_data 
FROM api_cache 
WHERE tool_name = 'market_graph';
```

### 3. Search for a Specific Ticker
Find all cached data (news, ratios, graph results) for a specific stock.
```sql
SELECT * 
FROM api_cache 
WHERE cache_key LIKE '%INFY.NS%';
```

### 4. Check Raw Tool Data (Yahoo/Duck)
Inspect raw data fetched from external APIs.
```sql
SELECT tool_name, cache_key, response_data 
FROM api_cache 
WHERE tool_name IN ('yahoo_finance', 'duckduckgo');
```

### 5. Check Cache Expiry Status
See how old the entries are.
```sql
SELECT tool_name, cache_key, 
       (strftime('%s','now') - created_at) / 3600.0 as age_hours 
FROM api_cache 
ORDER BY age_hours ASC;
```

### 6. Clear the Cache
Delete all entries to force fresh API calls.
```sql
DELETE FROM api_cache;
```

### 7. View Table Schema
```sql
.schema api_cache
```
