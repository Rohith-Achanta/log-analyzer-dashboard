from flask import Flask, render_template, request
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import os

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    summary = {}
    alerts = []
    top_errors = {}

    if request.method == "POST":
        logs = request.form.get("logs", "")

        # Parse logs into DataFrame
        lines = logs.splitlines()
        df = pd.DataFrame(lines, columns=["raw"])

        # Extract log levels
        df["level"] = df["raw"].str.extract("(INFO|WARN|ERROR)")

        #  Count log levels
        counts = df["level"].value_counts().to_dict()
        info = counts.get("INFO", 0)
        warn = counts.get("WARN", 0)
        error = counts.get("ERROR", 0)
        total = info + warn + error

        #  Determine health status
        health = "GREEN"
        if error > 5:
            health = "RED"
        elif warn > 3:
            health = "AMBER"

        # Immediate RED alert rules
        if df["raw"].str.contains("database", case=False).sum() >= 2:
            alerts.append({
                "title": "Database connection failures detected",
                "action": "Check DB connectivity, credentials, and connection pool"
            })

        if df["raw"].str.contains("timeout", case=False).sum() >= 3:
            alerts.append({
                "title": "Request timeout spike detected",
                "action": "Inspect backend response time and thread usage"
            })

        if total > 0 and (error / total) > 0.3:
            alerts.append({
                "title": "High error rate detected",
                "action": "Immediate investigation required"
            })

        #  Top error messages
        error_msgs = df[df["level"] == "ERROR"]["raw"].value_counts().head(3)
        top_errors = error_msgs.to_dict()

        #  Generate chart
        os.makedirs("static", exist_ok=True)
        plt.clf()
        plt.bar(["INFO", "WARN", "ERROR"], [info, warn, error])
        plt.title("Log Level Distribution")
        plt.ylabel("Count")
        plt.savefig("static/chart.png")

        #  Summary
        summary = {
            "total": total,
            "info": info,
            "warn": warn,
            "error": error,
            "health": health
        }

    return render_template(
        "index2.html",
        summary=summary,
        alerts=alerts,
        top_errors=top_errors
    )

if __name__ == "__main__":
    app.run()
