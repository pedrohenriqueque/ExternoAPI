#!/bin/bash

# Atualiza o sistema (opcional, mas recomendado)
sudo yum update -y

# Instala python3 caso não esteja instalado
sudo yum install -y python3

# Vai para a pasta do projeto
cd /home/ec2-user/externoapi || exit 1

# Instala as dependências com pip do python3
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt