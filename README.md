# DDASM

## Usage
>python ddasm.py program\_name.dda \[vhdl\_rom.vhd\]
  * ``program\_name.dda``: File containing the assembly program.
  * ``vhdl\_rom.vhd    ``: (optional) File where VHDL description of program ROM is written to. If not specified, the file name will be "program\_name.vhd".

Make sure ``ROM\_template.vhd`` and ``asminfo.py`` are placed in the same directory.

## DDASM documentation
DDASM (Digital Design Assembly) is the assembly language supported by the DDASM processor used in the lab sessions of the KU Leuven Digital Design courses 
taught at the Factulty of Engineering Technology - Campus Ghent:
* [Digital Design 1](https://onderwijsaanbod.kuleuven.be/syllabi/n/JPI228N.htm#activetab=doelstellingen_idp827408)
* [Digital Design 1 - preparatory programme](https://onderwijsaanbod.kuleuven.be/syllabi/n/JPI22BN.htm#activetab=doelstellingen_idp3088832)
* [Digital Design 2](https://onderwijsaanbod.kuleuven.be/syllabi/n/JPI0G1N.htm#activetab=doelstellingen_idp2947376)

The [documentation](https://github.com/DRAMCO-EDU/DDASM/tree/master/documentation) directory contains information about the instruction set and instruction formatting.
Syntax highlighting (currently, only for gedit), can be found in the [syntax-highlighting](https://github.com/DRAMCO-EDU/DDASM/tree/master/syntax_highlighting) directory.

## Notice
The repository has been moved from ``github.com/dramco`` to ``github.com/dramco-edu``.