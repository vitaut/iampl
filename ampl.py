# IPython extension defining the AMPL magic.

import errno
import os
import signal
import sys
import time
from subprocess import Popen, PIPE
from IPython.core.magic import Magics, magics_class, cell_magic
from IPython.utils import py3compat

def try_parse_float(value):
    """If value is a string representing a floating point number, parse the string
       and return the number. Otherwise return value itself."""
    try:
        return float(value)
    except ValueError:
        return value

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

    def _read(self, silent=True):
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
            if not silent:
               sys.stdout.write(block);
               sys.stdout.flush()
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
        result = {}
        for line in data:
            values = line.split(",")
            if nkeycols == 1:
                key = values[0]
            else:
                key = tuple(values[:nkeycols])
            if ndatacols == 1:
                value = try_parse_float(values[nkeycols])
            else:
                value = None
            result[key] = value
        if ndatacols == 0:
            return result.keys()
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
        is interpreted as AMPL code::
        
            In [1]: %%ampl
               ...: var x >= 42;
               ...: minimize o: x;
               ...: solve;

            MINOS 5.51: optimal solution found.
            0 iterations, objective 42

        After executing the code all the AMPL sets, parameters,
        variables, objectives and constraints become available as
        Python objects.
        """

        # Undefine old entities.
        for name, entity in self.entities.iteritems():
            if self.shell.user_ns.get(name) == entity:
                del self.shell.user_ns[name]

        first_time = not self.process
        if first_time:
            cmd = ["ampl", "-g", "-b"]
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
                self._read(silent=False)
            self._write(cell.encode('utf8', 'replace'))
            out = self._read(silent=False)
        except KeyboardInterrupt:
            try:
                # Send SIGINT to the AMPL process group that includes ampl
                # itself and a currently running solver if any.
                os.killpg(os.getpgid(p.pid), signal.SIGINT)
                self._read(silent=False)
            except OSError:
                pass
            except Exception as e:
                print "Error while terminating subprocess (pid=%i): %s" \
                    % (p.pid, e)
            return
        for set in ["_PARS", "_SETS", "_VARS", "_OBJS", "_CONS"]:
            for p in self._read_data(set):
                self._add_entity(p)

        # TODO: add an option to capture the AMPL output
        # See https://github.com/ipython/ipython/blob/master/IPython/core/magics/script.py

def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(AMPLMagic)
