<script setup lang="ts">
import { ref, nextTick } from "vue";
import axios from "axios";
import type { ChatMessage, ApiResponse } from "../types";
import CodePreview from "./CodePreview.vue";
import MarkdownViewer from "./MarkdownViewer.vue";

// --- 状态定义 ---

// 聊天记录列表，预置一条欢迎语
const messages = ref<ChatMessage[]>([
  {
    role: "assistant",
    content:
      "您好！我是您的 AI 教学助手。请告诉我您想制作什么课件？(例如：做一个物理平抛运动演示)",
  },
]);

// 当前右侧演示区显示的代码内容
const currentCode = ref<string>("");
// 当前右侧显示的内容
const currentContent = ref<string>("");
// 当前内容的类型：'code' | 'plan' | null
const currentType = ref<"code" | "plan" | null>(null);

// 用户输入框内容
const userInput = ref("");

// 网络请求加载状态
const isLoading = ref(false);

// --- 业务逻辑 ---

// 发送消息处理函数
const sendMessage = async () => {
  // 校验输入有效性
  if (!userInput.value.trim() || isLoading.value) return;

  const userMsg = userInput.value;

  // 1. 将用户消息推入列表
  messages.value.push({ role: "user", content: userMsg });
  userInput.value = "";
  isLoading.value = true;
  scrollToBottom();

  try {
    // 2. 调用后端全流程接口
    const response = await axios.post<ApiResponse>("/api/generate_all", {
      user_input: userMsg,
    });

    const data = response.data;
    const intent = data.router_info.intent;

    // 3. 将 AI 回复推入列表
    messages.value.push({
      role: "assistant",
      content: data.content,
      // 如果是 coder 就是 code，如果是 planner 就是 plan，其他都是 text
      type:
        intent === "agent_coder"
          ? "code"
          : intent === "agent_planner"
          ? "plan"
          : "text",
    });

    // 4. 更新右侧显示区逻辑
    if (intent === "agent_coder") {
      currentType.value = "code";
      currentContent.value = data.content;
    } else if (intent === "agent_planner") {
      // 如果是教案，也显示在右侧
      currentType.value = "plan";
      currentContent.value = data.content;
    }
  } catch (error) {
    console.error("请求失败:", error);
    messages.value.push({
      role: "assistant",
      content: "抱歉，系统出错了，请检查后端服务是否启动。",
    });
  } finally {
    isLoading.value = false;
    scrollToBottom();
  }
};

// 滚动聊天列表到底部
const scrollToBottom = async () => {
  await nextTick();
  const chatContainer = document.getElementById("chat-history");
  if (chatContainer) {
    chatContainer.scrollTop = chatContainer.scrollHeight;
  }
};
</script>

<template>
  <div class="flex h-screen bg-gray-100 overflow-hidden">
    <div class="w-[400px] flex flex-col border-r bg-white shadow-lg z-10">
      <header class="p-4 border-b bg-white">
        <h1 class="text-lg font-bold text-gray-800">AI 备课助手</h1>
        <p class="text-xs text-gray-500">Kimi 驱动 | 智能教学平台</p>
      </header>

      <div
        id="chat-history"
        class="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50"
      >
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="flex flex-col"
          :class="msg.role === 'user' ? 'items-end' : 'items-start'"
        >
          <div
            class="max-w-[90%] rounded-lg p-3 text-sm shadow-sm whitespace-pre-wrap leading-relaxed"
            :class="
              msg.role === 'user'
                ? 'bg-blue-600 text-white'
                : 'bg-white text-gray-800 border'
            "
          >
            <div v-if="msg.type !== 'code'">
              {{ msg.content }}
            </div>

            <div v-if="msg.type === 'code'" class="flex items-center gap-2 cursor-pointer" @click="currentType = 'code'; currentContent = msg.content">
              <span class="text-xl">🚀</span>
              <div>
                <p class="font-bold">交互课件已生成</p>
                <p class="text-xs opacity-80">点击加载演示</p>
              </div>
            </div>

            <div v-else-if="msg.type === 'plan'" class="flex items-center gap-2 cursor-pointer" @click="currentType = 'plan'; currentContent = msg.content">
              <span class="text-xl">📄</span>
              <div>
                <p class="font-bold">教学设计已生成</p>
                <p class="text-xs opacity-80">点击查看文档</p>
              </div>
            </div>
          </div>

          <span class="text-xs text-gray-400 mt-1 mx-1">
            {{ msg.role === "user" ? "我" : "AI 助手" }}
          </span>
        </div>

        <div
          v-if="isLoading"
          class="flex items-center gap-2 text-gray-500 text-sm p-2"
        >
          <div
            class="animate-spin h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full"
          ></div>
          正在思考并生成代码...
        </div>
      </div>

      <div class="p-4 border-t bg-white">
        <div class="flex gap-2">
          <input
            v-model="userInput"
            @keyup.enter="sendMessage"
            type="text"
            placeholder="请输入需求，如：演示勾股定理..."
            class="flex-1 border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            :disabled="isLoading"
          />
          <button
            @click="sendMessage"
            class="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-blue-700 disabled:bg-gray-400 transition"
            :disabled="isLoading"
          >
            发送
          </button>
        </div>
      </div>
    </div>

    <div class="flex-1 bg-gray-200 relative">
      <CodePreview 
        v-if="currentType === 'code' && currentContent" 
        :code="currentContent" 
      />
      
      <MarkdownViewer 
        v-else-if="currentType === 'plan' && currentContent" 
        :content="currentContent" 
      />
      
      <div v-else class="h-full flex flex-col items-center justify-center text-gray-400">
        <div class="text-6xl mb-4">🧠</div>
        <p class="text-lg font-medium">AI 备课工作台</p>
        <p class="text-sm">支持 生成交互课件(Code) 与 教学设计(Plan)</p>
      </div>
    </div>
  </div>
</template>
