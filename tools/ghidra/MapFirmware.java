// HyperRig offline import. RAM copy values come from each binary's reset code.
// @category HyperRig
import ghidra.app.script.GhidraScript;
import ghidra.program.model.address.Address;
import ghidra.program.model.mem.Memory;
import ghidra.program.model.mem.MemoryBlock;
import java.io.ByteArrayInputStream;

public class MapFirmware extends GhidraScript {
    @Override
    public void run() throws Exception {
        String[] args = getScriptArgs();
        if (args.length != 2) throw new IllegalArgumentException("RAM source address and size required");
        long source = Long.decode(args[0]);
        int size = Integer.decode(args[1]);
        Memory memory = currentProgram.getMemory();
        byte[] data = new byte[size];
        memory.getBytes(toAddr(source), data);
        MemoryBlock ram = memory.createInitializedBlock("ram_initialized", toAddr(0x1c00000L),
            new ByteArrayInputStream(data), size, monitor, false);
        ram.setRead(true); ram.setWrite(true); ram.setExecute(true);
        memory.createUninitializedBlock("ram_bss_and_heap", toAddr(0x1c00000L + size),
            0x80000 - size, false).setWrite(true);
        Address reset = toAddr(0x2000120L);
        currentProgram.getSymbolTable().addExternalEntryPoint(reset);
        createLabel(reset, "reset_entry", true);
        disassemble(reset);
        createFunction(reset, "reset_entry");
        println("HyperRig RAM mapping: " + Long.toHexString(source) + " -> 01c00000, size=" + size);
    }
}
