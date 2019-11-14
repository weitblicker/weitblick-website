# Weitblick Website

The new Weitblick website is *Django*, and *Python* based. The search engine we use is called *Elasticsearch*, which is Java based. Downloading this code you can run and test the website with default content on you computer.

## Installation

If you have [Docker](https://docs.docker.com/compose/install/) installed, you can just run:

            docker-compose up

It will install, build and run everything for you. For more info see the [Docker Documentation](https://docs.docker.com/compose/reference/overview/). Changes in the wbcore folder will be avaliable instantly, other changes will require a rebuild of the container using the `--build` flag when starting. Otherwise, follow the following steps to set up everything natively.

*Required Software & Tools:* [Python 3](https://www.python.org/), [Java 8](https://www.oracle.com/technetwork/java/javase/downloads/jdk8-downloads-2133151.html), [Tidy](http://binaries.html-tidy.org/) and [Elastic Search 2](https://www.elastic.co/de/downloads/past-releases/elasticsearch-2-4-2).

### Buildtools for Visual Studio 2019

Only necessary for Windows installation. Consider using [Chocolatey](https://chocolatey.org/packages/visualstudio2019buildtools).

### Install python

Download Python 3.6.8 [from the python website](https://www.python.org/downloads/) or using a package manager. For example using [Chocolatey](https://chocolatey.org/packages/python/3.6.8) for Windows.

### Install pip

      curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py

and then run:

      python get-pip.py

### Install pipenv

- for Linux: `sudo -H pip install pipenv`,
- for Windows run as Administrator: `pip install pipenv`

### Install project dependencies

Go to the project root folder. To install the requirements type: 

      pipenv install -r requirements.txt --three`

This can take a while. After that you are good to go.

### Install Java

Install Java 8 and be sure to set JAVA_HOME.

### Install Elastic Search

Install Elastic Search 2. You can download it [here](https://www.elastic.co/de/downloads/past-releases/elasticsearch-2-4-2) and unzip it.

## Running the server for the first time

### Elastic Search

Start Elastic Search.

On unix run :

      bin/elasticsearch

or on windows:

      bin\elasticsearch.bat

### Build index

Enter the virtual environment. This is required for **all following steps**.

      pipenv shell

Use the django module command to build the search index:

      python manage.py rebuild_index

Accept with `y` or add a `--noinput` to the rebuild command.

This search index should be updated later when adding content, for example by using a cron job running: 

      python manage.py update_index

### Setup Database

Database migration and loading data can be achieved running the script `initalize.sh`

#### Database Migration

      python manage.py makemigrations wbcore
      python manage.py migrate
      
#### Set up locale

Enable support for german 

    sudo locale-gen de_DE
    sudo update-locale

#### Loading Data

      python manage.py loaddata data/address.json
      python manage.py loaddata data/locations.json
      python manage.py loaddata data/hosts.json
      python manage.py loaddata data/images.json
      python manage.py loaddata data/news.json
      python manage.py loaddata data/blog.json
      python manage.py loaddata data/partners.json
      python manage.py loaddata data/projects.json

#### Create a SuperUser for Admin Interface

      python3 manage.py createsuperuser
      


#### Start Server

Next we run the django server:

      python manage.py runserver

Now if everything worked, you can access the website on `http://localhost:8000`

### Configure Microsoft Login

To enable the login via Microsoft OAuth2 with the official Weitblick intranet accounts visit [this site](http://localhost:8000/admin/sites/site/1/change/) and set the domain name to `localhost:8000`.

## FAE (Frequently Appearing Errors)

- **no such table when database is empty**: Run Database Migration
