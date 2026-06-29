import client from './client'

export function fetchCommunityPosts() {
  return client.get('/community/posts/')
}

export function fetchCommunityPost(postId) {
  return client.get(`/community/posts/${postId}/`)
}

export function fetchShareStatus(recommendationId) {
  return client.get('/community/posts/share-status/', {
    params: { recommendation_id: recommendationId },
  })
}

export function shareToCommunity({ recommendationId, title, body }) {
  return client.post('/community/posts/', {
    recommendation_id: Number(recommendationId),
    title,
    body,
  })
}

export function deleteCommunityPost(postId) {
  return client.delete(`/community/posts/${postId}/`)
}

export function togglePostLike(postId) {
  return client.post(`/community/posts/${postId}/like/`)
}

export function fetchComments(postId) {
  return client.get(`/community/posts/${postId}/comments/`)
}

export function createComment(postId, payload) {
  return client.post(`/community/posts/${postId}/comments/`, payload)
}

export function updateComment(postId, commentId, payload) {
  return client.patch(`/community/posts/${postId}/comments/${commentId}/`, payload)
}

export function deleteComment(postId, commentId) {
  return client.delete(`/community/posts/${postId}/comments/${commentId}/`)
}
