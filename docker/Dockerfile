# NOTE: this is a TEMPORARY dockerfile, update this when 2.0 release is up
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y \
	python3-pip \
	git \
&& rm -rf /var/lib/apt/lists/
RUN git clone https://github.com/medema-group/bigslice.git
RUN cd ./bigslice && git checkout ba4056ab33a2d944b62ea91579fbd8c4c303389c
RUN pip install ./bigslice/
RUN download_bigslice_hmmdb https://s3.amazonaws.com/share.jgi-ga.org/satria/bigslice-models.2022-11-30.tar.gz