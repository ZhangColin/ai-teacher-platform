<script setup lang="ts">
    import { computed } from 'vue';
    import MarkdownIt from 'markdown-it';
    
    // 初始化解析器
    const md = new MarkdownIt({
      html: true,       // 允许 HTML 标签
      linkify: true,    // 自动识别链接
      typographer: true // 优化排版
    });
    
    const props = defineProps<{
      content: string; // 接收 Markdown 源码
    }>();
    
    // 将 Markdown 转换为 HTML
    const renderedHtml = computed(() => {
      return md.render(props.content);
    });
    </script>
    
    <template>
      <div class="flex flex-col h-full bg-white border-l">
        <div class="bg-gray-50 px-4 py-2 flex justify-between items-center border-b shrink-0">
          <div class="flex items-center gap-2">
            <span class="text-xl">📄</span>
            <span class="text-sm text-gray-700 font-medium">智能教案预览</span>
          </div>
          <span class="text-xs text-gray-400">Markdown 渲染模式</span>
        </div>
    
        <div class="flex-1 overflow-y-auto p-8 bg-white">
          <div 
            class="prose prose-slate max-w-none prose-headings:text-gray-800 prose-p:text-gray-600"
            v-html="renderedHtml"
          ></div>
        </div>
      </div>
    </template>