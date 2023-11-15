# compute_stack.py
from aws_cdk import Stack, aws_lambda, aws_iam, aws_secretsmanager, aws_dynamodb, CfnOutput


from constructs import Construct

class AwsServerlessChatbotBackendStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        

        # IAM role for Lambda functions
        lambda_role = aws_iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=aws_iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                aws_iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess")
            ]
        )

        # Add inline policy to the lambda_role for accessing the secret
        secret_arn = "arn:aws:secretsmanager:us-east-2:868658902285:secret:prod/chatbot/secrectname-xPgLfu"  # Replace with your actual secret ARN
        lambda_role.add_to_policy(aws_iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=[secret_arn]
        ))

        # DynamoDB Table with On-Demand capacity
        context_table = aws_dynamodb.Table(
            self, "chBotContextTable",
            partition_key=aws_dynamodb.Attribute(name="user_id", type=aws_dynamodb.AttributeType.STRING),
            billing_mode=aws_dynamodb.BillingMode.PAY_PER_REQUEST
        )


        # Layer for Lambda
        lambda_layer = aws_lambda.LayerVersion(
            self, "MyChBotLayer",
            code=aws_lambda.Code.from_asset("lib_layer"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_11],
            description="A layer for shared libraries"
        )


        # Lambda function
        lambda_function_1 = aws_lambda.Function(
            self, "chBotBackEndLambda",
            runtime=aws_lambda.Runtime.PYTHON_3_11,
            handler="index.handler",
            code=aws_lambda.Code.from_asset("lambda_backend"),
            environment={
                "TABLE_NAME": context_table.table_name
            },
            role=lambda_role,
            layers=[lambda_layer]
        )

        # Grant Lambda function access to the DynamoDB table
        context_table.grant_full_access(lambda_function_1)

        # Outputs
        CfnOutput(self, "LambdaFunctionName", value=lambda_function_1.function_name)
        CfnOutput(self, "DynamoDBTableName", value=context_table.table_name)
