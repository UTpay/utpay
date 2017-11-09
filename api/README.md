# UTpay API

**API URL**

/api/v1/


## ユーザ作成
**HTTP Headers**
- Content-Type: application/json

**HTTP Request**

**GET** /api/v1/register/

**Parameters**

- username (required)
- email (required)
- password (required)

**Response**
```
{
    "id": 1,
    "username": "test",
    "email": "test@example.com"
}
```


## 認証
[JSON Web Token](https://jwt.io/) による認証を行います。

### トークン発行
**HTTP Headers**
- Content-Type: application/json

**HTTP Request**

**POST** /api/v1/token-auth/

**Parameters**

- username (required)
- password (required)

**Response**
```
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo3LCJ1c2VybmFtZSI6InRlc3Q0IiwiZXhwIjoxNTA5ODkxNTAzLCJlbWFpbCI6InRlc3RAdXRwYXkub3JnIiwib3JpZ19pYXQiOjE1MDk4OTExNzN9.q8bnWnWgMUunPFMR5D9J47j-ykdRNljVtqUrSSsMdtU"
}
```

### トークンリフレッシュ
**HTTP Headers**
- Content-Type: application/json

**HTTP Request**

**POST** /api/v1/token-refresh/

**Parameters**

- token (required)

**Response**
```
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo3LCJ1c2VybmFtZSI6InRlc3Q0IiwiZXhwIjoxNTA5ODkxNTAzLCJlbWFpbCI6InRlc3RAdXRwYXkub3JnIiwib3JpZ19pYXQiOjE1MDk4OTExNzN9.q8bnWnWgMUunPFMR5D9J47j-ykdRNljVtqUrSSsMdtU"
}
```

### トークン検証
トークンが有効であればトークンを返します。

**HTTP Headers**
- Content-Type: application/json

**HTTP Request**

**POST** /api/v1/token-verify/

**Parameters**

- token (required)

**Response**
```
{
    "token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjo3LCJ1c2VybmFtZSI6InRlc3Q0IiwiZXhwIjoxNTA5ODkxNTAzLCJlbWFpbCI6InRlc3RAdXRwYXkub3JnIiwib3JpZ19pYXQiOjE1MDk4OTExNzN9.q8bnWnWgMUunPFMR5D9J47j-ykdRNljVtqUrSSsMdtU"
}
```


## ユーザ取得
認証されたユーザの情報を返します。

**HTTP Headers**
- Content-Type: application/json
- Authorization: JWT [token]

**HTTP Request**

**GET** /api/v1/users/

**Response**
```
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "username": "test",
            "email": "test@example.com"
        }
    ]
}
```

## Ethereum アカウント取得
認証されたユーザの Ethereum アカウント情報を返します。

**HTTP Headers**
- Content-Type: application/json
- Authorization: JWT [token]

**HTTP Request**

**GET** /api/v1/eth_accounts/

**Response**
```
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "username": "test",
                "email": "test@example.com"
            },
            "address": "0x..."
        }
    ]
}
```

### 残高取得
指定されたアドレスの残高を返します。

**HTTP Headers**
- Content-Type: application/json
- Authorization: JWT [token]

**HTTP Request**

**GET** /api/v1/eth_accounts/[address]/get_balance/

**Response**
```
{
    "address": "0x...",
    "eth_balance": 0.9805516352,
    "balance": 1000,
    "balance_int": 1000000
}
```

### QRコード取得
指定されたアドレスのQRコード画像のURLを返します。

**HTTP Headers**
- Content-Type: application/json
- Authorization: JWT [token]

**HTTP Request**

**GET** /api/v1/eth_accounts/[address]/get_qrcode/

**Response**
```
{
    "address": "0x...",
    "qrcode_url": "/media/images/qrcode/0x....png"
}
```

## トランザクション取得
認証されたユーザのトランザクション情報を返します。

**HTTP Headers**
- Content-Type: application/json
- Authorization: JWT [token]

**HTTP Request**

**GET** /api/v1/transactions/

**Response**
```
{
    "count": 1,
    "next": null,
    "previous": null,
    "results": [
        {
            "id": 1,
            "user": {
                "id": 1,
                "username": "test",
                "email": "test@example.com"
            },
            "eth_account": {
                "id": 1,
                "user": {
                    "id": 1,
                    "username": "test",
                    "email": "test@example.com"
                },
                "address": "0x..."
            },
            "tx_hash": "0x...",
            "from_address": "0x...",
            "to_address": "0x...",
            "amount": 1000,
            "gas": 137531,
            "gas_price": 20000000000,
            "value": 0,
            "network_id": 3,
            "is_active": true,
            "created_at": "2017-11-04T23:10:31.246998+09:00"
        }
    ]
}
```

## UTCoin 送金
**HTTP Headers**
- Content-Type: application/json
- Authorization: JWT [token]

**HTTP Request**

**POST** /api/v1/transactions/transfer/

**Parameters**

- address (required)
- amount (required)

**Response**
```
{
    "success": true,
    "address": "0x...",
    "amount": 0.001,
    "fee": 0.001,
    "transaction": {
        "id": 2,
        "user": {
            "id": 1,
            "username": "test",
            "email": "test@example.com"
        },
        "eth_account": {
            "id": 1,
            "user": {
                "id": 1,
                "username": "test",
                "email": "test@example.com"
            },
            "address": "0x..."
        },
        "tx_hash": "0x...",
        "from_address": "0x...",
        "to_address": "0x...",
        "amount": 1,
        "gas": 137467,
        "gas_price": 10000000000,
        "value": 0,
        "network_id": 3,
        "is_active": true,
        "created_at": "2017-11-05T22:32:44.788388+09:00"
    }
}
```