# syntax=docker/dockerfile:1
FROM continuumio/miniconda3
RUN useradd testuser &&\
    mkdir /home/testuser &&\
    chown -R testuser:testuser /opt/conda &&\
    chown -R testuser:testuser /home/testuser
USER testuser
RUN conda install python=3.7 -y &&\
    conda install  git mobie_utils -c conda-forge -y &&\
    pip install render-python &&\
    pip install git+https://github.com/AllenInstitute/asap-modules/ --no-deps &&\
    pip install git+https://git.embl.de/schorb/pyem &&\
    pip install git+https://github.com/mobie/mobie-utils-python --no-deps \
    mkdir -p $(python -m site --user-site) \
    echo "import coverage" > $(python -m site --user-site)/subprocess_coverage.pth \
    echo "coverage.process_startup()" >> $(python -m site --user-site)/subprocess_coverage.pth
USER root
CMD ["/bin/bash"]

