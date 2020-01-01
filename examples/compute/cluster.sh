#!/bin/bash
set -xeou pipefail
name=test
ids=$(gcp-compute-new --num 3 $name)
gcp-compute-wait-for-ssh --yes $ids
gcp-compute-ssh $ids --yes --quiet --cmd 'ifconfig | grep "10\." | awk "{print \$2}"' 2>/dev/null
gcp-compute-ls $ids 2>&1 | column -t
gcp-compute-rm --yes $ids 2>/tmp/log
