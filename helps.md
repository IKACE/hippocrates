# Process:
Example: pmem_memcpy_TEST0_8bbb0af9c
exe_path:PosixPath('/home/yilegu/eecs582pj7/hippocrates/build/tests/validation/pmem_memcpy_TEST0_8bbb0af9c/pmem_memcpy')
bc_path: PosixPath('/home/yilegu/eecs582pj7/hippocrates/build/tests/validation/pmem_memcpy_TEST0_8bbb0af9c/pmem_memcpy.bc')
1. invoke python script verify
2. parse target in run_targets 
ToolRunner format: target_name, exe_path, bc_path, tool_type, suite, issue
3. if pmdk unit test: _run_pmdk_unit_test
    1. Run initial test via predefined tests e.g. build/validation/RUNTESTS_pmem_memcpy_TEST0_8bbb0af9c, input: executable path ./pmem_memcpy_TEST0_8bbb0af9c, test file TEST0
    2. Get trace from log file via parse-trace e.g. logfile: PosixPath('/home/yilegu/eecs582pj7/hippocrates/build/tests/validation/pmem_memcpy_TEST0_8bbb0af9c/pmemcheck0.log') tracefile: PosixPath('/home/yilegu/eecs582pj7/hippocrates/build/tests/validation/pmem_memcpy_TEST0_8bbb0af9c/pmemcheck0.trace') (logfile is summary, the output tracefile is detailed store and fence), parser takes two formats: PMTest and PMemcheck, bugs are highlighted in trace: is bug: True
    3. Link the bitcode with the library so that opt can find the functions via llvm-link-8, e.g. input: bitcode path PosixPath('/home/yilegu/eecs582pj7/hippocrates/build/tests/validation/pmem_memcpy_TEST0_8bbb0af9c/pmem_memcpy.bc'), and other bitcode needed to link, output: bitcode linked path PosixPath('/home/yilegu/eecs582pj7/hippocrates/build/tests/validation/pmem_memcpy_TEST0_8bbb0af9c/pmem_memcpy.bc.linked').
    4. Run the fixer script via apply-fixer， will invoke C++ implementation of BugFixer, input: trace file, executable path, linked bitcode path, output: a summary file of bug fix
    5. Re-run test

# In apply-fixer:
## PREPARE:
0. link with the persistent memory intrinsics, the fixer needs them.
1. opt to run the fixer
2. llc to compile the optimized bitcode 
3. clang to compile the assembly file and link libraries.

## DO:
0. link via llvm link: input: bitcode file
1. fix via opt: -load pass library...


# Question:
1. How to debug in BugFixer? Any best practice?
2. executable, bitcode, what is the relationship, how could opt help

# Idea:
1. BugFixer read trace, most of the work on interprocedural fix? We could focus on intraprocedural first
2. Provide Squint with alternative trace generation rule
3. Transaction potential issue? 

4. Merging changes from InsertTX and Hippocrates: who is the first?
Maybe better: trace from pmemcheck & Squint -> H -> bitcode -> source code -> insert TX -> source code new -> Squint
5. example of benifit of generating subprogram for trasaction insertion (hippocrates could help)
6. use PM access heuristic for finding the most accurate range? (hippocrates could help)
7. delete redundant persist after inserting transaction (hippocrates could help)
8. only partial stores are present in Squint log

make -C /home/yilegu/eecs582pj7/hippocrates/build   pmem_memcpy_TEST0_8bbb0af9c -j 80

# Troubleshooting:
1. compile error or llvm Producer Reader error: source build.env