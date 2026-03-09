FROM stain/jena-fuseki

USER root

RUN apk add --no-cache curl git

COPY load-ontology.sh /load-ontology.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /load-ontology.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
