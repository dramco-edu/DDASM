# DDASM

## Usage
>python ddasm.py program\_name.dda \[vhdl\_rom.vhd\]
  * program\_name.dda : File containing the assembly program.
  * vhdl\_rom.vhd     : (optional) File where VHDL description of program ROM is written to. If not specified, the file name will be "program\_name.vhd".

Make sure ROM\_template.vhd and asminfo.py are placed in the same directory.

## DDASM documentation
DDASM (Digital Design Assembly) is the assembly language supported by the DDASM processor used in the KU Leuven [Digital Design Lab Course](https://onderwijsaanbod.kuleuven.be/syllabi/n/JPI228N.htm#activetab=doelstellingen_idp827408). The [documentation](https://github.com/DRAMCO/DDASM/tree/master/documentation) directory contains information about the instruction set and instruction formatting.
Syntax highlighting (currently, only for gedit), can be found in the [syntax-highlighting](https://github.com/DRAMCO/DDASM/tree/master/syntax_highlighting) directory.
