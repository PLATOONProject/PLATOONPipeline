# PLATOON Pipeline

This repository contains basic settings for PLATOON Pipeline. 

- `scripts` - contains scripts used for transforming sources to RDF and loading it to triple store (Virtuoso)
      - `virtuoso-script.sh`  - used to remotely connect and load data using `isql-v` tool of virtuoso on command line
      - `load_to_virtuos.py` - used to load the transformed RDF data to virtuoso using the `virtuoso-script.sh` script
      - `transform_and_load.py` - performs both transforming raw data to RDF and loading it virtuoso using the `virtuoso-script.sh` script
      - `mapping_parser.py` - generates the necessary file for the execution of DeTrusty
- `configuration_files` - contains configuration files for the execution of the pipeline
      - `config_rdfizer.ini` - configuration file for materializing the Knowledge Graph using [SDM-RDFizer](https://github.com/SDM-TIB/SDM-RDFizer).
      - `config.ini` - configuration file for generating the DeTrusty configuration file.
- `docker-compose.yml` - docker compose setup for transforming data to RDF and load it to `Virtuoso` triple store.

# Creating RDF Dump using SDM-RDFizer


## Configure (Data Source credentials, output location, etc)

Edit `config_rdfizer.ini` file as follows:

Set the main directory in the `[default]` section 

```bash
	
[default]
main_directory: ./

```
Main directory for this setting is now, current folder. 

```bash

[datasets]
number_of_datasets: 8
output_folder: ${default:main_directory}/rdf-dump
all_in_one_file: yes
remove_duplicate: yes
name: observation-data	
dbtype: mysql
```


In `datasets` section, you can set global parameters such as the number of datasets, output folder, how dump file should be created, name of the dump file (if dump is set to be saved in one file), database type, etc.

-  *`number_of_datasets`* - how many datasets to transforms (create an rdf dump for). e.g., 8
- *`output_folder`* - sets where the transformed dump to be saved, e.g., `${default:main_directory}/rdf-dump` 
- *`all_in_one_file`* - takes `yes` or `no` values, and sets whether to put all datasets in one file or in a separate file names. If set `yes`, then the `name` parameter will be used as the name of the file, i.e., "$(name)".nt and stored in `output_folder`
- *`remove_duplicate`* - takes `yes` or `no` values, and sets wherther duplicates should be removed while generatting RDF triples from single source with different tables/files or multiple data sources that might have duplicate values while applying the transformation.
- *`name`* - sets the name of output RDF dump, if `all_in_one_file` parameter is set to `yes`.
- *`dbtype`* - sets the data source type, e.g., `csv`, `mysql`, `postgres`, `json`, `xml`, etc.

Once the `[default]` and `[datasets]` section is configures, then you need to put as many dataset specific setting as the `number_of_datasets` specified in `[datasets]` section.
For example, the first dataset, `wind_farm_properties`, is configured as follows

```bash

[dataset1]
name: pilot2a_wind_farm_props
user:root
password:1234
host:192.168.0.2
port:3306
db:platoon_db
mapping: ${default:main_directory}/mappings/Wind-Farm/wind-farm.ttl

```

In case that the data source is not a relational data base, the configuration file can be written as follows:

```bash

[dataset1]
name: pilot2a_wind_farm_props
mapping: ${default:main_directory}/mappings/Wind-Farm/wind-farm.ttl

```

Note on the dataset number, `[dataset1]`, dataset number 1 out of 8 datasets in this configuration. Each dataset will have its own configuration param values. In the snippet above, we set the name of dataset (this name will be used if `all_in_one_file` param of the global param is set to `no`). Other settings include: `user` and `password` - user name and password of the user to access the database, `host`, `port`, and `db` - hostname, port and database name of the dataset (dataset1->wind_farm_props), and finally the `mapping` param specifies where the RML mapping rules file is located. RML mapping rules need to conform the [RML Spec](http://rml.io/specs/rml/).

There need to be at least *8* unique names of `[dataset_n]` sections specifiying the parameters of each datasets in this configuration.

## Run `rdfizer` tool to create the RDF dump according to the above configuration and mapping files included in this config.

### Option 1: Using the `rdfizer` tool directly 

1. Install `SDM-RDFizer`

```bash

python3 -m pip install rdfizer

```

2. Then run `rdfizer` script

```bash

cd PLATOONPipeline/
python3 -m rdfizer -c config.ini

```

This will create the RDF dumps according the configuration file, `config.ini`.

### Option 2: Using docker

1. Run the docker compose file included in this repository.

(Prerequisite: *Docker-ce*, *Docker-compose*)

```bash

docker-compose up -d

```

2. Then run `rdfizer` script and load data to virtuoso

- Transform data 

The docker container created above using the docker-compose.yaml file will attach this repository as volume at `/data` endpoint. So running `rdfizer` script as follows will yield the same result as `Option 1` above.

```bash

cd PLATOONPipeline/
docker exec -it sdmrdfizer python3 -m rdfizer -c /data/config.ini 

```

This will create the RDF dumps according the configuration file, `config.ini`, and store the RDF dump in `/data/` volume, which in turn in "PLATOONPipeline/".
You can find the raw RDF file in `.nt` serialization inside 

- Load the RDF dump to Virtuoso


To load the generated RDF dump in step 2, we will use a script included in `/data/scripts/` folder as follows:

```bash

docker exec -it sdmrdfizer python3 /data/scripts/load_to_virtuoso.py 

```

OR to transform and load data automatically, run the following:

```bash

docker exec -it sdmrdfizer python3 /data/scripts/transform_and_load.py -c /data/config.ini

```

`transform_and_load.py` script performs the transformation step and loading to virtuoso after the transformation is performed.

Before running this, make sure you update the environmental variable in the `docker-compose.yml` file as follows:


```bash

environment:
      - SPARQL_ENDPOINT_IP=pilot2akg
      - SPARQL_ENDPOINT_USER=dba
      - SPARQL_ENDPOINT_PASSWD=dba
      - SPARQL_ENDPOINT_PORT=1116
      - SPARQL_ENDPOINT_GRAPH=http://platoon.eu/Pilot2A/KG 
      - RDF_DUMP_FOLDER_PATH=/data/rdf-dump

```

4. Open [http://localhost:8891/sparql](http://localhost:8891/sparql) on your browser

For example, write the following query to see the available classes (Concepts) in this endpoint:

```bash

SELECT DISTINCT ?Concept
WHERE {
	GRAPH <http://platoon.eu/Pilot2A/KG> {
		?s a ?Concept
	 }
  } LIMIT 1000

```

5. Configuring DeTrusty

Generate the source description for DeTrusty:
```bash
docker exec -it sdmrdfizer python3 /data/scripts/mapping_parser.py /path/to/your/config/file
```

The configuration file for mapping_parser.py is similar to the configuration file of the SDM-RDFizer. The main differencce is that it requires the `endpoint`.
Example:

```bash
      
[default]
main_directory: ./

[datasets]
number_of_datasets: 1
endpoint: http://example.org

[dataset1]
name: pilot2a_wind_farm_props
mapping: ${default:main_directory}/mappings/Wind-Farm/wind-farm.ttl
```

Then tell DeTrusty to reload the configuration:
```bash
docker exec -it detrusty /DeTrusty/Scripts/restart_workers.sh
```

6. Executing Query with DeTrusty

This API call is used to send a query to the federation and retrieve the result.
Queries can be executed from [http://localhost:5000/sparql](http://localhost:5000/sparql).
The result will be returned as a JSON (see example below).

Example call:

```bash
curl -X POST -d "query=SELECT ?s WHERE { ?s a <http://dbpedia.org/ontology/Scientist> } LIMIT 10" localhost:5000/sparql
```

Example output for the above query (shortened to two results):

```yaml
{
  "cardinality": 10,
  "execution_time": 0.1437232494354248,
  "output_version": "2.0",
  "head": { "vars": ["s"] },
  "results": {
    "bindings": [
      {
        "__meta__": { "is_verified": True },
        "s": {
          "type": "uri",
          "value": "http://dbpedia.org/resource/A.E._Dick_Howard"
        }
      },
      {
        "__meta__": { "is_verified": True },
        "s": {
          "type": "uri",
          "value": "http://dbpedia.org/resource/A.F.P._Hulsewé"
        }
      },
    ]
  }
}
```
'cardinality' is the number (integer) of results retrieved,
'execution_time' (float) gives the time in seconds the query engine has spent collecting the results,
'output_version' (string) indicates the version number of the output format, i.e., to differentiate the current output from possibly changed output in the future,
'variables' (list) returns a list of the variables found in the query,
'result' is a list of dictionaries containing the results of the query, using the variables as keys;
metadata about the result verification is included in the key '\_\_meta\_\_'.
The current version returns all results as verified as can be seen in the key 'is_verified' of the metadata.

When sending a SPARQL 1.1 query with the SERVICE clause, use the following call:
```bash
curl -X POST -d "query=SELECT ?s WHERE { SERVICE <https://dbpedia.org/sparql> { ?s a <http://dbpedia.org/ontology/Scientist> }} LIMIT 10" -d "sparql1_1=True" localhost:5000/sparql
```
