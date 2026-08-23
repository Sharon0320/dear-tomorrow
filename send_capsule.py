import json
import boto3
import os
from datetime import datetime,timezone

dynamodb = boto3.resource('dynamodb')
ses = boto3.client('ses')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def lambda_handler(event, context):
    now = datetime.now(timezone.utc).isoformat()

    # Query capsules ready to send
    response = table.scan(
    FilterExpression='#sd <= :now AND #st = :pending',
    ExpressionAttributeNames={
        '#sd': 'send_date',
        '#st': 'status'
    },
    ExpressionAttributeValues={
        ':now': now,
        ':pending': 'pending'
    }
    )

    capsules = response['Items']
    sent_count = 0

    for capsule in capsules:
        try:
            # Create AWS-styled HTML email
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        background-color: #F2F3F3;
                        margin: 0;
                        padding: 0;
                    }}
                    .email-container {{
                        max-width: 600px;
                        margin: 40px auto;
                        background: white;
                        border-radius: 8px;
                        overflow: hidden;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        background-color: #232F3E;
                        padding: 30px;
                        text-align: center;
                    }}
                    .header h1 {{
                        color: #FF9900;
                        margin: 0;
                        font-size: 28px;
                    }}
                    .header p {{
                        color: white;
                        margin: 10px 0 0 0;
                        opacity: 0.9;
                    }}
                    .content {{
                        padding: 40px 30px;
                    }}
                    .subject {{
                        color: #232F3E;
                        font-size: 24px;
                        margin-bottom: 20px;
                        border-bottom: 3px solid #FF9900;
                        padding-bottom: 10px;
                    }}
                    .message {{
                        color: #16191F;
                        font-size: 16px;
                        line-height: 1.8;
                        white-space: pre-line;
                    }}
                    .meta {{
                        background-color: #F2F3F3;
                        padding: 20px;
                        margin-top: 30px;
                        border-radius: 4px;
                        font-size: 13px;
                        color: #666;
                    }}
                    .footer {{
                        background-color: #232F3E;
                        color: white;
                        text-align: center;
                        padding: 20px;
                        font-size: 12px;
                        opacity: 0.8;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <h1>🕰️ Time Capsule</h1>
                        <p>Your message from the past has arrived</p>
                    </div>
                    <div class="content">
                        <h2 class="subject">{capsule['subject']}</h2>
                        <div class="message">{capsule['message']}</div>
                        <div class="meta">
                            <strong>Created:</strong> {capsule['created_at'][:10]}<br>
                            <strong>Scheduled:</strong> {capsule['send_date'][:10]}<br>
                            <strong>Delivered:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M')}
                        </div>
                    </div>
                    <div class="footer">
                        This time capsule was created with TimeCapsule service.<br>
                        Powered by AWS Free Tier
                    </div>
                </div>
            </body>
            </html>
            """

            # Send via SES
            ses.send_email(
                Source='sharon0320@gachon.ac.kr',
                Destination={'ToAddresses': [capsule['recipient_email']]},
                Message={
                    'Subject': {
                        'Data': f"🕰️ Time Capsule: {capsule['subject']}"
                    },
                    'Body': {
                        'Html': {'Data': html_body}
                    }
                }
            )

            # Update status
            table.update_item(
                Key={'capsule_id': capsule['capsule_id']},
                UpdateExpression='SET #st = :sent, sent_at = :sent_at',
                ExpressionAttributeNames={
                    '#st': 'status'
                },
                ExpressionAttributeValues={
                    ':sent': 'sent',
                    ':sent_at': datetime.now(timezone.utc).isoformat()
                }
            )

            sent_count += 1

        except Exception as e:
            print(f"Error: {str(e)}")

    return {
        'statusCode': 200,
        'body': json.dumps({'sent_count': sent_count})
    }
