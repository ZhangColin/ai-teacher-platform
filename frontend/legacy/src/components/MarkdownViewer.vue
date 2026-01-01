<script setup lang="ts">
import { computed } from "vue";
import MarkdownIt from "markdown-it";

const md = new MarkdownIt({
  html: true,
  linkify: true,
  typographer: true,
});

const props = defineProps<{
  content: string;
}>();

const renderedHtml = computed(() => {
  return md.render(props.content);
});

// --- 新增：下载功能 ---
const downloadPlan = () => {
  const blob = new Blob([props.content], { type: "text/markdown" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `lesson-plan-${new Date().getTime()}.md`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};
</script>

<template>
  <div class="flex flex-col h-full bg-white border-l">
    <div
      class="bg-gray-50 px-4 py-2 flex justify-between items-center border-b shrink-0"
    >
      <div class="flex items-center gap-2">
        <span class="text-xl">📄</span>
        <span class="text-sm text-gray-700 font-medium">智能教案预览</span>
      </div>

      <button
        @click="downloadPlan"
        class="bg-white border border-gray-300 text-gray-700 hover:bg-gray-100 hover:text-blue-600 px-3 py-1 text-xs rounded shadow-sm transition flex items-center gap-1"
      >
        <span>⬇️</span> 导出教案
      </button>
    </div>

    <div class="flex-1 overflow-y-auto p-8 bg-white">
      <div
        class="prose prose-slate max-w-none prose-headings:text-gray-800 prose-p:text-gray-600"
        v-html="renderedHtml"
      ></div>
    </div>
  </div>
</template>
