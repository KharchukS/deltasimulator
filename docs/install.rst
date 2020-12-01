Installation
============

This section will explain how to install a released version of Deltasimulator.
In this case users will obtained only the source code of the package without
test suite, tutorials, examples, and documentation. This is best suited for
those who would like to use the package as it is and do not change it.

For those who would like to get involved into development we suggest following
steps in :doc:`development`.

Prerequisites
^^^^^^^^^^^^^
.. note::
  Currently, we only support and test Deltasimulator on Ubuntu 20.04.

You will require 
`Python 3.8 <https://www.python.org/downloads/release/python-385/>`_.
Along with this you need `pip`, a python package manager, and python
development tools. You can get these using :code:`apt-get`.

.. code-block:: console
   
  $ sudo apt-get install python3-dev python3-pip

Next, install these additional dependencies with :code:`apt-get`.

.. code-block:: console

  $ sudo apt-get install autoconf flex bison libghc-zlib-dev libgmp-dev

Install `SysemC <https://www.accellera.org/downloads/standards/systemc>`_
by downloading the source and then following the instructions in the
downloaded :code:`INSTALL` file. We test and develop Deltasimulator
using SystemC version 2.3.3, so install that version to ensure compatibility.

Install `verilator 
<https://www.veripool.org/projects/verilator/wiki/Installing>`_ by following
their instructions to install via git. We test and develop Deltasimulator 
using verilator version 4.026, so install that version to ensure 
compatibility.

If you encounter difficulties in setting up these dependencies, you may want to
use our docker image, the :doc:`development` page describes how to do this.

We are in the process of extending both the supported operating systems and 
python versions.
If you have specfic requirements, you are welcome request support. Get in 
contact by `emailing us <mailto:deltaflow@riverlane.com>`_

Installing with pip
^^^^^^^^^^^^^^^^^^^

You can find the latest released version of Deltasimulator 
`here <https://pypi.org/project/deltasimulator>`_. 

This can be installed using the in-built python package manager, :code:`pip`.

.. code-block:: console

  $ pip install deltasimulator

This will fetch all python package dependencies and install Deltasimulator. 

.. TODO::
  Check PyPI org link works after release
