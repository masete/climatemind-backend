import os
import urllib

import networkx as nx
from sqlalchemy import create_engine

from app.models import Scores
from app.network_x_tools.network_x_local_graph import (
    make_acyclic,
    local_graph,
)


# TODO Figure out how to remove these duplicate methods without breaking things
def get_iri(full_iri):
    """Node IDs are the unique identifier in the IRI. This is provided to the
    front-end as a reference for the feed, but is never shown to the user.

    Example http://webprotege.stanford.edu/R8znJBKduM7l8XDXMalSWSl

    Parameters
    ----------
    node - A networkX node
    """
    offset = 4  # .edu <- to skip these characters and get the unique IRI
    pos = full_iri.find("edu") + offset
    return full_iri[pos:]


# TODO Figure out how to remove these duplicate methods without breaking things
def get_node_id(node):
    """Node IDs are the unique identifier in the IRI. This is provided to the
    front-end as a reference for the feed, but is never shown to the user.

    Example http://webprotege.stanford.edu/R8znJBKduM7l8XDXMalSWSl

    Parameters
    ----------
    node - A networkX node
    """
    offset = 4  # .edu <- to skip these characters and get the unique IRI
    full_iri = node["iri"]
    pos = full_iri.find("edu") + offset
    return full_iri[pos:]


def check_if_valid_postal_code(quiz_uuid):
    # Find the user's postal code and cast to an integer for lookup in the lrf_data table.
    # This will need to change if postal codes with letters are added later and the data type in the lrf_data table changes.

    score = Scores.query.filter_by(quiz_uuid=quiz_uuid).first()
    if score:
        try:
            postal_code = int(score.postal_code)
        except (ValueError, TypeError):
            # non integer values are not supported yet
            return None

        DB_CREDENTIALS = os.environ.get("DATABASE_PARAMS")
        SQLALCHEMY_DATABASE_URI = (
            "mssql+pyodbc:///?odbc_connect=%s" % urllib.parse.quote_plus(DB_CREDENTIALS)
        )

        engine = create_engine(SQLALCHEMY_DATABASE_URI, echo=True)

        with engine.connect() as con:
            # Check if postal code is in lrf_data table and create a list of values
            result = con.execute(
                "SELECT * FROM lrf_data WHERE lrf_data.postal_code=?",
                (postal_code,),
            ).fetchone()

            if not result:
                return None

            db_postal_codes = list(result)
            # Get the column names from the lrf_data table and create a list of names
            columns = con.execute(
                "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='lrf_data'"
            )
            column_names = columns.fetchall()
            column_names_list = []

            for name in column_names:
                column_names_list.append(name[0])

        if db_postal_codes:
            # Create a dictionary of lrf data for the specific postal code where the lrf_data table column names
            # (the postal code and the IRIs) are the keys matched to the lrf_data table values for that postal code.
            short_IRIs = [get_iri(long_iri) for long_iri in column_names_list[1:]]

            lrf_single_postcode_dict = dict(zip(short_IRIs, db_postal_codes[1:]))
            return lrf_single_postcode_dict

        else:
            return None


def get_starting_nodes(acyclic_graph):
    """
    Given a graph, find the terminal nodes (nodes that have no children with "causes_or_promotes" relationship) that are in the Test Ontology,
    and also are not in the class 'risk solution' (whether directly or indirectly) [doesn't include solution nodes].

    Parameters
    graph - an acyclic networkx graph of the climate mind ontology
    """
    starting_nodes = []
    for node in acyclic_graph.nodes:
        if not list(acyclic_graph.neighbors(node)):
            if (
                "test ontology" in acyclic_graph.nodes[node]
                and acyclic_graph.nodes[node]["test ontology"][0] == "test ontology"
            ):
                if "risk solution" in acyclic_graph.nodes[node]:
                    if (
                        "risk solution"
                        not in acyclic_graph.nodes[node]["risk solution"]
                    ):
                        starting_nodes.append(node)
                else:
                    starting_nodes.append(node)
        else:
            neighbor_nodes = acyclic_graph.neighbors(node)
            has_no_child = True
            for neighbor in neighbor_nodes:
                if acyclic_graph[node][neighbor]["type"] == "causes_or_promotes":
                    has_no_child = False
            if has_no_child:
                if (
                    "test ontology" in acyclic_graph.nodes[node]
                    and acyclic_graph.nodes[node]["test ontology"][0] == "test ontology"
                ):
                    if "risk solution" in acyclic_graph.nodes[node]:
                        if (
                            "risk solution"
                            not in acyclic_graph.nodes[node]["risk solution"]
                        ):
                            starting_nodes.append(node)
                    else:
                        starting_nodes.append(node)
    return starting_nodes


def build_localised_acyclic_graph(G, quiz_uuid):
    """
    Builds acyclic graph with all the nodes in it above the terminal nodes to have isPossiblyLocal field populated with 0 or 1,
    (0 for certainly not local, and 1 for maybe local or certainly local).

    Parameters
    G - networkx graph of the climate mind ontology
    quiz_uuid - session id from the SQL database
    """
    localised_acyclic_graph = make_acyclic(G)
    lrf_single_postcode_dict = check_if_valid_postal_code(quiz_uuid)
    if not lrf_single_postcode_dict:
        return G
    else:
        localised_acyclic_graph = add_lrf_data_to_graph(
            localised_acyclic_graph, lrf_single_postcode_dict
        )
        starting_nodes = get_starting_nodes(localised_acyclic_graph)

        visited_dictionary = {}
        for starting_node in starting_nodes:
            local_graph(starting_node, localised_acyclic_graph, visited_dictionary)

        return localised_acyclic_graph


def add_lrf_data_to_graph(graph, dict):
    graph_attributes = nx.get_node_attributes(graph, "all classes")

    lrf_to_iri_dict = {}
    for node in graph.nodes:
        lrf_to_iri_dict[get_node_id(graph.nodes[node])] = node
    for iri in dict.keys():
        if dict[iri] == False:
            nx.set_node_attributes(graph, {lrf_to_iri_dict[iri]: 0}, "isPossiblyLocal")
        if dict[iri] == True:
            nx.set_node_attributes(graph, {lrf_to_iri_dict[iri]: 1}, "isPossiblyLocal")

    return graph
