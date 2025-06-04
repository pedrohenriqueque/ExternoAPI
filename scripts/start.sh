#!/bin/bash
cd /home/ec2-user/externoapi
# Você pode usar nohup para rodar em background
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > log.txt 2>&1 &
