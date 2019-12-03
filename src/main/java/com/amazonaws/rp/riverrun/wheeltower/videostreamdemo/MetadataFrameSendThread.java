package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.dumpreader.DumpFileReader;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.dumpreader.DumpRecord;
import org.slf4j.Logger;

import javax.annotation.Nonnull;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.concurrent.atomic.AtomicInteger;

public class MetadataFrameSendThread extends SendThread {
    private final DumpFileReader metadataFrameDumpReader;

    public MetadataFrameSendThread(@Nonnull final String name, @Nonnull final Logger log,
                                   @Nonnull final String metadataFrameFilePath,
                                   @Nonnull final String ip, final int port,
                                   @Nonnull final AtomicInteger videoPacketTimestampWatermark) throws IOException {
        super(name, log, ip, port, videoPacketTimestampWatermark);

        this.metadataFrameDumpReader = new DumpFileReader(log, metadataFrameFilePath);
        this.setDumpFileReader(this.metadataFrameDumpReader);
    }

    private void writeMetadataFrame(@Nonnull DumpRecord metadataFrameRecord) throws IOException {
        this.outputStream.writeInt(metadataFrameRecord.getTimestamp());
        this.outputStream.writeInt(metadataFrameRecord.getBuffer().length);
        this.outputStream.write(metadataFrameRecord.getBuffer());
    }

    @Override
    public void run() {
        try {
            try {
                DumpRecord record = null;
                int lastTimestamp = -1;

                while (!this.isInterrupted()) {
                    int timestampWatermark = videoPacketTimestampWatermark.get();

                    if (lastTimestamp < timestampWatermark) {
                        if (record == null) {
                            record = this.metadataFrameDumpReader.readRecord();
                            if (record == null) // EOF
                                break;
                        }

                        if (record.getTimestamp() <= timestampWatermark) {
                            this.writeMetadataFrame(record);
                            lastTimestamp = record.getTimestamp();
                            record = null;
                        }
                    }

                    Thread.sleep(5);
                }
            } catch (InterruptedIOException e) {
                throw new InterruptedException(e.getMessage());
            }
        } catch (InterruptedException e) {
            // restore the interrupted status
            Thread.currentThread().interrupt();
        } catch (IOException e) {
            this.log.error("catch an exception during data sending:");
            e.printStackTrace();
            // nothing to do
        }
    }
}
