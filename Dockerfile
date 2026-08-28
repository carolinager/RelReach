# Preparation: 
## Pull docker image for stormpy 1.14.0: docker pull movesrwth/stormpy:1.14.0

# Then build docker image for RelProp with:
## docker build -t relprop . --no-cache
## docker build -t relprop . --no-cache --build-arg STORMPY_BASE=different_stormpy_image

ARG STORMPY_BASE=movesrwth/stormpy:1.14.0
FROM $STORMPY_BASE

# Obtain latest version of RelProp from public repository
WORKDIR /opt/
RUN git clone --depth 1 https://github.com/carolinager/RelProp

# Switch to RelProp directory
WORKDIR /opt/RelProp

# if not cloning from remote: 
# COPY . .

# Install dependencies for RelProp
RUN pip3 install termcolor

# To create a separate container for a specific RelReach command:
# uncomment the following line and insert the command
# CMD python3 relprop.py <insert_command_here>
