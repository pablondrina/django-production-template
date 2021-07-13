## 1. Project setup

###1.1 Create a virtual environment
(revisar essa parte, ver forma mais padronizada)
#### Considering you already have Python installed, ok

####Install pipx:
`sudo apt install pipx`

####Install virtualenv:
`pipx install virtualenv`

####Make it available globally:
`pipx ensurepath`

####Create the virtual environment:
`mkdir myproject`

`cd myproject`

`virtualenv venv -p python3.9 #for example`

####Remember to activate it:
`source venv/bin/activate`

`deactivate #if needed`

***
###1.2 Clone the repo

####(Desenvolver esse tópico)

***
###1.3 Install requirements
####First enter the project repo root folder
`cd template-name # you may change this name`

####Then, if locally:
`pip install -r requirements/local.txt`

***
###1.5 Install and config Postgres & Postgis
`sudo apt install python3-pip python3-dev libpq-dev postgresql postgresql-contrib nginx curl`
#### Criando o banco de dados e o usuário PostgreSQL

`sudo -u postgres psql`

`CREATE DATABASE nerp;
CREATE USER nerp WITH PASSWORD 'N3ls0n1997!';
ALTER ROLE nerp SET client_encoding TO 'utf8';
ALTER ROLE nerp SET default_transaction_isolation TO 'read committed';
ALTER ROLE nerp SET timezone TO 'UTC-3';
GRANT ALL PRIVILEGES ON DATABASE nerp TO nerp; CREATE EXTENSION postgis;`

`\q #exit`

#### Adicionando a extensão postgis ao banco de dados nerp

`sudo -u postgres psql nerp`

`CREATE EXTENSION postgis;`

***

#### Outros comandos básicos psql
`\c nerp # Conectar ao banco de dados nerp`

`\dt # Descrever as tabelas`

`\dt+ contacts_partner # Descrever a tabela tal`

`\d+ contacts_partner # Descrever as colunas da tabela tal`

***

#### Instalando GeoDjango (várias dependencias)
Base para instalação aqui, mais outras referências importantes:
https://docs.djangoproject.com/en/3.1/ref/contrib/gis/install/

* Precisei atualizar o Postgresql local, graças a esse tutorial, ufa!
https://dev.to/jkostolansky/how-to-upgrade-postgresql-from-11-to-12-2la6

#### Para verificar a versão do Postgres:
psql --version

#### Instalar as dependências
sudo apt-get install binutils libproj-dev gdal-bin

#### Instalar o Postgis
`sudo apt-get install postgis postgresql-12-postgis-scripts`

`sudo apt-get install postgresql-server-dev-12 # python-psycopg2`




***
###1.5 Start the django project
####Considering you are on project repo root folder, ok
####Migrate so the setted db can reflect your models:
`python manage.py migrate`
####Create a superuser:
`python manage.py createsuperuser`
####Run and have fun!
`python manage.py runserver`
