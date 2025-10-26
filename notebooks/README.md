# Notebooks (Research Environment)

Here go the notebooks used for research and development. The main idea is to try to simulate a real-world environment where data scientists use Jupyter Notebooks to explore the available data by doing Exploratory Data Analysis (EDA), data processing, testing different Machine Learning models for the determined task they are trying to solve, testing different hyperparameters for each model, and doing some feature engineering and selection (experimentations).

## Setup Credentials

If you haven't your credentials yet, please check the `docs` folder first and follow the setup instructions.

1. Set your `AWS Credentials` and `Kaggle API Credentials` (used to download the dataset) in the `credentials.yaml` file.

2. Execute the Jupyter notebooks in the following order:

- Download the data using the script (read the `README` file inside the `data` folder).
- Run the `EDA` notebook.
- Run the `Data Processing` notebook.
- Run the `Experimentations` notebook (will test different Machine Learning models, different hyperparameters for each model, and do some feature engineering and selection).
- Register the best models to the MLflow model registry using the `Experimentations` notebook (last cell) or the MLflow's user interface.
