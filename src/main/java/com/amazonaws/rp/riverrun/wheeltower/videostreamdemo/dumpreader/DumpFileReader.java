package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.dumpreader;

import org.slf4j.Logger;

import javax.annotation.Nonnull;
import java.io.*;

public class DumpFileReader implements Closeable {
    private final Logger log;
    private final DataInputStream inputStream;
    private DumpRecord lastRecord = null;

    public DumpFileReader(@Nonnull final Logger log, @Nonnull final String inputFilePath)
            throws FileNotFoundException {
        this.log = log;

        File inputFile = new File(inputFilePath);
        this.inputStream = new DataInputStream(new FileInputStream(inputFile));
    }

    public DumpRecord readRecord() throws IOException {
        DumpRecord record = null;
        try {
            record = DumpRecord.read(this.inputStream);
        } catch (EOFException e) {
            // nothing to do
        }
        this.lastRecord = record;
        return record;
    }

    public DumpRecord lastRecord() {
        return this.lastRecord;
    }

    @Override
    public void close() throws IOException {
        this.inputStream.close();
    }
}
