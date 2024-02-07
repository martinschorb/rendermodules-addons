# syntax=docker/dockerfile:1
FROM mambaorg/micromamba
RUN useradd testuser &&\
    mkdir /home/testuser &&\
    chown -R testuser:testuser /opt/conda &&\
    chown -R testuser:testuser /home/testuser
USER testuser
RUN mamba install python=3.7 -y &&\
    mamba install  git mobie_utils -c conda-forge -y &&\
    pip install render-python &&\
    pip install git+https://github.com/AllenInstitute/asap-modules/ &&\
    pip install git+https://git.embl.de/schorb/pyem &&\
    pip install git+https://github.com/mobie/mobie-utils-python --no-deps &&\
    pip install -r test_requirements.txt
USER root
CMD ["/bin/bash"]

