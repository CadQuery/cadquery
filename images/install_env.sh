
head -n -1 /tmp/environment.yml  > /tmp/environment_.yml
micromamba install -y -q -n base git
micromamba install -y -q -n base -f /tmp/environment_.yml
micromamba install -y -q -n base jupyterlab
micromamba run pip install -e /tmp/cq
micromamba list
micromamba clean --all --yes
