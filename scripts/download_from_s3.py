import boto3

# AWS S3 details
bucket_name = 'gramsaathi-rag-docs'  # your bucket name

# List of files to download
files_to_download = [
    'agri-infra-central.pdf',
    'atma-schemes-rd-central.pdf',
    'cibrc_registered_chemicals.pdf',
    'farm mechanization.pdf',
    'GOVERNMENT_SCHEMES_FOR_AGRICULTURE__Revised-26.12.2019.pdf',
    'Important Rural Development Programmes in India.pdf',
    'msp_allcrops.pdf',
    'NHB-pdf.pdf',
    'rurl development analysis.pdf',
    'samman_nidhi_pm.pdf'
]

# Create S3 client
s3 = boto3.client('s3')

# Download each file
for file_key in files_to_download:
    s3.download_file(bucket_name, file_key, file_key)  # saves with same name locally
    print(f"Downloaded {file_key} from {bucket_name}")

