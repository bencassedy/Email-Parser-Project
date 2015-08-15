Email-Parser-Project
====================

Test DB of Emails for Advanced Querying and Analytics

This is a test project to parse emails, store them in a document-based database (MongoDB), query them using Elasticsearch, and tag them using HTML and AngularJS. Part of the design philosophy with this project is that the records are all either JSON or a close equivalent (python dict or JS object), so that the records can easily be passed back and forth between the MVC components with minimal transformation or ORM. In my experience thus far with this project, python, mongo, es, and angularjs all play extremely nicely together (largely due to the JSON commonality), making this what I hope is an effective stack to scale to much larger datasets.

Most of the basic functionality is there (parsing, storage, querying, MVC views, etc.) but this is definitely a work in progress. Future plans for this project include aggregation/facet analysis and statistics, along with more advanced text analytics such as a binary classifier (naive Bayes), regression, knn, and clustering, all most likely via the scikit-learn Python package.

Running this application requires a running [MongoDB](http://www.mongodb.org "MongoDB homepage") instance, a running [Elasticsearch](http://elasticsearch.org "Elasticsearch homepage") instance, and the Python dependencies noted in the 'requirements.txt' file. Generally, those dependencies would be implemented via the standard virtualenv method, e.g., `source env/bin/activate` and `pip install -r requirements.txt`.

This application also presumes the existence of some email corpus to analyze; the Enron dataset is available [here](http://www.cs.cmu.edu/~./enron/) as flat text files (or can also be found on AWS public datasets). Assuming use of the flat text files, you could point the /bin/config.py file to any given email custodian's subdirectory (or the entire corpus, for that matter) and the mailparser.py file should take care of parsing them, which is essentially just leveraging the built-in Python email module. So, this should work with any other mail format with minor modification, i.e., I would imagine it to be fairly straightforward to use this with an mbox archive (gmail, linux, etc.) and I have future plans to do so.

Once the emails are parsed, they should be available as a MongoDB collection that can be accessed or queried in the `mongo` shell. But to get to the flask server and frontend, the `python app/app.py` command should be executed, and that should start the flask web server (future plans to move this to gunicorn and heroku), which can be accessed at `http://localhost:5000` or wherever your flask port may be.
