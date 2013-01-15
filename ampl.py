# This file defines the AMPL magic.

import errno
import signal
import sys
import time
from subprocess import Popen, PIPE
from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.utils import py3compat

class AMPLEntity:
    """AMPL entity such as a parameter, a variable, an objective
       or a constraint"""
    def __init__(self, ampl_magic, name):
        self.ampl_magic = ampl_magic
        self.name = name

    @property
    def val(self):
        return self.ampl_magic._read_data(self.name)

    def __len__(self):
        return len(self.val)

    def __getitem__(self, key):
        return self.ampl_magic._read_data(self.name, key)

    def __iter__(self):
        for item in self.val:
            yield item

    def __str__(self):
        return str(self.val)

@magics_class
class AMPLMagic(Magics):
    """Magics for talking to an AMPL interpreter
    
    This defines an `%%ampl` cell magic for running a cell
    with an AMPL interpreter.
    """

    def __init__(self, shell):
        Magics.__init__(self, shell)
        self.process = None
        self.entities = {}

    def _read(self):
        """Read AMPL output until the next prompt"""
        stdout = self.process.stdout
        out = ""
        while True:
            header = ""
            while True:
                c = stdout.read(1)
                if c == " ":
                    break
                header += c
            length = int(py3compat.bytes_to_str(header))
            data = py3compat.bytes_to_str(stdout.read(length))
            command, block = data.split("\n", 1)
            # TODO: handle errors
            if command.startswith("prompt"):
                break
            out += block
        return out

    def _read_data(self, name, key = None):
        if key:
            name += "["
            if isinstance(key, tuple):
                name += repr(key[0])
                for i in range(1, len(key)):
                    name += ", " + repr(key[i])
            else:
                name += repr(key)
            name += "]"
        self._write("_display %s;" % name)
        out = self._read()
        header, name, data = out.split("\n", 2)
        command, nkeycols, ndatacols, nrows = header.split(' ')
        nkeycols = int(nkeycols)
        ndatacols = int(ndatacols)
        nrows = int(nrows)
        if nkeycols == 0:
            return float(data.rstrip("\n")) # TODO: convert to float optionally
        data = data.split("\n")[0:nrows]
        if nkeycols == 1 and ndatacols == 0:
            return set(data)
        result = {}
        for line in data:
            values = line.split(",")
            if nkeycols == 1:
                key = values[0]
            else:
                key = tuple(values[:nkeycols])
            result[key] = float(values[nkeycols]) # TODO: convert to float optionally
        return result

    def _write(self, input):
        """Write input to AMPL"""
        stdin = self.process.stdin
        stdin.write("%d " % len(input))
        stdin.write(input)
        stdin.flush()

    def _add_entity(self, name):
        entity = AMPLEntity(self, name)
        self.shell.user_ns[name] = entity
        self.entities[name] = entity

    @cell_magic
    def ampl(self, line, cell):
        """Run a cell with an AMPL interpreter
        
        The `%%ampl` line specifies that the rest of the cell
        is interpreted as AMPL code.
        
        Examples
        --------
        ::
        
            In [1]: %%ampl
               ...: var x >= 42;
               ...: minimize o: x;
               ...: solve;
            MINOS 5.51: optimal solution found.
            0 iterations, objective 42
        """

        # Undefine old entities.
        for name, entity in self.entities.iteritems():
            if self.shell.user_ns.get(name) == entity:
                del self.shell.user_ns[name]

        first_time = not self.process
        if first_time:
            cmd = ["ampl", "-b"]
            try:
                p = Popen(cmd, stdout=PIPE, stdin=PIPE)
            except OSError as e:
                if e.errno == errno.ENOENT:
                    print "Couldn't find program: %r" % cmd[0]
                    return
                else:
                    raise
            self.process = p
        else:
            p = self.process

        try:
            if first_time:
                # Read the prompt.
                self._read()
            self._write(cell.encode('utf8', 'replace'))
            out = self._read()
            for set in ["_PARS", "_SETS", "_VARS", "_OBJS", "_CONS"]:
                for p in self._read_data(set):
                    self._add_entity(p)
        except KeyboardInterrupt:
            try:
                p.send_signal(signal.SIGINT)
                time.sleep(0.1)
                if p.poll() is not None:
                    print "Process is interrupted."
                    return
                p.terminate()
                time.sleep(0.1)
                if p.poll() is not None:
                    print "Process is terminated."
                    return
                p.kill()
                print "Process is killed."
            except OSError:
                pass
            except Exception as e:
                print "Error while terminating subprocess (pid=%i): %s" \
                    % (p.pid, e)
            return

        out = py3compat.bytes_to_str(out)
        # TODO: add an option to capture the AMPL output
        # See https://github.com/ipython/ipython/blob/master/IPython/core/magics/script.py
        sys.stdout.write(out)
        sys.stdout.flush()

get_ipython().register_magics(AMPLMagic)
