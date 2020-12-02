import os, subprocess
from hashlib import md5

tmp_pre = 'tmp'

diff_path_default = 'fc' if os.name == 'nt' else 'diff'
mars_path_default = os.path.join(os.path.dirname(__file__), 'kits', 'Mars_Changed.jar')
mars_timeout_default = 3


class VerificationFailed(Exception):
    pass


def _communicate_callback(proc, fp, handler, timeout=None):
    for line in proc.communicate(timeout=timeout)[0].decode(errors='ignore').splitlines():
        r = handler(line.strip())
        if r:
            fp.write(r + '\n')


def hash_file(fn):
    with open(fn, 'rb') as fp:
        return md5(fp.read()).hexdigest()[:10]


def kill_pid(pid):
    if os.name != 'nt':
        raise NotImplementedError
    subprocess.run(['taskkill', '/f', '/pid', str(pid)])


def kill_im(im):
    if os.name != 'nt':
        raise NotImplementedError
    subprocess.run(['taskkill', '/f', '/im', im])


class MARSError(VerificationFailed):
    pass


class BaseJudge:

    @staticmethod
    def __init__():
        if not os.path.isdir(tmp_pre):
            os.mkdir(tmp_pre)

    @staticmethod
    def _communicate(cmd, out_fn, handler, timeout, timeout_msg, error_meta, error_msg=None, cwd=None, env=None,
                     nt_kill=True):
        with open(out_fn, 'w', encoding='utf-8') as fp:
            with subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=cwd, env=env) as proc:
                try:
                    _communicate_callback(proc, fp, handler, timeout)
                except subprocess.TimeoutExpired as e:
                    proc.kill()
                    if nt_kill and os.name == 'nt':
                        im = cmd[0]
                        if not os.path.splitext(im)[1]:
                            im += '.exe'
                        kill_im(os.path.basename(im))
                    _communicate_callback(proc, fp, handler)
                    raise MARSError('{} timed out after {} secs'.format(error_meta, timeout)
                                    + ((', ' + timeout_msg) if timeout_msg else '')) from e
            if proc.returncode:
                raise MARSError(error_meta + ' subprocess returned ' + str(proc.returncode)
                                + ((', ' + error_msg) if error_msg else ''))

    @staticmethod
    def _mars_parse(s):
        if 'error' in s.lower():
            raise MARSError('MARS reported ' + s)
        if s.startswith('@'):
            return s

    def attach(self, mips):
        self.mips = mips

    def call_mars(self, asm_path, hex_path, ans_path, timeout=mars_timeout_default):
        self._communicate([self.java_path, '-jar', self.mars_path, asm_path,
                           'nc',
                           'db' if self.db else '',
                           'np' if self.np else '',
                           'mc', 'CompactDataAtZero', 'dump', '.text',
                           'HexText', hex_path],
                          ans_path, self._mars_parse, timeout,
                          'maybe an infinite loop, see ' + ans_path, 'MARS'
                          )

        if hasattr(self, 'mips'):
            with open(hex_path, 'r', encoding='utf-8') as fp:
                r = fp.read()
            r = self.mips(r, pc_start=self.pc_start, db=db)
            with open(ans_path, 'w', encoding='utf-8') as fp:
                fp.write(r)

    def diff(self, out_path, ans_path, log_path=None, keep=False):
        with subprocess.Popen([self.diff_path, out_path, ans_path],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE) as proc:
            res = proc.communicate()
            if proc.returncode:
                if log_path is None:
                    log_path = out_path + '.diff'
                with open(log_path, 'wb') as fp:
                    fp.write(res[0] + b'\n' + res[1])
                # res = res[0].decode(errors='ignore') + res[1].decode(errors='ignore')
                # print(res, file=sys.stderr)
                raise VerificationFailed('output differs, see {}, {}, and {} for diff logs'
                                         .format(out_path, ans_path, log_path))
            elif not keep:
                os.remove(out_path)
                os.remove(ans_path)
