from flask import Flask, render_template
from neo4j import GraphDatabase
from transformers import pipeline

translator = pipeline("translation_en_to_de", model="Helsinki-NLP/opus-mt-en-de", device=0)

# Flask-App initialisieren
app = Flask(__name__)

# Verbindung zur Neo4j-Datenbank herstellen
uri = "neo4j://localhost:7687"
user = "neo4j"
password = "adminadmin"
driver = GraphDatabase.driver(uri, auth=(user, password))

# Funktion, um Daten für den Graphen abzurufen
def get_graph_data():
    nodes = []
    edges = []

    with driver.session() as session:
        result = session.run("MATCH (n) RETURN n")
        for record in result:
            node = record['n']
            properties = dict(node)

            nodes.append({
                'id': str(node.id),
                'label': properties.get('name','Unknown').replace('_', ' '),
                'original_label': properties.get('name', 'Unknown').replace('_', ' '),
                'german_label': properties.get('german', ''),
                'definition': properties.get('definition', ''),
                'language': properties.get('language', ''),
                'cui': properties.get('CUI', ''),
                'synonyms': properties.get('synonyms', ''),
                'pso': properties.get('PSO', '')
            })

            # Beziehungen abrufen
            rel_result = session.run(f"MATCH (n)-[r]->(m) WHERE id(n)={node.id} RETURN r, m")
            for rel_record in rel_result:
                target_node_id = str(rel_record['m'].id)
                relationship_type = rel_record['r'].type

                original_rel_label= relationship_type.replace('_', ' ')
                translated_rel_label= translate_to_german(relationship_type)


                edges.append({
                    'from': str(node.id),
                    'to': target_node_id,
                    'label': original_rel_label,
                    'original_rel_label': original_rel_label,
                    'translated_rel_label': translated_rel_label,
                })

    return {'nodes': nodes, 'edges': edges}

def translate_to_german(name):
    german_term = translator(name.replace('_', ' '), max_length=40)[0]['translation_text']
    return german_term

# Hauptseite der Webanwendung
@app.route('/')
def index():
    # Daten für den Graphen abrufen und an das Template übergeben
    graph_data = get_graph_data()
    return render_template('index.html', graph_data=graph_data)

if __name__ == '__main__':
    # Flask-Anwendung im Debug-Modus starten
    app.run(debug=True)
