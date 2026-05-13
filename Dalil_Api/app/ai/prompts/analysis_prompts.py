"""
Analysis Prompt Templates
=========================
Specialized prompts for different types of data analysis tasks.
"""

TREND_DETECTION_PROMPT = """Analyze the following dataset for trends.

{schema}

SAMPLE DATA:
{sample}

Look for:
1. Time-based trends (increasing/decreasing patterns)
2. Seasonal patterns
3. Growth rates
4. Category-level trends

Write pandas code using `df` to compute the trends, then explain findings in business terms.
"""

ANOMALY_DETECTION_PROMPT = """Analyze the following dataset for anomalies and outliers.

{schema}

SAMPLE DATA:
{sample}

Look for:
1. Statistical outliers (values beyond 2 standard deviations)
2. Unusual patterns or sudden changes
3. Missing data patterns
4. Inconsistent values

Write pandas code using `df` to detect anomalies, then explain each finding.
"""

OPTIMIZATION_PROMPT = """Based on the following dataset, suggest business optimizations.

{schema}

SAMPLE DATA:
{sample}

Provide actionable recommendations for:
1. Revenue optimization
2. Cost reduction
3. Inventory management
4. Customer retention
5. Operational efficiency

Support each recommendation with data-driven reasoning.
"""

GENERAL_ANALYSIS_PROMPT = """You have access to a dataset with the following schema:

{schema}

SAMPLE DATA:
{sample}

{conversation_context}

USER QUESTION: {question}

Instructions:
- If computation is needed, write Python code using pandas with `df` as the DataFrame variable
- The `df` DataFrame has these exact columns: {column_names}
- Base your answer ONLY on the data available
- Be specific with numbers and percentages
"""

INSIGHT_GENERATION_PROMPT = """Generate key business insights from this dataset.

{schema}

Write pandas code using `df` to extract the top 5 most important insights.
Focus on:
- Revenue drivers
- Performance metrics
- Growth opportunities
- Risk factors
"""
