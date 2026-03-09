FROM stain/jena-fuseki

USER root

RUN apt-get update -qq && apt-get install -y --no-install-recommends curl git && rm -rf /var/lib/apt/lists/*

COPY load-ontology.sh /load-ontology.sh
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /load-ontology.sh /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
