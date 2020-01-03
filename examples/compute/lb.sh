#!/bin/bash
set -xeou pipefail
cd $(dirname $(realpath $0))

name=test

# make a new load balancer with autoscaling cluster of servers
gcp-compute-lb-new $name -i ./_http.sh

# delete it at script end
trap 'gcp-compute-lb-rm -y $name' EXIT

# get its ip
ip=$(gcp-compute-lb-ip $name)

# wait for it to come up, then curl /bar.txt
for i in {1..1000}; do
    (($i < 600))
    sleep 1
    bar=$(curl --fail --insecure https://$ip/bar.txt) || continue
    break
done

# assert value of bar
[ $bar = foo ]
