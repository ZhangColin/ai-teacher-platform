<template>
  <div class="code-runner-wrapper">
    <!-- 顶部工具栏 -->
    <div class="code-runner-header">
      <span class="language-badge" :class="`lang-${language}`">
        {{ languageDisplay }}
      </span>
      <button
        @click="rerun"
        :disabled="!isReady || isRunning"
        class="rerun-button"
        data-testid="rerun-button"
      >
        <span v-if="isRunning">运行中...</span>
        <span v-else>🔄 重新运行</span>
      </button>
    </div>

    <!-- 加载状态 -->
    <div v-if="isLoading" class="loading-state" data-testid="loading-state">
      <span class="spinner"></span>
      <span>{{ loadingText }}</span>
    </div>

    <!-- 输出区域 -->
    <div v-else class="output-container" data-testid="output-container">
      <div v-if="outputs.length === 0" class="output-empty" data-testid="output-empty">
        {{ language === 'python' ? 'Python' : 'JavaScript' }}环境已就绪，点击"重新运行"执行代码
      </div>
      <div v-else class="output-content" data-testid="output-content">
        <div
          v-for="(output, index) in outputs"
          :key="index"
          :class="['output-line', `output-${output.type}`]"
          data-testid="output-line"
        >
          <!-- 文本输出 -->
          <template v-if="output.type === 'stdout' || output.type === 'stderr'">
            <span class="output-prefix">{{ output.type === 'stdout' ? '>>> ' : '!!! ' }}</span>
            <span class="output-text">{{ output.text }}</span>
          </template>

          <!-- 图片输出 -->
          <template v-else-if="output.type === 'image'">
            <div class="output-image-wrapper">
              <span class="output-prefix">📷 </span>
              <img
                :src="`data:${output.mime};base64,${output.data}`"
                :alt="output.text || 'Generated image'"
                class="output-image"
                data-testid="output-image"
              />
              <span v-if="output.text" class="output-image-caption">{{ output.text }}</span>
            </div>
          </template>

          <!-- 错误输出 -->
          <template v-else-if="output.type === 'error'">
            <span class="output-error-icon">❌</span>
            <span class="output-error-text">{{ output.text }}</span>
          </template>
        </div>
      </div>
    </div>

    <!-- 隐藏的 iframe -->
    <iframe
      ref="iframeRef"
      :src="sandboxUrl"
      :key="sandboxKey"
      class="code-runner-iframe"
      sandbox="allow-scripts allow-same-origin"
      data-testid="code-runner-iframe"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue';

/**
 * 代码执行输出项
 */
interface OutputItem {
  type: 'stdout' | 'stderr' | 'image' | 'error';
  text?: string;
  mime?: string;  // 图片类型
  data?: string;  // Base64 数据
}

/**
 * 消息类型（从 iframe 接收）
 */
interface SandboxMessage {
  type: 'ready' | 'output' | 'error' | 'done';
  status?: string;
  output?: OutputItem;
}

/**
 * 组件 Props
 */
interface Props {
  content: string;
  language: 'python' | 'javascript';
}

const props = defineProps<Props>();

/**
 * 组件状态
 */
const iframeRef = ref<HTMLIFrameElement | null>(null);
const isReady = ref(false);     // iframe 是否已就绪
const isLoading = ref(false);   // 是否正在加载 Python 环境
const isRunning = ref(false);   // 代码是否正在运行
const outputs = ref<OutputItem[]>([]);  // 输出列表

/**
 * 沙箱 URL（根据语言选择）
 */
const sandboxUrl = computed(() => {
  if (props.language === 'python') {
    return '/sandboxes/python-sandbox.html';
  } else {
    return '/sandboxes/js-sandbox.html';
  }
});

/**
 * 沙箱 key（语言切换时重建 iframe）
 */
const sandboxKey = computed(() => props.language);

/**
 * 语言显示名称
 */
const languageDisplay = computed(() => {
  return props.language === 'python' ? 'Python 3' : 'JavaScript';
});

/**
 * 加载提示文本
 */
const loadingText = computed(() => {
  if (isRunning.value) {
    return '正在执行代码...';
  }
  return props.language === 'python' ? '正在加载 Python 环境（Pyodide）...' : '正在初始化 JavaScript 环境...';
});

/**
 * 发送执行命令到 iframe
 */
const executeCode = () => {
  if (!iframeRef.value?.contentWindow || !isReady.value) {
    console.warn('[CodeRunnerPreview] iframe 未就绪，无法执行代码');
    return;
  }

  // 清空输出
  outputs.value = [];
  isRunning.value = true;

  // 发送执行消息
  const message = {
    type: 'execute',
    code: props.content,
    language: props.language,
  };

  iframeRef.value.contentWindow.postMessage(message, window.location.origin);
  console.log('[CodeRunnerPreview] 发送执行命令:', message);
};

/**
 * 重新运行
 */
const rerun = () => {
  if (isReady.value && !isRunning.value) {
    executeCode();
  }
};

/**
 * 处理来自 iframe 的消息
 */
const handleMessage = (event: MessageEvent<SandboxMessage>) => {
  // 验证来源
  if (event.origin !== window.location.origin) {
    return;
  }

  // 验证消息来源 iframe
  if (event.source !== iframeRef.value?.contentWindow) {
    return;
  }

  const { type, status, output } = event.data;
  console.log('[CodeRunnerPreview] 收到消息:', event.data);

  switch (type) {
    case 'ready':
      // iframe 已就绪
      isReady.value = true;
      isLoading.value = false;
      isRunning.value = false;
      console.log('[CodeRunnerPreview] iframe 已就绪');
      break;

    case 'output':
      // 收到输出
      if (output) {
        outputs.value.push(output);
      }
      break;

    case 'error':
      // 收到错误
      if (output) {
        outputs.value.push({
          type: 'error',
          text: output.text || '未知错误',
        });
      }
      break;

    case 'done':
      // 执行完成
      isRunning.value = false;
      console.log('[CodeRunnerPreview] 执行完成');
      break;
  }
};

/**
 * 监听内容变化（自动重新执行）
 */
watch(
  () => props.content,
  (newContent) => {
    if (newContent && isReady.value && !isRunning.value) {
      // 延迟执行，避免频繁触发
      setTimeout(() => {
        executeCode();
      }, 100);
    }
  }
);

/**
 * 监听语言切换（重置状态）
 */
watch(
  () => props.language,
  () => {
    // 语言切换时，iframe 会重新加载（通过 key）
    isReady.value = false;
    isLoading.value = true;
    outputs.value = [];
  }
);

/**
 * 组件挂载
 */
onMounted(() => {
  // Python 需要加载 Pyodide，显示加载状态
  if (props.language === 'python') {
    isLoading.value = true;
  }

  // 监听消息
  window.addEventListener('message', handleMessage);
});

/**
 * 组件卸载
 */
onBeforeUnmount(() => {
  window.removeEventListener('message', handleMessage);
});
</script>

<style scoped>
.code-runner-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background-color: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;
}

/* 顶部工具栏 */
.code-runner-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background-color: #2d2d2d;
  border-bottom: 1px solid #404040;
}

.language-badge {
  padding: 4px 8px;
  border-radius: 3px;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
}

.language-badge.lang-python {
  background-color: #306998;
  color: #fff;
}

.language-badge.lang-javascript {
  background-color: #f7df1e;
  color: #000;
}

.rerun-button {
  padding: 4px 12px;
  border: none;
  border-radius: 3px;
  background-color: #0e639c;
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.rerun-button:hover:not(:disabled) {
  background-color: #1177bb;
}

.rerun-button:disabled {
  background-color: #404040;
  color: #888;
  cursor: not-allowed;
}

/* 加载状态 */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #ccc;
  font-size: 14px;
}

.spinner {
  width: 16px;
  height: 16px;
  margin-right: 8px;
  border: 2px solid #404040;
  border-top-color: #0e639c;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 输出容器 */
.output-container {
  flex: 1;
  overflow-y: auto;
  font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.output-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
  font-style: italic;
}

.output-content {
  padding: 12px;
}

/* 输出行 */
.output-line {
  padding: 4px 0;
  white-space: pre-wrap;
  word-break: break-all;
}

.output-prefix {
  color: #888;
  margin-right: 4px;
}

.output-text {
  color: #ccc;
}

.output-stdout .output-text {
  color: #4ec9b0;
}

.output-stderr .output-text {
  color: #f48771;
}

.output-error-icon {
  margin-right: 4px;
}

.output-error-text {
  color: #f48771;
  font-weight: 500;
}

/* 图片输出 */
.output-image-wrapper {
  display: inline-block;
  margin: 8px 0;
}

.output-image {
  max-width: 100%;
  max-height: 400px;
  border-radius: 4px;
  border: 1px solid #404040;
}

.output-image-caption {
  display: block;
  margin-top: 4px;
  color: #888;
  font-size: 12px;
}

/* 隐藏 iframe */
.code-runner-iframe {
  position: absolute;
  width: 0;
  height: 0;
  border: none;
  visibility: hidden;
}
</style>
