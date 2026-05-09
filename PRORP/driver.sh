#!/bin/bash


cbmc ./program_files/ex10.c --dimacs --outfile cnf-out
grep 'c ' cnf-out > var-mapping
#python3 progformulagen.py
#cryptominisat5 --verb 0 invariant_formula.cnf

