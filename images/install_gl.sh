apt update
apt install -y \
      libgl1 \
      libglx-mesa0 \
      libegl1 \
      libgl1-mesa-dri \
      mesa-utils \
      xauth
rm -rf /var/lib/apt/lists/*
