# Deep Learning for Malicious Traffic Detection

This university project investigates whether connection-level IoT network traffic can be classified as benign or malicious. The cleaned workflow uses IoT-23 Zeek connection logs, prevents preprocessing leakage, and evaluates an artificial neural network against a logistic-regression baseline.

The original project also tested CNN, LSTM, and Transformer architectures. Those experiments remain in [`archive/`](archive/) with their saved outputs, but they are not treated as production-ready comparisons because the ten input fields are unordered tabular features rather than a meaningful temporal sequence.

## Portfolio version

[`notebooks/iot23-malicious-traffic-detection.ipynb`](notebooks/iot23-malicious-traffic-detection.ipynb) is the canonical notebook. It:

1. discovers multiple IoT-23 connection logs, in either the format the dataset ships or a converted CSV export;
2. removes direct identifiers and detailed labels that would leak the target;
3. splits entire captures between training, validation, and testing;
4. fits imputation, one-hot encoding, and scaling on the training set only;
5. trains a class-weighted logistic-regression baseline and a dense neural network;
6. reports balanced accuracy, precision, recall, F1, ROC AUC, PR AUC, and normalized confusion matrices.

See [`RESULTS.md`](RESULTS.md) for the historical final-project results and their limitations.

## Dataset

The project uses the [IoT-23 dataset](https://www.stratosphereips.org/datasets-iot23) from Stratosphere Laboratory. Dataset files are not included. Obtain them from the [IoT-23 file index](https://mcfp.felk.cvut.cz/publicDatasets/IoT-23-Dataset/) or the [citable Zenodo snapshot](https://zenodo.org/records/4743746), review the dataset terms, and place the connection logs under `data/iot23/`.

Two layouts are accepted, and nested folders are searched:

```text
data/iot23/
  CTU-IoT-Malware-Capture-1-1conn.log.labeled       the Zeek logs the dataset ships
  CTU-IoT-Malware-Capture-3-1conn.log.labeled.csv   a converted export of the same captures
  ...
```

The logs Stratosphere publishes are tab separated, carry `#` header lines, and write
`tunnel_parents`, `label` and `detailed-label` as one space-separated field rather than the three
tab-separated fields their header declares. Converted exports are ordinary tables, usually pipe
separated. [`scripts/iot23.py`](scripts/iot23.py) reads both and is what the notebook and the merge
script use, so the same analysis works with either download.

The notebook accepts another location through the `IOT23_DATA_DIR` environment variable.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
jupyter lab
```

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
$env:IOT23_DATA_DIR = "D:\datasets\IoT-23"
$env:MAX_ROWS_PER_CAPTURE = "200000"
jupyter lab
```

`MAX_ROWS_PER_CAPTURE` controls the stratified sample taken from each capture. Set it to `0` to use every row when sufficient memory is available.

## Repository layout

```text
notebooks/       Canonical reproducible analysis
archive/         Original notebooks, figures, and exported code
scripts/         Dataset reader and preparation utilities
tests/           Offline checks for the dataset reader
data/            Dataset placement instructions; data is ignored by Git
```

## Offline checks

No dataset required: the checks build small captures in both formats and read them back.

```bash
python tests/test_iot23.py
```

## Important interpretation

- A random row split can leak capture-specific patterns into every partition. The cleaned notebook keeps capture IDs disjoint.
- Accuracy alone is misleading when malicious and benign flows are imbalanced, so the cleaned evaluation includes class-sensitive metrics.
- The historical numbers document the university project. They were not independently reproduced during repository cleanup.
- This repository analyzes saved network logs. It does not execute malware.

## Author

Jose E. Rodriguez Rios
