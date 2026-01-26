# pbk_report

## PHP Version

### Running pbk_report PHP with Docker

    docker run -d -p 8080:80  -v $(pwd):/var/www/html --name pbk_report php:8.2-apache

### Accessing pbk_report PHP

    http://localhost:8080/pbk_styling.php

## Python Version

### Running pbk_report Python with uv

    uv sync
    uv run python pbk_styling.py > output.html

### Run Unit Tests for pbk_report Python

    uv sync --group test 
    uv run pytest
    uv run pytest --cov=./ --cov-report=term
