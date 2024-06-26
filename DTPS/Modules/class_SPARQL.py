from queue import Queue
from fastapi import APIRouter
from SPARQLWrapper import SPARQLWrapper, JSON
# from .class_ComponentABC import Component
# from .class_Event import Event
#
# class class_SPARQL(Component):
class class_SPARQL():

    def __init__(self, _conf):
        #self._event = Event()

        #self._router = APIRouter()
        #self.configure_router()

        for item in _conf:
            self.__setattr__(item, _conf[item])

        self.Q = Queue()

        self.classname = self.semantics[ "class"]

        self.prefix_short = self.prefix.split(":")[0].split(" ")[1]
        self.prefix_uri = self.prefix.split(" ")[2].replace("<", "").replace(">", "")

        self.prefix_full = f"""{self.prefix}
                            PREFIX owl: <http://www.w3.org/2002/07/owl#>
                            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                           """
        self.parent = lambda: None
        self.parent._uid = "12341232412"

    def run(self):
        self.sparql = SPARQLWrapper(f"{self.url}/{self.repository}/statements")
        triples = ""
        objectproperties = ""

        for item in self.semantics["triples"]:
            triple = f"{self.prefix_short}:{self.parent._uid} {self.prefix_short}:{item} {self.prefix_short}:{self.semantics['triples'][item]} .\n"
            triples = triples + triple

        for item in self.semantics["objectproperties"]:
            objectproperty = f"{self.prefix_short}:{self.parent._uid} {self.prefix_short}:{item['name']} \"{item['value']}\"^^xsd:{item['type']} .\n"
            objectproperties = objectproperties + objectproperty

        insert = f"""
        INSERT DATA {{
        {self.prefix_short}:{self.parent._uid} rdf:type owl:NamedIndividual ,
        {self.prefix_short}:{self.semantics["class"]} .
        {triples}{objectproperties}
        }}
        """

        self.insert(insert)

    def last(self):
        self.delete(self.parent._uid)

    def query_individual(self, individual):

        self.sparql = SPARQLWrapper(f"{self.url}/{self.repository}")

        where = f"""
                SELECT *
                WHERE {{?individual a {self.prefix_short}:{self.classname}}}
                """

        query = f"{self.prefix_full}{where}"
        print(query)
        self.sparql.method = "GET"
        self.sparql.setQuery(query)

        self.sparql.setReturnFormat(JSON)
        results = self.sparql.query().convert()

        for result in results["results"]["bindings"]:
            for item in result:
                print(result[item]["value"].replace(self.prefix_uri, ""))
            print(result)


    def exists(self, name):
        self.sparql = SPARQLWrapper(f"{self.url}/{self.repository}")
        ask = f"""
                  ASK {{{self.prefix_short}:{name} rdf:type owl:NamedIndividual ,
                  {self.prefix_short}:{self.classname} .}}
                  """

        query = f"{self.prefix_full}{ask}"
        self.sparql.method = "GET"
        self.sparql.setQuery(query)

        # Convert results to JSON format
        self.sparql.setReturnFormat(JSON)
        result = self.sparql.query().convert()
        print(result)
        return result

    def Abfrage(self, Select, Where):
        self.sparql.setQuery(self.Prefix + " " + Select + " " + Where)
        # Convert results to JSON format
        self.sparql.setReturnFormat(JSON)
        Result = self.sparql.query().convert()
        ListeHersteller = []
        for hit in Result["results"]["bindings"]:
            for item in hit:
                Hersteller = hit[item]["value"].replace("http://www.semanticweb.org/lober/ontologies/2022/1/DMP#", "")
                ListeHersteller.append(Hersteller)
        return ListeHersteller

    def insert(self, insert):

        self.sparql = SPARQLWrapper(f"{self.url}/{self.repository}/statements")

        query = f"{self.prefix_full}{insert}"
        self.sparql.setQuery(query)

        self.sparql.method = "POST"
        self.sparql.query()

    def delete(self, name):

        self.sparql = SPARQLWrapper(f"{self.url}/{self.repository}/statements")

        delete = f"""
                DELETE WHERE {{{self.prefix_short}:{name} ?p ?o }}
                """
        query = f"{self.prefix_full}{delete}"

        self.sparql.setQuery(query)
        self.sparql.method = "POST"
        self.sparql.query()



conf = {
    "_id": "class_GraphDB",
    "url": "http://127.0.0.1:7200/repositories",
    "repository": "test",
    "prefix": "PREFIX RDM: <http://www.semanticweb.org/tim/ontologies/2022/10/RDM#>",
    "semantics": {
                  "class": "Resource",
                  "triples": {
                              "offersProductionService": "DrillingService",
                              "processToM": "Metal"
                              },
                  "objectproperties": [
                                        {
                                          "name": "minDiameterHoleResource",
                                          "value": 5.0,
                                          "type": "decimal"
                                        },
                                        {
                                          "name": "maxDiameterHoleResource",
                                          "value": 20.0,
                                          "type": "decimal"
                                        }
                                      ]
                  },
    "_subscribers": {
      },
    "_subscriptions": {
    }
}

tt = class_SPARQL(conf)

tt.run()

tt.exists(tt.parent._uid)

tt.query_individual("1234123412")

tt.last()

tt.exists(tt.parent._uid)

