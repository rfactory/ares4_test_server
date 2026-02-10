# Vault Agent 설정 파일: 자동 인증 및 인증서 템플릿 배달
exit_after_auth = false
pid_file = "/tmp/vault-agent.pid"

vault {
  address = "http://vault:8200"
}

auto_auth {
  method "approle" {
    config = {
      # dev-init.sh에서 주입해주는 경로와 일치시킵니다.
      role_id_file_path   = "/vault/file/role_id"
      secret_id_file_path = "/vault/file/secret_id"
      remove_secret_id_file_after_reading = false
    }
  }

  sink "file" {
    config = {
      path = "/vault/file/token.txt" 
    }
  }
}

# --- EMQX용 인증서 자동 발급 및 배달 설정 ---

# 1. EMQX 공개 키 (Certificate) - 'emqx' 별명 추가
template {
  contents = <<EOH
{{ with secret "pki_int/issue/ares-server-role" "common_name=ares4-mq-broker" (printf "ip_sans=%s,127.0.0.1" (env "SERVER_IP")) "alt_names=emqx,localhost" "ttl=24h" }}
{{ .Data.certificate }}
{{ end }}
EOH
  destination = "/vault/file/emqx.crt"
}

# 2. EMQX 개인 키 (Private Key) - 공개 키와 옵션 일치
template {
  contents = <<EOH
{{ with secret "pki_int/issue/ares-server-role" "common_name=ares4-mq-broker" (printf "ip_sans=%s,127.0.0.1" (env "SERVER_IP")) "alt_names=emqx,localhost" "ttl=24h" }}
{{ .Data.private_key }}
{{ end }}
EOH
  destination = "/vault/file/emqx.key"
}

# 3. 통합 CA 체인 (가장 중요: 중간 + 루트 인증서 합치기)
template {
  contents = <<EOH
{{ with secret "pki_int/cert/ca" }}{{ .Data.certificate }}{{ end }}
{{ with secret "pki/cert/ca" }}{{ .Data.certificate }}{{ end }}
EOH
  destination = "/vault/file/full_chain_ca.crt"
}