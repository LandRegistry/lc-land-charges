#!/usr/bin/env bash

export SETTINGS="config.DevelopmentConfig"
if [ "$1" != "CI" ]; then
    py.test --cov application tests/ --cov-report=term --cov-report=html --junit-xml=junit.xml
else
    test="$(py.test --cov application tests/ --cov-report=term --cov-report=html --junit-xml=junit.xml)"
    code=$?
    echo "${test}"
    cov=`echo ${test} | perl -nle 'm/TOTAL\s+\d+\s+\d+\s+(\d+)%/; print $1'`

    if [[ $cov -lt 80 ]]; then
        echo "Coverage < 80%"
    else
        echo "Coverage OK!"
    fi
    exit $code
fi
