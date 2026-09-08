import re
import numpy as np
import pandas as pd
import plotly.express as px

def resolve_column(df, requested):
    if not requested:
        return None
    requested = str(requested).strip().lower()
    exact = {str(c).lower(): c for c in df.columns}
    if requested in exact:
        return exact[requested]

    normalized = {
        re.sub(r"[^a-z0-9]", "", str(c).lower()): c
        for c in df.columns
    }
    key = re.sub(r"[^a-z0-9]", "", requested)
    if key in normalized:
        return normalized[key]

    for c in df.columns:
        if requested in str(c).lower():
            return c
    return None

def execute_plan(datasets, plan):
    results = []
    figures = []

    for step in plan.get("steps", []):
        action = step.get("action")
        dataset_name = step.get("dataset")
        df = datasets.get(dataset_name)

        if df is None:
            # Fall back to the first dataset if planner omitted the exact name.
            if not datasets:
                raise ValueError("No datasets available.")
            dataset_name, df = next(iter(datasets.items()))

        if action == "profile":
            results.append({
                "step": step.get("description", "Profile"),
                "dataset": dataset_name,
                "result": {
                    "shape": list(df.shape),
                    "columns": [str(c) for c in df.columns],
                    "missing": df.isna().sum().to_dict(),
                    "duplicates": int(df.duplicated().sum()),
                },
            })

        elif action == "aggregate":
            metric = resolve_column(df, step.get("metric"))
            group_by = resolve_column(df, step.get("group_by"))
            date_col = resolve_column(df, step.get("date_column"))
            agg = step.get("aggregation", "sum")

            if not metric:
                raise ValueError("Could not identify the requested metric column.")
            work = df.copy()

            if date_col:
                work[date_col] = pd.to_datetime(work[date_col], errors="coerce")
                work = work.dropna(subset=[date_col])
                freq = step.get("frequency", "M")
                work["_period"] = work[date_col].dt.to_period(freq).astype(str)
                group_cols = ["_period"] + ([group_by] if group_by else [])
            else:
                group_cols = [group_by] if group_by else []

            if not group_cols:
                value = getattr(work[metric], agg)()
                table = pd.DataFrame({"value": [float(value)]})
            else:
                table = work.groupby(group_cols, dropna=False)[metric].agg(agg).reset_index()
                table = table.rename(columns={metric: "value"})

            results.append({
                "step": step.get("description", "Aggregate"),
                "dataset": dataset_name,
                "result": table.head(100).to_dict(orient="records"),
                "columns": table.columns.tolist(),
            })

            if step.get("visualize") and len(table) > 1:
                x = table.columns[0]
                color = table.columns[1] if len(table.columns) > 2 else None
                fig = px.line(
                    table,
                    x=x,
                    y="value",
                    color=color,
                    markers=True,
                    title=step.get("chart_title", step.get("description", "Trend")),
                )
                fig.update_layout(template="plotly_white")
                figures.append(fig)

        elif action == "top_n":
            metric = resolve_column(df, step.get("metric"))
            group_by = resolve_column(df, step.get("group_by"))
            n = int(step.get("n", 10))
            if not metric or not group_by:
                raise ValueError("Top-N requires both metric and group-by columns.")
            table = (
                df.groupby(group_by, dropna=False)[metric]
                .sum()
                .sort_values(ascending=False)
                .head(n)
                .reset_index()
            )
            table.columns = [str(group_by), "value"]
            results.append({
                "step": step.get("description", "Top N"),
                "dataset": dataset_name,
                "result": table.to_dict(orient="records"),
            })
            fig = px.bar(
                table,
                x="value",
                y=str(group_by),
                orientation="h",
                title=step.get("chart_title", f"Top {n}"),
            )
            fig.update_layout(template="plotly_white")
            figures.append(fig)

        elif action == "correlation":
            cols = [resolve_column(df, c) for c in step.get("columns", [])]
            cols = [c for c in cols if c]
            if len(cols) < 2:
                cols = df.select_dtypes(include=np.number).columns.tolist()
            corr = df[cols].corr(numeric_only=True).round(4)
            results.append({
                "step": step.get("description", "Correlation"),
                "dataset": dataset_name,
                "result": corr.to_dict(),
            })
            fig = px.imshow(corr, text_auto=True, title="Correlation Matrix")
            fig.update_layout(template="plotly_white")
            figures.append(fig)

        elif action == "describe":
            cols = [resolve_column(df, c) for c in step.get("columns", [])]
            cols = [c for c in cols if c]
            if not cols:
                cols = df.select_dtypes(include=np.number).columns.tolist()
            desc = df[cols].describe().round(4)
            results.append({
                "step": step.get("description", "Descriptive statistics"),
                "dataset": dataset_name,
                "result": desc.to_dict(),
            })

        elif action == "outliers":
            metric = resolve_column(df, step.get("metric"))
            if not metric:
                raise ValueError("Outlier analysis requires a numeric metric.")
            s = pd.to_numeric(df[metric], errors="coerce").dropna()
            q1, q3 = s.quantile([0.25, 0.75])
            iqr = q3 - q1
            lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
            outliers = s[(s < lower) | (s > upper)]
            results.append({
                "step": step.get("description", "Outlier detection"),
                "dataset": dataset_name,
                "result": {
                    "metric": str(metric),
                    "q1": float(q1),
                    "q3": float(q3),
                    "lower_bound": float(lower),
                    "upper_bound": float(upper),
                    "outlier_count": int(len(outliers)),
                    "outlier_percentage": round(float(len(outliers) / max(len(s), 1) * 100), 2),
                },
            })

        else:
            results.append({
                "step": step.get("description", "Unsupported step"),
                "dataset": dataset_name,
                "result": {"status": "Skipped unsupported action", "action": action},
            })

    return results, figures
