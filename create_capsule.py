import json
import boto3
import os
import uuid
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime')

table = dynamodb.Table(os.environ['TABLE_NAME'])
S3_BUCKET = os.environ['S3_BUCKET']

MODEL_ID = os.environ.get(
    'BEDROCK_MODEL_ID',
    'amazon.nova-micro-v1:0'
)


def response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body, ensure_ascii=False)
    }


def generate_ai_message(original_message):
    system_prompt = """
당신은 Time Capsule 서비스의 메시지 편집 AI입니다.

사용자가 미래의 자신 또는 다른 사람에게 남긴 메시지를
마치 제3자가 그 사람에게 따뜻하게 이야기해주는 것처럼
자연스럽게 다시 작성하세요.

규칙:

1. 원래 메시지의 핵심 의미와 감정을 반드시 유지하세요.
2. 원문에 없는 구체적인 사건, 사람, 기억, 사실을 만들어내지 마세요.
3. 사용자의 감정을 존중하세요.
4. 제3자가 수신자에게 직접 이야기하는 느낌으로 작성하세요.
5. 따뜻하고 자연스러운 문체를 사용하세요.
6. 지나치게 감상적이거나 오글거리는 표현은 피하세요.
7. 원문의 핵심 감정과 의미를 유지하면서,
   필요하다면 원문보다 약 1.5~2.5배 정도 길게 자연스럽게 확장하세요.
8. 3~5개의 짧은 문단으로 구성해도 좋습니다.
9. 수신자가 실제로 편지를 읽고 있는 듯한 개인적인 느낌을 주세요.
10. 같은 응원 표현을 반복하지 마세요.
11. "우리 모두 너를 응원하고 있어"처럼 막연하고 반복적인 표현은 최소화하세요.
12. 설명이나 해설은 붙이지 말고 완성된 메시지만 출력하세요.
"""

    user_prompt = f"""
다음은 사용자가 작성한 원문입니다.

반드시 원문의 감정과 의미를 유지해야 합니다.
원문에 없는 구체적인 사실이나 상황을 추측해서 추가하지 마세요.

--- 원문 시작 ---
{original_message}
--- 원문 끝 ---

위 원문을 위의 규칙에 따라 자연스럽게 다시 작성하세요.
"""

    result = bedrock.converse(
        modelId=MODEL_ID,
        system=[
            {
                'text': system_prompt
            }
        ],
        messages=[
            {
                'role': 'user',
                'content': [
                    {
                        'text': user_prompt
                    }
                ]
            }
        ],
        inferenceConfig={
            'maxTokens': 1200,
            'temperature': 0.65,
            'topP': 0.9
        }
    )

    return result['output']['message']['content'][0]['text'].strip()


def lambda_handler(event, context):
    try:
        # API Gateway 요청의 body 처리
        raw_body = event.get('body')

        if raw_body is None:
            return response(400, {
                'error': 'Request body is missing'
            })

        if isinstance(raw_body, str):
            body = json.loads(raw_body)
        else:
            body = raw_body

        # 필수값 검사
        required_fields = [
            'recipient_email',
            'send_date',
            'subject',
            'message'
        ]

        for field in required_fields:
            if not body.get(field):
                return response(400, {
                    'error': f'Missing required field: {field}'
                })

        # send_date 검사
        send_date = datetime.fromisoformat(
            body['send_date'].replace('Z', '+00:00')
        )

        if send_date <= datetime.now(send_date.tzinfo):
            return response(400, {
                'error': 'Send date must be in the future'
            })

        capsule_id = str(uuid.uuid4())

        original_message = body['message']

        # AI 변환
        print('Calling Amazon Bedrock...')
        ai_message = generate_ai_message(original_message)
        print('AI message generated successfully.')

        # DynamoDB 저장
        item = {
            'capsule_id': capsule_id,
            'recipient_email': body['recipient_email'],
            'subject': body['subject'],

            # 사용자가 직접 작성한 원문
            'original_message': original_message,

            # AI가 변환한 최종 메시지
            'message': ai_message,

            'send_date': body['send_date'],

            'timezone': body.get(
                'timezone',
                'UTC'
            ),

            'created_at': datetime.now(
                timezone.utc
            ).isoformat(),

            'status': 'pending',

            'attachment_url': body.get(
                'attachment_url'
            )
        }

        table.put_item(Item=item)

        return response(201, {
            'capsule_id': capsule_id,
            'message': 'Time capsule created successfully!',
            'send_date': body['send_date'],
            'ai_message': ai_message
        })

    except Exception as e:
        print(f'ERROR: {str(e)}')

        return response(500, {
            'error': str(e)
        })
