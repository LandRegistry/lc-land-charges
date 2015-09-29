import subprocess

if __name__ == '__main__':
    subprocess.check_output(['alembic', 'upgrade', 'head'])
