#!/bin/bash

cd /home/ec2-user/externoapi || exit 1

# Caso use virtualenv, ative aqui
# source venv/bin/activate

# Atualiza pip e instala dependências
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Mata qualquer processo uvicorn rodando (opcional, para evitar conflitos)
pkill -f "uvicorn app.main:app" || true

# Inicia o uvicorn em background, salvando log
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > log.txt 2>&1 &