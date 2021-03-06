# Bases de Dados - Trabalho Prático

The code and resources available in this repository are to be used only in the scope of the _BD 2021_ course.

The main purpose of this repository is to provide examples on how to do the initial setup of the database-centric REST API that must be developed for the assignment. 
In particular, the projects available are totally automated to be easily deployed in third-party setups with the help of a tool (in this case `docker` or maven, depending on the project).


## Overview of the Contents

- [**`PostgreSQL`**](postgresql) - Database ready to run in a `docker` container with or without the help of the `docker-compose` tool;
- [**`Python`**](python) - Source code of web application template in python with `docker` container configured. Ready to run in `docker-compose` with PostgreSQL
  - [`app/`](python/app) folder is mounted to allow developing with container running


## Requirements

To execute this project it is required to have installed:

- `docker`
- `docker-compose`


## Demo [Python](python) REST API 


To start this demo with run the script (e.g. [`./docker-compose-python-psql.sh`](docker-compose-python-psql.sh)) to have both the server and the database running.
This script uses `docker-compose` and follows the configurations available in [`docker-compose-python-psql.yml`](docker-compose-python-psql.yml)).

The folder [`app`](python/app) is mapped into the container. 
You can modify the contents and the server will update the sources without requiring to rebuild or restart the container.

* Web browser access: http://localhost:8080


## Authors

* BD 2021 Team - https://dei.uc.pt/lei/
* University of Coimbra
