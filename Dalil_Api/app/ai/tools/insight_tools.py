"""
Insight Detection Tools
=======================
Automated trend detection and anomaly identification.
"""

from typing import Any, Dict, List

import polars as pl

from app.config import get_logger

logger = get_logger(__name__)


class InsightTools:
    """Automated insight extraction from data."""

    @staticmethod
    def detect_numeric_outliers(
        df: pl.DataFrame, column: str, std_threshold: float = 2.0
    ) -> Dict[str, Any]:
        """
        Detect outliers using the Z-score method.
        Values beyond `std_threshold` standard deviations are flagged.
        """
        if column not in df.columns:
            return {"error": f"Column '{column}' not found"}

        series = df[column].drop_nulls()
        if series.dtype not in (pl.Int32, pl.Int64, pl.Float32, pl.Float64):
            return {"error": f"Column '{column}' is not numeric"}

        mean = series.mean()
        std = series.std()

        if std == 0:
            return {"outliers_count": 0, "outliers": []}

        z_scores = ((series - mean) / std).abs()
        outlier_mask = z_scores > std_threshold
        outliers = series.filter(outlier_mask).to_list()

        return {
            "column": column,
            "mean": round(mean, 2),
            "std": round(std, 2),
            "threshold": std_threshold,
            "outliers_count": len(outliers),
            "outlier_values": outliers[:20],  # Cap at 20
        }

    @staticmethod
    def detect_trends(
        df: pl.DataFrame,
        date_column: str,
        value_column: str,
    ) -> Dict[str, Any]:
        """
        Detect simple linear trends in time-series data.
        Returns direction, slope, and change percentage.
        """
        if date_column not in df.columns or value_column not in df.columns:
            return {"error": "Required columns not found"}

        try:
            sorted_df = df.sort(date_column)
            values = sorted_df[value_column].drop_nulls()

            if values.len() < 3:
                return {"error": "Not enough data points for trend detection"}

            # Simple trend: compare first half mean to second half mean
            mid = values.len() // 2
            first_half_mean = values[:mid].mean()
            second_half_mean = values[mid:].mean()

            if first_half_mean == 0:
                change_pct = 0
            else:
                change_pct = ((second_half_mean - first_half_mean) / first_half_mean) * 100

            direction = "increasing" if change_pct > 5 else "decreasing" if change_pct < -5 else "stable"

            return {
                "date_column": date_column,
                "value_column": value_column,
                "direction": direction,
                "change_percentage": round(change_pct, 2),
                "first_half_avg": round(first_half_mean, 2),
                "second_half_avg": round(second_half_mean, 2),
                "data_points": values.len(),
            }

        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def find_top_performers(
        df: pl.DataFrame,
        category_col: str,
        metric_col: str,
        top_n: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find top performing categories by a metric."""
        if category_col not in df.columns or metric_col not in df.columns:
            return []

        try:
            result = (
                df.group_by(category_col)
                .agg(pl.col(metric_col).sum().alias("total"))
                .sort("total", descending=True)
                .head(top_n)
            )

            return [
                {"category": str(row[0]), "total": row[1]}
                for row in result.iter_rows()
            ]
        except Exception:
            return []

    @staticmethod
    def generate_auto_insights(df: pl.DataFrame) -> List[Dict[str, str]]:
        """
        Automatically generate key insights from the dataset.
        Useful for initial data overview.
        """
        insights = []

        # Dataset size insight
        insights.append({
            "type": "summary",
            "title": "Dataset Overview",
            "description": f"Dataset contains {df.height:,} rows and {df.width} columns.",
        })

        # Missing data insight
        total_nulls = sum(df[col].null_count() for col in df.columns)
        if total_nulls > 0:
            null_pct = (total_nulls / (df.height * df.width)) * 100
            insights.append({
                "type": "anomaly",
                "title": "Missing Data Detected",
                "description": f"{total_nulls:,} missing values ({null_pct:.1f}% of all cells).",
            })

        # Numeric column insights
        for col in df.columns:
            if df[col].dtype in (pl.Int32, pl.Int64, pl.Float32, pl.Float64):
                series = df[col].drop_nulls()
                if series.len() > 0:
                    cv = (series.std() / series.mean() * 100) if series.mean() != 0 else 0
                    if cv > 100:
                        insights.append({
                            "type": "anomaly",
                            "title": f"High Variability in '{col}'",
                            "description": f"Coefficient of variation is {cv:.0f}%, indicating high spread.",
                        })

        return insights[:10]  # Cap at 10 insights
