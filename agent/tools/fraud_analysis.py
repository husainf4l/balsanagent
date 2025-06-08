from typing import Any, List

def detect_suspicious_transactions(execute_sql_query, table: str, amount_threshold: float = 100000.0) -> str:
    """
    Detects potentially suspicious transactions in the given table.
    Flags:
      - Transactions above a high amount threshold
      - Transactions at unusual hours (e.g., late night)
      - Multiple transactions from the same user in a short time
    Returns a summary string.
    """
    # 1. Large transactions
    large_tx_query = f"""
        SELECT * FROM {table}
        WHERE amount > {amount_threshold}
        ORDER BY amount DESC
        LIMIT 5
    """
    large_tx = execute_sql_query(large_tx_query)

    # 2. Transactions at odd hours (e.g., between 00:00 and 05:00)
    odd_hour_query = f"""
        SELECT * FROM {table}
        WHERE EXTRACT(HOUR FROM timestamp) BETWEEN 0 AND 5
        ORDER BY timestamp DESC
        LIMIT 5
    """
    odd_hour_tx = execute_sql_query(odd_hour_query)

    # 3. Multiple transactions from same user in 1 day
    rapid_tx_query = f"""
        SELECT user_id, COUNT(*) as tx_count, MIN(timestamp) as first_tx, MAX(timestamp) as last_tx
        FROM {table}
        WHERE timestamp >= NOW() - INTERVAL '1 day'
        GROUP BY user_id
        HAVING COUNT(*) > 5
        ORDER BY tx_count DESC
        LIMIT 5
    """
    rapid_tx = execute_sql_query(rapid_tx_query)

    result = "Fraud Analysis Report:\n"
    result += f"\nLarge transactions (>{amount_threshold}):\n" + (str(large_tx) if large_tx else "None found")
    result += f"\n\nTransactions at odd hours (00:00-05:00):\n" + (str(odd_hour_tx) if odd_hour_tx else "None found")
    result += f"\n\nUsers with >5 transactions in 1 day:\n" + (str(rapid_tx) if rapid_tx else "None found")
    return result
