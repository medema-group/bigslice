# NOTE: this is a TEMPORARY dockerfile, update this when 2.0 release is up
FROM ubuntu:20.04
RUN apt-get update && apt-get install -y \
	python3-pip \
	git \
&& rm -rf /var/lib/apt/lists/
RUN git clone https://github.com/medema-group/bigslice.git
RUN cd ./bigslice && git checkout 81d4f3f8990827b179b31021135d29a4e8d58deb
RUN pip install ./bigslice/
RUN download_bigslice_hmmdb https://s3.amazonaws.com/share.jgi-ga.org/satria/bigslice-models.2022-11-30.tar.gz
