FROM stain/jena-fuseki

USER root

COPY load-ontology.sh /load-ontology.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /load-ontology.sh /entrypoint.sh

USER fuseki

ENTRYPOINT ["/entrypoint.sh"]
