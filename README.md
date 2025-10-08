## Description

This notebook trains and compares deep learning models to detect malicious network traffic using IoT 23 Zeek logs only. It loads Zeek tables such as `conn.log`, cleans and samples the data for Colab, encodes labels, applies standard scaling, splits into train, validation, and test sets, and then trains four neural models. ANN. CNN. LSTM. A small Transformer. The notebook reports accuracy, precision, recall, F1, ROC AUC, and confusion matrices, and saves simple charts and CSVs so you can review results and reuse the workflow. On held out tests, the ANN performed best on this feature set.

## Data sources

This project uses only Zeek logs from the IoT 23 dataset by Stratosphere Laboratory. You do not need PCAP files.

- Overview and docs: https://www.stratosphereips.org/datasets-iot23  
- File index with per scenario folders and Zeek logs: https://mcfp.felk.cvut.cz/publicDatasets/IoT-23-Dataset/  
- Citable snapshot on Zenodo: https://zenodo.org/record/4743746

## What it does

1. Loads Zeek logs from IoT 23 and selects features such as duration, proto, service, conn_state, bytes, packets, and ip_bytes.  
2. Cleans data, removes direct identifiers, and samples a large dataset to fit Colab limits.  
3. Encodes labels and applies standard scaling.  
4. Splits the data into train, validation, and test sets with fixed seeds for reproducibility.  
5. Trains and compares ANN, CNN, LSTM, and a small Transformer on a Colab T4 GPU with Adam and early stopping.  
6. Evaluates each model with standard metrics and confusion matrices.  
7. Saves metrics and plots for quick comparison and future runs.

## How to use

- Open the notebook in Colab or locally and set the path to your IoT 23 Zeek logs.  
- Run the cells top to bottom.  
- Review metrics and confusion matrices to pick the model and operating point that fit your needs.
