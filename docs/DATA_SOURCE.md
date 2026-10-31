# Dataset provenance and use

Source: Synerise Universal Behavioral Modeling dataset, raw six-month retailer interaction release.

- Publisher schema and download: https://recsys.synerise.com/data-set
- Challenge and license statement: https://www.recsyschallenge.com/2025/
- Publisher license: Creative Commons Attribution-NonCommercial 4.0 International. Review the source terms before reuse and retain attribution. This project does not relicense the source dataset.
- The manifest in reports/pipeline_audit.json records local file sizes, verified row counts and SHA-256 checksums. The original download date was not recorded and is not invented.
- The pipeline audit reports the actual timestamp range. Challenge publication year is not the observation year.
- The original six Parquet files stay in data/raw/ and are excluded from Git. Individual predictions and saved models stay in data/processed/ and are excluded from Git.
- The dataset is anonymized. Reports contain aggregate outcomes and metrics; shopper/product IDs are not exported to published reports.

The original license and publisher documentation control dataset use. The financial assumptions in this repository are hypothetical and are not supplied by Synerise.
