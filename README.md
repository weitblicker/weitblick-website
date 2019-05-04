# Weitblick Website

The new Weitblick website is *Django*, and *Python* based. The search engine we use is called *Elasticsearch*, which is Java based. Downloading this code you can run and test the website with default content on you computer.

## Installation

### Required Software & Tools 

* [Python 3](https://www.python.org/)
* [Java 11](https://jdk.java.net/11/)
* [Tidy](http://binaries.html-tidy.org/)
* [Elastic Search 2](https://www.elastic.co/de/downloads/past-releases/elasticsearch-2-4-2)  (see Elastic Search section below.)
* [Git Large File Storage](https://git-lfs.github.com/)
   - `git lfs install`
   - `git lfs fetch`
   - `git lfs pull`
### Python Environment (Unix)

* If you do not have `pip` installed install it using:
`curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py`
and then hit: `curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py`
* Install *pipenv* `sudo -H pip install pipenv`
* Go to the project root folder. To install the requirements type: `pipenv install -r requirements.txt --three`. This can take a while. After that you are good to go.
* Enter the virtual environment: `pipenv shell`
* Next we run the django server with out application: `python manage.py runserver`. This still will cause some problems, since we have to migrate the database, load data and also to install elastic search.

### Database Migration

* `python manage.py makemigrations wbcore`
* `python manage.py migrate`

### Load Weitblick Data:

* `python manage.py loaddata data/address.json`
* `python manage.py loaddata data/hosts.json`
* `python manage.py loaddata data/images.json`
* `python manage.py loaddata data/news.json`
* `python manage.py loaddata data/blog.json`
* `python manage.py loaddata data/locations.json`
* `python manage.py loaddata data/partners.json`
* `python manage.py loaddata data/projects.json`

### Create a SuperUser for Admin Interface

* `python3 manage.py createsuperuser`

### Elastic Search

Install Elastic Search 2. You can download it here: https://www.elastic.co/de/downloads/past-releases/elasticsearch-2-4-2 and unzip it.

* Run `bin/elasticsearch` on unix, or `bin\elasticsearch.bat` on windows.
* Use the django module command to build the search index: `python manage.py rebuild_index` type `y` or add a `--noinput` to the rebuild command. 
* This search index should be updated later when adding content, for example by using a cron job running: `python manage.py update_index`




