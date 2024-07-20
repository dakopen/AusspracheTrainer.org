# Start from Ubuntu 20.04 LTS as the base image
FROM ubuntu:20.04

# Avoid prompts from apt
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.8 and other necessary packages
RUN apt-get update && \
    apt-get install -y python3.8 python3-pip ffmpeg gettext && \
    rm -rf /var/lib/apt/lists/*

# Update Python commands to Python3.8 and Pip3
RUN ln -s /usr/bin/python3.8 /usr/local/bin/python && \
    ln -s /usr/bin/pip3 /usr/local/bin/pip

# Set the working directory in the container
WORKDIR /usr/src/app

COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# db
RUN python manage.py makemigrations && \
    python manage.py migrate

# language files
RUN python manage.py compilemessages

# Collect static files
# RUN python manage.py collectstatic --noinput

# create superuser if not exists
RUN python manage.py createsuperuserifnotexists

# Expose port for Gunicorn
EXPOSE 8000

# Start Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "aussprachetrainer.wsgi:application"]
