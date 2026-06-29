<script setup>
import { useRouter } from 'vue-router'

const router = useRouter()

function startTrip() {
  router.push({ name: 'trip' })
}

// 히어로 우측 미리보기용 더미 짐 리스트
const previewItems = [
  { emoji: '🛂', name: '여권 (잔여 6개월↑)', tag: '필수' },
  { emoji: '🔌', name: '멀티 어댑터 (C형)', tag: '필수' },
  { emoji: '🧴', name: 'SPF50+ 선크림', tag: '권장' },
  { emoji: '☂️', name: '접이식 우산', tag: '권장' },
  { emoji: '🧦', name: '압박 양말', tag: '선택' },
]
</script>

<template>
  <div class="home">
    <section class="hero">
      <div class="hero__copy">
        <span class="kicker">애인처럼 야무지게 챙겨주는 여행 짐</span>
        <h1 class="title">
          <span class="title__emoji">🧳</span>
          <span class="title__text">야무짐</span>
        </h1>
        <p class="catch">자기야, 그거 챙겼어?</p>
        <p class="desc">
          어디 가는지만 말해줘.<br />
          날씨·치안·문화까지 따져서 깜빡할 것 하나 없이 다 챙겨놓을게.
        </p>

        <div class="cta-row">
          <button type="button" class="cta" @click="startTrip">
            어디 가는지 말해줘 →
          </button>
          <span class="cta-note">블로그 10번 검색할 시간에, 야무짐 한 번</span>
        </div>

        <div class="features">
          <div class="feature">
            <span class="feature__icon">🌤️</span>
            <div>
              <strong>날씨까지 챙김</strong>
              <span>그날 기온·강수 기반 추천</span>
            </div>
          </div>
          <div class="feature">
            <span class="feature__icon">🎯</span>
            <div>
              <strong>네 취향대로</strong>
              <span>위생·더위·준비성 반영</span>
            </div>
          </div>
          <div class="feature">
            <span class="feature__icon">👥</span>
            <div>
              <strong>다 같이 공유</strong>
              <span>커뮤니티 짐 리스트</span>
            </div>
          </div>
        </div>
      </div>

      <div class="hero__visual" aria-hidden="true">
        <div class="preview-card">
          <div class="preview-card__head">
            <span class="dot dot--coral"></span>
            <span class="dot dot--gold"></span>
            <span class="dot dot--ocean"></span>
            <span class="preview-card__loc">🇯🇵 후쿠오카 · 3박 4일</span>
          </div>
          <p class="preview-card__title">야무짐이 챙긴 캐리어</p>
          <ul class="preview-list">
            <li v-for="item in previewItems" :key="item.name">
              <span class="pi-emoji">{{ item.emoji }}</span>
              <span class="pi-name">{{ item.name }}</span>
              <span class="pi-tag" :class="`pi-tag--${item.tag}`">{{ item.tag }}</span>
            </li>
          </ul>
          <div class="preview-card__foot">
            <span>✅ 23개 아이템 · 이유까지 한 번에</span>
          </div>
        </div>
        <div class="floaty floaty--1">🧴</div>
        <div class="floaty floaty--2">🛂</div>
        <div class="floaty floaty--3">📷</div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.home {
  min-height: calc(100vh - 52px);
  display: flex;
  align-items: center;
  padding: 48px 24px 64px;
}
.hero {
  width: 100%;
  max-width: var(--container-wide);
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.05fr 0.95fr;
  align-items: center;
  gap: 56px;
}

/* ---- 좌측 카피 ---- */
.kicker {
  display: inline-block;
  font-size: 0.82rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
  border: 1px solid var(--line);
  padding: 7px 14px;
  border-radius: 999px;
  margin-bottom: 22px;
}
.title {
  display: flex;
  align-items: center;
  gap: 14px;
  margin: 0 0 10px;
}
.title__emoji { font-size: 3.4rem; }
.title__text {
  font-size: 4.6rem;
  line-height: 1;
  font-weight: 900;
  background: var(--grad-hero);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  letter-spacing: -0.02em;
}
.catch {
  margin: 0 0 18px;
  font-size: 1.5rem;
  font-weight: 800;
  color: var(--coral);
}
.desc {
  margin: 0 0 32px;
  font-size: 1.05rem;
  line-height: 1.7;
  color: var(--muted);
  max-width: 30ch;
}
.cta-row {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  margin-bottom: 40px;
}
.cta {
  border: none;
  border-radius: 16px;
  padding: 18px 30px;
  background: var(--grad-hero);
  color: #fff;
  font-size: 1.08rem;
  font-weight: 800;
  box-shadow: var(--shadow-lift);
  transition: transform 0.15s, box-shadow 0.15s;
}
.cta:hover {
  transform: translateY(-3px);
  box-shadow: 0 26px 64px rgba(26, 83, 92, 0.26);
}
.cta-note { font-size: 0.86rem; color: var(--muted); font-weight: 600; }

.features {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
}
.feature {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  box-shadow: var(--shadow-soft);
  flex: 1;
  min-width: 180px;
}
.feature__icon { font-size: 1.7rem; }
.feature strong { display: block; font-size: 0.92rem; color: var(--ink); }
.feature span { font-size: 0.76rem; color: var(--muted); }

/* ---- 우측 미리보기 비주얼 ---- */
.hero__visual {
  position: relative;
  display: flex;
  justify-content: center;
}
.preview-card {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 420px;
  background: rgba(255, 255, 255, 0.92);
  border: 1px solid var(--line);
  border-radius: var(--radius-lg);
  padding: 22px 22px 18px;
  box-shadow: var(--shadow-lift);
  transform: rotate(-2deg);
}
.preview-card__head {
  display: flex;
  align-items: center;
  gap: 7px;
  margin-bottom: 18px;
}
.dot { width: 11px; height: 11px; border-radius: 50%; }
.dot--coral { background: var(--coral); }
.dot--gold { background: var(--gold); }
.dot--ocean { background: var(--ocean); }
.preview-card__loc {
  margin-left: auto;
  font-size: 0.78rem;
  font-weight: 700;
  color: var(--ocean);
}
.preview-card__title {
  margin: 0 0 14px;
  font-size: 1.1rem;
  font-weight: 800;
  color: var(--ink);
}
.preview-list { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 9px; }
.preview-list li {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 11px 13px;
  background: var(--lining);
  border-radius: 13px;
}
.pi-emoji { font-size: 1.15rem; }
.pi-name { flex: 1; font-size: 0.9rem; font-weight: 600; color: var(--ink); }
.pi-tag {
  font-size: 0.68rem;
  font-weight: 800;
  padding: 3px 9px;
  border-radius: 999px;
}
.pi-tag--필수 { background: rgba(255, 107, 107, 0.16); color: #d6453f; }
.pi-tag--권장 { background: rgba(26, 83, 92, 0.12); color: var(--ocean); }
.pi-tag--선택 { background: rgba(212, 168, 83, 0.2); color: #a9802f; }
.preview-card__foot {
  margin-top: 16px;
  text-align: center;
  font-size: 0.82rem;
  font-weight: 700;
  color: var(--ocean);
}
.floaty {
  position: absolute;
  font-size: 2rem;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 18px;
  width: 60px; height: 60px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: var(--shadow-soft);
  z-index: 3;
  animation: bob 4s ease-in-out infinite;
}
.floaty--1 { top: -22px; right: 8px; animation-delay: 0s; }
.floaty--2 { bottom: 40px; left: -26px; animation-delay: 0.8s; }
.floaty--3 { bottom: -20px; right: 54px; animation-delay: 1.6s; }
@keyframes bob {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-10px); }
}

@media (max-width: 880px) {
  .hero { grid-template-columns: 1fr; gap: 44px; text-align: center; }
  .title, .cta-row, .features { justify-content: center; }
  .desc { margin-left: auto; margin-right: auto; }
  .hero__visual { order: -1; }
  .title__text { font-size: 3.6rem; }
}
@media (max-width: 480px) {
  .home { padding: 28px 18px 48px; }
  .title__text { font-size: 3rem; }
  .catch { font-size: 1.25rem; }
  .floaty { display: none; }
}
</style>
