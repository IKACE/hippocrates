#pragma once 
/**
 * 
 */

#include <unordered_set>

#include "llvm/IR/Module.h"
#include "llvm/IR/Instruction.h"
#include "llvm/IR/Function.h"

#include "FixGenerator.hpp"
#include "BugReports.hpp"

namespace pmfix {

/**
 * Runs all the fixing algorithms.
 * 
 * First, computes all the fixes that need to be performed. Then, removes any
 * redundancy of operations from the computed fixes. Then, runs the fix generator
 * over the reduced patch.
 */
class BugFixer {
private:
    llvm::Module &module_;
    TraceInfo &trace_;
    BugLocationMapper mapper_;

    /**
     * We're not allowed to insert fixes into some functions. These are some 
     * smart defaults.
     */
    std::unordered_set<llvm::Function*> immutableFns_;
    static const std::string immutableFnNames_[];
    static const std::string immutableLibNames_[];

    /**
     * High-level description of the fix that needs to be applied.
     * 
     * (iangneal): the flush+fence combo exists because for that case, the fence
     * is applied after the instruction generated by adding the flush, so the
     * ordering of that fix matters.
     * 
     * (iangneal): There is no way to infer the safety of removing a fence, as 
     * it can effect the safety of concurrent memory modifications.
     * - Future work could be to combine with concurrency bug fixers?
     * 
     * (iangneal): Sometimes, to remove a flush, it needs to be conditioned on
     * some global variables.
     * 
     */
    enum FixType {
        NO_FIX = -1,
        // Correctness, low-level
        ADD_FLUSH_ONLY = 0,
        ADD_FENCE_ONLY,
        ADD_FLUSH_AND_FENCE,
        // Correctness, high-level
        ADD_PERSIST_CALLSTACK_OPT,
        // Performance, known always redundant.
        REMOVE_FLUSH_ONLY,
        // Performance, not known always redundant.
        REMOVE_FLUSH_CONDITIONAL,    
    };

    /**
     * A description of the fix to be applied. This is essentially:
     *  1. The kind of fix.
     *  2. The location of the fix.
     *  3. The constraints on the fix.
     *      - I believe that this can essentially be ordering requirements, as
     *      in A => this => B, meaning this must post-dominate A and B must 
     *      post-dominate this.
     */
    struct FixDesc {
        FixType type;
        const std::vector<LocationInfo> *dynStack;
        /**
         * Used for the callstack optimized version.
         */
        int stackIdx;
        /**
         * Slightly jank, but these two fields are just for conditional flushing.
         */
        FixLoc original;
        std::list<llvm::Instruction*> points;

        /* Methods and constructors */

        FixDesc() 
            : type(NO_FIX), dynStack(nullptr), stackIdx(0), 
            original(), points() {}
        
        FixDesc(FixType t, const std::vector<LocationInfo> &l, int si=0) 
            : type(t), dynStack(&l), stackIdx(si), original(), points() {}
        
        FixDesc(FixType t, const std::vector<LocationInfo> &l, 
                const FixLoc &o, std::list<llvm::Instruction*> p) 
            : type(t), dynStack(&l), stackIdx(0), original(o), points(p) {}

        bool operator==(const FixDesc &f) const {
            return type == f.type && original == f.original && points == f.points;
        }

        bool operator!=(const FixDesc &f) const {
            return !(*this == f);
        }
    };

    std::unordered_map<FixLoc, FixDesc, FixLoc::Hash> fixMap_;

    /**
     * Utility to update the fix map. This provides basic fix coalescing (i.e.,
     * purely redundant fixes or upgrading fixes from flush/fence only to 
     * flush+fence).
     * Returns true if a new fix was added, false if the fix would be redundant.
     * 
     * (iangneal): return value mostly for debugging.
     * (iangneal): Add some dependent fixes.
     *
     * Same as above, but with a range of instructions.
     */
    bool addFixToMapping(const FixLoc &loc, FixDesc desc);

    /**
     * Handle fix generation for a missing persist call.
     */
    bool handleAssertPersisted(const TraceEvent &te, int bug_index);

    /**
     * Handle fix generation for a missing ordering call.
     * 
     * Since we cannot re-order stores, the only fix here is to insert a fence.
     */
    bool handleAssertOrdered(const TraceEvent &te, int bug_index);

    /**
     * Handle fix generation for a redundant flush.
     */
    bool handleRequiredFlush(const TraceEvent &te, int bug_index);

    /**
     * Iterate over the fix map and see if there's anywhere we can do some fixing.
     * 
     * We do this AFTER running all the fixers so that we have complete information.
     */
    bool runFixMapOptimization(void);

    /**
     * This is one fix map optimization. Adds the directive to do a higher-level
     * flush+fence fix.
     */
    bool raiseFixLocation(const FixLoc &fl, const FixDesc &desc);

    /**
     * Figure out how to fix the given bug and add the fix to the map. Generally
     * will call a handler function based on the kind of fix that needs to be
     * applied after validating that the request is well-formed.
     * 
     * Returns true if a new fix was added, false if an existing fix also fixes
     * the given bug. This is mostly used as debug information.
     */
    bool computeAndAddFix(const TraceEvent &te, int bug_index);

    /**
     * Run the fix generator to fix the specified bug.
     */
    bool fixBug(FixGenerator *fixer, const FixLoc &fl, const FixDesc &desc);

public:
    BugFixer(llvm::Module &m, TraceInfo &ti);

    /**
     * Do the program repair!
     * 
     * This follows these general steps:
     * 
     * 1. Compute all initial fixes.
     * 2. Optimize fixes.
     * 3. Apply.
     * 
     * Returns true if modifications were made to the program.
     */
    bool doRepair(void);

    // Utilities
    void addImmutableFunction(const std::string &fnName);

    void addImmutableModule(const std::string &modName);
};

}