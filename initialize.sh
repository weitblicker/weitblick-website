#!/bin/bash

# Initialize database
echo "Starting migration to the database"
python manage.py makemigrations wbcore
python manage.py migrate
echo ""
# Load Weitblick data
echo "Starting to load the data in the database"
python manage.py loaddata data/address.json
python manage.py loaddata data/locations.json
python manage.py loaddata data/hosts.json
python manage.py loaddata data/images.json
python manage.py loaddata data/news.json
python manage.py loaddata data/blog.json
python manage.py loaddata data/partners.json
python manage.py loaddata data/projects.json
echo ""


echo "Finished wih the initialization of the system."
echo "Please create the super user with the command:  \"python manage.py createsuperuser\""
echo "Next, start the project with \"python manage.py runserver\""
echo "Finally, rebuild the index with \"python manage.py rebuild_index\""
