import os, socket, base64, time, stat
from pathlib import PurePosixPath

class Host:
    def __init__(self):
        import paramiko
        self.paramiko = paramiko
        values = os.environ['SFTP_HOST_PUBLIC_KEY'].split()
        i = next(i for i, value in enumerate(values) if value.startswith(('ssh-', 'ecdsa-')))
        self.key = paramiko.PKey.from_type_string(values[i], base64.b64decode(values[i+1], validate=True))
        self.transport = None
        self.opened = 0

    def close(self):
        if self.transport is not None:
            self.transport.close()
            self.transport = None

    def session(self):
        if self.transport and self.transport.is_active() and time.monotonic() - self.opened < 45:
            return self.sftp
        self.close()
        self.transport = self.paramiko.Transport(socket.create_connection((os.environ['SFTP_HOST'].strip(), 22), timeout=25))
        self.transport.start_client(timeout=25)
        if self.transport.get_remote_server_key().asbytes() != self.key.asbytes():
            raise ValueError('Hosting server identity mismatch')
        self.transport.auth_password(os.environ['SFTP_USER'].strip(), os.environ['SFTP_PASSWORD'])
        self.transport.set_keepalive(12)
        self.sftp = self.paramiko.SFTPClient.from_transport(self.transport)
        self.sftp.get_channel().settimeout(40)
        self.opened = time.monotonic()
        return self.sftp

    def run(self, operation):
        for attempt in range(3):
            try:
                return operation(self.session())
            except (EOFError, ConnectionError, TimeoutError, self.paramiko.SSHException) as exc:
                self.close()
                if isinstance(exc, self.paramiko.AuthenticationException) or attempt == 2:
                    raise
                time.sleep(attempt + 1)


def read(sftp, path):
    try:
        with sftp.open(str(path), 'rb') as f:
            return f.read()
    except FileNotFoundError:
        return None


def guarded_replace(sftp, path, expected, data):
    current = read(sftp, path)
    if current == data:
        return
    if current != expected:
        raise RuntimeError('Concurrent site edit: ' + str(path))
    if data is None:
        sftp.remove(str(path))
        return
    parent = PurePosixPath(path.anchor or '.')
    for segment in path.parts[(1 if path.anchor else 0):-1]:
        parent /= segment
        try:
            if not stat.S_ISDIR(sftp.stat(str(parent)).st_mode):
                raise ValueError('Expected a directory: ' + str(parent))
        except FileNotFoundError:
            sftp.mkdir(str(parent))
    temp = str(path) + '.trade-stage'
    with sftp.open(temp, 'wb') as f:
        f.write(data)
    sftp.chmod(temp, 0o644)
    sftp.posix_rename(temp, str(path))
    if read(sftp, path) != data:
        raise RuntimeError('Hosting write verification failed: ' + str(path))


def backup(sftp, location, archive):
    with sftp.open(location + '.stage', 'wb') as f:
        f.write(archive)
    sftp.chmod(location + '.stage', 0o600)
    if read(sftp, location + '.stage') != archive:
        raise RuntimeError('Rollback archive verification failed')
    sftp.posix_rename(location + '.stage', location)


