FROM python:3.8

# needed by xvfb
ENV DISPLAY :99

WORKDIR /hellen-one

# Copy all files
COPY . ./

# Install all system dependencies
RUN apt-get update && apt-get install -y python3-dev gcc g++ libc-dev libffi-dev libcairo2-dev libjpeg-dev zlib1g-dev xvfb libx11-dev

# Install all python dependencies
RUN pip install --no-cache-dir -r bin/requirements.txt

# Make it executable
RUN chmod a+x run_tests.sh

# Run!
CMD [ "/bin/bash", "run_tests.sh" ]
