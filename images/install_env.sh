head -n -1 $MYDIR/environment.yml  > $MYDIR/environment_.yml
micromamba install -y -q -n base git
micromamba install -y -q -n base -f $MYDIR/environment_.yml
micromamba install -y -q -n base jupyterlab
micromamba run pip install -e $MYDIR/cq
micromamba list
micromamba clean --all --yes
