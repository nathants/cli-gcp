FROM archlinux:latest

RUN \
    echo  'Server = https://mirrors.ocf.berkeley.edu/archlinux/$repo/os/$arch'  > /etc/pacman.d/mirrorlist && \
    echo  'Server = https://mirrors.rit.edu/archlinux/$repo/os/$arch'          >> /etc/pacman.d/mirrorlist && \
    echo  'Server = https://mirrors.rutgers.edu/archlinux/$repo/os/$arch'      >> /etc/pacman.d/mirrorlist && \
    echo  'Server = https://mirrors.lug.mtu.edu/archlinux/$repo/os/$arch'      >> /etc/pacman.d/mirrorlist && \
    echo  'Server = https://mirrors.kernel.org/archlinux/$repo/os/$arch'       >> /etc/pacman.d/mirrorlist

RUN \
    pacman -Syu --noconfirm && \
    pacman -Sy --noconfirm \
      git \
      python-pip \
      python-setuptools \
      python-virtualenv

RUN \
    rm -rf /var/cache/* /root/.cache/*

RUN \
    pip install -IU \
    git+https://github.com/nathants/py-util \
    git+https://github.com/nathants/py-pool \
    git+https://github.com/nathants/py-schema \
    git+https://github.com/nathants/py-web

EXPOSE 8080

COPY main.py .

CMD ["python", "main.py"]
