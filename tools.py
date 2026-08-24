"""
Mocked AWS operations tool layer.

Design Note:
In production this layer would use Boto3 with an IAM least-privilege role.
It is mocked here to safely demonstrate agent decision-making, policy enforcement,
and audit workflow without live destructive AWS permissions.
"""

from typing import List, Dict, Any, Optional


def read_ec2() -> List[Dict[str, Any]]:
    return [
        {"id": "i-demo001", "name": "Web-Server", "state": "running", "type": "t3.micro"},
        {"id": "i-demo002", "name": "Test-Server", "state": "stopped", "type": "t3.micro"},
    ]


def read_s3() -> List[str]:
    return ["demo-app-assets", "demo-backups"]


def read_account() -> Dict[str, Any]:
    return {"account_id": "000000000000", "region": "ap-south-1", "environment": "demo"}


def stop_ec2(target: Optional[str] = None) -> Dict[str, Any]:
    target_name = target if target else "specified instance"
    return {
        "status": "SUCCESS",
        "action": "STOP_EC2",
        "target": target_name,
        "message": f"EC2 instance '{target_name}' has been stopped successfully."
    }


def start_ec2(target: Optional[str] = None) -> Dict[str, Any]:
    target_name = target if target else "specified instance"
    return {
        "status": "SUCCESS",
        "action": "START_EC2",
        "target": target_name,
        "message": f"EC2 instance '{target_name}' has been started successfully."
    }


def terminate_ec2(target: Optional[str] = None) -> Dict[str, Any]:
    # Should never actually be called — policy engine blocks CRITICAL risk actions
    target_name = target if target else "specified instance"
    return {
        "status": "SUCCESS",
        "action": "TERMINATE_EC2",
        "target": target_name,
        "message": f"EC2 instance '{target_name}' terminated."
    }


def delete_s3(target: Optional[str] = None) -> Dict[str, Any]:
    # Should never actually be called — policy engine blocks CRITICAL risk actions
    target_name = target if target else "specified bucket"
    return {
        "status": "SUCCESS",
        "action": "DELETE_S3",
        "target": target_name,
        "message": f"S3 bucket '{target_name}' deleted."
    }


def delete_account(target: Optional[str] = None) -> Dict[str, Any]:
    # Should never actually be called — policy engine blocks CRITICAL risk actions
    return {
        "status": "SUCCESS",
        "action": "DELETE_ACCOUNT",
        "target": target,
        "message": "AWS Account deletion initiated."
    }
