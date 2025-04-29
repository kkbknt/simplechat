# lambda/index.py
import json
import os
import requests


def lambda_handler(event, context):
    try:
        # 環境変数からFastAPIエンドポイントURLを取得
        MODEL_API_URL = os.environ.get("MODEL_API_URL", "https://your-api-url.com")  # Lambdaの環境変数で定義
        
        print("Received event:", json.dumps(event))
        
        # Cognitoで認証されたユーザー情報を取得
        user_info = None
        if 'requestContext' in event and 'authorizer' in event['requestContext']:
            user_info = event['requestContext']['authorizer']['claims']
            print(f"Authenticated user: {user_info.get('email') or user_info.get('cognito:username')}")
        
        # リクエストボディの解析
        body = json.loads(event['body'])
        message = body['message']
        conversation_history = body.get('conversationHistory', [])
        
        print("Processing message:", message)
        
        # FastAPIへのPOST用ペイロード
        payload = {
            "prompt": message
        }
        
        print("Calling FastAPI prediction API with payload:", json.dumps(payload))
        
        # FastAPIへPOSTリクエスト
        response = requests.post(
            f"{MODEL_API_URL}/generate",
            headers={"Content-Type": "application/json"},
            json=payload
        )
        response.raise_for_status()
        
        # FastAPIからの応答をパース
        response_body = response.json()
        print("FastAPI response:", json.dumps(response_body, default=str))
        
        # アシスタントの応答を取得
        assistant_response = response_body["generated_text"]
        
        # 会話履歴に追加
        messages = conversation_history.copy()
        messages.append({
            "role": "user",
            "content": message
        })
        messages.append({
            "role": "assistant",
            "content": assistant_response
        })
        
        # 成功レスポンスを返却
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body":json.dumps({
                "success": True,
                "response": assistant_response,
                "conversationHistory": messages
            })
        }

        
    except Exception as error:
        print("Error:", str(error))
        
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
                "Access-Control-Allow-Methods": "OPTIONS,POST"
            },
            "body": json.dumps({
                "success": False,
                "error": str(error)
            })
        }
