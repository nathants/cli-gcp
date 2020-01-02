#!/bin/bash
set -xeou pipefail
dir=$(mktemp -d)
(
    cd $dir
    mkdir data
    echo foo > data/bar.txt
    id=$(gcp-compute-new test)
    gcp-compute-wait-for-ssh -y $id
    gcp-compute-scp -y data/bar.txt :/tmp/bar.txt $id
    val=$(gcp-compute-ssh $id -yqc 'cat /tmp/bar.txt')
    [ foo = $val ]
    gcp-compute-rm -y $id
)
rm -rfv $dir
