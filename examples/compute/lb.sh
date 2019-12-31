#!/bin/bash
set -xeou pipefail
name=test
gcp-compute-lb-new $name -i _http.sh
while true; do
    curl --fail --insecure https://$(gcp-compute-lb-ip $name) || continue
    break
done
gcp-compute-lb-rm -y $name
