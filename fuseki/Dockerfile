FROM stain/jena-fuseki:5.1.0

USER root

RUN apk add --no-cache curl git

COPY valor-config.ttl /fuseki/configuration/valor.ttl
COPY load-ontology.sh /load-ontology.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /load-ontology.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["/jena-fuseki/fuseki-server"]
