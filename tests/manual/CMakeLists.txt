link_directories(${PMTEST_LIBS})

add_test_executable(TARGET 000_MissingFlush_PMTest
                    SOURCES 000_missing_flush_pmtest.c
                    INCLUDE ${PMTEST_INCLUDE}
                    EXTRA_LIBS pmtest pthread
                    DEPENDS PMTEST
                    TOOL PMTEST
                    SUITE MANUAL)

add_test_executable(TARGET 000_MissingFlush_PMEMCheck
                    SOURCES 000_missing_flush_pmemcheck.c
                    INCLUDE ${PMCHK_INCLUDE}
                    DEPENDS PMEMCHECK
                    TOOL PMEMCHECK
                    SUITE MANUAL)

add_test_executable(TARGET 001_MissingFence_PMTest
                    SOURCES 001_missing_fence_pmtest.c
                    INCLUDE ${PMTEST_INCLUDE}
                    EXTRA_LIBS pmtest pthread
                    DEPENDS PMTEST
                    TOOL PMTEST
                    SUITE MANUAL)

add_test_executable(TARGET 001_MissingFence_PMEMCheck
                    SOURCES 001_missing_fence_pmemcheck.c
                    INCLUDE ${PMCHK_INCLUDE}
                    DEPENDS PMEMCHECK
                    TOOL PMEMCHECK
                    SUITE MANUAL)

add_test_executable(TARGET 002_MissingFlushAndFence_PMTest
                    SOURCES 002_missing_flush_and_fence_pmtest.c
                    INCLUDE ${PMTEST_INCLUDE}
                    EXTRA_LIBS pmtest pthread
                    DEPENDS PMTEST
                    TOOL PMTEST
                    SUITE MANUAL)

add_test_executable(TARGET 002_MissingFlushAndFence_PMEMCheck
                    SOURCES 002_missing_flush_and_fence_pmemcheck.c
                    INCLUDE ${PMCHK_INCLUDE}
                    DEPENDS PMEMCHECK
                    TOOL PMEMCHECK
                    SUITE MANUAL)

add_test_executable(TARGET 003_ExtraFlush_PMTest
                    SOURCES 003_extra_flush_pmtest.c
                    INCLUDE ${PMTEST_INCLUDE}
                    EXTRA_LIBS pmtest pthread
                    DEPENDS PMTEST
                    TOOL PMTEST
                    SUITE MANUAL)

add_test_executable(TARGET 004_ExtraFlushComplex_PMTest
                    SOURCES 004_extra_flush_complex_pmtest.c
                    INCLUDE ${PMTEST_INCLUDE}
                    EXTRA_LIBS pmtest pthread
                    DEPENDS PMTEST
                    TOOL PMTEST
                    SUITE MANUAL)

add_test_executable(TARGET 005_ImmutableFunction_PMEMCheck
                    SOURCES 005_immutable_fn_pmemcheck.c
                    INCLUDE ${PMCHK_INCLUDE}
                    DEPENDS PMEMCHECK
                    TOOL PMEMCHECK
                    SUITE MANUAL)