package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.dumpreader;

import javax.annotation.Nonnull;
import java.io.DataInputStream;
import java.io.EOFException;
import java.io.IOException;

@lombok.Data
@lombok.NonNull
public class DumpRecord {
    private final int timestamp;
    private final byte[] buffer;

    public static DumpRecord read(@Nonnull final DataInputStream inputStream) throws IOException {
        int timestamp = inputStream.readInt();
        int bufferLen = inputStream.readInt();
        byte[] buffer = inputStream.readNBytes(bufferLen);
        if (buffer.length == 0)
            throw new EOFException();

        return new DumpRecord(timestamp, buffer);
    }
}
