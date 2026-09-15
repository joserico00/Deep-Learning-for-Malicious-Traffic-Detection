# Historical Project Files

This directory preserves the original university work and its saved outputs. These files show how the project developed, but they are not the recommended reproducible workflow.

## Notebooks

| File | Historical role |
|---|---|
| `original-merged-dataset-run.ipynb` | Final four-model comparison over a random sample of the merged IoT-23 captures |
| `original-single-capture-run.ipynb` | Earlier experiment using one capture |
| `colab-version.ipynb` | Shorter Google Colab iteration |
| `small-deep-learning-run.ipynb` | Small-resource experiment |
| `network-traffic-classification.ipynb` | Separate dense-network workflow with saved preprocessing experiments |

Two equivalent notebook copies were removed during cleanup. The canonical workflow now lives in [`../notebooks/`](../notebooks/).

## Known limitations

- hard-coded Google Drive paths;
- preprocessing fitted before the train/test split;
- random row splitting across capture sources;
- raw warnings, failed cells, and empty cells;
- accuracy-heavy evaluation on imbalanced classes;
- CNN, LSTM, and Transformer layers applied to unordered tabular feature columns.

The figures under `results/` and the Python export under `exports/` are retained only to document the original work.
