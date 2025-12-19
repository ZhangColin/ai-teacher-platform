<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  code: string;
}>();

const safeSrcDoc = computed(() => {
  return props.code;
});

// --- 新增：下载功能 ---
const downloadCode = () => {
  // 1. 创建 Blob 对象 (文件内容)
  const blob = new Blob([props.code], { type: "text/html" });
  // 2. 创建下载链接
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  // 给文件起个名，加个时间戳防止重名
  a.download = `ai-courseware-${new Date().getTime()}.html`;
  // 3. 触发点击并清理
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
</script>

<template>
  <div class="flex flex-col h-full bg-white border-l">
    <div
      class="bg-gray-50 px-4 py-2 flex justify-between items-center border-b"
    >
      <div class="flex items-center gap-2">
        <span class="w-2 h-2 rounded-full bg-green-500"></span>
        <span class="text-sm text-gray-700 font-medium">实时演示窗口</span>
      </div>

      <div class="flex items-center gap-2">
        <span class="text-xs text-gray-400 mr-2">HTML5 Preview</span>
        <button
          @click="downloadCode"
          class="bg-white border border-gray-300 text-gray-700 hover:bg-gray-100 hover:text-blue-600 px-3 py-1 text-xs rounded shadow-sm transition flex items-center gap-1"
        >
          <span>⬇️</span> 下载源码
        </button>
      </div>
    </div>

    <iframe
      :srcdoc="safeSrcDoc"
      class="w-full h-full border-none bg-white"
      sandbox="allow-scripts allow-modals allow-forms allow-popups allow-same-origin"
      title="演示预览"
    ></iframe>
  </div>
</template>
