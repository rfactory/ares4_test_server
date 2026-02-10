# KV v2 엔진을 사용할 경우 /data/ 경로를 반드시 포함해야 합니다.
path "secret/data/ares4/hmac/*" {
  capabilities = ["create", "update", "read", "list"]
}

# (옵션) 나중에 키 삭제가 필요하다면 아래도 추가
path "secret/metadata/ares4/hmac/*" {
  capabilities = ["list", "delete"]
}