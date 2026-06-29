<script setup>
import { ref, computed, onMounted } from 'vue'
import {
  fetchCommunityPosts,
  fetchCommunityPost,
  fetchComments,
  togglePostLike,
  createComment,
  updateComment,
  deleteComment,
  deleteCommunityPost,
} from '../api/community'

const posts = ref([])
const loading = ref(true)
const error = ref('')
const expandedId = ref(null)
const detail = ref(null)
const comments = ref([])
const detailLoading = ref(false)
const commentText = ref('')
const replyParentId = ref(null)
const replyText = ref('')
const submitting = ref(false)
const editingId = ref(null)
const editText = ref('')

function avatarLetter(author) {
  return (author?.nickname || '여')[0]
}

function packingItems(snapshot) {
  if (!snapshot) return []
  const general = (snapshot.general_items || []).map((item) => ({
    name: item.name,
    category: item.category,
    quantity: item.quantity,
  }))
  const catalog = (snapshot.catalog_items || []).map((item) => ({
    name: item.item_name,
    category: item.category,
    quantity: '',
  }))
  return [...general, ...catalog]
}

async function loadPosts() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await fetchCommunityPosts()
    posts.value = data
  } catch {
    error.value = '게시글을 불러오지 못했습니다.'
  } finally {
    loading.value = false
  }
}

async function toggleExpand(post) {
  if (expandedId.value === post.id) {
    expandedId.value = null
    detail.value = null
    comments.value = []
    return
  }
  expandedId.value = post.id
  detailLoading.value = true
  replyParentId.value = null
  replyText.value = ''
  commentText.value = ''
  try {
    const [postRes, commentRes] = await Promise.all([
      fetchCommunityPost(post.id),
      fetchComments(post.id),
    ])
    detail.value = postRes.data
    comments.value = commentRes.data
    const idx = posts.value.findIndex((p) => p.id === post.id)
    if (idx >= 0) {
      posts.value[idx] = {
        ...posts.value[idx],
        like_count: postRes.data.like_count,
        comment_count: postRes.data.comment_count,
        liked_by_me: postRes.data.liked_by_me,
      }
    }
  } catch {
    error.value = '게시글 상세를 불러오지 못했습니다.'
    expandedId.value = null
  } finally {
    detailLoading.value = false
  }
}

async function onLike(post, event) {
  event?.stopPropagation()
  try {
    const { data } = await togglePostLike(post.id)
    post.liked_by_me = data.liked
    post.like_count = data.like_count
    if (detail.value?.id === post.id) {
      detail.value.liked_by_me = data.liked
      detail.value.like_count = data.like_count
    }
  } catch {
    error.value = '좋아요 처리에 실패했습니다.'
  }
}

async function submitComment() {
  if (!expandedId.value || !commentText.value.trim()) return
  submitting.value = true
  try {
    const { data } = await createComment(expandedId.value, {
      content: commentText.value.trim(),
    })
    comments.value.push(data)
    commentText.value = ''
    bumpCommentCount(1)
  } catch (e) {
    error.value = e.response?.data?.content?.[0] || '댓글 등록에 실패했습니다.'
  } finally {
    submitting.value = false
  }
}

async function submitReply(parentId) {
  if (!expandedId.value || !replyText.value.trim()) return
  submitting.value = true
  try {
    const { data } = await createComment(expandedId.value, {
      content: replyText.value.trim(),
      parent_id: parentId,
    })
    const parent = comments.value.find((c) => c.id === parentId)
    if (parent) {
      parent.replies = [...(parent.replies || []), data]
    }
    replyParentId.value = null
    replyText.value = ''
    bumpCommentCount(1)
  } catch (e) {
    error.value = e.response?.data?.content?.[0] || '답글 등록에 실패했습니다.'
  } finally {
    submitting.value = false
  }
}

function bumpCommentCount(delta) {
  const id = expandedId.value
  const post = posts.value.find((p) => p.id === id)
  if (post) post.comment_count = (post.comment_count || 0) + delta
  if (detail.value?.id === id) {
    detail.value.comment_count = (detail.value.comment_count || 0) + delta
  }
}

function startEdit(comment) {
  editingId.value = comment.id
  editText.value = comment.content
}

function cancelEdit() {
  editingId.value = null
  editText.value = ''
}

async function saveEdit(comment) {
  if (!editText.value.trim()) return
  try {
    const { data } = await updateComment(expandedId.value, comment.id, {
      content: editText.value.trim(),
    })
    applyCommentUpdate(comment.id, data)
    cancelEdit()
  } catch {
    error.value = '댓글 수정에 실패했습니다.'
  }
}

function applyCommentUpdate(commentId, data) {
  const top = comments.value.find((c) => c.id === commentId)
  if (top) {
    Object.assign(top, data)
    return
  }
  for (const parent of comments.value) {
    const reply = (parent.replies || []).find((r) => r.id === commentId)
    if (reply) {
      Object.assign(reply, data)
      return
    }
  }
}

async function removeComment(comment) {
  if (!confirm('댓글을 삭제할까요?')) return
  try {
    await deleteComment(expandedId.value, comment.id)
    if (comment.parent_id) {
      for (const parent of comments.value) {
        parent.replies = (parent.replies || []).filter((r) => r.id !== comment.id)
      }
    } else {
      comments.value = comments.value.filter((c) => c.id !== comment.id)
    }
    bumpCommentCount(-1)
  } catch {
    error.value = '댓글 삭제에 실패했습니다.'
  }
}

async function removePost(post, event) {
  event?.stopPropagation()
  if (!confirm('게시글을 삭제할까요?')) return
  try {
    await deleteCommunityPost(post.id)
    posts.value = posts.value.filter((p) => p.id !== post.id)
    if (expandedId.value === post.id) {
      expandedId.value = null
      detail.value = null
      comments.value = []
    }
  } catch {
    error.value = '게시글 삭제에 실패했습니다.'
  }
}

const expandedPacking = computed(() =>
  packingItems(detail.value?.packing_snapshot),
)

onMounted(loadPosts)
</script>

<template>
  <div class="community">
    <header class="hero">
      <span class="kicker">COMMUNITY</span>
      <h1>여행자 커뮤니티</h1>
      <p>다른 여행자들의 짐 리스트를 구경하고 이야기를 나눠보세요.</p>
    </header>

    <div v-if="loading" class="state">불러오는 중...</div>
    <div v-else-if="!posts.length" class="state empty">
      아직 공유된 짐 리스트가 없어요.<br />
      추천 결과 화면에서 <strong>커뮤니티에 공유</strong>해 보세요!
    </div>

    <ul v-else class="post-list">
      <li
        v-for="post in posts"
        :key="post.id"
        class="post-wrap"
        :class="{ 'is-open': expandedId === post.id }"
      >
        <article
          class="post"
          :class="{ 'post--open': expandedId === post.id }"
          @click="toggleExpand(post)"
        >
          <div class="post__top">
            <div class="author">
              <img
                v-if="post.author?.profile_image_url"
                :src="post.author.profile_image_url"
                alt=""
                class="author__img"
              />
              <span v-else class="author__avatar">{{ avatarLetter(post.author) }}</span>
              <div>
                <strong>{{ post.author?.nickname || '여행자' }}</strong>
                <span class="post__date">{{ post.created_at?.slice(0, 10) }}</span>
              </div>
            </div>
            <button
              v-if="post.is_mine"
              type="button"
              class="delete-post"
              @click="removePost(post, $event)"
            >
              삭제
            </button>
          </div>

          <h2 class="post__title">{{ post.title }}</h2>
          <p class="post__place">{{ post.country_name }} · {{ post.city_name }}</p>
          <p class="post__meta">
            {{ post.nights }}박{{ post.nights + 1 }}일 ·
            {{ post.start_date }} ~ {{ post.end_date }} ·
            {{ post.companion_label }}
            <span v-if="post.companion_count > 1">({{ post.companion_count }}명)</span>
          </p>

          <div class="post__actions" @click.stop>
            <button
              type="button"
              class="like-btn"
              :class="{ 'like-btn--on': post.liked_by_me }"
              @click="onLike(post, $event)"
            >
              {{ post.liked_by_me ? '♥' : '♡' }} {{ post.like_count }}
            </button>
            <span class="comment-count">💬 {{ post.comment_count }}</span>
            <span class="expand-hint">{{ expandedId === post.id ? '접기' : '짐 보기' }}</span>
          </div>
        </article>

        <section v-if="expandedId === post.id" class="detail">
          <div v-if="detailLoading" class="state small">상세 불러오는 중...</div>
          <template v-else-if="detail">
            <p class="post-body">{{ detail.body }}</p>

            <div class="detail-cols">
            <div class="detail-col">
            <h3 class="detail__title">🧳 짐 리스트 ({{ expandedPacking.length }}개)</h3>
            <ul class="packing-list">
              <li v-for="(item, i) in expandedPacking" :key="i">
                <span class="cat">{{ item.category }}</span>
                <span class="name">{{ item.name }}</span>
                <span v-if="item.quantity" class="qty">{{ item.quantity }}</span>
              </li>
            </ul>
            </div>

            <div class="comments">
              <h3 class="detail__title">💬 댓글</h3>
              <div class="comment-form">
                <input
                  v-model="commentText"
                  type="text"
                  class="input"
                  maxlength="500"
                  placeholder="댓글을 남겨보세요"
                  @keyup.enter="submitComment"
                />
                <button
                  type="button"
                  class="btn"
                  :disabled="submitting"
                  @click="submitComment"
                >
                  등록
                </button>
              </div>

              <div v-if="!comments.length" class="muted small">첫 댓글을 남겨보세요.</div>

              <div v-for="comment in comments" :key="comment.id" class="comment-block">
                <div class="comment">
                  <div class="author author--sm">
                    <img
                      v-if="comment.author?.profile_image_url"
                      :src="comment.author.profile_image_url"
                      alt=""
                      class="author__img author__img--sm"
                    />
                    <span v-else class="author__avatar author__avatar--sm">
                      {{ avatarLetter(comment.author) }}
                    </span>
                    <div>
                      <strong>{{ comment.author?.nickname }}</strong>
                      <span v-if="comment.is_edited" class="edited">수정됨</span>
                    </div>
                  </div>
                  <div v-if="editingId === comment.id" class="edit-row">
                    <input v-model="editText" type="text" class="input" maxlength="500" />
                    <button type="button" class="btn btn--sm" @click="saveEdit(comment)">저장</button>
                    <button type="button" class="btn btn--ghost btn--sm" @click="cancelEdit">취소</button>
                  </div>
                  <p v-else class="comment__text">{{ comment.content }}</p>
                  <div class="comment__actions">
                    <button
                      type="button"
                      class="link"
                      @click="replyParentId = replyParentId === comment.id ? null : comment.id"
                    >
                      답글
                    </button>
                    <template v-if="comment.is_mine">
                      <button type="button" class="link" @click="startEdit(comment)">수정</button>
                      <button type="button" class="link danger" @click="removeComment(comment)">삭제</button>
                    </template>
                  </div>
                </div>

                <div v-if="replyParentId === comment.id" class="reply-form">
                  <input
                    v-model="replyText"
                    type="text"
                    class="input"
                    maxlength="500"
                    placeholder="답글을 남겨보세요"
                    @keyup.enter="submitReply(comment.id)"
                  />
                  <button
                    type="button"
                    class="btn btn--sm"
                    :disabled="submitting"
                    @click="submitReply(comment.id)"
                  >
                    등록
                  </button>
                </div>

                <div
                  v-for="reply in comment.replies"
                  :key="reply.id"
                  class="comment comment--reply"
                >
                  <div class="author author--sm">
                    <img
                      v-if="reply.author?.profile_image_url"
                      :src="reply.author.profile_image_url"
                      alt=""
                      class="author__img author__img--sm"
                    />
                    <span v-else class="author__avatar author__avatar--sm">
                      {{ avatarLetter(reply.author) }}
                    </span>
                    <div>
                      <strong>{{ reply.author?.nickname }}</strong>
                      <span v-if="reply.is_edited" class="edited">수정됨</span>
                    </div>
                  </div>
                  <div v-if="editingId === reply.id" class="edit-row">
                    <input v-model="editText" type="text" class="input" maxlength="500" />
                    <button type="button" class="btn btn--sm" @click="saveEdit(reply)">저장</button>
                    <button type="button" class="btn btn--ghost btn--sm" @click="cancelEdit">취소</button>
                  </div>
                  <p v-else class="comment__text">{{ reply.content }}</p>
                  <div v-if="reply.is_mine" class="comment__actions">
                    <button type="button" class="link" @click="startEdit(reply)">수정</button>
                    <button type="button" class="link danger" @click="removeComment(reply)">삭제</button>
                  </div>
                </div>
              </div>
            </div>
            </div>
          </template>
        </section>
      </li>
    </ul>

    <p v-if="error" class="error">⚠️ {{ error }}</p>
  </div>
</template>

<style scoped>
.community {
  max-width: var(--container);
  margin: 0 auto;
  padding: 40px 24px 64px;
}
.hero { margin-bottom: 26px; }
.kicker {
  display: inline-block;
  font-size: 0.78rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: var(--ocean);
  background: rgba(26, 83, 92, 0.08);
  border: 1px solid var(--line);
  padding: 6px 13px;
  border-radius: 999px;
  margin-bottom: 14px;
}
.hero h1 {
  font-family: 'Casquare Code Std', 'Noto Sans KR', sans-serif;
  color: var(--ink);
  font-size: 2.1rem;
  font-weight: 900;
  letter-spacing: -0.01em;
  margin: 0 0 8px;
}
.hero p { margin: 0; color: var(--muted); font-size: 1rem; }
.state {
  text-align: center;
  color: var(--muted);
  padding: 48px 16px;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
}
.state.small { padding: 20px; }
.empty strong { color: var(--ocean); }
.post-list {
  list-style: none; margin: 0; padding: 0;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  align-items: start;
}
.post-wrap.is-open { grid-column: 1 / -1; }
.post {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius-md);
  padding: 20px;
  cursor: pointer;
  box-shadow: var(--shadow-soft);
  transition: transform 0.15s, border-color 0.15s, box-shadow 0.15s;
}
.post:hover {
  transform: translateY(-3px);
  border-color: rgba(26, 83, 92, 0.28);
  box-shadow: var(--shadow-lift);
}
.post--open {
  border-color: rgba(26, 83, 92, 0.28);
  box-shadow: var(--shadow-lift);
  border-radius: var(--radius-md) var(--radius-md) 0 0;
}
.post__top { display: flex; justify-content: space-between; align-items: flex-start; gap: 8px; }
.author { display: flex; align-items: center; gap: 10px; }
.author__avatar {
  width: 40px; height: 40px; border-radius: 50%;
  background: var(--ocean); color: #fff;
  display: flex; align-items: center; justify-content: center;
  font-weight: 700; flex-shrink: 0;
}
.author__avatar--sm { width: 32px; height: 32px; font-size: 0.85rem; }
.author__img { width: 40px; height: 40px; border-radius: 50%; object-fit: cover; }
.author__img--sm { width: 32px; height: 32px; }
.post__date { display: block; font-size: 0.72rem; color: var(--muted); font-weight: 400; }
.delete-post {
  border: none; background: none; color: #c62828; font-size: 0.78rem; cursor: pointer;
}
.post__title { margin: 12px 0 4px; font-size: 1.1rem; color: var(--ink); }
.post__place { margin: 0; font-size: 0.82rem; color: var(--muted); }
.post-body {
  margin: 0 0 12px;
  font-size: 0.92rem;
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--ink);
  padding: 12px 14px;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 12px;
}
.post__meta { margin: 0; font-size: 0.82rem; color: var(--muted); }
.post__actions {
  display: flex; align-items: center; gap: 12px; margin-top: 12px;
  font-size: 0.85rem;
}
.like-btn {
  border: 1px solid rgba(26, 83, 92, 0.15);
  background: rgba(255, 255, 255, 0.8);
  border-radius: 999px;
  padding: 4px 12px;
  font-weight: 600;
  color: var(--muted);
}
.like-btn--on { color: #e53935; border-color: rgba(229, 57, 53, 0.35); }
.comment-count { color: var(--muted); }
.expand-hint { margin-left: auto; color: var(--ocean); font-weight: 600; font-size: 0.8rem; }
.detail {
  margin-top: -4px;
  padding: 0 12px 16px;
  background: rgba(255, 255, 255, 0.55);
  border: 1px solid rgba(26, 83, 92, 0.1);
  border-top: none;
  border-radius: 0 0 16px 16px;
}
.detail-cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  align-items: start;
}
.detail__title { font-size: 0.92rem; color: var(--ocean); margin: 16px 0 10px; }
.packing-list {
  list-style: none; margin: 0; padding: 0;
  display: flex; flex-direction: column; gap: 6px;
  max-height: 360px; overflow-y: auto;
}
.packing-list li {
  display: flex; align-items: center; gap: 8px;
  font-size: 0.84rem; padding: 8px 10px;
  background: rgba(255, 255, 255, 0.7);
  border-radius: 10px;
}
.cat {
  font-size: 0.68rem; font-weight: 600; color: var(--ocean);
  background: rgba(26, 83, 92, 0.1); padding: 2px 8px; border-radius: 8px;
  flex-shrink: 0;
}
.name { flex: 1; }
.qty { font-size: 0.75rem; color: var(--muted); }
.comments { margin-top: 8px; border-top: 1px dashed rgba(26, 83, 92, 0.15); padding-top: 8px; }
.comment-form, .reply-form, .edit-row {
  display: flex; gap: 8px; margin-bottom: 12px;
}
.input {
  flex: 1; border: 1px solid rgba(26, 83, 92, 0.2);
  border-radius: 10px; padding: 9px 12px; font-size: 0.9rem;
}
.btn {
  border: none; border-radius: 10px; background: var(--ocean);
  color: #fff; font-weight: 600; padding: 0 14px; white-space: nowrap;
}
.btn--sm { padding: 0 12px; font-size: 0.82rem; }
.btn--ghost { background: transparent; color: var(--muted); border: 1px solid rgba(26, 83, 92, 0.15); }
.comment-block { margin-bottom: 14px; }
.comment {
  padding: 10px 12px;
  background: rgba(255, 255, 255, 0.75);
  border-radius: 12px;
}
.comment--reply { margin-left: 28px; margin-top: 8px; }
.comment__text { margin: 8px 0 4px; font-size: 0.9rem; white-space: pre-wrap; }
.comment__actions { display: flex; gap: 10px; }
.link {
  border: none; background: none; color: var(--ocean);
  font-size: 0.78rem; font-weight: 600; cursor: pointer; padding: 0;
}
.link.danger { color: #c62828; }
.edited { font-size: 0.68rem; color: var(--muted); margin-left: 6px; }
.muted { color: var(--muted); }
.error { color: #c62828; text-align: center; margin-top: 16px; font-size: 0.85rem; }

@media (max-width: 760px) {
  .post-list { grid-template-columns: 1fr; }
  .detail-cols { grid-template-columns: 1fr; gap: 8px; }
}
@media (max-width: 480px) {
  .community { padding: 28px 16px 56px; }
  .hero h1 { font-size: 1.7rem; }
}
</style>
