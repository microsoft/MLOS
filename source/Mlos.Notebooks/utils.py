import os
import random
import string
import subprocess
import sys

def generate_random_password(length=10):
    """ Generates a random password of specified length with at least one of each: lowercase letter, uppercase letter, digit.

    :param length:
    :return:
    """
    assert length > 3
    legal_chars = string.ascii_letters + string.digits
    naive_password = [random.choice(legal_chars) for _ in range(length)]

    # We need at least one of each: lower case letter, upper case letter, digit
    random_lowercase_letter = random.choice(string.ascii_lowercase)
    random_uppercase_letter = random.choice(string.ascii_uppercase)
    random_digit = random.choice(string.digits)

    # Note: we have to generate them simultaneously to guarantee uniqueness.
    random_positions = random.sample(range(length), 3)

    new_chars_positions = zip(random_positions, [
        random_lowercase_letter,
        random_uppercase_letter,
        random_digit
    ])
    for position, new_char in new_chars_positions:
        naive_password[position] = new_char
    return ''.join(naive_password)

def build_docker_image(sa_password):
    pushd("../Mlos.Python")
    docker_command = f"docker build -f Docker/Dockerfile -t mssql-server-linux-with-mlos-python --build-arg SA_PASSWORD={sa_password} ."
    run_command_and_stream_output(docker_command)
    popd()

def run_docker_container():
    command = "docker run --detach -p50051:50051 --name MlosOptimizerService mssql-server-linux-with-mlos-python"
    print(command)
    run_command_and_stream_output(command=command)

def stop_docker_container():
    command = "docker stop MlosOptimizerService"
    print(command)
    run_command_and_stream_output(command)

def remove_docker_container():
    command = "docker container rm MlosOptimizerService"
    print(command)
    run_command_and_stream_output(command)

def run_command_and_stream_output(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in iter(process.stdout.readline, b''):
        sys.stdout.write(line)

    for line in iter(process.stderr.readline, b''):
        sys.stderr.write(line)

# Little directory helpers.
#
dir_stack = []

def pushd(new_dir):
    global dir_stack
    dir_stack.append(os.getcwd())
    os.chdir(new_dir)

def popd():
    global dir_stack
    if not dir_stack:
        return
    os.chdir(dir_stack.pop())
