import os
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
)
from constructs import Construct


class IoTDeviceFilesS3Bucket(Construct):

    def __init__(
        self,
            scope: Construct,
            construct_id: str,
            deploy_sample_files: bool = False,
            **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an S3 bucket for IoT device files
        self._iot_device_files_bucket = s3.Bucket(
            self, "IotDeviceFilesS3Bucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            versioned=True,
        )

        if deploy_sample_files:
            # Deploy files from a local disk to S3 bucket
            s3_deployment.BucketDeployment(
                self, "SampleIoTDeviceFiles",
                destination_bucket=self._iot_device_files_bucket,
                sources=[s3_deployment.Source.asset(os.path.join(
                    os.path.dirname(__file__), "sample_iot_device_files"))]
            )

    @ property
    def bucket_name(self) -> str:
        return self._iot_device_files_bucket.bucket_name
