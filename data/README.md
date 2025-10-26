# Data

The data will not stored locally but rether in an AWS S3 bucket to simulate a real-world scenario with different dataset version(data versioning) and it is easier for each member of the group to down it.

Before downloading the data, you need to do one prerequisite step:
> Set you `AWS Credentials` and [Kaggle API Credentials](https://www.kaggle.com/settings/account) (used to download the dataset) in the `credentials.yaml` file.

Finnaly, you can download both current(testing) and (training and validation) using following command:

```bash
bash download.sh curent 'raw'
```

```bash
bash download.sh curent 'current'
```

The dataset will temporarily saved locally (inside the `data` folder) and tranferred to your AWS S3 bucket. After that, the dataset will be deleted. if you choose to not use an AWS S3 Bucket, the the dataset will be stored into the `data` folder.
