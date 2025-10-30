#!/usr/bin/env python
# coding: utf-8

# ## Import library

# In[1]:


import yaml
import os
import boto3
import pandas as pd
from pprint import pprint
import shutil
import pickle
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, OneHotEncoder, LabelBinarizer

import warnings
warnings.filterwarnings("ignore")


# In[2]:


def read_yaml_file(path, file):
    with open(os.path.join(path, file)) as f:
        try:
            content = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise e
    
    return content


CONFIG_PATH = os.path.join("..", "src", "config")


# In[3]:


credentials = read_yaml_file(path=CONFIG_PATH, file="credentials.yaml")
settings = read_yaml_file(path=CONFIG_PATH, file="settings.yaml")

AWS_ACCESS_KEY = credentials['AWS_ACCESS_KEY']
AWS_SECRET_KEY = credentials['AWS_SECRET_KEY']
S3_NAME = credentials['S3']

ARTIFACTS_OUTPUT_PATH = settings['ARTIFACTS_PATH']
FEATURES_OUTPUT_PATH = settings['FEATURES_PATH']
RAW_FILE_PATH = os.path.join(settings["DATA_PATH"], settings["RAW_FILE_NAME"])
PROCESSED_RAW_FILE = "Preprocessed_" + settings["RAW_FILE_NAME"]
PROCESSED_RAW_FILE_PATH = os.path.join(settings["DATA_PATH"], PROCESSED_RAW_FILE)


# In[4]:


settings["RAW_FILE_NAME"]


# In[5]:


RAW_FILE_PATH = f"../{RAW_FILE_PATH}"
PROCESSED_RAW_FILE_PATH = f"../{PROCESSED_RAW_FILE_PATH}"
ARTIFACTS_OUTPUT_PATH = f"../{ARTIFACTS_OUTPUT_PATH}"
FEATURES_OUTPUT_PATH = f"../{FEATURES_OUTPUT_PATH}"


# In[6]:


# Inittials S3 client (for low-level operations)
s3_client = boto3.client(
    service_name = 's3',
    aws_access_key_id = AWS_ACCESS_KEY,
    aws_secret_access_key = AWS_SECRET_KEY
)
if not os.path.exists(RAW_FILE_PATH):
    s3_client.download_file(S3_NAME, settings["RAW_FILE_NAME"], RAW_FILE_PATH)


# ## Data cleaning

# In[7]:


df = pd.read_csv(RAW_FILE_PATH)
df.drop('id', axis=1, inplace=True)
df.head()


# ### Removing Duplicates

# In[8]:


df = df.drop_duplicates(keep='first')
pprint(f"Data Shape: {df.shape}")


# ### Transform Height units to Cetimeters

# In[9]:


df['Height'] *= 100


# ### Removing Outliers

# In[10]:


df.describe()


# In[11]:


# calculating the upper and lower limits
Q1 = df["Age"].quantile(0.25)
Q3 = df["Age"].quantile(0.75)
# threshold = 1.5
threshold = 3.0
IQR = Q3 - Q1

pprint(f"Dataset shape before removing the outliers: {df.shape}")

# removing the data samples that exceeds the upper or lower limits
df = df[~((df["Age"] >= (Q3 + threshold * IQR)) | (df["Age"] <= (Q1 - threshold * IQR)))]
pprint(f"Dataset shape after removing the outliers: {df.shape}")


# ## Creating New Features

# ### Body Mass Index (BMI)

# In[12]:


df["BMI"] = df["Weight"] / (df["Height"] ** 2)


# ### Ideal Number of Main Meals? (INMM)

# In[28]:


df["INMM"] = df["NCP"] == 3
df["INMM"] = df["INMM"].astype(int)


# In[14]:


df.info()


# ### Transforming `Age` Column Into a Categorical Column

# Reducing the impact of outliers in the `Age` column using *Quantile Bucketing*

# In[15]:


values, bins = pd.qcut(x=df["Age"], q=4, retbins=True, labels=["q1", "q2", "q3", "q4"])


# In[16]:


print(type(bins))
print(bins)


# In[17]:


bins = np.concatenate(([-np.inf], bins[1:-1], [np.inf]))

df["Age"] = values
df["Age"] = df["Age"].astype("object")
df.head()


# In[18]:


print(type(bins))
print(bins)


# ### Transforming `INMM` into Categorical Columns
# 

# In[19]:


df["INMM"] = df["INMM"].astype("object")
df.head()


# ### Spliting data into training and validation sets

# In[20]:


X = df.drop("NObeyesdad", axis=1)
y = df["NObeyesdad"].values


# In[21]:


X_train, X_val, y_train, y_val = train_test_split(X, y, train_size=0.8, stratify=y ,random_state=42)

X_train = X_train.reset_index(drop=True)
X_val = X_val.reset_index(drop=True)

pprint(f"Train set shape: {X_train.shape} and {y_train.shape}")
pprint(f"Validation set shape: {X_val.shape} and {y_val.shape}")


# ### Transform numerical columns (Log + 1 tranformation)

# In[23]:


numerical_columns = df.select_dtypes(include=["number"]).columns.to_list()

for col in numerical_columns:
    X_train[col] = np.log1p(X_train[col])
    X_val[col] = np.log1p(X_val[col])


# In[24]:


numerical_columns


# ### Scaling the numerical columns

# In[ ]:


pprint("Training set skewness before scaling:")
pprint(X_train[numerical_columns].skew())
pprint("Validation set skewness before scaling:")
pprint(X_val[numerical_columns].skew())


# **Fit:** Use `fit()` on your training data to calculate the mean and standard deviation for each feature. <br>
# **Transform:** Use `transform()` to apply the scaling to your training and test data. It's crucial to use the same fitted scaler for both to ensure consistency.
# 
# 
# - *Outliers:* `StandardScaler` can be sensitive to outliers
# - *Data leakage:* Always fit the `StandardScaler` only on the training data and then apply the learned transformation to both training and test sets.

# In[ ]:


scalers = {}

for col in numerical_columns:
    sc = StandardScaler()

    sc.fit(X_train[col].to_numpy().reshape(-1,1))

    X_train[col] = sc.transform(X_train[col].to_numpy().reshape(-1,1))
    X_val[col] = sc.transform(X_val[col].to_numpy().reshape(-1,1))
    scalers[col] = sc


# In[ ]:


scalers


# In[ ]:


pprint("Training set skewness after scaling:")
pprint(X_train[numerical_columns].skew())
print()
pprint("Validation set skewness after scaling:")
pprint(X_val[numerical_columns].skew())


# ### Encoding categorical columns

# In[ ]:


categorical_columns = X_train.select_dtypes(include=['object', 'category']).columns.to_list()

encoder = OneHotEncoder(drop='first', sparse_output=False, handle_unknown='infrequent_if_exist', min_frequency=20)
encoder.fit(X_train[categorical_columns])

train_encoder_df  = pd.DataFrame(
    data=encoder.transform(X_train[categorical_columns]),
    columns=encoder.get_feature_names_out(categorical_columns)
)

val_encoder_df  = pd.DataFrame(
    data=encoder.transform(X_val[categorical_columns]),
    columns=encoder.get_feature_names_out(categorical_columns)
)

new_train_df = pd.concat([train_encoder_df, X_train.drop(categorical_columns, axis=1)], axis=1)
new_val_df = pd.concat([val_encoder_df, X_val.drop(categorical_columns, axis=1)], axis=1)

X_train = new_train_df.values.copy()
X_val = new_val_df.values.copy()


# In[ ]:


encoder.get_feature_names_out()


# ### Encoding the labels

# In[ ]:


label_encoder = LabelBinarizer(sparse_output=False)
label_encoder.fit(y_train)

original_y_train = y_train.copy()
original_y_valid = y_val.copy()

y_train = label_encoder.transform(y_train)
y_val = label_encoder.transform(y_val)


# In[ ]:


pprint(f"Train set shape: {X_train.shape} and {y_train.shape}")
pprint(f"Validation set shape: {X_val.shape} and {y_val.shape}")


# In[ ]:


label_encoder.classes_


# ### Saving the Artifacts

# In[ ]:


# saving the artifacts locally
os.makedirs(ARTIFACTS_OUTPUT_PATH, exist_ok=True)
os.makedirs(FEATURES_OUTPUT_PATH, exist_ok=True)

with open(os.path.join(ARTIFACTS_OUTPUT_PATH, 'scalers.pkl'), 'wb') as f:
    pickle.dump(scalers, f)
with open(os.path.join(ARTIFACTS_OUTPUT_PATH, 'features_encoder.pkl'), 'wb') as f:
    pickle.dump(encoder, f)
with open(os.path.join(ARTIFACTS_OUTPUT_PATH, 'label_encoder.pkl'), 'wb') as f:
    pickle.dump(label_encoder, f)
with open(os.path.join(ARTIFACTS_OUTPUT_PATH, 'qcut_bins.pkl'), 'wb') as f:
    pickle.dump(bins, f)


with open(os.path.join(FEATURES_OUTPUT_PATH, 'X_train.pkl'), 'wb') as f:
    pickle.dump(X_train, f)
with open(os.path.join(FEATURES_OUTPUT_PATH, 'X_val.pkl'), 'wb') as f:
    pickle.dump(X_val, f)
with open(os.path.join(FEATURES_OUTPUT_PATH, 'y_train.pkl'), 'wb') as f:
    pickle.dump(y_train, f)
with open(os.path.join(FEATURES_OUTPUT_PATH, 'y_val.pkl'), 'wb') as f:
    pickle.dump(y_val, f)


# In[ ]:


# saving the preprocessed dataset locally
new_train_df['NObeyesdad'] = original_y_train
new_val_df['NObeyesdad'] = original_y_valid

preprocessed_data = pd.concat([new_train_df, new_val_df])
preprocessed_data.to_csv(PROCESSED_RAW_FILE_PATH, index=False, sep=",")


# In[ ]:


def upload_folder_s3(root_path: str, s3_folder_prefix=""):
    try:
        for root, dirs, files in os.walk(root_path):
            for file_name in files:
                local_path = os.path.join(root, file_name)
                relative_path = os.path.relpath(local_path, root_path)

                if s3_folder_prefix:
                    s3_key = f"{s3_folder_prefix}/{relative_path}".replace("\\", "/")
                else:
                    s3_key = relative_path.replace("\\", "/")

                s3_client.upload_file(local_path, S3_NAME, s3_key)
                print(f"✅ Uploaded: {local_path} → s3://{S3_NAME}/{s3_key}")
    except Exception as err:
        print(f"❌ Upload failed: {err}")

if os.path.exists(ARTIFACTS_OUTPUT_PATH):
    upload_folder_s3(ARTIFACTS_OUTPUT_PATH, s3_folder_prefix="artifacts")

if os.path.exists(FEATURES_OUTPUT_PATH):
    upload_folder_s3(FEATURES_OUTPUT_PATH, s3_folder_prefix="features")

# sending preprocessed dataset saved locally to the aws s3 bucket
s3_client.upload_file(
    PROCESSED_RAW_FILE_PATH,
    credentials["S3"],
    PROCESSED_RAW_FILE
)


# In[ ]:


# if os.path.exists(ARTIFACTS_OUTPUT_PATH):
#     shutil.rmtree(ARTIFACTS_OUTPUT_PATH)

# if os.path.exists(FEATURES_OUTPUT_PATH):
#     shutil.rmtree(FEATURES_OUTPUT_PATH)

# if os.path.exists(RAW_FILE_PATH):
#     os.remove(RAW_FILE_PATH)

# if os.path.exists(PROCESSED_RAW_FILE_PATH):
#     os.remove(PROCESSED_RAW_FILE_PATH)


# In[ ]:




