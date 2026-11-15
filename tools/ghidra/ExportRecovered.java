// C-like decompiler output is evidence, not original or buildable C source.
// @category HyperRig
import ghidra.app.script.GhidraScript;
import ghidra.app.decompiler.DecompInterface;
import ghidra.app.decompiler.DecompileResults;
import ghidra.program.model.listing.Function;
import ghidra.program.model.listing.FunctionIterator;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.io.BufferedWriter;

public class ExportRecovered extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        Path folder = Path.of(args[0]);
        Files.createDirectories(folder);
        DecompInterface decompiler = new DecompInterface();
        decompiler.openProgram(currentProgram);
        int ok = 0, failed = 0;
        try (BufferedWriter c = Files.newBufferedWriter(folder.resolve("decompiled.c"), StandardCharsets.UTF_8);
             BufferedWriter index = Files.newBufferedWriter(folder.resolve("functions.tsv"), StandardCharsets.UTF_8)) {
            c.write("/* AUTOMATIC RECOVERY: incomplete pi32v2 semantics; not original C, not buildable.\n"
                  + " * Inspect assembly before using any inferred logic. */\n\n");
            index.write("address\tname\tstatus\n");
            FunctionIterator functions = currentProgram.getFunctionManager().getFunctions(true);
            while (functions.hasNext() && !monitor.isCancelled()) {
                Function f = functions.next();
                DecompileResults result = decompiler.decompileFunction(f, 12, monitor);
                c.write("\n/* " + f.getEntryPoint() + " " + f.getName() + " */\n");
                if (result.decompileCompleted() && result.getDecompiledFunction() != null) {
                    c.write(result.getDecompiledFunction().getC());
                    index.write(f.getEntryPoint() + "\t" + f.getName() + "\tok\n");
                    ok++;
                } else {
                    c.write("/* Could not decompile this function. */\n");
                    index.write(f.getEntryPoint() + "\t" + f.getName() + "\tfailed\n");
                    failed++;
                }
            }
        } finally {
            decompiler.dispose();
        }
        Files.writeString(folder.resolve("status.txt"), "decompiled=" + ok + "\nfailed=" + failed
            + "\nPartial automatic recovery; hardware and semantics not validated.\n");
        println("HyperRig export: decompiled=" + ok + ", failed=" + failed);
    }
}
