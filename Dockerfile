FROM cadquery/pythonocc-core

LABEL source="https://github.com/CadQuery/cadquery/tree/master/docker" \
      issues="https://github.com/CadQuery/cadquery/issues" \
      license="https://github.com/CadQuery/cadquery/blob/master/LICENSE"

RUN ln -s /usr/bin/python3.6 /usr/bin/python

# Install python dependencies
RUN python -m pip install pyparsing

COPY . /cadquery
WORKDIR /cadquery

RUN python setup.py install --single-version-externally-managed --record=record.txt
RUN python runtests.py

COPY cadquery.sh cadquery

# Run CadQuery CLI script
CMD ["./cadquery"]
