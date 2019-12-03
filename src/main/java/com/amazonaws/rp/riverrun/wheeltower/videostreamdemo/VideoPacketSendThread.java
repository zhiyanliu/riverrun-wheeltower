package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.dumpreader.DumpFileReader;
import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.dumpreader.DumpRecord;
import org.slf4j.Logger;

import javax.annotation.Nonnull;
import java.io.IOException;
import java.io.InterruptedIOException;
import java.util.concurrent.atomic.AtomicInteger;

public class VideoPacketSendThread extends SendThread {
    private final DumpFileReader videoPacketReader;

    private DumpRecord lastRecord;

    public VideoPacketSendThread(@Nonnull final String name, @Nonnull final Logger log,
                                 @Nonnull final String videoPacketFilePath,
                                 @Nonnull final String ip, final int port,
                                 @Nonnull final AtomicInteger videoPacketTimestampWatermark) throws IOException {
        super(name, log, ip, port, videoPacketTimestampWatermark);

        this.videoPacketReader = new DumpFileReader(this.log, videoPacketFilePath);
        this.setDumpFileReader(this.videoPacketReader);
    }

    private boolean isNewFrame(@Nonnull final DumpRecord videoPacketRecord) {
        if (this.lastRecord == null)
            return true;

        return this.lastRecord.getTimestamp() != videoPacketRecord.getTimestamp();
    }

    private void writeVideoPacket(@Nonnull final DumpRecord videoPacketRecord) throws IOException {
        this.outputStream.writeInt(videoPacketRecord.getBuffer().length);
        this.outputStream.write(videoPacketRecord.getBuffer());
    }

    @Override
    public void run() {
        try {
            try {
                while (!this.isInterrupted()) {
                    DumpRecord record = this.videoPacketReader.readRecord();
                    if (record == null) // EOF
                        break;

                    this.videoPacketTimestampWatermark.set(record.getTimestamp());

                    this.writeVideoPacket(record);

                    if (this.isNewFrame(record))
                        Thread.sleep(35); // change this to control FPS/workload pressure

                    this.lastRecord = record;
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
