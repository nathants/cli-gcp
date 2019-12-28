#!/bin/bash
cd $(dirname $(realpath $0))
name=$(basename $(pwd))
gcloud functions deploy \
       $name \
       --allow-unauthenticated \
       --trigger-http \
       --region us-central1 \
       --runtime python37 \
       --entry-point main
