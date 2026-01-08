# pbk_report

## Running pbk_report with Docker

    docker run -d -p 8080:80  -v $(pwd):/var/www/html --name pbk_report php:8.2-apache

## Accessing pbk_report

    http://localhost:8080/pbk_styling.php