"""内置支持的模型提供商和模型定义"""

# 内置供应商定义
BUILTIN_PROVIDERS = {
    "deepseek": {
        "name": "DeepSeek",
        "default_base_url": "https://api.deepseek.com",
        "description": "DeepSeek AI 模型"
    },
    "openai": {
        "name": "OpenAI",
        "default_base_url": "https://api.openai.com/v1",
        "description": "OpenAI 模型"
    },
    "kimi": {
        "name": "Kimi (Moonshot)",
        "default_base_url": "https://api.moonshot.cn/v1",
        "description": "Moonshot AI 模型"
    },
    "glm": {
        "name": "智谱 AI",
        "default_base_url": "https://open.bigmodel.cn/api/paas/v4",
        "description": "智谱 AI 大模型"
    },
    "doubao": {
        "name": "豆包 (字节跳动)",
        "default_base_url": "https://ark.cn-beijing.volces.com/api/v3",
        "description": "字节跳动豆包大模型"
    },
    "claude": {
        "name": "Claude (Anthropic 直接 API)",
        "default_base_url": "https://api.anthropic.com/v1",
        "description": "Anthropic Claude 模型（直接 API 调用）"
    },
    "bedrock": {
        "name": "AWS Bedrock (Claude)",
        "default_base_url": "us-west-2",
        "description": "AWS Bedrock Claude 模型（支持 API Key 认证）"
    },
    "google": {
        "name": "Google Gemini",
        "default_base_url": "https://generativelanguage.googleapis.com/v1beta",
        "description": "Google Gemini 模型"
    },
    "newapi": {
        "name": "NewAPI",
        "default_base_url": "https://your-newapi-domain.com/v1",
        "description": "AI 聚合平台，兼容 OpenAI API 规范"
    },
}

# 内置模型定义
BUILTIN_MODELS = {
    "deepseek": {
        # V3.2 系列 (2025年12月发布，当前最新)
        "deepseek-v3.2": {
            "name": "DeepSeek V3.2",
            "capabilities": ["chat", "code"],
            "description": "DeepSeek 最新旗舰模型 (2025年12月)，增强 Agent 能力，推理和代码性能优秀"
        },
        "deepseek-v3.2-reasoning": {
            "name": "DeepSeek V3.2 Reasoning",
            "capabilities": ["chat", "code"],
            "description": "DeepSeek V3.2 推理增强版"
        },
        # R1 推理系列
        "deepseek-r1": {
            "name": "DeepSeek R1",
            "capabilities": ["chat", "code"],
            "description": "DeepSeek 推理专家模型"
        },
        "deepseek-r1-distill-qwen-32b": {
            "name": "DeepSeek R1 Distill Qwen 32B",
            "capabilities": ["chat", "code"],
            "description": "R1 蒸馏版 (Qwen 32B)"
        },
        "deepseek-r1-distill-llama-70b": {
            "name": "DeepSeek R1 Distill Llama 70B",
            "capabilities": ["chat", "code"],
            "description": "R1 蒸馏版 (Llama 70B)"
        },
        # V3 系列
        "deepseek-v3": {
            "name": "DeepSeek V3",
            "capabilities": ["chat", "code"],
            "description": "DeepSeek V3 通用模型 (671B 参数)"
        },
        # VL2 视觉语言模型
        "deepseek-vl2": {
            "name": "DeepSeek VL2",
            "capabilities": ["chat", "image"],
            "description": "DeepSeek 视觉语言模型"
        },
        # 经典模型 (兼容保留)
        "deepseek-chat": {
            "name": "DeepSeek Chat",
            "capabilities": ["chat", "code"],
            "description": "DeepSeek 对话模型 (建议使用 V3.2)"
        },
        "deepseek-coder": {
            "name": "DeepSeek Coder",
            "capabilities": ["code"],
            "description": "DeepSeek 代码模型 (建议使用 V3.2)"
        },
    },
    "openai": {
        # GPT-5 系列 (2026年最新)
        "gpt-5.4": {
            "name": "GPT-5.4",
            "capabilities": ["chat", "image", "code"],
            "description": "OpenAI 最新旗舰模型 (2026年3月)，支持 1.05M 上下文"
        },
        "gpt-5.4-mini": {
            "name": "GPT-5.4 Mini",
            "capabilities": ["chat", "image", "code"],
            "description": "GPT-5.4 经济型版本"
        },
        "gpt-5.4-thinking": {
            "name": "GPT-5.4 Thinking",
            "capabilities": ["chat", "code"],
            "description": "GPT-5.4 推理增强版"
        },
        "gpt-5.3-codex": {
            "name": "GPT-5.3 Codex",
            "capabilities": ["code"],
            "description": "GPT-5.3 代码专家模型，优化 Agent 编程"
        },
        "gpt-5.2-codex": {
            "name": "GPT-5.2 Codex",
            "capabilities": ["code"],
            "description": "GPT-5.2 代码模型"
        },
        "gpt-5-codex": {
            "name": "GPT-5 Codex",
            "capabilities": ["code"],
            "description": "GPT-5 代码模型"
        },
        # GPT-4 系列 (API 仍可用，ChatGPT 已退役)
        "gpt-4o": {
            "name": "GPT-4o",
            "capabilities": ["chat", "image", "code"],
            "description": "GPT-4o 多模态模型 (已从 ChatGPT 退役，API 仍可用)"
        },
        "gpt-4o-mini": {
            "name": "GPT-4o Mini",
            "capabilities": ["chat", "image", "code"],
            "description": "GPT-4o Mini (API 仍可用)"
        },
        "gpt-4.1": {
            "name": "GPT-4.1",
            "capabilities": ["chat", "image", "code"],
            "description": "GPT-4.1 (已退役，建议使用 GPT-5.4)"
        },
        "gpt-4.1-mini": {
            "name": "GPT-4.1 Mini",
            "capabilities": ["chat", "image", "code"],
            "description": "GPT-4.1 Mini (已退役)"
        },
        # o 系列推理模型
        "o3": {
            "name": "o3",
            "capabilities": ["chat", "code"],
            "description": "o3 推理模型"
        },
        "o3-mini": {
            "name": "o3-mini",
            "capabilities": ["chat", "code"],
            "description": "o3 迷你推理版"
        },
        # 经典模型
        "gpt-4-turbo": {
            "name": "GPT-4 Turbo",
            "capabilities": ["chat", "code"],
            "description": "GPT-4 Turbo (建议使用 GPT-5 系列)"
        },
        "gpt-3.5-turbo": {
            "name": "GPT-3.5 Turbo",
            "capabilities": ["chat", "code"],
            "description": "GPT-3.5 Turbo (建议使用 GPT-5.4-mini)"
        },
    },
    "kimi": {
        # K2.5 系列 (2026年1月发布，最新旗舰)
        "kimi-k2.5": {
            "name": "Kimi K2.5",
            "capabilities": ["chat", "image", "code"],
            "description": "Kimi 最新旗舰 (2026年1月)，万亿参数 MoE 模型，支持 256K 超长上下文，原生多模态"
        },
        "kimi-k2.5-thinking": {
            "name": "Kimi K2.5 Thinking",
            "capabilities": ["chat", "code"],
            "description": "Kimi K2.5 推理增强版"
        },
        "kimi-k2.5-vision": {
            "name": "Kimi K2.5 Vision",
            "capabilities": ["chat", "image", "code"],
            "description": "Kimi K2.5 视觉增强版，支持视觉推理"
        },
        # V1 系列
        "moonshot-v1-1m": {
            "name": "Moonshot V1 1M",
            "capabilities": ["chat", "code"],
            "description": "Moonshot V1 超长上下文版，支持 1M token"
        },
        "moonshot-v1-128k": {
            "name": "Moonshot V1 128K",
            "capabilities": ["chat", "code"],
            "description": "Moonshot V1 长上下文版，支持 128K token"
        },
        "moonshot-v1-32k": {
            "name": "Moonshot V1 32K",
            "capabilities": ["chat", "code"],
            "description": "Moonshot V1 标准版，支持 32K token"
        },
        "moonshot-v1-8k": {
            "name": "Moonshot V1 8K",
            "capabilities": ["chat"],
            "description": "Moonshot V1 基础版，支持 8K token"
        },
    },
    "glm": {
        # GLM-5 系列 (最新旗舰)
        "glm-5": {
            "name": "GLM-5",
            "capabilities": ["chat", "image", "code"],
            "description": "最新旗舰基座，编程能力对齐 Claude Opus 4.5，200K 上下文"
        },
        "glm-5-turbo": {
            "name": "GLM-5-Turbo",
            "capabilities": ["chat", "code"],
            "description": "龙虾增强基座，复杂长任务执行连续性好，200K 上下文"
        },
        # GLM-4 系列 (高智能)
        "glm-4.7": {
            "name": "GLM-4.7",
            "capabilities": ["chat", "code"],
            "description": "高智能模型，全面升级，编程更强更稳，200K 上下文"
        },
        "glm-4.7-flashx": {
            "name": "GLM-4.7-FlashX",
            "capabilities": ["chat"],
            "description": "轻量高速，小尺寸强能力，适用于中文写作、翻译等"
        },
        "glm-4.6": {
            "name": "GLM-4.6",
            "capabilities": ["chat", "code"],
            "description": "超强性能，200K 上下文，高级编码能力"
        },
        # GLM-4.5 系列 (高性价比)
        "glm-4.5-air": {
            "name": "GLM-4.5-Air",
            "capabilities": ["chat", "code"],
            "description": "高性价比，推理编码强劲，128K 上下文"
        },
        "glm-4.5-airx": {
            "name": "GLM-4.5-AirX",
            "capabilities": ["chat"],
            "description": "高性价比极速版，推理速度快，128K 上下文"
        },
        # 超长上下文
        "glm-4-long": {
            "name": "GLM-4-Long",
            "capabilities": ["chat"],
            "description": "超长输入，支持 1M 上下文长度"
        },
        # 免费模型
        "glm-4.7-flash": {
            "name": "GLM-4.7-Flash",
            "capabilities": ["chat"],
            "description": "免费模型，最新基座普惠版本"
        },
        # 视觉模型
        "glm-4.6v": {
            "name": "GLM-4.6V",
            "capabilities": ["chat", "image"],
            "description": "旗舰视觉推理，原生支持工具调用"
        },
        "glm-ocr": {
            "name": "GLM-OCR",
            "capabilities": ["chat", "image"],
            "description": "轻量图文解析，高精度高效率"
        },
        # 图像生成
        "glm-image": {
            "name": "GLM-Image",
            "capabilities": ["image"],
            "description": "旗舰图像生成，文字渲染 SOTA"
        },
        "cogview-4": {
            "name": "CogView-4",
            "capabilities": ["image"],
            "description": "高质量图像生成"
        },
        "cogview-3-flash": {
            "name": "CogView-3-Flash",
            "capabilities": ["image"],
            "description": "免费图像生成模型"
        },
        # 视频生成
        "cogvideox-3": {
            "name": "CogVideoX-3",
            "capabilities": ["video"],
            "description": "高智能旗舰，主观清晰度大幅提升"
        },
        "cogvideox-flash": {
            "name": "CogVideoX-Flash",
            "capabilities": ["video"],
            "description": "免费视频生成模型"
        },
        # 语音模型
        "glm-tts": {
            "name": "GLM-TTS",
            "capabilities": ["audio"],
            "description": "语音合成模型，超拟人语音"
        },
        "glm-4-voice": {
            "name": "GLM-4-Voice",
            "capabilities": ["audio"],
            "description": "语音模型，直接理解和生成中英文语音"
        },
    },
    # 豆包/字节跳动 (火山引擎 Doubao Seed 2.0 系列)
    # 使用推理接入点ID (ep-开头)
    # 官方文档: https://www.volcengine.com/docs/82379/1330310
    "doubao": {
        # Doubao-Seed-2.0-pro - 最新旗舰
        "ep-20260322151359-pk8n2": {
            "name": "豆包 Seed 2.0 Pro",
            "capabilities": ["chat", "image", "code"],
            "description": "豆包最新旗舰模型，高性能场景"
        },
        # Doubao-Seed-2.0-lite - 平衡版
        "ep-20260322151700-vnb6f": {
            "name": "豆包 Seed 2.0 Lite",
            "capabilities": ["chat", "code"],
            "description": "平衡资源和性能"
        },
        # Doubao-Seed-2.0-mini - 轻量版
        "ep-20260322151739-6zm8m": {
            "name": "豆包 Seed 2.0 Mini",
            "capabilities": ["chat"],
            "description": "轻量版，快速响应"
        },
        # Doubao-Seed-2.0-Code - 代码专家
        "ep-20260322151811-9wmc5": {
            "name": "豆包 Seed 2.0 Code",
            "capabilities": ["code"],
            "description": "代码专家模型"
        },
    },
    # Claude/Anthropic (Claude 4.6 系列 - 2026年2月发布)
    "claude": {
        "claude-opus-4.6": {
            "name": "Claude Opus 4.6",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude 最新旗舰 (2026年)，最高智能等级，改进代码能力"
        },
        "claude-sonnet-4.6": {
            "name": "Claude Sonnet 4.6",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4.6 (2026年2月)，Opus 级智能，更快速度，1/5 成本"
        },
        "claude-sonnet-4.5": {
            "name": "Claude Sonnet 4.5",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4.5"
        },
        "claude-haiku-4.6": {
            "name": "Claude Haiku 4.6",
            "capabilities": ["chat"],
            "description": "Claude Haiku 4.6 快速版"
        },
        "claude-haiku-4.5": {
            "name": "Claude Haiku 4.5",
            "capabilities": ["chat"],
            "description": "Claude Haiku 4.5 经济版"
        },
        # 经典版本
        "claude-opus-4.5": {
            "name": "Claude Opus 4.5",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Opus 4.5 (建议使用 4.6)"
        },
        "claude-sonnet-4": {
            "name": "Claude Sonnet 4",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4"
        },
    },
    # AWS Bedrock (Claude 模型，使用 Bedrock 专用模型 ID)
    # 参考: https://platform.claude.com/docs/zh-CN/build-with-claude/claude-on-amazon-bedrock
    # 模型 ID 格式: us.anthropic.claude-opus-4-6-v1:0 (区域端点)
    #              anthropic.claude-opus-4-6-v1 (全局端点，无 us. 前缀)
    "bedrock": {
        # Claude Opus 4.6
        "us.anthropic.claude-opus-4-6-v1:0": {
            "name": "Claude Opus 4.6 (us-west-2)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Opus 4.6 美国区域端点（推荐用于数据驻留要求）"
        },
        "anthropic.claude-opus-4-6-v1": {
            "name": "Claude Opus 4.6 (Global)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Opus 4.6 全局端点，动态路由实现最大可用性"
        },
        # Claude Sonnet 4.6
        "us.anthropic.claude-sonnet-4-6": {
            "name": "Claude Sonnet 4.6 (us-west-2)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4.6 美国区域端点"
        },
        "anthropic.claude-sonnet-4-6": {
            "name": "Claude Sonnet 4.6 (Global)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4.6 全局端点"
        },
        # Claude Sonnet 4.5
        "us.anthropic.claude-sonnet-4-5-20250929-v1:0": {
            "name": "Claude Sonnet 4.5 (us-west-2)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4.5 美国区域端点"
        },
        "anthropic.claude-sonnet-4-5-20250929-v1:0": {
            "name": "Claude Sonnet 4.5 (Global)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4.5 全局端点"
        },
        # Claude Opus 4.5
        "us.anthropic.claude-opus-4-5-20251101-v1:0": {
            "name": "Claude Opus 4.5 (us-west-2)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Opus 4.5 美国区域端点"
        },
        "anthropic.claude-opus-4-5-20251101-v1:0": {
            "name": "Claude Opus 4.5 (Global)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Opus 4.5 全局端点"
        },
        # Claude Haiku 4.5
        "us.anthropic.claude-haiku-4-5-20251001-v1:0": {
            "name": "Claude Haiku 4.5 (us-west-2)",
            "capabilities": ["chat"],
            "description": "Claude Haiku 4.5 美国区域端点"
        },
        "anthropic.claude-haiku-4-5-20251001-v1:0": {
            "name": "Claude Haiku 4.5 (Global)",
            "capabilities": ["chat"],
            "description": "Claude Haiku 4.5 全局端点"
        },
        # Claude 3.5 Haiku (经典版本)
        "us.anthropic.claude-3-5-haiku-20241022-v1:0": {
            "name": "Claude 3.5 Haiku (us-west-2)",
            "capabilities": ["chat"],
            "description": "Claude 3.5 Haiku 美国区域端点"
        },
        # Claude Sonnet 4 (经典版本)
        "us.anthropic.claude-sonnet-4-20250514-v1:0": {
            "name": "Claude Sonnet 4 (us-west-2)",
            "capabilities": ["chat", "image", "code"],
            "description": "Claude Sonnet 4 美国区域端点"
        },
    },
    # Google Gemini (Gemini 3.1 系列 - 2026年3月最新)
    "google": {
        # Gemini 3.1 系列 (最新)
        "gemini-3.1-pro-preview": {
            "name": "Gemini 3.1 Pro Preview",
            "capabilities": ["chat", "image", "code"],
            "description": "Gemini 3.1 Pro (2026年3月最新)，推理优先，1M 上下文，原生多模态"
        },
        "gemini-3.1-flash-lite-preview": {
            "name": "Gemini 3.1 Flash-Lite Preview",
            "capabilities": ["chat", "code"],
            "description": "Gemini 3.1 Flash-Lite，2026年最快最便宜的模型"
        },
        # Gemini 2.5 系列
        "gemini-2.5-pro": {
            "name": "Gemini 2.5 Pro",
            "capabilities": ["chat", "image", "code"],
            "description": "Gemini 2.5 Pro，稳定可靠"
        },
        "gemini-2.5-flash": {
            "name": "Gemini 2.5 Flash",
            "capabilities": ["chat", "code"],
            "description": "Gemini 2.5 Flash"
        },
        # Gemini 2.0 系列 (2026年6月将退役)
        "gemini-2.0-flash": {
            "name": "Gemini 2.0 Flash",
            "capabilities": ["chat", "code"],
            "description": "Gemini 2.0 Flash (2026年6月1日将退役)"
        },
        "gemini-2.0-flash-lite": {
            "name": "Gemini 2.0 Flash-Lite",
            "capabilities": ["chat"],
            "description": "Gemini 2.0 Flash-Lite (2026年6月1日将退役)"
        },
        # 1.5 系列
        "gemini-1.5-pro": {
            "name": "Gemini 1.5 Pro",
            "capabilities": ["chat", "image", "code"],
            "description": "Gemini 1.5 Pro"
        },
        "gemini-1.5-flash": {
            "name": "Gemini 1.5 Flash",
            "capabilities": ["chat", "code"],
            "description": "Gemini 1.5 Flash"
        },
    },
}

# 能力类型定义
CAPABILITY_TYPES = {
    "chat": "文字对话",
    "image": "图片生成",
    "audio": "音频生成",
    "video": "视频生成",
}

# 所有能力的列表
ALL_CAPABILITIES = list(CAPABILITY_TYPES.keys())


def get_builtin_providers():
    """获取内置供应商列表"""
    return [
        {
            "code": code,
            "name": config["name"],
            "default_base_url": config["default_base_url"],
            "description": config.get("description", "")
        }
        for code, config in BUILTIN_PROVIDERS.items()
    ]


def get_builtin_models(provider_code: str = None):
    """获取内置模型列表"""
    if provider_code:
        models = BUILTIN_MODELS.get(provider_code, {})
        return [
            {
                "code": model_code,
                "name": config["name"],
                "capabilities": config["capabilities"],
                "description": config.get("description", "")
            }
            for model_code, config in models.items()
        ]

    # 返回所有模型
    result = []
    for provider_code, models in BUILTIN_MODELS.items():
        for model_code, config in models.items():
            result.append({
                "code": model_code,
                "provider_code": provider_code,
                "name": config["name"],
                "capabilities": config["capabilities"],
                "description": config.get("description", "")
            })
    return result


def validate_provider_code(provider_code: str) -> bool:
    """验证供应商代码是否有效"""
    return provider_code in BUILTIN_PROVIDERS


def validate_model_code(provider_code: str, model_code: str) -> bool:
    """验证模型代码是否有效"""
    if provider_code not in BUILTIN_MODELS:
        return False
    return model_code in BUILTIN_MODELS[provider_code]