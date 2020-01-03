#!/bin/bash
set -xeou pipefail

name=test

# make 3 instances
ids=$(gcp-compute-new --num 3 $name)

# delete them at script end
trap 'gcp-compute-rm --yes $ids' EXIT

# wait for ssh to succeed
gcp-compute-wait-for-ssh --yes $ids

# assert ssh ipv4 gets 3 entries
output=$(gcp-compute-ssh $ids --yes --quiet --cmd 'whoami')
[ 3 = $(echo "$output" | wc -l) ]

# assert list by id gets 3 entries
ls=$(gcp-compute-ls $ids)
[ 3 = $(echo "$ls" | wc -l) ]
