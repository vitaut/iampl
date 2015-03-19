=========================
IPython interface to AMPL
=========================

This is an IPython extension for working with AMPL.

See `AMPL magic: using IPython as an interface to AMPL
<http://zverovich.net/2013/01/08/ampl-magic-using-ipython-as-an-interface-to-ampl.html>`__
for an introduction on how to use this extension.

It is licensed under the terms of the `BSD license <COPYING.txt>`__.

Installation
============

Using `pip`
-----------

The following command installs the ampl extension using
`pip <http://www.pip-installer.org/en/latest/>`__::

    $ pip install ampl

Using `easy_install`
--------------------

The following command installs the ampl extension using
`easy_install <http://pythonhosted.org/setuptools/easy_install.html>`__::

    $ easy_install ampl

Usage
=====

To load the ampl extension while IPython is running, use the ``%load_ext`` magic::

    In [1]: %load_ext ampl

To load it each time IPython starts, list it in your configuration file:

.. code-block:: python

    c.InteractiveShellApp.extensions = ['ampl']

Credits
=======

Thanks Leonardo Taccari (`sbebo <https://github.com/sbebo>`__) for implementing
the realtime output.
