package com.amazonaws.rp.riverrun.wheeltower.videostreamdemo;

import com.amazonaws.rp.riverrun.wheeltower.videostreamdemo.dumpreader.DumpFileReader;
import lombok.Setter;
import org.slf4j.Logger;

import javax.annotation.Nonnull;
import java.io.Closeable;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.Proxy;
import java.net.Socket;
import java.util.concurrent.atomic.AtomicInteger;

public abstract class SendThread extends Thread implements Closeable {
    protected Logger log;

    @Setter
    protected DumpFileReader dumpFileReader = null;

    protected Socket clientSocket;

    protected DataOutputStream outputStream;

    protected AtomicInteger videoPacketTimestampWatermark;

    public SendThread(@Nonnull final String name, @Nonnull final Logger log,
                      @Nonnull final String ip, final int port,
                      @Nonnull final AtomicInteger videoPacketTimestampWatermark) throws IOException {
        super(name);

        this.log = log;

        this.clientSocket = new Socket(Proxy.NO_PROXY);
        this.clientSocket.connect(new InetSocketAddress(ip, port), 5000);

        this.outputStream = new DataOutputStream(this.clientSocket.getOutputStream());

        this.videoPacketTimestampWatermark = videoPacketTimestampWatermark;
    }

    @Override
    public void close() throws IOException {
        if (this.dumpFileReader != null)
            this.dumpFileReader.close();

        this.clientSocket.close();

        this.outputStream.close();
    }
}
