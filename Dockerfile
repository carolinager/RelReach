# Preparation: 
## build docker image for storm-1.12-master -> yourusername/	storm-relprop
## build stormpy docker image with --build-arg STORM_BASE=yourusername/storm-relprop -> yourusername/stormpy-relprop

# Then build docker image for RelProp with:
## docker build -t yourusername/relprop . --no-cache

FROM yourusername/stormpy-relprop

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
