import client from './client'

// 카카오 인가 URL 조회 (REST 키/redirect_uri는 백엔드 .env가 단일 소스)
export function fetchKakaoAuthorizeUrl() {
  return client.get('/auth/kakao/url/', { _skipAuth: true })
}

// 카카오 인가 코드로 서비스 JWT 발급 → { access, refresh, is_new_user, user }
// redirect_uri는 보내지 않으면 백엔드가 settings.KAKAO_REDIRECT_URI를 사용한다.
export function kakaoLogin(code) {
  return client.post('/auth/kakao/', { code }, { _skipAuth: true })
}

// 개발/시연용 즉시 로그인 (백엔드 DEBUG 전용) → 카카오와 동일한 응답 형태
export function devLogin(username) {
  return client.post('/auth/dev/', { username }, { _skipAuth: true })
}

// 내 정보
export function fetchMe() {
  return client.get('/auth/me/')
}

// 성별·생년월일 프로필 저장
export function updateProfile(payload) {
  return client.put('/auth/me/', payload)
}

// 닉네임 변경 (최대 10글자)
export function updateNickname(nickname) {
  return client.patch('/auth/me/', { nickname })
}

export function updateProfileImage(file) {
  const formData = new FormData()
  formData.append('profile_image', file)
  return client.patch('/auth/me/', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
