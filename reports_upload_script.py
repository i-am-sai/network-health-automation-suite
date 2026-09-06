import boto3
import os
import logging
from botocore.exceptions import ClientError

BUCKET_NAME = "network-health-automation-reports"
RESULTS_DIR = "reports/results"

boto3.set_stream_logger("boto3", logging.DEBUG)
boto3.set_stream_logger("botocore", logging.DEBUG)

def upload_report_to_s3(bucket_name=BUCKET_NAME):
    s3 = boto3.client("s3")

    if not os.path.isdir(RESULTS_DIR):
        print(f"Results directory not found: {RESULTS_DIR}")
        return False


    # Find all JSON files in reports/results/
    json_files = [
        os.path.join(RESULTS_DIR, file)
        for file in os.listdir(RESULTS_DIR)
        if file.endswith(".json")
    ]

    if not json_files:
        print("No JSON report found.")
        return False

    # Pick the most recently generated/modified JSON file
    local_file_path = max(json_files, key=os.path.getmtime)

    filename = os.path.basename(local_file_path)

    # S3 destination
    s3_key = f"reports/{filename}"

    try:
        s3.upload_file(
            local_file_path,
            bucket_name,
            s3_key
        )

        print(f"Uploaded {filename}")
        print(f"s3://{bucket_name}/{s3_key}")

        return True

    except ClientError as e:
        print(f"S3 upload failed: {e}")
        return False


if __name__ == "__main__":
    upload_report_to_s3()