#!/bin/bash

pm2 delete Statistic-Worker
pm2 start --name=Statistic-Worker -i 2 eventListener.py --interpreter=python3
