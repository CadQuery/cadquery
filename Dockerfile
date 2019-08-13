FROM cadquery/pythonocc-core

LABEL source="https://github.com/CadQuery/cadquery/tree/master/docker" \
      issues="https://github.com/CadQuery/cadquery/issues" \
      license="https://github.com/CadQuery/cadquery/blob/master/LICENSE"

# Install dependencies
RUN pip3 install pyparsing

COPY . /cadquery
WORKDIR /cadquery
RUN mkdir cmake-build

RUN python3 setup.py install --single-version-externally-managed --record=record.txt
RUN python3 runtests.py

COPY cadquery.sh cadquery.sh

# Run CadQuery CLI script
ENTRYPOINT ["./cadquery.sh"]
