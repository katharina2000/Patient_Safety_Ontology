Verbindung mit Neo4j und Erstellung Graphen in neo4j

Docker Instanz starten:
 docker run \
    --restart always \
    --publish=7474:7474 --publish=7687:7687 \
    --env NEO4J_AUTH=neo4j/adminadmin \
    neo4j:5.19.0

Im Browser öffnen:
http://localhost:7474/

Für die Anmeldung:
 URL: "neo4j://localhost:7687"
 user:"neo4j"
 password:"adminadmin
