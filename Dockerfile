# syntax=docker/dockerfile:1
FROM condaforge/mambaforge
RUN useradd testuser &&\
    mkdir /home/testuser &&\
    chown -R testuser:testuser /opt/conda &&\
    chown -R testuser:testuser /home/testuser
USER testuser
RUN mamba install python=3.10 -y &&\
    mamba install --file asap_conda_requirements.txt -c conda-forge
RUN pip install -r asap_requirements.txt &&\
    pip install git+https://github.com/AllenInstitute/asap-modules/ --no-deps &&\
    pip install git+https://git.embl.de/schorb/pyem
RUN pip install -r test_requirements.txt
USER root
CMD ["/bin/bash"]

