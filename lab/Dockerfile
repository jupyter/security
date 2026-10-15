FROM python:3.12-slim

ARG SECURITY_OVERVIEW_REF=0a31e9e8b6f7027780401c5ee10af3021db46418

RUN pip install --no-cache-dir \
      jupyterlab==4.6.3 \
      pandas==3.0.5 \
      matplotlib==3.11.1 \
      "security-overview @ https://github.com/Yann-P/github-security-overview/archive/${SECURITY_OVERVIEW_REF}.tar.gz"

RUN useradd --create-home --uid 1000 lab
USER lab
WORKDIR /home/lab/work

COPY --chown=lab:lab advisories.ipynb .

EXPOSE 8888
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--no-browser", "--ServerApp.root_dir=/home/lab/work"]
