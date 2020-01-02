#!/bin/bash
set -xeou pipefail
dir=$(mktemp -d)
(
    cd $dir
    mkdir data
    echo foo > data/bar.txt
    id=$(gcp-compute-new test)
    gcp-compute-wait-for-ssh -y $id
    gcp-compute-rsync -y data :/tmp $id
    val=$(gcp-compute-ssh $id -yqc 'cat /tmp/data/bar.txt')
    [ foo = $val ]
    gcp-compute-rm -y $id
)
rm -rfv $dir
