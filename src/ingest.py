from pathlib import Path
import pandas as pd
import logging
import yaml

logger = logging.getLogger(__name__)

# Set min log level
logging.basicConfig(
    level = logging.ERROR
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
    if not set(file.columns) == set(expected_cols):
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
    logger.info("All initial validation checks passed.")
    return file

def read_file(file_path):
    try:
        return pd.read_csv(file_path)
    
    except Exception:
        logger.error(f"Failed to read csv file at {file_path}")
        raise

def get_data_path(file_name):
    return Path("..") / "data" / file_name

def get_config_path():
    return Path("..") / "config" / "datasets.yaml"

def validate_foreign_key(child_values, parent_values):

    # Get items in child values that are not in parent values
    diff = set(child_values) - set(parent_values)
    
    # Determine which child values don't exist in parent (if any)
    if diff:
        logger.error(f"Child set contains unmapped item(s) {diff}")
        raise ValueError(f"Child set contains unmapped item(s) {diff}")
    
    logger.info("Foreign Key Validation Passed")

def load_config(file_path):
    try:
        with open(file_path, "r") as file:
            config = yaml.safe_load(file)

        return config

    except:
        logger.error("Failed to load config file at {file_path}")
        raise

def validate_config(config):
    ...

def main():

    logger.info("Starting script execution...")

    config = load_config(get_config_path())
    validate_config(config)
    datasets = config["datasets"]

    data = {}

    # First ingest all the datasets
    for name, ds in datasets.items():
        data[name] = ingest_file(
            get_data_path(ds["file_name"]),
            ds["primary_key"],
            ds["expected_cols"]
        )

    # Then loop through datasets again to validate all foreign key relationships
    for name, ds in datasets.items():
        for fk in ds["foreign_keys"]:

            if fk["reference_dataset"] not in data:
                logger.error(f"Foreign key dataset {fk['reference_dataset']} not found in data")
                raise KeyError(f"Foreign key dataset {fk['reference_dataset']} not found in data")
            
            if fk["reference_column"] not in data[fk['reference_dataset']]:
                logger.error(f"Foreign key {fk['reference_column']} not found in {fk['reference_dataset']}")
                raise KeyError(f"Foreign key {fk['reference_column']} not found in {fk['reference_dataset']}")
            
            if fk["column"] not in data[name]:
                logger.error(f"Foreign key {fk['column']} not found in {name}")
                raise KeyError(f"Foregin key {fk['column']} not found in {name}")
                
            validate_foreign_key(
                data[name][fk["column"]],
                data[fk['reference_dataset']][fk["reference_column"]]
            )

if __name__ == "__main__":
    main()
