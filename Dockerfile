# syntax=docker/dockerfile:1
FROM continuumio/miniconda3
RUN useradd testuser &&\
    mkdir /home/testuser &&\
    chown -R testuser:testuser /opt/conda &&\
    chown -R testuser:testuser /home/testuser &&\
    pdir=$(which python) &&\
    pthfile=${pdir%%/bin/python}/subprocess_coverage.pth &&\
    echo "import coverage" > $pthfile &&\
    echo "coverage.process_startup()" >> $pthfile &&\
    chmod o+rx $pthfile
USER testuser
RUN conda install python=3.7 -y &&\
    conda install  git mobie_utils -c conda-forge -y &&\
    pip install render-python &&\
    pip install git+https://github.com/AllenInstitute/asap-modules/ --no-deps &&\
    pip install git+https://git.embl.de/schorb/pyem &&\
    pip install git+https://github.com/mobie/mobie-utils-python --no-deps \

USER root
CMD ["/bin/bash"]

