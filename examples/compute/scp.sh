#!/bin/bash
set -xeou pipefail

dir=$(mktemp -d)
trap 'rm -rfv $dir' EXIT

(
    # make some data
    cd $dir
    mkdir data
    echo foo > data/bar.txt

    # make an instance
    id=$(gcp-compute-new test)
    trap 'gcp-compute-rm -y $id' EXIT

    # wait for ssh
    gcp-compute-wait-for-ssh -y $id

    # scp the data
    gcp-compute-scp -y data/bar.txt :/tmp/bar.txt $id

    # assert the data got there
    val=$(gcp-compute-ssh $id -yqc 'cat /tmp/bar.txt')
    [ foo = $val ]

    # scp the data back
    gcp-compute-scp -y :/tmp/bar.txt data.txt $id

    # assert it's the same
    [ foo = $(cat data.txt) ]

)

false # make sure tests fail via runner
