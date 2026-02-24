#!/bin/sh
set -e

SERVER_URL="${1:-http://rdf4j:8080/rdf4j-server}"
REPOSITORY_ID="${2:-logre}"
REPOSITORY_LABEL="Logre (${REPOSITORY_ID})"

echo "Ensuring RDF4J repository '$REPOSITORY_ID' exists at $SERVER_URL"

if curl -fsS -o /dev/null "$SERVER_URL/repositories/$REPOSITORY_ID"; then
  echo "Repository '$REPOSITORY_ID' already available."
  exit 0
fi

echo "Repository missing. Creating..."

cat <<EOF | curl -fsS -o /dev/null -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @- \
  "$SERVER_URL/repositories/SYSTEM/statements"
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rep: <http://www.openrdf.org/config/repository#> .
@prefix sr: <http://www.openrdf.org/config/repository/sail#> .
@prefix sail: <http://www.openrdf.org/config/sail#> .
@prefix ns: <http://www.openrdf.org/config/sail/native#> .

[] a rep:Repository ;
   rep:repositoryID "${REPOSITORY_ID}" ;
   rdfs:label "${REPOSITORY_LABEL}" ;
   rep:repositoryImpl [
       rep:repositoryType "openrdf:SailRepository" ;
       sr:sailImpl [
           sail:sailType "openrdf:NativeStore" ;
           ns:tripleIndexes "spoc,posc"
       ]
   ] .
EOF

echo "Repository '$REPOSITORY_ID' created."
