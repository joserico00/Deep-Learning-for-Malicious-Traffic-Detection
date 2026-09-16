# Dataset Placement

Place lawful copies of the IoT-23 Zeek connection logs in this directory. Dataset contents are ignored by Git.

Expected filename patterns, either the files the dataset ships or a converted export:

```text
*conn.log.labeled
*conn.log.labeled.csv
```

The notebook also searches nested folders. Set `IOT23_DATA_DIR` when the data lives elsewhere.
