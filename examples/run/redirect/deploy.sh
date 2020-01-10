#!/bin/bash
set -xeou pipefail

project=$(gcloud config get-value project)
container=gcr.io/$project/run-redirect:latest
docker build . -t $container
docker push $container
gcloud beta run deploy \
       run-redirect \
       --allow-unauthenticated \
       --region us-central1 \
       --platform managed \
       --image $container
