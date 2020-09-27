#!/bin/bash

pm2 start --name=Chart-Worker -i 2 eventListener.py --interpreter=python3
