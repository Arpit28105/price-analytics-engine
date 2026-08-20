import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import psycopg2
from apscheduler.schedulers.blocking import BlockingScheduler
from dotenv import load_dotenv

# Ensure proper root paths
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(ROOT_DIR, ".env"))

LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "pipeline_run.log")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout)
    ]
)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "price_analytics")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")


def record_pipeline_run(status, message):
    """Logs the execution status into a dedicated PostgreSQL audit table for Metabase monitoring."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS pipeline_audit_log (
                    run_id SERIAL PRIMARY KEY,
                    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status VARCHAR(20) NOT NULL,
                    message TEXT
                );
            """)
            cur.execute("""
                INSERT INTO pipeline_audit_log (status, message)
                VALUES (%s, %s);
            """, (status, message))
            conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Failed to record run audit to DB: {e}")


def run_pipeline():
    logging.info("=" * 60)
    logging.info("🚀 Starting Daily Price Analytics Pipeline Execution")
    logging.info("=" * 60)

    try:
        # Step 1: Data Generation
        logging.info("📦 Step 1: Generating synthetic daily batch...")
        import generate_data
        prods = generate_data.generate_products()
        generate_data.generate_price_and_sales(prods)
        logging.info("✅ Generation complete.")

        # Step 2: Data Quality Gate
        logging.info("🛡️ Step 2: Running Data Quality checks...")
        import validate
        validate.run_all_validations()
        logging.info("✅ Quality checks passed.")

        # Step 3: SCD Type 2 & Fact Loading
        logging.info("💾 Step 3: Ingesting into PostgreSQL (SCD Type 2 + Fact)...")
        import load_to_db
        load_to_db.main()
        logging.info("✅ Database load complete.")

        # Step 4: Analytical Transformation Layer
        logging.info("🧠 Step 4: Refreshing Analytical Views...")
        import run_analytics
        run_analytics.execute_analytics()
        logging.info("✅ Analytics layer refreshed.")

        # Audit success
        record_pipeline_run("SUCCESS", "All 4 pipeline stages executed cleanly.")
        logging.info("🎉 Pipeline run SUCCESSFUL!")

    except Exception as e:
        error_msg = f"Pipeline execution failed: {str(e)}"
        logging.error(f"❌ {error_msg}")
        record_pipeline_run("FAILED", error_msg)


if __name__ == "__main__":
    # If run directly with '--now', execute immediately once
    if len(sys.argv) > 1 and sys.argv[1] == "--now":
        run_pipeline()
    else:
        scheduler = BlockingScheduler()
        # Schedule the pipeline to run every day at 09:00 AM
        scheduler.add_job(run_pipeline, 'cron', hour=9, minute=0)
        logging.info("⏰ APScheduler initialized. Pipeline scheduled daily at 09:00 AM.")
        logging.info("💡 (To run a manual test right now, execute: python src/pipeline.py --now)")
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logging.info("🛑 Scheduler stopped.")