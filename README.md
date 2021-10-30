# GBD Benchmark Database Tools
GBD Tools consists of two python tools, one command-line interface ```gbd``` and the micro-services and website ```gbd-server```. 
GBD facilitates the management of features of benchmark instances and thus the differentiated analysis of runtime experiments. 

GBD was created for analysis of experiments in SAT Solving and to distribute benchmark instances in DIMACS CNF. 
Internally, Benchmark Instances are identified using GBD-Hash which hashes the normalized version of a CNF file, such that benchmark instance recognition is invariant to comments, compression, filename, line-encoding, etc. 
GBD can be used in other domains, if GBD-Hash is replaced accordingly. 

## Programming Language
- Python 3
- SQLite

## Installation
- Setup python3 and pip3
- Install GBD via ```pip3 install gbd-tools```

## Configuration
- Download a database, e.g., [http://gbd.iti.kit.edu/getdatabase/meta.db](http://gbd.iti.kit.edu/getdatabase/meta.db), and safe it as [path/file]
- ```export GBD_DB=[path/file]``` (and put it in your .bashrc)
- GBD_DB can contain several colon-spararted paths (semi-colon on Windows)
- GBD_DB can be overriden by command-line argument ```gbd --db=[path/other]```

## GBD Command Line Interface
An overview on the commands of the gbd command-line interface is generated by gbd-help:
> ```gbd --help```
> 
> ```gbd [command] --help```


### Accessing information with GBD
In order to get an overview over the features stored in your database:
> ```gbd info```
> 
> ```gbd info [feature]```

To get the list of benchmark instances referenced in your database (assuming the features 'result', 'filename' and 'family' are present in the database you use):
> ```gbd get```
> 
> ```gbd get -r filename```
> 
> ```gbd get -r result family```

GBD Queries can be used to filter the instances:
> ```gbd get "family = hardware-bmc" -r filename```

> ```gbd get "family = hardware-bmc and (filename like %ibm% or author = biere)" -r filename```

> ```gbd get "family = uniform-random and (clauses / variables) = 4.2" -r filename```

In order to use gbd in your experimentation workflow, gbd has to store the paths to the locally available benchmark instances. As this involves unpacking and hashing of all your instances, we recommend using gbds parallelization support. Also, we recommend installing the python acceleration module [https://github.com/Udopia/gbdhash](https://github.com/Udopia/gbdhash). In case you have downloaded your database from another source, this database might reference paths which are not available on your disk. GBD will ask you to remove them, just do it, this will not affect other features stored in the database. 
> ```gbd -j[nof-cores] init local [path/to/cnf]```

Once you initialized the database with your local paths, you can run gbd queries and resolve the result against your local paths. If you have duplicates, you might want to use -c to collapse multiple values into one. 
> ```gbd get "family = hardware-bmc" -r local```

> ```gbd get "family = hardware-bmc" -r local -c min```

Having initialized the instance feature ```local```, gbd can be used for experimentation.
> ```while read -r hash path; do ./solve $path > $hash.out; done < <(gbd get "competition_track = main_2020" -r local)```

GBD Queries are not the only way to retrieve instance features. Given a list of hashes, you can use pipes to retrieve data about the benchmark instances.
> ```echo $hashes | gbd get -r family```

Since instances are sometimes shuffled from one competition to another, we provide means to recognize the equivalence class of shuffled instances. You can generate the degree-sequence-hash for each instance with another sub-command of the init-command. GBDs degree-sequence-hash is the sorted sequence of in- and out-degrees of the polarity-perserving clause-variable graph. 
> ```gbd -j[nof-cores] init degree_sequence_hash```

GBD Queries by default generate a list of gbd-hashes which is subsequently joined with the requested features. You can override this default grouping-behaviour, and e.g. group by degree_sequence_hash to display the equivalence groups, or to filter for only one representative. 
> ```gbd get -g degree_sequence_hash -r hash```

> ```gbd get -g degree_sequence_hash -r hash local -c min```


### Maintenance of Benchmark Instance Data with GBD
In GBD all data-points are seen as features of instances. Like this also runtimes of solvers on an instance can be stored as a specific featres. GBD provides means to bootstrap default-features, to distribute databases storing features and to create your own features. 

## GBD Create, Rename, Delete

## GBD Import

## GBD Set


### Evaluating Experiments

## GBD Feaure Meta-Info and Types


## GBD Server and Micro-Services
GBD-Server starts a Web-Service alongside a bunch of micro-services which facilitates the distribution of benchmark instances and their feature over the web. 

> ```gbd-server --help```.
