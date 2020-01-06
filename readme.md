### composable, succinct scripts to complement the gcp cli

##### installation

install google-cloud-sdk:

- https://cloud.google.com/sdk/install

auth google-cloud-sdk:

- ```
gcloud auth login
gcloud config set project $PROJECT_NAME
gcloud auth application-default login
```

install the package:

- ```
git clone https://github.com/nathants/cli-gcp
cd cli-gcp
pip install -r requirements.txt
python setup.py install
```

add to bashrc:

- ```
export GCP_PROJECT=$PROJECT_NAME
export GCP_REGION=us-central1
export GCP_ZONE=us-central1-b
export GCP_COMPUTE_TYPE=c2-standard-4
```

add your ssh key to gcloud:

- ```
gcloud compute os-login ssh-keys list
gcloud compute os-login ssh-keys add --key-file=$(realpath ~/.ssh/id_rsa.pub)
```

##### usage and help

- `gcp-*-* --help`

- `gcp-compute-ssh --help`

##### examples

- `ls examples`

##### test

- `tox`
