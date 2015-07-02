#!/usr/bin/env bash

export SETTINGS="config.DevelopmentConfig"
py.test --cov application tests/ --cov-report=term --cov-report=html