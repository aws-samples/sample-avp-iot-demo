import aws_cdk as core
import aws_cdk.assertions as assertions

from avp_iot_demo.avp_iot_demo_stack import AvpIotDemoStack

# example tests. To run these tests, uncomment this file along with the example
# resource in avp_iot_demo/avp_iot_demo_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = AvpIotDemoStack(app, "avp-iot-demo")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
