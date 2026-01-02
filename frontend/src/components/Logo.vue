<template>
  <div class="logo" @click="handleClick">
    <span class="logo-text">AI Platform</span>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function handleClick() {
  router.push('/modules/ai-tools')
}
</script>

<style scoped>
.logo {
  display: flex;
  align-items: center;
  cursor: pointer;
  padding: 8px 0;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.7;
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
  letter-spacing: -0.5px;
}

/* 平板端响应式（768px - 1023px） */
@media (min-width: 768px) and (max-width: 1023px) {
  .logo-text {
    font-size: 17px;
  }
}

/* 移动端响应式（<768px） */
@media (max-width: 767px) {
  .logo-text {
    font-size: 16px;
  }
}
</style>

