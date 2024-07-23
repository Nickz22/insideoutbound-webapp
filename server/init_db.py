from app import create_app, db
from app.models import User, AuthToken, CodeVerifier, Session
from sqlalchemy import inspect, text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()
app.config["SQLALCHEMY_ECHO"] = True

with app.app_context():
    logger.info(f"Recognized models: {db.Model.metadata.tables.keys()}")
    logger.info(f"Database URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Test database connection
    try:
        db.session.execute(text("SELECT 1"))
        logger.info("Successfully connected to the database.")
    except Exception as e:
        logger.error(f"Failed to connect to the database: {e}")
        exit(1)

    logger.info("Creating tables...")
    db.create_all()
    logger.info("create_all() executed successfully.")

    # Verify tables were created
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    logger.info(f"Tables in database: {tables}")

    if not tables:
        logger.warning("No tables were created!")
    else:
        logger.info("Tables were successfully created.")

        # List columns for each table
        for table_name in tables:
            columns = [col["name"] for col in inspector.get_columns(table_name)]
            logger.info(f"Table '{table_name}' columns: {columns}")

print("Database initialization complete.")
