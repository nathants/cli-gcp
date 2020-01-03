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

    # rsync the data
    gcp-compute-rsync -y data :/tmp $id

    # assert the data got there
    val=$(gcp-compute-ssh $id -yqc 'cat /tmp/data/bar.txt')
    [ foo = $val ]

    # rsync the data back
    gcp-compute-rsync -y :/tmp/data/ back/ $id

    # assert it's the same
    [ foo = $(cat back/bar.txt) ]

)
