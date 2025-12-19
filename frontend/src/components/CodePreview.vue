<script setup lang="ts">
    import { computed } from 'vue';
    
    // 定义组件接收的参数
    const props = defineProps<{
      code: string; // 接收 AI 生成的 HTML 源码
    }>();
    
    // 计算属性：直接返回源码作为 iframe 的内容
    // 未来如果需要对源码进行安全清洗，可以在这里处理
    const safeSrcDoc = computed(() => {
      return props.code;
    });
    </script>
    
    <template>
      <div class="flex flex-col h-full bg-white border-l">
        <div class="bg-gray-50 px-4 py-2 flex justify-between items-center border-b">
          <div class="flex items-center gap-2">
            <span class="w-2 h-2 rounded-full bg-green-500"></span>
            <span class="text-sm text-gray-700 font-medium">实时演示窗口</span>
          </div>
          <span class="text-xs text-gray-400">基于 HTML5 Canvas / SVG 渲染</span>
        </div>
    
        <iframe
          :srcdoc="safeSrcDoc"
          class="w-full h-full border-none bg-white"
          sandbox="allow-scripts allow-modals allow-forms allow-popups allow-same-origin"
          title="演示预览"
        ></iframe>
      </div>
    </template>