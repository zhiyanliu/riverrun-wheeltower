package com.amazonaws.rp.riverrun.wheeltower.utils;

import com.amazonaws.services.cloudformation.AmazonCloudFormation;
import com.amazonaws.services.cloudformation.AmazonCloudFormationClientBuilder;
import com.amazonaws.services.cloudformation.model.*;

import java.util.List;

public class StackOutputQuerier {
    public String query(String stackName, String outputKey) {
        AmazonCloudFormation client = AmazonCloudFormationClientBuilder.defaultClient();

        DescribeStacksRequest req = new DescribeStacksRequest();
        req.setStackName(stackName);

        try {
            DescribeStacksResult result = client.describeStacks(req);
            List<Stack> stacks = result.getStacks();

            List<Output> outputs = stacks.get(0).getOutputs();

            for (Output output : outputs) {
                if (output.getOutputKey().equals(outputKey))
                    return output.getOutputValue();
            }
        } catch (AmazonCloudFormationException e) {
            if (!e.getMessage().contains(String.format("Stack with id %s does not exist", stackName)))
                throw e;
        }

        return null;
    }
}
