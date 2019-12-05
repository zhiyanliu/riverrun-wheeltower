package com.amazonaws.rp.riverrun.wheeltower.utils;

import com.amazonaws.services.greengrass.AWSGreengrass;
import com.amazonaws.services.greengrass.AWSGreengrassClientBuilder;
import com.amazonaws.services.greengrass.model.*;
import org.slf4j.Logger;

public class Greengrass {
    public void resetGroupDeployment(final Logger log, final String greengrassGroupId) {
        AWSGreengrass greengrassClient = AWSGreengrassClientBuilder.defaultClient();

        log.debug("connected to AWS IoT Greengrass service");


        ResetDeploymentsRequest req = new ResetDeploymentsRequest();
        req.setForce(true);
        req.setGroupId(greengrassGroupId);

        ResetDeploymentsResult result = greengrassClient.resetDeployments(req);

        this.waitGroupDeployDone(log, greengrassGroupId, result.getDeploymentId());
    }

    private String queryGroupDeployStatus(final Logger log, final AWSGreengrass greengrassClient,
                                          final String greengrassGroupId, final String deploymentId) {

        GetDeploymentStatusRequest deploymentStatusReq = new GetDeploymentStatusRequest();
        deploymentStatusReq.setGroupId(greengrassGroupId);
        deploymentStatusReq.setDeploymentId(deploymentId);

        GetDeploymentStatusResult deploymentStatusResult = greengrassClient.getDeploymentStatus(deploymentStatusReq);
        deploymentStatusResult.getDeploymentStatus();

        // Building, InProgress, Success or Failure.
        return deploymentStatusResult.getDeploymentStatus();
    }

    public void waitGroupDeployDone(final Logger log, final String greengrassGroupId, final String deploymentId) {
        AWSGreengrass greengrassClient = AWSGreengrassClientBuilder.defaultClient();

        log.debug("connected to AWS IoT Greengrass service");

        String status, lastStatus = null;
        do {
            status = this.queryGroupDeployStatus(log, greengrassClient, greengrassGroupId, deploymentId);

            if (!status.equals(lastStatus)) {
                log.debug(String.format("the deployment status of Greengrass group %s: %s", greengrassGroupId, status));

                if (status.equals("Success") || status.equals("Failure"))
                    break;
            }

            lastStatus = status;

            try {
                Thread.sleep(1000);
            } catch (InterruptedException ie) {
                break;
            }
        } while (true);
    }
}
