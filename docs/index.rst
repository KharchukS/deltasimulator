.. title:: Overview

Deltasimulator documentation
============================

Deltasimulator (The Deltaflow simulator) is one of a few
self-contained components of |Deltaflow-on-ARTIQ|_ that
allows users to run Deltaflow programs on *simulated* hardware.

This build system can be used to compile SystemC
modules for nodes in a Deltaflow graph and wire the nodes up.
From there a complete runtime executable can be compiled,
or the graph can be connected to a larger platform representing physical
devices such as the ARTIQ platform via a Hardware Abstraction Layer (HAL).

In these webpages you will find explanations for the different
build environments and tools we have as part of Deltasimulator.
These will help you develop your
own build flows for the SystemC runtime to meet your platform's needs.

.. toctree::
        :maxdepth: 2
        :caption: Contents
        :hidden:

        install
        license
        development

.. Links

.. |Deltaflow-on-ARTIQ| replace:: **Deltaflow-on-ARTIQ**
.. _Deltaflow-on-ARTIQ: https://riverlane.github.io/deltaflow-on-artiq
