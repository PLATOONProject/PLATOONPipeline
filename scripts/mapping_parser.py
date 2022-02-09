import sys
import rdflib
import json


def get_linked_to(dic):
	links = []
	for predicate in dic["predicates"]:
		for parent_class in predicate["range"]:
			links.append(parent_class)
	return links


def get_predicates(dic):
	predicates = []
	for predicate in dic["predicates"]:
		predicates.append(predicate["predicate"])
	return predicates


def mapping_parser(endpoint, mapping_file):
	"""
	(Private function, not accessible from outside this package)

	Takes a mapping file in Turtle (.ttl) or Notation3 (.n3) format and parses it into a list of
	TriplesMap objects (refer to TriplesMap.py file)

	Parameters
	----------
	mapping_file : string
		Path to the mapping file

	Returns
	-------
	A list of TriplesMap objects containing all the parsed rules from the original mapping file
	"""
	mapping_graph = rdflib.Graph()

	try:
		mapping_graph.load(mapping_file, format='n3')
	except Exception as n3_mapping_parse_exception:
		print(n3_mapping_parse_exception)
		print('Could not parse {} as a mapping file'.format(mapping_file))
		print('Aborting...')
		sys.exit(1)

	mapping_query = """
		prefix rr: <http://www.w3.org/ns/r2rml#> 
		prefix rml: <http://semweb.mmlab.be/ns/rml#> 
		prefix ql: <http://semweb.mmlab.be/ns/ql#> 
		prefix d2rq: <http://www.wiwiss.fu-berlin.de/suhl/bizer/D2RQ/0.1#> 
		select distinct  ?Class  ?predicate ?range
		where {
              ?s <http://www.w3.org/ns/r2rml#subjectMap> ?o2 .
              ?o2 <http://www.w3.org/ns/r2rml#class> ?Class .
              ?s <http://www.w3.org/ns/r2rml#predicateObjectMap> ?o4 .
              ?o4 <http://www.w3.org/ns/r2rml#predicate> ?predicate.
              OPTIONAL {?o4 rr:objectMap ?_object_map .
						?_object_map rr:parentTriplesMap ?object_parent_triples_map .
						?object_parent_triples_map <http://www.w3.org/ns/r2rml#subjectMap> ?o5 .
						?o5 <http://www.w3.org/ns/r2rml#class> ?range .}
			} ORDER BY ?Class """

	mapping_query_results = mapping_graph.query(mapping_query)
	class_list = {}
	json_file = []
	json_name = "/data/DeTrusty/Config/rdfmts.json"
	for result_triples_map in mapping_query_results:
		if str(result_triples_map.Class) not in class_list:
			class_list[str(result_triples_map.Class)] = ""
			if str(result_triples_map.range) != "None":
				json_file.append({"rootType": str(result_triples_map.Class), "predicates": [{"predicate": str(result_triples_map.predicate), "range": [str(result_triples_map.range)]}]})
			else:
				json_file.append({"rootType": str(result_triples_map.Class), "predicates": [{"predicate": str(result_triples_map.predicate), "range": []}]})
		else:
			for root in json_file:

				if str(result_triples_map.Class) == root["rootType"]:
					new_predicate = True
					for predicate in root["predicates"]:
						if predicate["predicate"] == str(result_triples_map.predicate):
							if str(result_triples_map.range) != "None":
								predicate["range"].append(str(result_triples_map.range))
							new_predicate = False
					if new_predicate:
						if str(result_triples_map.range) != "None":
							root["predicates"].append({"predicate": str(result_triples_map.predicate), "range": [str(result_triples_map.range)]})
						else:
							root["predicates"].append({"predicate": str(result_triples_map.predicate), "range": []})

	for root in json_file:
		root["linkedTo"] = get_linked_to(root)
		root["wrappers"] = [{"url": str(endpoint), "predicates": get_predicates(root), "urlparam": "", "wrapperType":"SPARQLEndpoint"}]

	json.dump(json_file, open(json_name, 'w+'))


if __name__ == '__main__':
	mapping_parser(str(sys.argv[1]), str(sys.argv[2]))
