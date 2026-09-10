// Batchmode reproduction harness.
// Copy into an Editor/ folder (ideally under Assets/_Prototypes/<bug>/Editor/),
// rename the class, and edit the marked section to exercise the bug.
//
// Run (agent-friendly, exits with code 0/1 and prints a greppable verdict):
//
//   Unity -batchmode -nographics -projectPath <path> \
//         -executeMethod BatchmodeRepro.Run -logFile - -quit
//
// Parse the log for lines starting with [REPRO-a4f2].
// RESULT=PASS means the bug did NOT occur; RESULT=FAIL means it reproduced.
// (For git bisect: exit code 0 = good, 1 = bad, so FAIL exits 1.)

using System;
using UnityEditor;
using UnityEngine;

public static class BatchmodeRepro
{
    // Tag every line so Phase 6 cleanup is a single grep.
    const string Tag = "[REPRO-a4f2]";

    public static void Run()
    {
        int exitCode;
        try
        {
            bool bugReproduced = Repro();
            Debug.Log($"{Tag} RESULT={(bugReproduced ? "FAIL" : "PASS")}");
            exitCode = bugReproduced ? 1 : 0;
        }
        catch (Exception e)
        {
            // An unexpected exception is treated as a repro — the loop's
            // signal must be sharp, so tighten Repro() if this fires for
            // unrelated reasons.
            Debug.Log($"{Tag} RESULT=FAIL EXCEPTION={e.GetType().Name}: {e.Message}");
            Debug.LogException(e);
            exitCode = 1;
        }

        if (Application.isBatchMode)
            EditorApplication.Exit(exitCode);
    }

    // --- edit below ------------------------------------------------------
    // Return true if the bug reproduced. Keep it deterministic:
    //   - seed randomness:      var rng = new Unity.Mathematics.Random(1234);
    //   - pass dt explicitly rather than reading Time.*
    //   - serialize jobs:       Unity.Jobs.LowLevel.Unsafe.JobsUtility.JobWorkerCount = 0;
    //   - for ECS: create a scratch World, add entities, update the system,
    //     assert on output components, dispose the World.
    // Log intermediate values with the same Tag prefix.

    static bool Repro()
    {
        Debug.Log($"{Tag} setting up repro");

        // Example shape:
        // using var world = new Unity.Entities.World("Repro");
        // var em = world.EntityManager;
        // ... build input entities ...
        // var sys = world.GetOrCreateSystem<SuspectSystem>();
        // sys.Update(world.Unmanaged);
        // em.CompleteAllTrackedJobs();
        // var result = em.GetComponentData<Output>(entity);
        // Debug.Log($"{Tag} result={result.Value}");
        // return result.Value != expected;

        throw new NotImplementedException($"{Tag} edit Repro() to exercise the bug");
    }

    // --- edit above ------------------------------------------------------
}
