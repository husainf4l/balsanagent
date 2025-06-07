from typing import Dict, List, Any, Tuple
from tools.db_tools import execute_sql_query
from tools.summary_tools import save_summary

def process_analysis(sales_tables: List[Tuple[str, str, str, str]], years: List[str], periods: List[str]) -> str:
    """Process sales analysis for the given tables, years, and periods."""
    print(f"\n=== Processing {len(sales_tables)} best tables ===")
    
    for schema, table, date_column, sales_column in sales_tables:
        print(f"\nAnalyzing table: {schema}.{table}")
        
        # Check data quality
        print("Checking data quality...")
        quality_check_query = f"""
        SELECT 
            COUNT(*) as total_rows,
            COUNT(CASE WHEN {sales_column} IS NULL OR {sales_column} = 0 THEN 1 END) as zero_or_null_count,
            MIN({sales_column}) as min_amount,
            MAX({sales_column}) as max_amount,
            AVG({sales_column}) as avg_amount
        FROM {schema}.{table}
        """
        
        try:
            quality_results = execute_sql_query.invoke({"query": quality_check_query})
            if not quality_results:
                print("Warning: No data quality results returned")
                continue
                
            print(f"Data quality results: {quality_results}")
            
            # Extract quality metrics
            total_rows = quality_results[0].get('total_rows', 0)
            zero_or_null_count = quality_results[0].get('zero_or_null_count', 0)
            
            if zero_or_null_count > 0:
                print(f"⚠️ Warning: Found {zero_or_null_count} records with zero or missing sales amounts")
            
            # Generate comparison query if years are specified
            if len(years) >= 2:
                print(f"\nGenerating comparison query for years: {years}")
                comparison_query = f"""
                SELECT 
                    EXTRACT(YEAR FROM {date_column}) as year,
                    SUM({sales_column}) as total_sales
                FROM {schema}.{table}
                WHERE EXTRACT(YEAR FROM {date_column}) IN ({', '.join(years)})
                """
                if periods:
                    print(f"Adding period conditions for: {periods}")
                    period_conditions = []
                    for period in periods:
                        months = period.split('-')
                        if len(months) == 2:
                            start_month, end_month = months
                            period_conditions.append(f"""
                            (EXTRACT(MONTH FROM {date_column}) BETWEEN 
                            EXTRACT(MONTH FROM DATE '{start_month.strip()} 1, 2024') AND 
                            EXTRACT(MONTH FROM DATE '{end_month.strip()} 1, 2024'))
                            """)
                    if period_conditions:
                        comparison_query += " AND (" + " OR ".join(period_conditions) + ")"
                
                comparison_query += f" GROUP BY EXTRACT(YEAR FROM {date_column}) ORDER BY year"
                print(f"Final comparison query: {comparison_query}")
                
                comparison_results = execute_sql_query.invoke({"query": comparison_query})
                if not comparison_results:
                    print("Warning: No comparison results returned")
                    continue
                    
                print(f"Comparison results: {comparison_results}")
                
                # Calculate year-over-year growth
                if len(comparison_results) >= 2:
                    sales_2024 = float(comparison_results[0]['total_sales'])
                    sales_2025 = float(comparison_results[1]['total_sales'])
                    growth = sales_2025 - sales_2024
                    growth_percent = (growth / sales_2024) * 100 if sales_2024 != 0 else 0
                    print(f"Calculated growth: {growth:,.2f} ({growth_percent:.1f}%)")
                    
                    # Save insight to summaries table
                    insight = f"Sales increased by {growth:,.2f} from {years[0]} to {years[1]} ({growth_percent:.1f}% growth)."
                    print(f"Saving insight: {insight}")
                    save_summary.invoke({"summary": insight, "query": comparison_query})
                    
                    # Generate response with data quality warnings and insights
                    response = f"Here is your {periods[0] if periods else 'yearly'} sales comparison for {years[0]} and {years[1]}:\n\n"
                    response += f"{periods[0] if periods else 'Year'} {years[0]} total sales: {sales_2024:,.2f}\n"
                    response += f"{periods[0] if periods else 'Year'} {years[1]} total sales: {sales_2025:,.2f}\n\n"
                    response += f"Insights:\n\n"
                    response += f"Sales increased by {growth:,.2f} from {years[0]} to {years[1]}.\n"
                    response += f"This is a year-over-year growth of about {growth_percent:.1f}% for the same period.\n"
                    response += f"This positive trend suggests improvements, but I recommend investigating the drivers (products, regions, or customers) and checking for one-off, seasonal, or repeatable factors.\n\n"
                    response += f"Owner's Summary: Your sales for {periods[0] if periods else 'the year'} increased nearly {growth_percent:.1f}% in {years[1]} compared to the same period in {years[0]}. If you want a breakdown by brand, city, or customer, just let me know.\n\n"
                    response += "Note: This response is based on early, incomplete prototype data sent by Al Bilsan Group on Monday, May 12, 2025, and may not reflect the final validated dataset."
                    
                    print("\n=== Final Response ===")
                    print(response)
                    return response
            
            # If no years specified, just return total sales
            print("\nNo years specified, calculating total sales...")
            total_query = f"SELECT SUM({sales_column}) as total_sales FROM {schema}.{table}"
            total_results = execute_sql_query.invoke({"query": total_query})
            if not total_results:
                print("Warning: No total sales results returned")
                continue
                
            print(f"Total sales results: {total_results}")
            
            response = f"Total sales from {schema}.{table}: {total_results[0]['total_sales']:,.2f}\n\nNote: This analysis is based on prototype data and may not reflect the final validated dataset."
            print("\n=== Final Response ===")
            print(response)
            return response
            
        except Exception as e:
            print(f"Error processing table {schema}.{table}: {str(e)}")
            continue
    
    return "Could not find suitable columns for sales amount and date in any sales table." 