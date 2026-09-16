from pathlib import Path
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Set min log level to info so we can see logs in terminal
logging.basicConfig(
    level = logging.INFO
)

def ingest_file(file_path, primary_key, expected_cols):

    logger.info(f"Starting ingestion process for {file_path}...")

    # 1. Check if args are correctly formatted
    if not file_path:
        logger.error("Missing file_path argument.")
        raise ValueError("Missing file_path argument.")
    
    if not expected_cols:
        logger.error("Missing expected_cols argument.")
        raise ValueError("Missing expected_cols argument.")
    
    # Check if primary_key is actually in expected_cols
    if not set(primary_key).issubset(expected_cols):
        logger.error("Primary_key arg missing or does not exist in expected_cols")
        raise ValueError("Primary_key arg missing or does not exist in expected_cols")

    # 2. Check if file exists
    if not file_path.exists():
        logger.error("File does not exist.")
        raise FileNotFoundError("Provided file at file_path does not exist.")

    # 3. Read the file
    file = read_file(file_path)
    
    logger.info(f"File read successfully. Read {file.shape[0]} rows.")

    # 4. Check if empty
    if file.empty:
        logger.error("Input file is empty.")
        raise ValueError("Read file failed: File empty.")

    # 5. Check expected columns
    # Using a set to ignore order 
    if not set(file.columns) == expected_cols:
        logger.error(f"Expected columns not found: {expected_cols}.")
        raise ValueError("Expected columns not found.")
    
    logger.info('Schema validation passed.')

    # 6. Check primary key for uniqueness

    if file.duplicated(subset=primary_key).any():
        logger.error("Primary key is not unique.")
        raise ValueError(f"Primary key columns '{primary_key}' are not unique.")
    
    # 7. Check primary key for nulls
    if file[primary_key].isnull().any().any():
        logger.error(f"At least 1 '{primary_key}' is NULL.")
        raise ValueError(f"At least 1 '{primary_key}' is NULL.")
    
    logger.info('Primary key validation passed.')

    # 8. Return the data
    logger.info("Validation checks passed.")
    return file

def read_file(file_path):
    return pd.read_csv(file_path)

def get_data_path(file_name):
    return Path("..") / "data" / file_name
    
def main():

    logger.info("Starting script execution...")

    # Primary key is a list to allow for multiple keys
    datasets = {
        "orders": {
            "file_name": "orders.csv",
            "primary_key": ["order_id"],
            "expected_cols": {"order_id", "user_id", "eval_set", "order_number", "order_dow", "order_hour_of_day", "days_since_prior_order"}
        },
        "products": {
            "file_name": "products.csv",
            "primary_key": ["product_id"],
            "expected_cols": {"product_id", "product_name", "aisle_id", "department_id"}
        },
        "aisles": {
            "file_name": "aisles.csv",
            "primary_key": ["aisle_id"],
            "expected_cols": {"aisle_id", "aisle"}
        },
        "departments": {
            "file_name": "departments.csv",
            "primary_key": ["department_id"],
            "expected_cols": {"department_id", "department"}
        }
    }

    for ds in datasets.values():
        ingest_file(get_data_path(ds["file_name"]),
                    ds["primary_key"],
                    ds["expected_cols"]
        )

if __name__ == "__main__":
    main()
