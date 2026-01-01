<script setup lang="ts">
import { ref, nextTick } from "vue";
import axios from "axios";
import type { ChatMessage, ApiResponse } from "../types";
import CodePreview from "./CodePreview.vue";
import MarkdownViewer from "./MarkdownViewer.vue";

// --- 状态定义 ---

// 聊天记录列表
const messages = ref<ChatMessage[]>([
  {
    role: "assistant",
    content:
      "您好！我是您的 AI 教学助手。请告诉我您想制作什么课件？(例如：做一个物理平抛运动演示)",
  },
]);

// 当前右侧显示的内容
const currentContent = ref<string>("");
// 当前内容的类型：'code' (HTML/SVG) | 'plan' (Markdown) | null
const currentType = ref<"code" | "plan" | null>(null);

// 用户输入框
const userInput = ref("");
const isLoading = ref(false);

// --- 工具函数：终极代码清洗器 ---
const cleanCode = (raw: string): string => {
  // 1. 第一层过滤：Markdown 代码块提取
  // 正则含义：找到 ``` 后面跟任意字符(或没有)，换行，然后是核心内容，最后是 ```
  // [\w-]* : 匹配 html, xml, vue, javascript 等任意语言标记
  // \s* : 允许标记后有空格或换行
  // ([\s\S]*?) : 核心捕获组，非贪婪匹配
  const mdMatch = raw.match(/```[\w-]*\s*([\s\S]*?)```/);

  if (mdMatch && mdMatch[1]) {
    return mdMatch[1].trim();
  }

  // 2. 第二层过滤：暴力寻找 HTML/SVG 特征头
  // 如果 AI 没打 Markdown 标记，或者正则失效，我们直接去文本里“挖”代码

  // 常见的起始标签
  const patterns = ["<!DOCTYPE html>", "<html", "<svg"];

  let bestStartIndex = -1;

  // 找到最早出现的特征头
  for (const p of patterns) {
    const idx = raw.indexOf(p);
    if (idx !== -1) {
      if (bestStartIndex === -1 || idx < bestStartIndex) {
        bestStartIndex = idx;
      }
    }
  }

  // 如果找到了特征头
  if (bestStartIndex !== -1) {
    // 从特征头开始，截取到最后
    // (通常 AI 的废话都在前面，后面的废话较少，且 HTML 容错性高，多余的尾部文本通常不影响渲染)
    return raw.substring(bestStartIndex);
  }

  // 3. 实在救不回来，返回原始文本
  return raw;
};

// --- 业务逻辑 ---

const sendMessage = async () => {
  if (!userInput.value.trim() || isLoading.value) return;

  const userMsg = userInput.value;

  messages.value.push({ role: "user", content: userMsg });
  userInput.value = "";
  isLoading.value = true;
  scrollToBottom();

  try {
    const historyPayload = messages.value.slice(0, -1).map((msg) => ({
      role: msg.role,
      content: msg.content,
    }));

    const response = await axios.post<ApiResponse>("/api/generate_all", {
      user_input: userMsg,
      history: historyPayload,
    });

    const data = response.data;
    const intent = data.router_info.intent;

    // 自动清洗内容 (如果是代码类意图)
    let finalContent = data.content;
    if (intent === "agent_coder" || intent === "agent_visual") {
      finalContent = cleanCode(data.content);
    }

    // 确定消息类型
    // agent_visual (SVG) 也归类为 'code'，因为 CodePreview 组件能直接渲染 SVG
    const msgType =
      intent === "agent_coder" || intent === "agent_visual"
        ? "code"
        : intent === "agent_planner"
        ? "plan"
        : "text";

    messages.value.push({
      role: "assistant",
      content: finalContent, // 存入清洗后的内容
      type: msgType,
    });

    // 自动更新右侧演示区
    if (intent === "agent_coder" || intent === "agent_visual") {
      currentType.value = "code";
      currentContent.value = finalContent;
    } else if (intent === "agent_planner") {
      currentType.value = "plan";
      currentContent.value = finalContent;
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
    <div
      class="w-[400px] flex flex-col border-r bg-white shadow-lg z-10 shrink-0"
    >
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
            <div v-if="!msg.type || msg.type === 'text'">
              {{ msg.content }}
            </div>

            <div
              v-else-if="msg.type === 'code'"
              class="flex items-center gap-2 cursor-pointer hover:opacity-80 transition"
              @click="
                currentType = 'code';
                currentContent = msg.content;
              "
            >
              <span class="text-xl">🎨</span>
              <div>
                <p class="font-bold">可视化素材已生成</p>
                <p class="text-xs opacity-80">点击预览渲染结果</p>
              </div>
            </div>

            <div
              v-else-if="msg.type === 'plan'"
              class="flex items-center gap-2 cursor-pointer hover:opacity-80 transition"
              @click="
                currentType = 'plan';
                currentContent = msg.content;
              "
            >
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
          正在思考并生成内容...
        </div>
      </div>

      <div class="p-4 border-t bg-white">
        <div class="flex gap-2">
          <input
            v-model="userInput"
            @keyup.enter="sendMessage"
            type="text"
            placeholder="请输入需求，如：画一个植物细胞SVG..."
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

    <div class="flex-1 bg-gray-200 relative overflow-hidden">
      <CodePreview
        v-if="currentType === 'code' && currentContent"
        :code="currentContent"
      />

      <MarkdownViewer
        v-else-if="currentType === 'plan' && currentContent"
        :content="currentContent"
      />

      <div
        v-else
        class="h-full flex flex-col items-center justify-center text-gray-400 select-none"
      >
        <div class="text-6xl mb-4">🧠</div>
        <p class="text-lg font-medium">AI 备课工作台</p>
        <p class="text-sm mt-2">就绪</p>
      </div>
    </div>
  </div>
</template>
