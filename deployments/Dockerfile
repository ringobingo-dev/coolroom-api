FROM amazonlinux:2

# Install required tools and dependencies
RUN yum install -y \
    gcc gcc-c++ make wget \
    bzip2-devel zlib-devel xz-devel \
    openssl-devel libffi-devel tar && \
    yum clean all

# Build and install Python 3.9.9
RUN cd /usr/src && \
    wget https://www.python.org/ftp/python/3.9.9/Python-3.9.9.tgz && \
    tar xzf Python-3.9.9.tgz && \
    cd Python-3.9.9 && \
    ./configure --enable-optimizations 2>&1 | tee configure.log && \
    make -j$(nproc) 2>&1 | tee make.log && \
    make altinstall && \
    rm -rf /usr/src/Python-3.9.9*

# Set up application directory
WORKDIR /app
COPY requirements.txt .

# Install Python dependencies
RUN python3.9 -m pip install -r requirements.txt -t .

# Create the deployment package
CMD ["zip", "-r", "/app/deployment_package.zip", "."]

